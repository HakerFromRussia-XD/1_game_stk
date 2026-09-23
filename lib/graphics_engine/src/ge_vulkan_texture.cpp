#include "ge_vulkan_texture.hpp"

#include "ge_main.hpp"
#include "ge_mipmap_generator.hpp"
#include "ge_compressor_astc_4x4.hpp"
#include "ge_compressor_bptc_bc7.hpp"
#include "ge_compressor_s3tc_bc3.hpp"
#include "ge_texture.hpp"
#include "ge_vulkan_command_loader.hpp"
#include "ge_vulkan_features.hpp"
#include "ge_vulkan_driver.hpp"

extern "C"
{
    #include <mipmap/img.h>
    #include <mipmap/imgresize.h>
}

#include <cassert>
#include <cstring>
#include <cstdio>
#include <IAttributes.h>
#include <IImageLoader.h>
#include <IReadFile.h>
#include <limits>
#include <stdexcept>
#include <vector>

namespace GE
{
namespace
{
// ASTC stores its dimensions as little-endian 24-bit fields after a 16-byte
// header. iOS packaging keeps that header and replaces only the PNG/JPEG body.
constexpr uint8_t ASTC_MAGIC[] = { 0x13, 0xab, 0xa1, 0x5c };

uint32_t readASTC24(const uint8_t* value)
{
    return uint32_t(value[0]) | (uint32_t(value[1]) << 8) |
        (uint32_t(value[2]) << 16);
}

bool readASTC6x6(const io::path& path, core::dimension2du* size,
                 std::vector<uint8_t>* payload)
{
    io::IReadFile* file = io::createReadFile(path);
    if (!file)
        return false;

    uint8_t header[16] = {};
    const bool header_read = file->read(header, sizeof(header)) ==
        (s32)sizeof(header);
    if (!header_read || memcmp(header, ASTC_MAGIC, sizeof(ASTC_MAGIC)) != 0)
    {
        file->drop();
        return false;
    }

    const uint32_t width = readASTC24(header + 7);
    const uint32_t height = readASTC24(header + 10);
    const uint32_t depth = readASTC24(header + 13);
    const uint64_t payload_size = uint64_t((width + 5) / 6) *
        uint64_t((height + 5) / 6) * 16;
    const uint64_t expected_size = 16 + payload_size;
    const bool valid = header[4] == 6 && header[5] == 6 && header[6] == 1 &&
        width != 0 && height != 0 && depth == 1 &&
        expected_size == (uint64_t)file->getSize() &&
        payload_size <= std::numeric_limits<size_t>::max();
    if (!valid)
    {
        file->drop();
        return false;
    }

    payload->resize((size_t)payload_size);
    const bool payload_read = file->read(payload->data(),
        (s32)payload_size) == (s32)payload_size;
    file->drop();
    if (!payload_read)
    {
        payload->clear();
        return false;
    }
    *size = core::dimension2du(width, height);
    return true;
}
}   // anonymous namespace

GEVulkanTexture::GEVulkanTexture(const std::string& path,
                         std::function<void(video::IImage*)> image_mani)
               : video::ITexture(path.c_str()), m_image_mani(image_mani),
                 m_locked_data(NULL),
                 m_vulkan_device(getVKDriver()->getDevice()),
                 m_image(VK_NULL_HANDLE), m_vma_allocation(VK_NULL_HANDLE),
                 m_vma_info(), m_layer_count(1),
                 m_image_view_type(VK_IMAGE_VIEW_TYPE_2D),
                 m_disable_reload(false), m_has_mipmaps(true),
                 m_ondemand_load(false), m_ondemand_loading(false),
                 m_internal_format(VK_FORMAT_R8G8B8A8_UNORM),
                 m_vk(getVKDriver())
{
    core::dimension2du max_size = getDriver()->getDriverAttributes()
        .getAttributeAsDimension2d("MAX_TEXTURE_SIZE");
    m_full_path = getDriver()->getFileSystem()->getAbsolutePath(NamedPath);
    if (!getDriver()->getFileSystem()->existFileOnly(m_full_path))
    {
        LoadingFailed = true;
        return;
    }

    auto& paths = getGEConfig()->m_ondemand_load_texture_paths;
    auto path_itr = paths.find(m_full_path.c_str());
    m_ondemand_load = (path_itr != paths.end());
    if (m_ondemand_load)
    {
        paths.erase(path_itr);
        video::IImageLoader* loader = NULL;
        io::IReadFile* file = io::createReadFile(m_full_path);
        getDriver()->createImageFromFile(file, &loader);
        if (loader && loader->getImageSize(file, &m_orig_size))
        {
            m_size = getResizingTarget(m_orig_size, max_size);
            if (m_size.Width < 4 || m_size.Height < 4)
                m_has_mipmaps = false;
            setPlaceHolderView();
        }
        else
            LoadingFailed = true;
        file->drop();
        return;
    }

    m_size_lock.lock();
    m_image_view_lock.lock();
    m_thread_loading_lock.lock();
    GEVulkanCommandLoader::addMultiThreadingCommand(
        std::bind(&GEVulkanTexture::reloadInternal, this, max_size));
}   // GEVulkanTexture

// ----------------------------------------------------------------------------
GEVulkanTexture::GEVulkanTexture(video::IImage* img, const std::string& name)
               : video::ITexture(name.c_str()), m_image_mani(nullptr),
                 m_locked_data(NULL),
                 m_vulkan_device(getVKDriver()->getDevice()),
                 m_image(VK_NULL_HANDLE), m_vma_allocation(VK_NULL_HANDLE),
                 m_vma_info(), m_layer_count(1),
                 m_image_view_type(VK_IMAGE_VIEW_TYPE_2D),
                 m_disable_reload(true), m_has_mipmaps(true),
                 m_ondemand_load(false), m_ondemand_loading(false),
                 m_internal_format(VK_FORMAT_R8G8B8A8_UNORM),
                 m_vk(getVKDriver())
{
    if (!img)
    {
        LoadingFailed = true;
        return;
    }
    m_size = m_orig_size = img->getDimension();
    if (m_size.Width < 4 || m_size.Height < 4)
        m_has_mipmaps = false;
    uint8_t* data = (uint8_t*)img->lock();
    bgraConversion(data);
    upload(data, m_has_mipmaps/*generate_hq_mipmap*/);
    img->unlock();
    img->drop();
}   // GEVulkanTexture

// ----------------------------------------------------------------------------
GEVulkanTexture::GEVulkanTexture(const std::string& name, unsigned int size,
                                 bool single_channel)
           : video::ITexture(name.c_str()), m_image_mani(nullptr),
             m_locked_data(NULL), m_vulkan_device(getVKDriver()->getDevice()),
             m_image(VK_NULL_HANDLE), m_vma_allocation(VK_NULL_HANDLE),
             m_vma_info(), m_layer_count(1),
             m_image_view_type(VK_IMAGE_VIEW_TYPE_2D), m_disable_reload(true),
             m_has_mipmaps(true), m_ondemand_load(false),
             m_ondemand_loading(false), m_internal_format(single_channel ?
             VK_FORMAT_R8_UNORM : VK_FORMAT_R8G8B8A8_UNORM),
             m_vk(getVKDriver())
{
    if (isSingleChannel() && !GEVulkanFeatures::supportsR8Blit())
        m_has_mipmaps = false;
    else if (!isSingleChannel() && !GEVulkanFeatures::supportsRGBA8Blit())
        m_has_mipmaps = false;

    m_orig_size.Width = size;
    m_orig_size.Height = size;
    m_size = m_orig_size;

    std::vector<uint8_t> data;
    data.resize(size * size * (isSingleChannel() ? 1 : 4), 0);
    upload(data.data());
}   // GEVulkanTexture

// ----------------------------------------------------------------------------
GEVulkanTexture::~GEVulkanTexture()
{
    m_thread_loading_lock.lock();
    m_thread_loading_lock.unlock();

    if (m_image_view || m_image != VK_NULL_HANDLE ||
        m_vma_allocation != VK_NULL_HANDLE)
        m_vk->waitIdle();

    clearVulkanData();
}   // ~GEVulkanTexture

// ----------------------------------------------------------------------------
bool GEVulkanTexture::createTextureImage(uint8_t* texture_data,
                                         bool generate_hq_mipmap)
{
    VkDeviceSize mipmap_data_size = 0;
    GEMipmapGenerator* mipmap_generator = NULL;

    const bool precompressed_astc =
        m_internal_format == VK_FORMAT_ASTC_6x6_UNORM_BLOCK;
    unsigned channels = (isSingleChannel() ? 1 : 4);
    VkDeviceSize image_size = precompressed_astc ?
        VkDeviceSize((m_size.Width + 5) / 6) *
        VkDeviceSize((m_size.Height + 5) / 6) * 16 :
        VkDeviceSize(m_size.Width) * m_size.Height * channels;
    if (generate_hq_mipmap)
    {
        const bool normal_map = (std::string(NamedPath.getPtr()).find(
            "_Normal.") != std::string::npos);
        bool texture_compression = getGEConfig()->m_texture_compression;
        if (texture_compression && GEVulkanFeatures::supportsASTC4x4())
        {
            image_size = get4x4CompressedTextureSize(m_size.Width,
                m_size.Height);
            m_internal_format = VK_FORMAT_ASTC_4x4_UNORM_BLOCK;
            mipmap_generator = new GECompressorASTC4x4(texture_data, channels,
                m_size, normal_map);
        }
        else if (texture_compression && GEVulkanFeatures::supportsBPTCBC7())
        {
            image_size = get4x4CompressedTextureSize(m_size.Width,
                m_size.Height);
            m_internal_format = VK_FORMAT_BC7_UNORM_BLOCK;
            mipmap_generator = new GECompressorBPTCBC7(texture_data, channels,
                m_size, normal_map);
        }
        else if (texture_compression && GEVulkanFeatures::supportsS3TCBC3())
        {
            image_size = get4x4CompressedTextureSize(m_size.Width,
                m_size.Height);
            m_internal_format = VK_FORMAT_BC3_UNORM_BLOCK;
            mipmap_generator = new GECompressorS3TCBC3(texture_data, channels,
                m_size, normal_map);
        }
        else
        {
            m_internal_format = (isSingleChannel() ?
                VK_FORMAT_R8_UNORM : VK_FORMAT_R8G8B8A8_UNORM);
            mipmap_generator = new GEMipmapGenerator(texture_data, channels,
                m_size, normal_map);
        }
        mipmap_data_size = mipmap_generator->getMipmapSizes();
    }

    VkDeviceSize image_total_size = image_size + mipmap_data_size;
    VkBuffer staging_buffer;
    VmaAllocation staging_buffer_allocation;
    VmaAllocationCreateInfo staging_buffer_create_info = {};
    staging_buffer_create_info.usage = VMA_MEMORY_USAGE_AUTO_PREFER_HOST;
    staging_buffer_create_info.flags = VMA_ALLOCATION_CREATE_HOST_ACCESS_SEQUENTIAL_WRITE_BIT;
    staging_buffer_create_info.preferredFlags = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;

    bool success = m_vk->createBuffer(image_total_size,
        VK_BUFFER_USAGE_TRANSFER_SRC_BIT, staging_buffer_create_info,
        staging_buffer, staging_buffer_allocation);

    if (!success)
        return false;

    VkResult ret = VK_SUCCESS;
    uint8_t* data;
    VkCommandBuffer command_buffer = VK_NULL_HANDLE;
    if ((ret = vmaMapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation,
        (void**)&data)) != VK_SUCCESS)
        goto destroy;

    if (mipmap_generator)
    {
        for (GEImageLevel& level : mipmap_generator->getAllLevels())
        {
            memcpy(data, level.m_data, level.m_size);
            data += level.m_size;
        }
    }
    else
        memcpy(data, texture_data, image_size);
    vmaUnmapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation);
    vmaFlushAllocation(m_vk->getVmaAllocator(),
        staging_buffer_allocation, 0, image_total_size);

    success = createImage(VK_IMAGE_USAGE_TRANSFER_SRC_BIT |
        VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT);
    if (!success)
    {
        ret = VK_NOT_READY;
        goto destroy;
    }

    command_buffer = GEVulkanCommandLoader::beginSingleTimeCommands();

    transitionImageLayout(command_buffer, VK_IMAGE_LAYOUT_UNDEFINED,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);

    if (mipmap_generator)
    {
        unsigned offset = 0;
        std::vector<GEImageLevel>& levels = mipmap_generator->getAllLevels();
        for (unsigned i = 0; i < levels.size(); i++)
        {
            GEImageLevel& level = levels[i];
            copyBufferToImage(command_buffer, staging_buffer,
                level.m_dim.Width, level.m_dim.Height, 0, 0, offset, i, 0);
            offset += level.m_size;
        }
    }
    else
    {
        copyBufferToImage(command_buffer, staging_buffer, m_size.Width,
            m_size.Height, 0, 0, 0, 0, 0);
    }

    transitionImageLayout(command_buffer, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    GEVulkanCommandLoader::endSingleTimeCommands(command_buffer);

destroy:
    delete mipmap_generator;
    vmaDestroyBuffer(m_vk->getVmaAllocator(), staging_buffer,
        staging_buffer_allocation);
    return ret == VK_SUCCESS;
}   // createTextureImage

// ----------------------------------------------------------------------------
bool GEVulkanTexture::createImage(VkImageUsageFlags usage)
{
    VkImageCreateInfo image_info = {};
    image_info.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    image_info.imageType = VK_IMAGE_TYPE_2D;
    image_info.extent.width = m_size.Width;
    image_info.extent.height = m_size.Height;
    image_info.extent.depth = 1;
    image_info.mipLevels = getMipmapLevels();
    image_info.arrayLayers = m_layer_count;
    image_info.format = m_internal_format;
    image_info.tiling = VK_IMAGE_TILING_OPTIMAL;
    image_info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    image_info.usage = usage;
    image_info.samples = VK_SAMPLE_COUNT_1_BIT;
    image_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    if (m_image_view_type == VK_IMAGE_VIEW_TYPE_CUBE ||
        m_image_view_type == VK_IMAGE_VIEW_TYPE_CUBE_ARRAY)
        image_info.flags = VK_IMAGE_CREATE_CUBE_COMPATIBLE_BIT;
    if (m_internal_format != getSRGBformat(m_internal_format))
        image_info.flags |= VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT;

    m_vma_info = {};
    VmaAllocationCreateInfo alloc_info = {};
    alloc_info.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE;
    if ((usage & VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT) != 0)
        alloc_info.preferredFlags = VK_MEMORY_PROPERTY_LAZILY_ALLOCATED_BIT;
    VkResult result = vmaCreateImage(m_vk->getVmaAllocator(), &image_info,
        &alloc_info, &m_image, &m_vma_allocation, &m_vma_info);

    if (result != VK_SUCCESS)
        return false;

    return true;
}   // createImage

// ----------------------------------------------------------------------------
void GEVulkanTexture::transitionImageLayout(VkCommandBuffer command_buffer,
                                            VkImageLayout old_layout,
                                            VkImageLayout new_layout)
{
    VkImageMemoryBarrier barrier = {};
    barrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    barrier.oldLayout = old_layout;
    barrier.newLayout = new_layout;
    barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.image = m_image;
    barrier.subresourceRange.baseMipLevel = 0;
    barrier.subresourceRange.levelCount = getMipmapLevels();
    barrier.subresourceRange.baseArrayLayer = 0;
    barrier.subresourceRange.layerCount = m_layer_count;

    if (new_layout == VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)
    {
        barrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT;
    }
    else
    {
        barrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    }

    VkPipelineStageFlags source_stage;
    VkPipelineStageFlags destination_stage;

    if (old_layout == VK_IMAGE_LAYOUT_UNDEFINED &&
        new_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL)
    {
        barrier.srcAccessMask = 0;
        barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;

        source_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;
        destination_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL &&
        new_layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)
    {
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;

        source_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
        destination_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL &&
        new_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL)
    {
        barrier.srcAccessMask = VK_ACCESS_SHADER_READ_BIT;
        barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;

        source_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        destination_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL &&
        new_layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)
    {
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;

        source_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
        destination_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL &&
        new_layout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL)
    {
        barrier.srcAccessMask = VK_ACCESS_SHADER_READ_BIT;
        barrier.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;

        source_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
        destination_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_UNDEFINED &&
        new_layout == VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)
    {
        barrier.srcAccessMask = 0;
        barrier.dstAccessMask = VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
            VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;

        source_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;
        destination_stage = VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_UNDEFINED &&
        new_layout == VK_IMAGE_LAYOUT_GENERAL)
    {
        barrier.srcAccessMask = 0;
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;

        source_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;
        destination_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_UNDEFINED &&
        new_layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)
    {
        barrier.srcAccessMask = 0;
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;

        source_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;
        destination_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
    }
    else if (old_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL &&
        new_layout == VK_IMAGE_LAYOUT_GENERAL)
    {
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;

        source_stage = VK_PIPELINE_STAGE_TRANSFER_BIT;
        destination_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT;
    }
    else
    {
        return;
    }

    vkCmdPipelineBarrier(command_buffer, source_stage, destination_stage, 0, 0,
        NULL, 0, NULL, 1, &barrier);
}   // transitionImageLayout

// ----------------------------------------------------------------------------
void GEVulkanTexture::copyBufferToImage(VkCommandBuffer command_buffer,
                                        VkBuffer buffer, u32 w, u32 h, s32 x,
                                        s32 y, u32 offset, u32 mipmap_level,
                                        u32 layer_level)
{
    VkBufferImageCopy region = {};
    region.bufferOffset = offset;
    region.bufferRowLength = 0;
    region.bufferImageHeight = 0;
    region.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    region.imageSubresource.mipLevel = mipmap_level;
    region.imageSubresource.baseArrayLayer = layer_level;
    region.imageSubresource.layerCount = 1;
    region.imageOffset = {x, y, 0};
    region.imageExtent = {w, h, 1};

    vkCmdCopyBufferToImage(command_buffer, buffer, m_image,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);
}   // copyBufferToImage

// ----------------------------------------------------------------------------
bool GEVulkanTexture::createImageView(VkImageAspectFlags aspect_flags,
                                      bool create_srgb_view)
{
    VkImageViewCreateInfo view_info = {};
    view_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    view_info.image = m_image;
    view_info.viewType = m_image_view_type;
    view_info.format = m_internal_format;
    view_info.subresourceRange.aspectMask = aspect_flags;
    view_info.subresourceRange.baseMipLevel = 0;
    view_info.subresourceRange.levelCount = getMipmapLevels();
    view_info.subresourceRange.baseArrayLayer = 0;
    view_info.subresourceRange.layerCount = m_layer_count;
    if (isSingleChannel())
    {
        view_info.components.r = VK_COMPONENT_SWIZZLE_ONE;
        view_info.components.g = VK_COMPONENT_SWIZZLE_ONE;
        view_info.components.b = VK_COMPONENT_SWIZZLE_ONE;
        view_info.components.a = VK_COMPONENT_SWIZZLE_R;
    }

    auto image_view = std::make_shared<std::atomic<VkImageView> >();
    VkImageView view_ptr = VK_NULL_HANDLE;
    VkResult result = vkCreateImageView(m_vulkan_device, &view_info, NULL,
        &view_ptr);
    if (result == VK_SUCCESS)
    {
        image_view.get()->store(view_ptr);
        m_image_view = image_view;
        VkFormat srgb_format = getSRGBformat(m_internal_format);
        if (create_srgb_view && m_internal_format != srgb_format)
        {
            image_view = std::make_shared<std::atomic<VkImageView> >();
            view_info.format = srgb_format;
            view_ptr = VK_NULL_HANDLE;
            if (vkCreateImageView(m_vulkan_device, &view_info,
                NULL, &view_ptr) == VK_SUCCESS)
            {
                image_view.get()->store(view_ptr);
                m_image_view_srgb = image_view;
            }
        }

        if (m_placeholder_view)
            m_placeholder_view.get()->store(VK_NULL_HANDLE);
        m_ondemand_loading.store(false);
        return true;
    }
    else
    {
        m_ondemand_loading.store(false);
        return false;
    }
}   // createImageView

// ----------------------------------------------------------------------------
void GEVulkanTexture::clearVulkanData()
{
    if (m_image_view)
    {
        vkDestroyImageView(m_vulkan_device, m_image_view.get()->load(), NULL);
        m_image_view.get()->store(VK_NULL_HANDLE);
        m_image_view.reset();
        if (m_image_view_srgb)
        {
            vkDestroyImageView(m_vulkan_device,
                m_image_view_srgb.get()->load(), NULL);
            m_image_view_srgb.get()->store(VK_NULL_HANDLE);
            m_image_view_srgb.reset();
        }
    }
    if (m_image != VK_NULL_HANDLE)
    {
        vmaDestroyImage(m_vk->getVmaAllocator(), m_image, m_vma_allocation);
        m_image = VK_NULL_HANDLE;
        m_vma_allocation = VK_NULL_HANDLE;
        m_vma_info = {};
    }
}   // clearVulkanData

// ----------------------------------------------------------------------------
void GEVulkanTexture::reloadInternal(const core::dimension2du& max_size)
{
    // Callers lock these three mutexes before queueing this function.  Keep
    // their release exception-safe: a malformed texture must become a
    // missing/placeholder texture, never strand a loader or terminate iOS.
    bool size_locked = true;
    bool image_view_locked = true;
    bool loading_locked = true;
    const auto unlock_size = [&]()
    {
        if (size_locked)
        {
            m_size_lock.unlock();
            size_locked = false;
        }
    };
    const auto unlock_image_view = [&]()
    {
        if (image_view_locked)
        {
            m_image_view_lock.unlock();
            image_view_locked = false;
        }
    };
    const auto unlock_loading = [&]()
    {
        if (loading_locked)
        {
            m_thread_loading_lock.unlock();
            loading_locked = false;
        }
    };
    const auto unlock_all = [&]()
    {
        unlock_size();
        unlock_image_view();
        unlock_loading();
    };

    try
    {
        if (m_disable_reload)
        {
            unlock_all();
            return;
        }

        clearVulkanData();

        core::dimension2du astc_size;
        std::vector<uint8_t> astc_payload;
        if (readASTC6x6(m_full_path, &astc_size, &astc_payload))
        {
            if (m_image_mani || !GEVulkanFeatures::supportsASTC6x6() ||
                astc_size.Width > max_size.Width || astc_size.Height > max_size.Height)
            {
                printf("Unsupported raw ASTC 6x6 texture: %s\n",
                    m_full_path.c_str());
                m_ondemand_loading.store(false);
                unlock_all();
                return;
            }

            m_orig_size = m_size = astc_size;
            // The package contains one ASTC level. Vulkan must not advertise
            // generated levels that have no compressed data behind them.
            m_has_mipmaps = false;
            m_internal_format = VK_FORMAT_ASTC_6x6_UNORM_BLOCK;
            unlock_size();
            const bool uploaded = createTextureImage(astc_payload.data(), false) &&
                createImageView(VK_IMAGE_ASPECT_COLOR_BIT);
            unlock_image_view();
            unlock_loading();
            if (!uploaded)
                printf("Could not upload raw ASTC 6x6 texture: %s\n",
                    m_full_path.c_str());
            return;
        }

        video::IImage* texture_image = getResizedImageFullPath(m_full_path,
            max_size, &m_orig_size);
        if (texture_image == NULL)
        {
            printf("Missing texture_image in getResizedImageFullPath%s for %s\n",
                m_ondemand_load ? " during ondemand loading" : "",
                m_full_path.c_str());
            m_ondemand_loading.store(false);
            unlock_all();
            return;
        }

        m_size = texture_image->getDimension();
        if (m_size.Width < 4 || m_size.Height < 4)
            m_has_mipmaps = false;
        else
            m_has_mipmaps = true;
        unlock_size();

        if (m_image_mani)
            m_image_mani(texture_image);

        uint8_t* data = (uint8_t*)texture_image->lock();
        bgraConversion(data);
        upload(data, m_has_mipmaps/*generate_hq_mipmap*/);
        unlock_image_view();

        texture_image->unlock();
        texture_image->drop();
        unlock_loading();
    }
    catch (const std::exception& e)
    {
        printf("Texture load failed for %s: %s\n", m_full_path.c_str(),
            e.what());
        m_ondemand_loading.store(false);
        unlock_all();
    }
    catch (...)
    {
        printf("Texture load failed for %s: unknown exception\n",
            m_full_path.c_str());
        m_ondemand_loading.store(false);
        unlock_all();
    }
}   // reloadInternal

// ----------------------------------------------------------------------------
void GEVulkanTexture::upload(uint8_t* data, bool generate_hq_mipmap)
{
    if (!createTextureImage(data, generate_hq_mipmap))
    {
        m_ondemand_loading.store(false);
        return;
    }
    if (!createImageView(VK_IMAGE_ASPECT_COLOR_BIT))
        return;
}   // upload

// ----------------------------------------------------------------------------
void* GEVulkanTexture::lock(video::E_TEXTURE_LOCK_MODE mode, u32 mipmap_level)
{
    uint8_t* texture_data = getTextureData();
    if (!texture_data)
        return NULL;
    if (isSingleChannel())
    {
        m_locked_data = new uint8_t[m_size.Width * m_size.Height * 4]();
        for (unsigned int i = 0; i < m_size.Width * m_size.Height; i++)
        {
            m_locked_data[i * 4 + 2] = texture_data[i];
            m_locked_data[i * 4 + 3] = 255;
        }
        delete [] texture_data;
        return m_locked_data;
    }
    else
    {
        m_locked_data = texture_data;
        bgraConversion(m_locked_data);
        return m_locked_data;
    }
}   // lock

// ----------------------------------------------------------------------------
uint8_t* GEVulkanTexture::getTextureData()
{
    if (m_internal_format != VK_FORMAT_R8G8B8A8_UNORM &&
        m_internal_format != VK_FORMAT_R8_UNORM)
    {
        if (m_full_path.empty())
            return NULL;

        const core::dimension2du& max_size = getDriver()->getDriverAttributes()
            .getAttributeAsDimension2d("MAX_TEXTURE_SIZE");
        video::IImage* texture_image = getResizedImageFullPath(m_full_path,
            max_size, NULL, &m_size);
        if (texture_image == NULL)
            return NULL;
        texture_image->setDeleteMemory(false);
        uint8_t* data = (uint8_t*)texture_image->lock();
        texture_image->drop();
        return data;
    }

    if (!waitImageView())
        return NULL;

    VkBuffer buffer;
    VmaAllocation buffer_allocation;
    VkDeviceSize image_size =
        m_size.Width * m_size.Height * (isSingleChannel() ? 1 : 4);
    VmaAllocationCreateInfo buffer_create_info = {};
    buffer_create_info.usage = VMA_MEMORY_USAGE_AUTO;
    buffer_create_info.flags = VMA_ALLOCATION_CREATE_HOST_ACCESS_RANDOM_BIT;
    buffer_create_info.preferredFlags = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;

    if (!m_vk->createBuffer(image_size,
        VK_BUFFER_USAGE_TRANSFER_DST_BIT, buffer_create_info, buffer,
        buffer_allocation))
        return NULL;

    VkCommandBuffer command_buffer = GEVulkanCommandLoader::beginSingleTimeCommands();

    transitionImageLayout(command_buffer,
        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);

    VkBufferImageCopy region = {};
    region.bufferOffset = 0;
    region.bufferRowLength = 0;
    region.bufferImageHeight = 0;
    region.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    region.imageSubresource.mipLevel = 0;
    region.imageSubresource.baseArrayLayer = 0;
    region.imageSubresource.layerCount = 1;
    region.imageOffset = {0, 0, 0};
    region.imageExtent = {m_size.Width, m_size.Height, 1};

    vkCmdCopyImageToBuffer(command_buffer, m_image,
        VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, buffer, 1, &region);

    transitionImageLayout(command_buffer, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    GEVulkanCommandLoader::endSingleTimeCommands(command_buffer);

    uint8_t* texture_data = new uint8_t[image_size];
    void* mapped_data;
    if (vmaMapMemory(m_vk->getVmaAllocator(), buffer_allocation,
        &mapped_data) != VK_SUCCESS)
    {
        delete [] texture_data;
        texture_data = NULL;
        goto cleanup;
    }

    vmaInvalidateAllocation(m_vk->getVmaAllocator(), buffer_allocation,
        0, image_size);
    memcpy(texture_data, mapped_data, image_size);
    vmaUnmapMemory(m_vk->getVmaAllocator(), buffer_allocation);

cleanup:
    vmaDestroyBuffer(m_vk->getVmaAllocator(), buffer, buffer_allocation);
    return texture_data;
}   // getTextureData

//-----------------------------------------------------------------------------
void GEVulkanTexture::updateTexture(void* data, video::ECOLOR_FORMAT format,
                                    u32 w, u32 h, u32 x, u32 y)
{
    if (!waitImageView())
        return;

    VkBuffer staging_buffer;
    VmaAllocation staging_buffer_allocation;
    VmaAllocationCreateInfo staging_buffer_create_info = {};
    staging_buffer_create_info.usage = VMA_MEMORY_USAGE_AUTO_PREFER_HOST;
    staging_buffer_create_info.flags = VMA_ALLOCATION_CREATE_HOST_ACCESS_SEQUENTIAL_WRITE_BIT;
    staging_buffer_create_info.preferredFlags = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
    if (isSingleChannel())
    {
        if (format == video::ECF_R8)
        {
            unsigned image_size = w * h;
            if (!m_vk->createBuffer(image_size,
                VK_BUFFER_USAGE_TRANSFER_SRC_BIT, staging_buffer_create_info,
                staging_buffer, staging_buffer_allocation))
                return;

            void* mapped_data;
            vmaMapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation,
                &mapped_data);
            memcpy(mapped_data, data, (size_t)(image_size));
            vmaUnmapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation);
            vmaFlushAllocation(m_vk->getVmaAllocator(),
                staging_buffer_allocation, 0, image_size);
        }
    }
    else
    {
        if (format == video::ECF_R8)
        {
            unsigned image_size = w * h * 4;
            if (!m_vk->createBuffer(w * h * 4,
                VK_BUFFER_USAGE_TRANSFER_SRC_BIT, staging_buffer_create_info,
                staging_buffer, staging_buffer_allocation))
                return;

            const unsigned int size = w * h;
            std::vector<uint8_t> image_data(size * 4, 255);
            uint8_t* orig_data = (uint8_t*)data;
            for (unsigned int i = 0; i < size; i++)
                image_data[4 * i + 3] = orig_data[i];
            void* mapped_data;
            vmaMapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation,
                &mapped_data);
            memcpy(mapped_data, image_data.data(), (size_t)(image_size));
            vmaUnmapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation);
            vmaFlushAllocation(m_vk->getVmaAllocator(),
                staging_buffer_allocation, 0, image_size);
        }
        else if (format == video::ECF_A8R8G8B8)
        {
            unsigned image_size = w * h * 4;
            if (!m_vk->createBuffer(w * h * 4,
                VK_BUFFER_USAGE_TRANSFER_SRC_BIT, staging_buffer_create_info,
                staging_buffer, staging_buffer_allocation))
                return;

            uint8_t* u8_data = (uint8_t*)data;
            for (unsigned int i = 0; i < w * h; i++)
            {
                uint8_t tmp_val = u8_data[i * 4];
                u8_data[i * 4] = u8_data[i * 4 + 2];
                u8_data[i * 4 + 2] = tmp_val;
            }
            void* mapped_data;
            vmaMapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation,
                &mapped_data);
            memcpy(mapped_data, u8_data, (size_t)(image_size));
            vmaUnmapMemory(m_vk->getVmaAllocator(), staging_buffer_allocation);
            vmaFlushAllocation(m_vk->getVmaAllocator(),
                staging_buffer_allocation, 0, image_size);
        }
    }

    VkCommandBuffer command_buffer = GEVulkanCommandLoader::beginSingleTimeCommands();
    transitionImageLayout(command_buffer,
        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
        VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    copyBufferToImage(command_buffer, staging_buffer, w, h, x, y, 0, 0, 0);

    bool blit_mipmap = true;
    if (isSingleChannel() && !GEVulkanFeatures::supportsR8Blit())
        blit_mipmap = false;
    else if (!isSingleChannel() && !GEVulkanFeatures::supportsRGBA8Blit())
        blit_mipmap = false;
    if (blit_mipmap)
    {
        VkImageMemoryBarrier barrier = {};
        barrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        barrier.image = m_image;
        barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        barrier.subresourceRange.baseArrayLayer = 0;
        barrier.subresourceRange.layerCount = 1;
        barrier.subresourceRange.levelCount = 1;

        int mip_width = m_size.Width;
        int mip_height = m_size.Height;
        unsigned mip_levels = getMipmapLevels();

        for (unsigned i = 1; i < mip_levels; i++)
        {
            barrier.subresourceRange.baseMipLevel = i - 1;
            barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            barrier.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;

            vkCmdPipelineBarrier(command_buffer,
                VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                0, 0, NULL, 0, NULL, 1, &barrier);

            VkImageBlit blit{};
            blit.srcOffsets[0] = {0, 0, 0};
            blit.srcOffsets[1] = {mip_width, mip_height, 1};
            blit.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            blit.srcSubresource.mipLevel = i - 1;
            blit.srcSubresource.baseArrayLayer = 0;
            blit.srcSubresource.layerCount = 1;
            blit.dstOffsets[0] = {0, 0, 0};
            blit.dstOffsets[1] =
            {
                mip_width > 1 ? mip_width / 2 : 1,
                mip_height > 1 ? mip_height / 2 : 1,
                1
            };
            blit.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            blit.dstSubresource.mipLevel = i;
            blit.dstSubresource.baseArrayLayer = 0;
            blit.dstSubresource.layerCount = 1;

            vkCmdBlitImage(command_buffer,
                m_image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                m_image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &blit,
                VK_FILTER_LINEAR);

            barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            barrier.srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
            barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;

            vkCmdPipelineBarrier(command_buffer,
                VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0, NULL, 1,
                &barrier);

            if (mip_width > 1) mip_width /= 2;
            if (mip_height > 1) mip_height /= 2;
        }
    }

    transitionImageLayout(command_buffer, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);
    GEVulkanCommandLoader::endSingleTimeCommands(command_buffer);

    vmaDestroyBuffer(m_vk->getVmaAllocator(), staging_buffer,
        staging_buffer_allocation);
}   // updateTexture

//-----------------------------------------------------------------------------
void GEVulkanTexture::bgraConversion(uint8_t* img_data)
{
    for (unsigned int i = 0; i < m_size.Width * m_size.Height; i++)
    {
        uint8_t tmp_val = img_data[i * 4];
        img_data[i * 4] = img_data[i * 4 + 2];
        img_data[i * 4 + 2] = tmp_val;
    }
}   // bgraConversion

//-----------------------------------------------------------------------------
void GEVulkanTexture::reload()
{
    // Copied from waitImageView
    if (!m_ondemand_load)
    {
        m_image_view_lock.lock();
        m_image_view_lock.unlock();
    }
    else
    {
        bool is_currently_loading = m_ondemand_loading.load();
        if (is_currently_loading || m_image == VK_NULL_HANDLE)
            return;
    }

    if (m_image_view || m_image != VK_NULL_HANDLE ||
        m_vma_allocation != VK_NULL_HANDLE)
        m_vk->waitIdle();

    if (m_ondemand_load)
    {
        clearVulkanData();
        setPlaceHolderView();
    }
    else if (!m_disable_reload)
    {
        core::dimension2du max_size = getDriver()->getDriverAttributes()
            .getAttributeAsDimension2d("MAX_TEXTURE_SIZE");
        m_size_lock.lock();
        m_image_view_lock.lock();
        m_thread_loading_lock.lock();
        GEVulkanCommandLoader::addMultiThreadingCommand(
            std::bind(&GEVulkanTexture::reloadInternal, this, max_size));
    }
}   // reload

//-----------------------------------------------------------------------------
void GEVulkanTexture::setPlaceHolderView()
{
    auto tex = static_cast<GEVulkanTexture*>(m_vk->getTransparentTexture());
    auto image_view = std::make_shared<std::atomic<VkImageView> >();
    image_view.get()->store((VkImageView)tex->getTextureHandler());
    if (m_placeholder_view)
        m_placeholder_view.get()->store(VK_NULL_HANDLE);
    m_placeholder_view = image_view;
}   // setPlaceHolderView

//-----------------------------------------------------------------------------
std::shared_ptr<std::atomic<VkImageView> > GEVulkanTexture::getImageViewLive(
                                                               bool srgb) const
{
    assert(m_ondemand_load && m_placeholder_view);
    if (m_ondemand_loading.load() == false)
    {
        if (m_image_view)
        {
            if (srgb && m_image_view_srgb)
                return m_image_view_srgb;
            else
                return m_image_view;
        }
        else
        {
            GEVulkanTexture* tex = const_cast<GEVulkanTexture*>(this);
            core::dimension2du max_size = getDriver()->getDriverAttributes()
                .getAttributeAsDimension2d("MAX_TEXTURE_SIZE");
            tex->m_thread_loading_lock.lock();
            tex->m_ondemand_loading.store(true);
            GEVulkanCommandLoader::addMultiThreadingCommand(
                std::bind(&GEVulkanTexture::reloadInternal, tex, max_size));
            return m_placeholder_view;
        }
    }
    return m_placeholder_view;
}   // getImageViewLive

}

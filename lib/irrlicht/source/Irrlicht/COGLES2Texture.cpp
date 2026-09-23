// Copyright (C) 2013 Patryk Nadrowski
// Heavily based on the OpenGL driver implemented by Nikolaus Gebhardt
// OpenGL ES driver implemented by Christian Stehno and first OpenGL ES 2.0
// driver implemented by Amundis.
// This file is part of the "Irrlicht Engine".
// For conditions of distribution and use, see copyright notice in Irrlicht.h

#include "IrrCompileConfig.h"

#ifdef _IRR_COMPILE_WITH_OGLES2_

#include "irrTypes.h"
#include "COGLES2Texture.h"
#include "COGLES2Driver.h"
#include "os.h"
#include "CImage.h"
#include "CColorConverter.h"
#include "IAttributes.h"
#include "IrrlichtDevice.h"
#include "IReadFile.h"

#include "irrString.h"

#include <algorithm>
#include <cstring>
#include <vector>

#ifdef ENABLE_LIBASTCENC
#include <astcenc.h>
#endif

#ifndef IOS_FLUXARA_DRIFT
#include <GLES2/gl2.h>
#include <GLES2/gl2ext.h>
#include <EGL/egl.h>
#endif

namespace
{
#ifndef GL_BGRA
// we need to do this for the IMG_BGRA8888 extension
int GL_BGRA=GL_RGBA;
#endif
}

namespace irr
{
namespace video
{

namespace
{
const u8 ASTC_MAGIC[4] = { 0x13, 0xab, 0xa1, 0x5c };

u32 astcRead24(const u8* bytes)
{
	return (u32)bytes[0] | ((u32)bytes[1] << 8) | ((u32)bytes[2] << 16);
}

GLenum astcFormat(u8 block_x, u8 block_y)
{
	if (block_x == 6 && block_y == 6)
		return GL_COMPRESSED_RGBA_ASTC_6x6_KHR;
	return 0;
}
}

// ---------------------------------------------------------------------------
ITexture* COGLES2Texture::createASTCTexture(io::IReadFile* file,
	const io::path& name, COGLES2Driver* driver)
{
	if (!file || !driver)
		return 0;

	u8 header[16];
	file->seek(0);
	if (file->read(header, sizeof(header)) != sizeof(header) ||
		memcmp(header, ASTC_MAGIC, sizeof(ASTC_MAGIC)) != 0)
		return 0;

	const u8 block_x = header[4];
	const u8 block_y = header[5];
	const u8 block_z = header[6];
	const u32 width = astcRead24(header + 7);
	const u32 height = astcRead24(header + 10);
	const u32 depth = astcRead24(header + 13);
	const GLenum format = astcFormat(block_x, block_y);
	if (!format || block_z != 1 || depth != 1 || width == 0 || height == 0 ||
		width > driver->MaxTextureSize || height > driver->MaxTextureSize)
		return 0;

	const u32 block_count_x = (width + block_x - 1) / block_x;
	const u32 block_count_y = (height + block_y - 1) / block_y;
	const u32 compressed_size = block_count_x * block_count_y * 16;
	if (file->getSize() != (long)(sizeof(header) + compressed_size))
		return 0;

	std::vector<u8> payload(compressed_size);
	if (file->read(payload.data(), compressed_size) != (s32)compressed_size)
		return 0;

	if (!driver->queryOpenGLFeature(COGLES2ExtensionHandler::IRR_KHR_texture_compression_astc_ldr))
	{
#ifdef ENABLE_LIBASTCENC
		astcenc_config config;
		if (astcenc_config_init(ASTCENC_PRF_LDR, block_x, block_y, block_z,
			ASTCENC_PRE_FASTEST, 0, &config) != ASTCENC_SUCCESS)
			return 0;
		astcenc_context* context = 0;
		if (astcenc_context_alloc(&config, 1, &context) != ASTCENC_SUCCESS)
			return 0;

		std::vector<u8> decoded(width * height * 4);
		void* image_data[1] = { decoded.data() };
		astcenc_image image = { width, height, 1, ASTCENC_TYPE_U8, image_data };
		astcenc_swizzle swizzle = { ASTCENC_SWZ_R, ASTCENC_SWZ_G,
			ASTCENC_SWZ_B, ASTCENC_SWZ_A };
		const astcenc_error result = astcenc_decompress_image(context, payload.data(),
			compressed_size, &image, &swizzle, 0);
		astcenc_context_free(context);
		if (result != ASTCENC_SUCCESS)
			return 0;

		// Irrlicht's A8R8G8B8 memory layout is BGRA on little-endian iOS.
		for (u32 offset = 0; offset < decoded.size(); offset += 4)
			std::swap(decoded[offset], decoded[offset + 2]);
		IImage* software_image = driver->createImageFromData(ECF_A8R8G8B8,
			core::dimension2du(width, height), decoded.data(), false);
		if (!software_image)
			return 0;
		ITexture* texture = new COGLES2Texture(software_image, name, 0, driver);
		software_image->drop();
		os::Printer::log("Loaded ASTC texture through software fallback", file->getFileName());
		return texture;
#else
		return 0;
#endif
	}

	COGLES2Texture* texture = new COGLES2Texture(name, driver);
	texture->ImageSize = core::dimension2du(width, height);
	texture->TextureSize = texture->ImageSize;
	texture->ColorFormat = ECF_A8R8G8B8;
	texture->HasMipMaps = driver->getTextureCreationFlag(ETCF_CREATE_MIP_MAPS);
	texture->AutomaticMipmapUpdate = false;
	texture->InternalFormat = format;
	texture->PixelFormat = GL_RGBA;
	texture->PixelType = GL_UNSIGNED_BYTE;

	glGenTextures(1, &texture->TextureName);
	driver->setActiveTexture(0, texture);
	driver->getBridgeCalls()->setTexture(0);
	glCompressedTexImage2D(GL_TEXTURE_2D, 0, format, width, height, 0,
		compressed_size, payload.data());
	if (!driver->testGLError() && texture->HasMipMaps)
	{
		// Preserve the original loader's mip behaviour without retaining an
		// uncompressed source image in the bundle. iOS generates the lower
		// levels on the GPU from the ASTC base level.
		glGenerateMipmap(GL_TEXTURE_2D);
		if (driver->testGLError())
			texture->HasMipMaps = false;
	}
	if (texture->HasMipMaps)
	{
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
			GL_LINEAR_MIPMAP_NEAREST);
		texture->StatesCache.MipMapStatus = true;
	}
	else
	{
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		texture->StatesCache.MipMapStatus = false;
	}
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	texture->StatesCache.BilinearFilter = true;
	texture->StatesCache.TrilinearFilter = false;
	if (driver->testGLError())
	{
		texture->drop();
		return 0;
	}

	os::Printer::log("Loaded ASTC texture", file->getFileName());
	return texture;
}

//! constructor for usual textures
COGLES2Texture::COGLES2Texture(IImage* origImage, const io::path& name, void* mipmapData, COGLES2Driver* driver)
	: ITexture(name), ColorFormat(ECF_A8R8G8B8), Driver(driver), Image(0), MipImage(0),
	TextureName(0), InternalFormat(GL_RGBA), PixelFormat(GL_BGRA_EXT),
	PixelType(GL_UNSIGNED_BYTE), MipLevelStored(0),
	IsRenderTarget(false), AutomaticMipmapUpdate(false),
	ReadOnlyLock(false), KeepImage(true)
{
	#ifdef _DEBUG
	setDebugName("COGLES2Texture");
	#endif

	HasMipMaps = Driver->getTextureCreationFlag(ETCF_CREATE_MIP_MAPS);
	getImageValues(origImage);

	glGenTextures(1, &TextureName);

	if (ImageSize==TextureSize)
	{
		Image = Driver->createImage(ColorFormat, ImageSize);
		origImage->copyTo(Image);
	}
	else
	{
		Image = Driver->createImage(ColorFormat, TextureSize);
		// scale texture
		origImage->copyToScaling(Image);
	}
	uploadTexture(true, mipmapData);
	if (!KeepImage)
	{
		Image->drop();
		Image=0;
	}
}


//! constructor for basic setup (only for derived classes)
COGLES2Texture::COGLES2Texture(const io::path& name, COGLES2Driver* driver)
	: ITexture(name), ColorFormat(ECF_A8R8G8B8), Driver(driver), Image(0), MipImage(0),
	TextureName(0), InternalFormat(GL_RGBA), PixelFormat(GL_BGRA_EXT),
	PixelType(GL_UNSIGNED_BYTE), MipLevelStored(0), HasMipMaps(true),
	IsRenderTarget(false), AutomaticMipmapUpdate(false),
	ReadOnlyLock(false), KeepImage(true)
{
	#ifdef _DEBUG
	setDebugName("COGLES2Texture");
	#endif
}


//! destructor
COGLES2Texture::~COGLES2Texture()
{
	if (TextureName)
		glDeleteTextures(1, &TextureName);
	if (Image)
		Image->drop();
}


//! Choose best matching color format, based on texture creation flags
ECOLOR_FORMAT COGLES2Texture::getBestColorFormat(ECOLOR_FORMAT format)
{
	ECOLOR_FORMAT destFormat = ECF_A8R8G8B8;
	switch (format)
	{
		case ECF_A1R5G5B5:
			if (!Driver->getTextureCreationFlag(ETCF_ALWAYS_32_BIT))
				destFormat = ECF_A1R5G5B5;
		break;
		case ECF_R5G6B5:
			if (!Driver->getTextureCreationFlag(ETCF_ALWAYS_32_BIT))
				destFormat = ECF_A1R5G5B5;
		break;
		case ECF_A8R8G8B8:
			if (Driver->getTextureCreationFlag(ETCF_ALWAYS_16_BIT) ||
					Driver->getTextureCreationFlag(ETCF_OPTIMIZED_FOR_SPEED))
				destFormat = ECF_A1R5G5B5;
		break;
		case ECF_R8G8B8:
			if (Driver->getTextureCreationFlag(ETCF_ALWAYS_16_BIT) ||
					Driver->getTextureCreationFlag(ETCF_OPTIMIZED_FOR_SPEED))
				destFormat = ECF_A1R5G5B5;
		default:
		break;
	}
	if (Driver->getTextureCreationFlag(ETCF_NO_ALPHA_CHANNEL))
	{
		switch (destFormat)
		{
			case ECF_A1R5G5B5:
				destFormat = ECF_R5G6B5;
			break;
			case ECF_A8R8G8B8:
				destFormat = ECF_R8G8B8;
			break;
			default:
			break;
		}
	}
	return destFormat;
}


// prepare values ImageSize, TextureSize, and ColorFormat based on image
void COGLES2Texture::getImageValues(IImage* image)
{
	if (!image)
	{
		os::Printer::log("No image for OpenGL texture.", ELL_ERROR);
		return;
	}

	ImageSize = image->getDimension();

	if ( !ImageSize.Width || !ImageSize.Height)
	{
		os::Printer::log("Invalid size of image for OpenGL Texture.", ELL_ERROR);
		return;
	}

	const f32 ratio = (f32)ImageSize.Width/(f32)ImageSize.Height;
	if ((ImageSize.Width>Driver->MaxTextureSize) && (ratio >= 1.0f))
	{
		ImageSize.Width = Driver->MaxTextureSize;
		ImageSize.Height = (u32)(Driver->MaxTextureSize/ratio);
	}
	else if (ImageSize.Height>Driver->MaxTextureSize)
	{
		ImageSize.Height = Driver->MaxTextureSize;
		ImageSize.Width = (u32)(Driver->MaxTextureSize*ratio);
	}
	TextureSize=ImageSize.getOptimalSize(false);
    const core::dimension2du max_size = Driver->getDriverAttributes()
                                 .getAttributeAsDimension2d("MAX_TEXTURE_SIZE");

    if (max_size.Width> 0 && TextureSize.Width > max_size.Width)
    {
        TextureSize.Width = max_size.Width;
    }
    if (max_size.Height> 0 && TextureSize.Height > max_size.Height)
    {
        TextureSize.Height = max_size.Height;
    }

	ColorFormat = getBestColorFormat(image->getColorFormat());
}


//! copies the the texture into an open gl texture.
void COGLES2Texture::uploadTexture(bool newTexture, void* mipmapData, u32 level)
{
	// check which image needs to be uploaded
	IImage* image = level?MipImage:Image;
	if (!image)
	{
		os::Printer::log("No image for OGLES2 texture to upload", ELL_ERROR);
		return;
	}

#ifndef GL_BGRA
	// whoa, pretty badly implemented extension...
	if (Driver->FeatureAvailable[COGLES2ExtensionHandler::IRR_IMG_texture_format_BGRA8888] || Driver->FeatureAvailable[COGLES2ExtensionHandler::IRR_EXT_texture_format_BGRA8888])
		GL_BGRA=0x80E1;
	else
		GL_BGRA=GL_RGBA;
#endif

	GLenum oldInternalFormat = InternalFormat;
	void(*convert)(const void*, s32, void*)=0;
	switch (Image->getColorFormat())
	{
		case ECF_A1R5G5B5:
			InternalFormat=GL_RGBA;
			PixelFormat=GL_RGBA;
			PixelType=GL_UNSIGNED_SHORT_5_5_5_1;
			convert=CColorConverter::convert_A1R5G5B5toR5G5B5A1;
			break;
		case ECF_R5G6B5:
			InternalFormat=GL_RGB;
			PixelFormat=GL_RGB;
			PixelType=GL_UNSIGNED_SHORT_5_6_5;
			break;
		case ECF_R8G8B8:
			InternalFormat=GL_RGB;
			PixelFormat=GL_RGB;
			PixelType=GL_UNSIGNED_BYTE;
			convert=CColorConverter::convert_R8G8B8toB8G8R8;
			break;
		case ECF_A8R8G8B8:
			PixelType=GL_UNSIGNED_BYTE;
			if (!Driver->queryOpenGLFeature(COGLES2ExtensionHandler::IRR_IMG_texture_format_BGRA8888) && !Driver->queryOpenGLFeature(COGLES2ExtensionHandler::IRR_EXT_texture_format_BGRA8888))
			{
				convert=CColorConverter::convert_A8R8G8B8toA8B8G8R8;
				InternalFormat=GL_RGBA;
				PixelFormat=GL_RGBA;
			}
			else
			{
				InternalFormat=GL_BGRA;
				PixelFormat=GL_BGRA;
			}
			break;
		default:
			os::Printer::log("Unsupported texture format", ELL_ERROR);
			break;
	}
	// Hack for iPhone SDK, which requires a different InternalFormat
#ifdef _IRR_IOS_PLATFORM_
	if (InternalFormat==GL_BGRA)
		InternalFormat=GL_RGBA;
#endif
	// make sure we don't change the internal format of existing matrices
	if (!newTexture)
		InternalFormat=oldInternalFormat;

    Driver->setActiveTexture(0, this);
	Driver->getBridgeCalls()->setTexture(0);

	if (Driver->testGLError())
		os::Printer::log("Could not bind Texture", ELL_ERROR);

	// mipmap handling for main texture
	if (!level && newTexture)
	{
#ifndef DISABLE_MIPMAPPING
		// auto generate if possible and no mipmap data is given
		if (HasMipMaps && !mipmapData)
		{
			if (Driver->getTextureCreationFlag(ETCF_OPTIMIZED_FOR_SPEED))
				glHint(GL_GENERATE_MIPMAP_HINT, GL_FASTEST);
			else if (Driver->getTextureCreationFlag(ETCF_OPTIMIZED_FOR_QUALITY))
				glHint(GL_GENERATE_MIPMAP_HINT, GL_NICEST);
			else
				glHint(GL_GENERATE_MIPMAP_HINT, GL_DONT_CARE);

			AutomaticMipmapUpdate=true;
		}
		else
		{
			// Either generate manually due to missing capability
			// or use predefined mipmap data
			AutomaticMipmapUpdate=false;
			regenerateMipMapLevels(mipmapData);
		}

		if (HasMipMaps) // might have changed in regenerateMipMapLevels
		{
			// enable bilinear mipmap filter
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

            StatesCache.BilinearFilter = true;
            StatesCache.TrilinearFilter = false;
            StatesCache.MipMapStatus = true;
		}
		else
#else
			HasMipMaps=false;
			os::Printer::log("Did not create OpenGL texture mip maps.", ELL_INFORMATION);
#endif
		{
			// enable bilinear filter without mipmaps
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

            StatesCache.BilinearFilter = true;
            StatesCache.TrilinearFilter = false;
            StatesCache.MipMapStatus = false;
		}
	}

	// now get image data and upload to GPU
	void* source = image->lock();
	IImage* tmpImage=0;

	if (convert)
	{
		tmpImage = new CImage(image->getColorFormat(), image->getDimension());
		void* dest = tmpImage->lock();
		convert(source, image->getDimension().getArea(), dest);
		image->unlock();
		source = dest;
	}

	if (newTexture)
		glTexImage2D(GL_TEXTURE_2D, level, InternalFormat, image->getDimension().Width,
			image->getDimension().Height, 0, PixelFormat, PixelType, source);
	else
		glTexSubImage2D(GL_TEXTURE_2D, level, 0, 0, image->getDimension().Width,
			image->getDimension().Height, PixelFormat, PixelType, source);

	if (convert)
	{
		tmpImage->unlock();
		tmpImage->drop();
	}
	else
		image->unlock();

	if (AutomaticMipmapUpdate)
		glGenerateMipmap(GL_TEXTURE_2D);

	if (Driver->testGLError())
		os::Printer::log("Could not glTexImage2D", ELL_ERROR);
}


//! lock function
void* COGLES2Texture::lock(E_TEXTURE_LOCK_MODE mode, u32 mipmapLevel)
{
	// store info about which image is locked
	IImage* image = (mipmapLevel==0)?Image:MipImage;

	return image->lock();
}


//! unlock function
void COGLES2Texture::unlock()
{
	// test if miplevel or main texture was locked
	IImage* image = MipImage?MipImage:Image;
	if (!image)
		return;
	// unlock image to see changes
	image->unlock();
	// copy texture data to GPU
	if (!ReadOnlyLock)
		uploadTexture(false, 0, MipLevelStored);
	ReadOnlyLock = false;
	// cleanup local image
	if (MipImage)
	{
		MipImage->drop();
		MipImage=0;
	}
	else if (!KeepImage)
	{
		Image->drop();
		Image=0;
	}
	// update information
	if (Image)
		ColorFormat=Image->getColorFormat();
	else
		ColorFormat=ECF_A8R8G8B8;
}


//! Returns size of the original image.
const core::dimension2d<u32>& COGLES2Texture::getOriginalSize() const
{
	return ImageSize;
}


//! Returns size of the texture.
const core::dimension2d<u32>& COGLES2Texture::getSize() const
{
	return TextureSize;
}


//! returns driver type of texture, i.e. the driver, which created the texture
E_DRIVER_TYPE COGLES2Texture::getDriverType() const
{
	return EDT_OGLES2;
}


//! returns color format of texture
ECOLOR_FORMAT COGLES2Texture::getColorFormat() const
{
	return ColorFormat;
}


//! returns pitch of texture (in bytes)
u32 COGLES2Texture::getPitch() const
{
	if (Image)
		return Image->getPitch();
	else
		return 0;
}


//! return open gl texture name
u64 COGLES2Texture::getTextureHandler() const
{
	return TextureName;
}


//! Returns whether this texture has mipmaps
bool COGLES2Texture::hasMipMaps() const
{
	return HasMipMaps;
}


//! Regenerates the mip map levels of the texture. Useful after locking and
//! modifying the texture
void COGLES2Texture::regenerateMipMapLevels(void* mipmapData)
{
	if (AutomaticMipmapUpdate || !HasMipMaps || !Image)
		return;
	if ((Image->getDimension().Width==1) && (Image->getDimension().Height==1))
		return;

	// Manually create mipmaps or use prepared version
	u32 width=Image->getDimension().Width;
	u32 height=Image->getDimension().Height;
	u32 i=0;
	u8* target = static_cast<u8*>(mipmapData);
	do
	{
		if (width>1)
			width>>=1;
		if (height>1)
			height>>=1;
		++i;
		if (!target)
			target = new u8[width*height*Image->getBytesPerPixel()];
		// create scaled version if no mipdata available
		if (!mipmapData)
			Image->copyToScaling(target, width, height, Image->getColorFormat());
		glTexImage2D(GL_TEXTURE_2D, i, InternalFormat, width, height,
				0, PixelFormat, PixelType, target);
		// get next prepared mipmap data if available
		if (mipmapData)
		{
			mipmapData = static_cast<u8*>(mipmapData)+width*height*Image->getBytesPerPixel();
			target = static_cast<u8*>(mipmapData);
		}
	}
	while (width!=1 || height!=1);
	// cleanup
	if (!mipmapData)
		delete [] target;
}


bool COGLES2Texture::isRenderTarget() const
{
	return IsRenderTarget;
}


void COGLES2Texture::setIsRenderTarget(bool isTarget)
{
	IsRenderTarget = isTarget;
}


bool COGLES2Texture::isFrameBufferObject() const
{
	return false;
}


//! Bind Render Target Texture
void COGLES2Texture::bindRTT()
{
}


//! Unbind Render Target Texture
void COGLES2Texture::unbindRTT()
{
}


//! Get an access to texture states cache.
COGLES2Texture::SStatesCache& COGLES2Texture::getStatesCache() const
{
	return StatesCache;
}


/* FBO Textures */

// helper function for render to texture
static bool checkOGLES2FBOStatus(COGLES2Driver* Driver);

//! RTT ColorFrameBuffer constructor
COGLES2FBOTexture::COGLES2FBOTexture(const core::dimension2d<u32>& size,
					const io::path& name, COGLES2Driver* driver,
					ECOLOR_FORMAT format)
	: COGLES2Texture(name, driver), DepthTexture(0), ColorFrameBuffer(0)
{
	#ifdef _DEBUG
	setDebugName("COGLES2Texture_FBO");
	#endif

	ImageSize = size;
	TextureSize = size;
	HasMipMaps = false;
	IsRenderTarget = true;
	ColorFormat = getBestColorFormat(format);

	switch (ColorFormat)
	{
	case ECF_A8R8G8B8:
		InternalFormat = GL_RGBA;
		PixelFormat = GL_RGBA;
		PixelType = GL_UNSIGNED_BYTE;
		break;
	case ECF_R8G8B8:
		InternalFormat = GL_RGB;
		PixelFormat = GL_RGB;
		PixelType = GL_UNSIGNED_BYTE;
		break;
		break;
	case ECF_A1R5G5B5:
		InternalFormat = GL_RGBA;
		PixelFormat = GL_RGBA;
		PixelType = GL_UNSIGNED_SHORT_5_5_5_1;
		break;
		break;
	case ECF_R5G6B5:
		InternalFormat = GL_RGB;
		PixelFormat = GL_RGB;
		PixelType = GL_UNSIGNED_SHORT_5_6_5;
		break;
	default:
		os::Printer::log( "color format not handled", ELL_WARNING );
		break;
	}

	// generate frame buffer
	glGenFramebuffers(1, &ColorFrameBuffer);
	bindRTT();

	// generate color texture
	glGenTextures(1, &TextureName);

    Driver->setActiveTexture(0, this);
	Driver->getBridgeCalls()->setTexture(0);

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

	StatesCache.BilinearFilter = true;
    StatesCache.WrapU = ETC_CLAMP_TO_EDGE;
    StatesCache.WrapV = ETC_CLAMP_TO_EDGE;

	glTexImage2D(GL_TEXTURE_2D, 0, InternalFormat, ImageSize.Width, ImageSize.Height, 0, PixelFormat, PixelType, 0);

#ifdef _DEBUG
	driver->testGLError();
#endif

	// attach color texture to frame buffer
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, TextureName, 0);
#ifdef _DEBUG
	checkOGLES2FBOStatus(Driver);
#endif

	unbindRTT();
}


//! destructor
COGLES2FBOTexture::~COGLES2FBOTexture()
{
	if (DepthTexture)
		if (DepthTexture->drop())
			Driver->removeDepthTexture(DepthTexture);
	if (ColorFrameBuffer)
		glDeleteFramebuffers(1, &ColorFrameBuffer);
}


bool COGLES2FBOTexture::isFrameBufferObject() const
{
	return true;
}


//! Bind Render Target Texture
void COGLES2FBOTexture::bindRTT()
{
	if (ColorFrameBuffer != 0)
		glBindFramebuffer(GL_FRAMEBUFFER, ColorFrameBuffer);
}


//! Unbind Render Target Texture
void COGLES2FBOTexture::unbindRTT()
{
	if (ColorFrameBuffer != 0)
		glBindFramebuffer(GL_FRAMEBUFFER, Driver->getDefaultFramebuffer());
}


/* FBO Depth Textures */

//! RTT DepthBuffer constructor
COGLES2FBODepthTexture::COGLES2FBODepthTexture(
		const core::dimension2d<u32>& size,
		const io::path& name,
		COGLES2Driver* driver,
		bool useStencil)
	: COGLES2Texture(name, driver), DepthRenderBuffer(0),
	StencilRenderBuffer(0), UseStencil(useStencil)
{
#ifdef _DEBUG
	setDebugName("COGLES2TextureFBO_Depth");
#endif

	ImageSize = size;
	TextureSize = size;
	InternalFormat = GL_RGBA;
	PixelFormat = GL_RGBA;
	PixelType = GL_UNSIGNED_BYTE;
	HasMipMaps = false;

	if (useStencil)
	{
		glGenRenderbuffers(1, &DepthRenderBuffer);
		glBindRenderbuffer(GL_RENDERBUFFER, DepthRenderBuffer);
#ifdef GL_OES_packed_depth_stencil
		if (Driver->queryOpenGLFeature(COGLES2ExtensionHandler::IRR_OES_packed_depth_stencil))
		{
			// generate packed depth stencil buffer
			glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8_OES, ImageSize.Width, ImageSize.Height);
			StencilRenderBuffer = DepthRenderBuffer; // stencil is packed with depth
		}
		else // generate separate stencil and depth textures
#endif
		{
			glRenderbufferStorage(GL_RENDERBUFFER, Driver->getZBufferBits(), ImageSize.Width, ImageSize.Height);

			glGenRenderbuffers(1, &StencilRenderBuffer);
			glBindRenderbuffer(GL_RENDERBUFFER, StencilRenderBuffer);
			glRenderbufferStorage(GL_RENDERBUFFER, GL_STENCIL_INDEX8, ImageSize.Width, ImageSize.Height);
		}
	}
	else
	{
		// generate depth buffer
		glGenRenderbuffers(1, &DepthRenderBuffer);
		glBindRenderbuffer(GL_RENDERBUFFER, DepthRenderBuffer);
		glRenderbufferStorage(GL_RENDERBUFFER, Driver->getZBufferBits(), ImageSize.Width, ImageSize.Height);
	}
}


//! destructor
COGLES2FBODepthTexture::~COGLES2FBODepthTexture()
{
	if (DepthRenderBuffer)
		glDeleteRenderbuffers(1, &DepthRenderBuffer);

	if (StencilRenderBuffer && StencilRenderBuffer != DepthRenderBuffer)
		glDeleteRenderbuffers(1, &StencilRenderBuffer);
}


//combine depth texture and rtt
bool COGLES2FBODepthTexture::attach(ITexture* renderTex)
{
	if (!renderTex)
		return false;
	COGLES2FBOTexture* rtt = static_cast<COGLES2FBOTexture*>(renderTex);
	rtt->bindRTT();

	// attach stencil texture to stencil buffer
	if (UseStencil)
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_STENCIL_ATTACHMENT, GL_RENDERBUFFER, StencilRenderBuffer);

	// attach depth renderbuffer to depth buffer
	glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, DepthRenderBuffer);

	// check the status
	if (!checkOGLES2FBOStatus(Driver))
	{
		os::Printer::log("FBO incomplete");
		return false;
	}
	rtt->DepthTexture=this;
	rtt->DepthBufferTexture = DepthRenderBuffer;
	grab(); // grab the depth buffer, not the RTT
	rtt->unbindRTT();
	return true;
}


//! Bind Render Target Texture
void COGLES2FBODepthTexture::bindRTT()
{
}


//! Unbind Render Target Texture
void COGLES2FBODepthTexture::unbindRTT()
{
}


bool checkOGLES2FBOStatus(COGLES2Driver* Driver)
{
	GLenum status = glCheckFramebufferStatus(GL_FRAMEBUFFER);

	switch (status)
	{
		case GL_FRAMEBUFFER_COMPLETE:
			return true;

		case GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
			os::Printer::log("FBO has one or several incomplete image attachments", ELL_ERROR);
			break;

		case GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
			os::Printer::log("FBO missing an image attachment", ELL_ERROR);
			break;

		case GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS:
			os::Printer::log("FBO has one or several image attachments with different dimensions", ELL_ERROR);
			break;

		case GL_FRAMEBUFFER_UNSUPPORTED:
			os::Printer::log("FBO format unsupported", ELL_ERROR);
			break;

		default:
			break;
	}

	os::Printer::log("FBO error", ELL_ERROR);

	return false;
}


} // end namespace video
} // end namespace irr

#endif // _IRR_COMPILE_WITH_OGLES2_


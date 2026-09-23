// Shared raster-layer layout for the approved 360 x 780 Fluxara screens.
#ifndef HEADER_FLUXARA_UI_HPP
#define HEADER_FLUXARA_UI_HPP

#include "graphics/2dutils.hpp"
#include "graphics/central_settings.hpp"
#include "graphics/irr_driver.hpp"
#include "guiengine/engine.hpp"
#include "guiengine/scalable_font.hpp"
#include "guiengine/widget.hpp"
#include "io/file_manager.hpp"
#ifdef IOS_FLUXARA_DRIFT
#include "utils/fluxara_orientation_ios.hpp"
#endif
#include <IGUIButton.h>
#include <IVideoDriver.h>
#include <SMaterial.h>
#include <algorithm>
#include <cmath>
#include <vector>

namespace FluxaraUI
{
inline void rasterHitTarget(GUIEngine::Widget* widget)
{
    auto* button = widget->getIrrlichtElement<irr::gui::IGUIButton>();
    if (!button) return;
    button->setDrawBorder(false);
    button->setText(L"");
}
inline irr::video::ITexture* nativeTexture(const std::string& path)
{
    // FLUXARA_DRIFT normally caps textures at 512 px unless the global HD option is
    // enabled.  Fluxara UI rasters are screen-space artwork, not world
    // textures, so loading them through that cap makes a portrait background
    // roughly 288 x 512 on a Retina screen.  Raise the limit only while the
    // texture object captures its load parameters, then restore the user's
    // graphics setting for track/kart textures.
    auto& attributes = irr_driver->getVideoDriver()->getNonConstDriverAttributes();
    const irr::core::dimension2du previous =
        attributes.getAttributeAsDimension2d("MAX_TEXTURE_SIZE");
    attributes.setAttribute("MAX_TEXTURE_SIZE",
                            irr::core::dimension2du(4096, 4096));
    irr::video::ITexture* result = irr_driver->getTexture(path);
    attributes.setAttribute("MAX_TEXTURE_SIZE", previous);
    return result;
}
inline irr::video::ITexture* texture(const std::string& path)
{
    return nativeTexture(file_manager->getAsset(
        "gui/fluxara/" + path + ".png"));
}

// UIKit changes its drawable asynchronously.  During that short interval a
// 360x780 composition must stay hidden: rendering it through the old
// landscape target produces a narrow, distorted screen.  A background has no
// interactive geometry, however, so it can safely fill the old target and
// avoids exposing Irrlicht's default purple clear colour.
inline void transitionBackdrop(irr::video::ITexture* texture,
                               unsigned alpha = 255)
{
    if (!texture) return;
    const auto target = irr_driver->getActualScreenSize();
    const auto source = texture->getSize();
    if (target.Width == 0 || target.Height == 0 ||
        source.Width == 0 || source.Height == 0)
        return;

    const float target_aspect = float(target.Width) / float(target.Height);
    const float source_aspect = float(source.Width) / float(source.Height);
    irr::core::recti crop(0, 0, source.Width, source.Height);
    if (source_aspect > target_aspect)
    {
        const int width = int(std::lround(source.Height * target_aspect));
        const int x = int(source.Width - width) / 2;
        crop = irr::core::recti(x, 0, x + width, source.Height);
    }
    else
    {
        const int height = int(std::lround(source.Width / target_aspect));
        const int y = int(source.Height - height) / 2;
        crop = irr::core::recti(0, y, source.Width, y + height);
    }
    draw2DImage(texture, irr::core::recti(0, 0, target.Width, target.Height),
                crop, nullptr, irr::video::SColor(alpha, 255, 255, 255),
                true);
}

struct Canvas
{
    float scale, x, y;
    bool stable;
    Canvas()
    {
        const auto size = irr_driver->getActualScreenSize();
        scale = std::min(size.Width / 360.0f, size.Height / 780.0f);
        x = (size.Width - 360 * scale) * .5f;
        y = (size.Height - 780 * scale) * .5f;
#ifdef IOS_FLUXARA_DRIFT
        stable = !fluxaraOrientationTransitionPending();
#else
        stable = true;
#endif
    }
    bool isStable() const { return stable; }
    irr::core::recti rect(float left, float top, float width, float height) const
    {
        return irr::core::recti(int(std::lround(x + left * scale)),
            int(std::lround(y + top * scale)),
            int(std::lround(x + (left + width) * scale)),
            int(std::lround(y + (top + height) * scale)));
    }
    void move(GUIEngine::Widget* widget, float left, float top, float width, float height) const
    {
        const auto r = rect(left, top, width, height);
        widget->move(r.UpperLeftCorner.X, r.UpperLeftCorner.Y, r.getWidth(), r.getHeight());
    }
    void image(irr::video::ITexture* t, float left, float top, float width, float height,
               bool cover = false, unsigned alpha = 255,
               const irr::core::recti* clip = nullptr) const
    {
        if (!stable || !t) return;
        // iOS can upload an NPOT raster into a differently proportioned GPU
        // texture. Sample the entire uploaded texture, but use the source
        // artwork's dimensions for layout so buttons keep their approved
        // proportions instead of becoming square or repeating.
        const auto source_size = t->getSize();
        auto layout_size = t->getOriginalSize();
        if (layout_size.Width == 0 || layout_size.Height == 0)
            layout_size = source_size;
        irr::core::recti source(0, 0, source_size.Width, source_size.Height);
        auto destination = rect(left, top, width, height);
        if (cover)
        {
            const float s = std::max(width / layout_size.Width,
                                     height / layout_size.Height);
            const float crop_w = width / s;
            const float crop_h = height / s;
            const float x0 = (layout_size.Width - crop_w) * .5f;
            const float y0 = (layout_size.Height - crop_h) * .5f;
            const float sx = source_size.Width / float(layout_size.Width);
            const float sy = source_size.Height / float(layout_size.Height);
            source = irr::core::recti(
                int(std::lround(x0 * sx)), int(std::lround(y0 * sy)),
                int(std::lround((x0 + crop_w) * sx)),
                int(std::lround((y0 + crop_h) * sy)));
        }
        else
        {
            const float fit = std::min(width / layout_size.Width,
                                       height / layout_size.Height);
            const float w = layout_size.Width * fit;
            const float h = layout_size.Height * fit;
            destination = rect(left + (width-w)*.5f, top + (height-h)*.5f,w,h);
        }
        draw2DImage(t, destination, source, clip,
                   irr::video::SColor(alpha,255,255,255), true);
    }
    void roundedImage(irr::video::ITexture* t, float left, float top,
                      float width, float height, float radius,
                      const irr::core::recti* clip = nullptr) const
    {
        if (!stable || !t) return;
        const auto texture_size = t->getSize();
        auto layout_size = t->getOriginalSize();
        if (texture_size.Width == 0 || texture_size.Height == 0) return;
        if (layout_size.Width == 0 || layout_size.Height == 0)
            layout_size = texture_size;

        // Cover-crop in source-art coordinates, then translate the crop to
        // the uploaded texture.  The rounded polygon clips in destination
        // space, so square and panoramic screenshots get identical corners.
        const float cover = std::max(width / layout_size.Width,
                                     height / layout_size.Height);
        const float crop_w = width / cover;
        const float crop_h = height / cover;
        const float crop_x = (layout_size.Width - crop_w) * .5f;
        const float crop_y = (layout_size.Height - crop_h) * .5f;
        const float u0 = crop_x / layout_size.Width;
        const float v0 = crop_y / layout_size.Height;
        const float u1 = (crop_x + crop_w) / layout_size.Width;
        const float v1 = (crop_y + crop_h) / layout_size.Height;

        const irr::core::recti destination = rect(left, top, width, height);
        const float l = float(destination.UpperLeftCorner.X);
        const float t0 = float(destination.UpperLeftCorner.Y);
        const float r = float(destination.LowerRightCorner.X);
        const float b = float(destination.LowerRightCorner.Y);
        const float corner = std::min(radius * scale,
            std::min((r - l) * .5f, (b - t0) * .5f));
        const irr::video::SColor white(255, 255, 255, 255);

        std::vector<irr::video::S3DVertex> vertices;
        std::vector<irr::u16> indices;
        vertices.reserve(38);
        indices.reserve(39);
        const auto append = [&](float px, float py)
        {
            const float nx = (px - l) / std::max(1.0f, r - l);
            const float ny = (py - t0) / std::max(1.0f, b - t0);
            vertices.emplace_back(px, py, 0.0f, 0.0f, 0.0f, 0.0f, white,
                u0 + (u1 - u0) * nx, v0 + (v1 - v0) * ny);
        };
        append((l + r) * .5f, (t0 + b) * .5f);
        const float centers[][2] = {
            {r - corner, t0 + corner}, {r - corner, b - corner},
            {l + corner, b - corner}, {l + corner, t0 + corner}
        };
        constexpr int segments = 8;
        constexpr float pi = 3.14159265358979323846f;
        for (int quadrant = 0; quadrant < 4; ++quadrant)
        {
            const float start = (-90.0f + quadrant * 90.0f) * pi / 180.0f;
            for (int step = 0; step <= segments; ++step)
            {
                const float angle = start +
                    (pi * .5f * float(step) / float(segments));
                append(centers[quadrant][0] + std::cos(angle) * corner,
                       centers[quadrant][1] + std::sin(angle) * corner);
            }
        }
        indices.push_back(0);
        for (irr::u16 i = 1; i < vertices.size(); ++i)
            indices.push_back(i);
        indices.push_back(1);

        irr::video::SMaterial material;
        material.setTexture(0, t);
        material.MaterialType = irr::video::EMT_TRANSPARENT_ALPHA_CHANNEL;
        irr_driver->getVideoDriver()->setMaterial(material);
        if (clip) irr_driver->getVideoDriver()->enableScissorTest(*clip);
        if (CVS->isGLSL())
        {
            glEnable(GL_BLEND);
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        }
        draw2DVertexPrimitiveList(t, vertices.data(),
            static_cast<irr::u32>(vertices.size()), indices.data(),
            static_cast<irr::u32>(indices.size() - 2), irr::video::EVT_STANDARD,
            irr::scene::EPT_TRIANGLE_FAN, irr::video::EIT_16BIT);
        if (CVS->isGLSL()) glDisable(GL_BLEND);
        if (clip) irr_driver->getVideoDriver()->disableScissorTest();
    }
    void label(const irr::core::stringw& text, float left, float top,
               float width, float height, float point_size,
               const irr::core::recti* clip = nullptr) const
    {
        if (!stable) return;
        // Fluxara's Figma type is the skin's normal Baloo face.  The upstream
        // title face is a synthetic BoldFace with an FLUXARA_DRIFT-style dark outline;
        // using it here would leak that treatment into every Fluxara screen.
        auto* font = GUIEngine::getFont();
        const float saved = font->getScale();
        font->setScale(1.0f);
        const auto size = font->getDimension(text.c_str());
        const auto sample = font->getDimension(L"M");
        font->setScale(std::min(point_size * scale / std::max(1u, sample.Height),
                                width * scale / std::max(1u, size.Width)));
        const auto r = rect(left, top, width, height);
        auto shadow = r;
        shadow += irr::core::position2di(0, std::max(1, int(2 * scale)));
        font->draw(text, shadow, irr::video::SColor(160,8,18,59), true, true, clip);
        font->draw(text, r, irr::video::SColor(255,255,255,255), true, true, clip);
        font->setScale(saved);
    }
};
}
#endif

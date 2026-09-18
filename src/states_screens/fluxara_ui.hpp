// Shared raster-layer layout for the approved 360 x 780 Fluxara screens.
#ifndef HEADER_FLUXARA_UI_HPP
#define HEADER_FLUXARA_UI_HPP

#include "graphics/2dutils.hpp"
#include "graphics/irr_driver.hpp"
#include "guiengine/engine.hpp"
#include "guiengine/scalable_font.hpp"
#include "guiengine/widget.hpp"
#include "io/file_manager.hpp"
#include <IGUIButton.h>
#include <algorithm>
#include <cmath>

namespace FluxaraUI
{
inline void rasterHitTarget(GUIEngine::Widget* widget)
{
    auto* button = widget->getIrrlichtElement<irr::gui::IGUIButton>();
    if (!button) return;
    button->setDrawBorder(false);
    button->setText(L"");
}
inline irr::video::ITexture* texture(const std::string& path)
{
    return irr_driver->getTexture(file_manager->getAsset("gui/fluxara/" + path + ".png"));
}

struct Canvas
{
    float scale, x, y;
    Canvas()
    {
        const auto size = irr_driver->getActualScreenSize();
        scale = std::min(size.Width / 360.0f, size.Height / 780.0f);
        x = (size.Width - 360 * scale) * .5f;
        y = (size.Height - 780 * scale) * .5f;
    }
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
               bool cover = false, unsigned alpha = 255) const
    {
        if (!t) return;
        const auto size = t->getOriginalSize();
        irr::core::recti source(0, 0, size.Width, size.Height);
        auto destination = rect(left, top, width, height);
        if (cover)
        {
            const float s = std::max(width / size.Width, height / size.Height);
            const int w = int(width / s), h = int(height / s);
            source = irr::core::recti((size.Width - w) / 2, (size.Height - h) / 2,
                                     (size.Width + w) / 2, (size.Height + h) / 2);
        }
        else
        {
            const float fit = std::min(width / size.Width, height / size.Height);
            const float w = size.Width * fit, h = size.Height * fit;
            destination = rect(left + (width-w)*.5f, top + (height-h)*.5f,w,h);
        }
        draw2DImage(t, destination, source, nullptr,
                   irr::video::SColor(alpha,255,255,255), true);
    }
    void label(const irr::core::stringw& text, float left, float top,
               float width, float height, float point_size) const
    {
        auto* font = GUIEngine::getTitleFont();
        const float saved = font->getScale();
        font->setScale(1.0f);
        const auto size = font->getDimension(text.c_str());
        const auto sample = font->getDimension(L"M");
        font->setScale(std::min(point_size * scale / std::max(1u, sample.Height),
                                width * scale / std::max(1u, size.Width)));
        const auto r = rect(left, top, width, height);
        auto shadow = r;
        shadow += irr::core::position2di(0, std::max(1, int(2 * scale)));
        font->draw(text, shadow, irr::video::SColor(160,8,18,59), true, true);
        font->draw(text, r, irr::video::SColor(255,255,255,255), true, true);
        font->setScale(saved);
    }
};
}
#endif

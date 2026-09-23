// Copyright (C) 2002-2015 Nikolaus Gebhardt
//               2013 Glenn De Jonghe
// This file is part of the "Irrlicht Engine".
// For conditions of distribution and use, see copyright notice in irrlicht.h

#include "guiengine/widgets/CGUIFLUXARA_DRIFTListBox.hpp"

#include "font/font_drawer.hpp"
#include "graphics/2dutils.hpp"
#include "IGUISkin.h"
#include "IGUIEnvironment.h"
#include "IVideoDriver.h"
#include "IGUIFont.h"
#include "IGUISpriteBank.h"
#include "IGUIScrollBar.h"
#include "utils/string_utils.hpp"
#include "utils/time.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>

namespace irr
{
namespace gui
{

//! constructor
CGUIFLUXARA_DRIFTListBox::CGUIFLUXARA_DRIFTListBox(IGUIEnvironment* environment, IGUIElement* parent,
            s32 id, core::rect<s32> rectangle, bool clip,
            bool drawBack, bool moveOverSelect)
: IGUIElement(EGUIET_LIST_BOX, environment, parent, id, rectangle), Selected(-1),
    m_item_height(0),ItemHeightOverride(0),
    TotalItemHeight(0), ItemsIconWidth(0), MousePosY(0), m_font(0), IconBank(0),
    ScrollBar(0), selectTime(0), Selecting(false), Moving(false),
    DrawBack(drawBack), MoveOverSelect(moveOverSelect), AutoScroll(true),
    HighlightWhenNotFocused(true), m_touch_inertia_enabled(false),
    m_touch_scroll_velocity(0.0f), m_touch_scroll_position(0.0f),
    m_last_touch_time(0),
    m_last_inertia_time(0)
{
    m_alternating_darkness = false;
    #ifdef _DEBUG
    setDebugName("CGUIFLUXARA_DRIFTListBox");
    #endif

    IGUISkin* skin = Environment->getSkin();

    ScrollBar = Environment->addScrollBar(false, core::recti(0, 0, 1, 1), this, -1);
    ScrollBar->grab();
    ScrollBar->setSubElement(true);
    ScrollBar->setTabStop(false);
    ScrollBar->setAlignment(EGUIA_LOWERRIGHT, EGUIA_LOWERRIGHT, EGUIA_UPPERLEFT, EGUIA_LOWERRIGHT);
    ScrollBar->setVisible(false);
    ScrollBar->setPos(0);

    updateScrollBarSize(skin->getSize(EGDS_SCROLLBAR_SIZE));

    setNotClipped(!clip);

    // this element can be tabbed to
    setTabStop(true);
    setTabOrder(-1);

    updateAbsolutePosition();
    m_deactivated = false;
}


//! destructor
CGUIFLUXARA_DRIFTListBox::~CGUIFLUXARA_DRIFTListBox()
{
    if (ScrollBar)
        ScrollBar->drop();

    if (m_font)
        m_font->drop();

    if (IconBank)
        IconBank->drop();
}


//! returns amount of list items
u32 CGUIFLUXARA_DRIFTListBox::getItemCount() const
{
    return Items.size();
}



const wchar_t* CGUIFLUXARA_DRIFTListBox::getCellText(u32 row_num, u32 col_num) const
{
        if ( row_num >= Items.size() )
                return 0;
        if ( col_num >= Items[row_num].m_contents.size() )
                return 0;
    return Items[row_num].m_contents[col_num].m_text.c_str();
}

CGUIFLUXARA_DRIFTListBox::ListItem CGUIFLUXARA_DRIFTListBox::getItem(u32 id) const
{
    return Items[id];
}


//! Returns the icon of an item
s32 CGUIFLUXARA_DRIFTListBox::getIcon(u32 row_num, u32 col_num) const
{
    if ( row_num >= Items.size() )
            return -1;
    if ( col_num >= Items[row_num].m_contents.size() )
            return -1;
    return Items[row_num].m_contents[col_num].m_icon;
}

void CGUIFLUXARA_DRIFTListBox::removeItem(u32 id)
{
    if (id >= Items.size())
        return;

    if ((u32)Selected==id)
    {
        Selected = -1;
    }
    else if ((u32)Selected > id)
    {
        Selected -= 1;
        selectTime = (u32)FluxaraDriftTime::getTimeSinceEpoch();
    }

    Items.erase(id);

    recalculateItemHeight();
}


s32 CGUIFLUXARA_DRIFTListBox::getItemAt(s32 xpos, s32 ypos) const
{
    if (     xpos < AbsoluteRect.UpperLeftCorner.X || xpos >= AbsoluteRect.LowerRightCorner.X
        ||    ypos < AbsoluteRect.UpperLeftCorner.Y || ypos >= AbsoluteRect.LowerRightCorner.Y
        )
        return -1;

    if ( m_item_height == 0 )
        return -1;

    s32 item = ((ypos - AbsoluteRect.UpperLeftCorner.Y - 1) + ScrollBar->getPos()) / m_item_height;
    if ( item < 0 || item >= (s32)Items.size())
        return -1;

    return item;
}

//! clears the list
void CGUIFLUXARA_DRIFTListBox::clear()
{
    Items.clear();
    ItemsIconWidth = 0;
    Selected = -1;

    if (ScrollBar)
        ScrollBar->setPos(0);

    recalculateItemHeight();
}

// ----------------------------------------------------------------------------
void CGUIFLUXARA_DRIFTListBox::setTouchInertiaEnabled(bool enabled)
{
    m_touch_inertia_enabled = enabled;
    m_touch_scroll_velocity = 0.0f;
    m_touch_scroll_position = ScrollBar->getPos();
    m_last_touch_time = 0;
    m_last_inertia_time = 0;
}

// ----------------------------------------------------------------------------
float CGUIFLUXARA_DRIFTListBox::getTouchScrollPosition() const
{
    return m_touch_inertia_enabled ? m_touch_scroll_position :
        float(ScrollBar->getPos());
}

// ----------------------------------------------------------------------------
float CGUIFLUXARA_DRIFTListBox::getTouchScrollMaximum() const
{
    return float(std::max(0, TotalItemHeight - AbsoluteRect.getHeight()));
}

// ----------------------------------------------------------------------------
void CGUIFLUXARA_DRIFTListBox::setTouchScrollPosition(float position, bool rubber_band)
{
    const float maximum = getTouchScrollMaximum();
    if (rubber_band && (position < 0.0f || position > maximum))
    {
        // Same diminishing rubber-band principle as UIScrollView: the more
        // the finger pulls past an edge, the less extra distance is shown.
        const float edge = position < 0.0f ? 0.0f : maximum;
        const float overscroll = position - edge;
        const float dimension = std::max(1.0f,
            float(AbsoluteRect.getHeight()));
        position = edge + (overscroll * 0.55f) /
            (1.0f + std::abs(overscroll) * 0.55f / dimension);
    }
    m_touch_scroll_position = position;
    ScrollBar->setPos((s32)std::lround(std::max(0.0f,
        std::min(maximum, position))));
}

// ----------------------------------------------------------------------------
void CGUIFLUXARA_DRIFTListBox::updateTouchInertia()
{
    if (!m_touch_inertia_enabled || Selecting || Moving)
    {
        m_last_inertia_time = FluxaraDriftTime::getMonoTimeMs();
        return;
    }

    const uint64_t now = FluxaraDriftTime::getMonoTimeMs();
    if (m_last_inertia_time == 0)
    {
        m_last_inertia_time = now;
        return;
    }
    const float seconds = std::min(0.05f,
        float(now - m_last_inertia_time) / 1000.0f);
    m_last_inertia_time = now;
    if (seconds <= 0.0f)
        return;

    const float maximum = getTouchScrollMaximum();
    const float edge = std::max(0.0f,
        std::min(maximum, m_touch_scroll_position));
    const float overscroll = m_touch_scroll_position - edge;
    if (std::abs(overscroll) > 0.5f)
    {
        // Critically damped edge return. It is intentionally independent of
        // item height, so card rows never make the bounce step or snap.
        m_touch_scroll_velocity += -overscroll * 125.0f * seconds;
        m_touch_scroll_velocity *= std::exp(-15.0f * seconds);
    }
    else
    {
        // UIScrollViewDecelerationRateNormal is 0.998 per millisecond.
        // Exponential decay keeps the same feel at 60 and 120 Hz.
        const float decay = std::pow(0.998f, seconds * 1000.0f);
        m_touch_scroll_velocity *= decay;
    }

    if (std::abs(m_touch_scroll_velocity) < 8.0f &&
        std::abs(overscroll) < 0.5f)
    {
        m_touch_scroll_velocity = 0.0f;
        setTouchScrollPosition(edge, false);
        return;
    }
    setTouchScrollPosition(m_touch_scroll_position +
        m_touch_scroll_velocity * seconds, true);
}


void CGUIFLUXARA_DRIFTListBox::updateDefaultItemHeight()
{
    if (ItemHeightOverride == 0)
        m_item_height = m_font->getHeightPerLine() + 4;
}


void CGUIFLUXARA_DRIFTListBox::recalculateItemHeight()
{
    IGUISkin* skin = Environment->getSkin();

    if (m_font != skin->getFont())
    {
        if (m_font)
            m_font->drop();

        m_font = skin->getFont();
        if ( 0 == ItemHeightOverride )
            m_item_height = 0;

        if (m_font)
        {
            updateDefaultItemHeight();
            m_font->grab();
        }
    }

    TotalItemHeight = m_item_height * Items.size();
    ScrollBar->setMax( core::max_(0, TotalItemHeight - AbsoluteRect.getHeight()) );
    s32 minItemHeight = m_item_height > 0 ? m_item_height : 1;
    ScrollBar->setSmallStep ( minItemHeight );
    ScrollBar->setLargeStep ( 2*minItemHeight );

    if ( TotalItemHeight <= AbsoluteRect.getHeight() )
        ScrollBar->setVisible(false);
    else
        ScrollBar->setVisible(true);
}


//! returns id of selected item. returns -1 if no item is selected.
s32 CGUIFLUXARA_DRIFTListBox::getSelected() const
{
    return Selected;
}


//! sets the selected item. Set this to -1 if no item should be selected
void CGUIFLUXARA_DRIFTListBox::setSelected(s32 id)
{
    if ((u32)id>=Items.size())
        Selected = -1;
    else
        Selected = id;

    selectTime = (u32)FluxaraDriftTime::getTimeSinceEpoch();

    recalculateScrollPos();
}

s32 CGUIFLUXARA_DRIFTListBox::getRowByCellText(const wchar_t * text)
{
    s32 row_index = -1;
    s32 col_index = -1;
    if (text)
    {
        for ( row_index = 0; row_index < (s32) Items.size(); ++row_index )
        {
            for ( col_index = 0; col_index < (s32) Items[row_index].m_contents.size(); ++col_index )
            {
                if ( Items[row_index].m_contents[col_index].m_text == text ) return row_index;
            }
        }
    }
    return -1;
}

//! sets the selected item. Set this to -1 if no item should be selected
void CGUIFLUXARA_DRIFTListBox::setSelectedByCellText(const wchar_t * text)
{
    setSelected(getRowByCellText(text));
}

s32 CGUIFLUXARA_DRIFTListBox::getRowByInternalName(const std::string & text) const
{
    s32 row_index = -1;
    if (text != "")
    {
        for ( row_index = 0; row_index < (s32) Items.size(); ++row_index )
        {
            if (Items[row_index].m_internal_name == text) return row_index;
        }
    }
    return -1;
}

//! called if an event happened.
bool CGUIFLUXARA_DRIFTListBox::OnEvent(const SEvent& event)
{
    if (isEnabled())
    {
        switch(event.EventType)
        {
        case EET_GUI_EVENT:
            switch(event.GUIEvent.EventType)
            {
            case gui::EGET_SCROLL_BAR_CHANGED:
                if (event.GUIEvent.Caller == ScrollBar)
                    return true;
                break;
            case gui::EGET_ELEMENT_FOCUS_LOST:
                {
                    if (event.GUIEvent.Caller == this)
                    {
                        Moving = false;
                        Selecting = false;
                    }
                    break;
                }
            default:
            break;
            }
            break;

        case EET_MOUSE_INPUT_EVENT:
            {
                core::position2d<s32> p(event.MouseInput.X, event.MouseInput.Y);

                switch(event.MouseInput.Event)
                {
                case EMIE_MOUSE_WHEEL:
                    ScrollBar->setPos(ScrollBar->getPos() + event.MouseInput.Wheel * - m_item_height / 2);
                    return true;

                case EMIE_LMOUSE_PRESSED_DOWN:
                {
                    Selecting = true;
                    Moving = false;
                    MousePosY = event.MouseInput.Y;
                    m_touch_scroll_velocity = 0.0f;
                    m_touch_scroll_position = ScrollBar->getPos();
                    m_last_touch_time = FluxaraDriftTime::getMonoTimeMs();
                    m_last_inertia_time = m_last_touch_time;
                    return true;
                }

                case EMIE_LMOUSE_LEFT_UP:
                {
                    Selecting = false;

                    if (isPointInside(p) && !Moving)
                        selectNew(event.MouseInput.Y);
                    if (m_touch_inertia_enabled)
                        m_last_inertia_time = FluxaraDriftTime::getMonoTimeMs();
                    Moving = false;

                    return true;
                }

                case EMIE_MOUSE_MOVED:
                {
                    if (!event.MouseInput.isLeftPressed())
                    {
                        Selecting = false;
                        Moving = false;
                    }

                    // UIKit's pan recognizer waits for roughly ten points,
                    // rather than a fraction of a list row. Derive the same
                    // physical slop from this element's current height.
                    const s32 drag_threshold = m_touch_inertia_enabled ?
                        std::max(12, AbsoluteRect.getHeight() / 64) :
                        std::max(1, m_item_height / 3);
                    if (Selecting && std::abs(event.MouseInput.Y - MousePosY) >
                        drag_threshold)
                    {
                        Moving = true;
                        Selecting = false;
                    }

                    if (Moving)
                    {
                        const int delta = MousePosY - event.MouseInput.Y;
                        const uint64_t now = FluxaraDriftTime::getMonoTimeMs();
                        const float seconds = std::max(0.001f,
                            float(now - m_last_touch_time) / 1000.0f);
                        if (m_touch_inertia_enabled)
                        {
                            const float instant_velocity = delta / seconds;
                            // Sample recent pan velocity; touch deltas arrive
                            // already in the device's pixel coordinate space.
                            m_touch_scroll_velocity = std::max(-9000.0f,
                                std::min(9000.0f, m_touch_scroll_velocity *
                                0.2f + instant_velocity * 0.8f));
                        }
                        setTouchScrollPosition(m_touch_scroll_position + delta,
                            m_touch_inertia_enabled);
                        MousePosY = event.MouseInput.Y;
                        m_last_touch_time = now;
                    }
                    break;
                }
                default:
                break;
                }
            }
            break;
        case EET_KEY_INPUT_EVENT: // keyboard events are captured and handled elsewhere
        case EET_LOG_TEXT_EVENT:
        case EET_USER_EVENT:
        case EET_JOYSTICK_INPUT_EVENT:
        case EEVENT_TYPE::EGUIET_FORCE_32_BIT:
            break;
        default:
            break;
        }
    }

    return IGUIElement::OnEvent(event);
}


void CGUIFLUXARA_DRIFTListBox::selectNew(s32 ypos, bool onlyHover)
{
    u32 now = (u32)FluxaraDriftTime::getRealTime() * 1000;
    s32 oldSelected = Selected;

    Selected = getItemAt(AbsoluteRect.UpperLeftCorner.X, ypos);
    if (Selected == -1 || Items.empty() || m_deactivated)
    {
        Selected = -1;
        return;
    }

    recalculateScrollPos();

    selectTime = now;
    // post the news
    if (Parent && !onlyHover)
    {
        SEvent event;
        event.EventType = EET_GUI_EVENT;
        event.GUIEvent.Caller = this;
        event.GUIEvent.Element = 0;
        
#if !defined(MOBILE_FLUXARA_DRIFT)
        if (Selected != oldSelected /*|| now < selectTime + 500*/)
            event.GUIEvent.EventType = EGET_LISTBOX_CHANGED;
        else
#endif
            event.GUIEvent.EventType = EGET_LISTBOX_SELECTED_AGAIN;
            
        Parent->OnEvent(event);
    }
}


//! Update the position and size of the listbox, and update the scrollbar
void CGUIFLUXARA_DRIFTListBox::updateAbsolutePosition()
{
    IGUIElement::updateAbsolutePosition();
    for (unsigned int i = 0; i < Items.size(); i++)
    {
        for (unsigned int j = 0; j < Items[i].m_contents.size(); j++)
        {
            Items[i].m_contents[j].m_glyph_layouts.clear();
        }
    }

    if (m_font)
        updateDefaultItemHeight();
    ItemsIconWidth = 0;
    if (!Items.empty())
        recalculateIconWidth();
}


//! draws the element and its children
void CGUIFLUXARA_DRIFTListBox::draw()
{
#ifndef SERVER_ONLY
    if (!IsVisible)
        return;

    updateTouchInertia();

    recalculateItemHeight(); // if the font changed

    IGUISkin* skin = Environment->getSkin();
    updateScrollBarSize(skin->getSize(EGDS_SCROLLBAR_SIZE));

    core::rect<s32>* clipRect = 0;

    // draw background
    core::rect<s32> frameRect(AbsoluteRect);

    // draw items

    core::rect<s32> clientClip(AbsoluteRect);
    clientClip.UpperLeftCorner.Y += 1;
    if (ScrollBar->isVisible())
        clientClip.LowerRightCorner.X -= ScrollBar->getRelativePosition().getWidth();
    clientClip.LowerRightCorner.Y -= 1;
    clientClip.clipAgainst(AbsoluteClippingRect);

    skin->draw3DSunkenPane(this, skin->getColor(EGDC_3D_HIGH_LIGHT), true,
        DrawBack, frameRect, &clientClip);

    if (clipRect)
        clientClip.clipAgainst(*clipRect);

    frameRect = AbsoluteRect;
    if (ScrollBar->isVisible())
        frameRect.LowerRightCorner.X -= ScrollBar->getRelativePosition().getWidth();

    frameRect.LowerRightCorner.Y = AbsoluteRect.UpperLeftCorner.Y + m_item_height;

    frameRect.UpperLeftCorner.Y -= ScrollBar->getPos();
    frameRect.LowerRightCorner.Y -= ScrollBar->getPos();

    bool hl = (HighlightWhenNotFocused || Environment->hasFocus(this) || Environment->hasFocus(ScrollBar));

    FontDrawer::startBatching();
    for (s32 i=0; i<(s32)Items.size(); ++i)
    {
        if (frameRect.LowerRightCorner.Y >= AbsoluteRect.UpperLeftCorner.Y &&
            frameRect.UpperLeftCorner.Y <= AbsoluteRect.LowerRightCorner.Y)
        {
            if (m_alternating_darkness && i % 2 != 0)
            {
                video::SColor color(0);
                color.setAlpha(30);
                GL32_draw2DRectangle(color, frameRect, &clientClip);
            }
            if (i == Selected && hl)
                skin->draw2DRectangle(this, skin->getColor(EGDC_HIGH_LIGHT), frameRect, &clientClip);

            core::rect<s32> textRect = frameRect;
            
            if (!ScrollBar->isVisible())
                textRect.LowerRightCorner.X = textRect.LowerRightCorner.X - skin->getSize(EGDS_SCROLLBAR_SIZE);

            if (m_font)
            {
                int total_proportion = 0;
                for(unsigned int x = 0; x < Items[i].m_contents.size(); ++x)
                {
                    total_proportion += Items[i].m_contents[x].m_proportion;
                }

                int total_width = textRect.getWidth();
                
                for(unsigned int x = 0; x < Items[i].m_contents.size(); ++x)
                {
                    int part_size = total_width * Items[i].m_contents[x].m_proportion / total_proportion;
                    
                    textRect.LowerRightCorner.X = textRect.UpperLeftCorner.X + part_size;
                    textRect.UpperLeftCorner.X += 3;

                    if (IconBank && (Items[i].m_contents[x].m_icon > -1))
                    {
                        core::position2di iconPos = textRect.UpperLeftCorner;
                        iconPos.Y += textRect.getHeight() / 2;
                        
                        if (Items[i].m_contents[x].m_center && Items[i].m_contents[x].m_text.size() == 0)
                        {
                            iconPos.X += part_size/2 - 3;
                        }
                        else
                        {
                            iconPos.X += ItemsIconWidth/2;
                        }

                        EGUI_LISTBOX_COLOR icon_color = EGUI_LBC_ICON;
                        bool highlight=false;
                        if ( i==Selected && hl )
                        {
                            icon_color = EGUI_LBC_ICON_HIGHLIGHT;
                            highlight=true;
                        }

                        IconBank->draw2DSprite(
                            (u32)Items[i].m_contents[x].m_icon,
                            iconPos, &clientClip,
                            hasItemOverrideColor(i, icon_color) ? getItemOverrideColor(i, icon_color) : getItemDefaultColor(icon_color),
                            (highlight) ? selectTime : 0, (i==Selected) ? (u32)FluxaraDriftTime::getTimeSinceEpoch() : 0, false, true);

                        textRect.UpperLeftCorner.X += ItemsIconWidth;
                    }

                    textRect.UpperLeftCorner.X += 3;

                    EGUI_LISTBOX_COLOR font_color = EGUI_LBC_TEXT;
                    if ( i==Selected && hl )
                        font_color = EGUI_LBC_TEXT_HIGHLIGHT;

                    if (!Items[i].m_contents[x].m_text.empty() &&
                        Items[i].m_contents[x].m_glyph_layouts.empty())
                    {
                        int text_width = (textRect.LowerRightCorner.X - textRect.UpperLeftCorner.X);
                        m_font->initGlyphLayouts(Items[i].m_contents[x].m_text,
                            Items[i].m_contents[x].m_glyph_layouts);
                        // Remove highlighted link if cache already has it
                        gui::removeHighlightedURL(Items[i].m_contents[x].m_glyph_layouts);
                        if (Items[i].m_word_wrap)
                        {
                            gui::breakGlyphLayouts(Items[i].m_contents[x].m_glyph_layouts,
                                text_width, m_font->getInverseShaping(), m_font->getScale());
                        }
                    }

                    m_font->draw(
                        Items[i].m_contents[x].m_glyph_layouts,
                        textRect,
                        hasItemOverrideColor(i, font_color) ? getItemOverrideColor(i, font_color) : getItemDefaultColor(font_color),
                        Items[i].m_contents[x].m_center, true, &clientClip);

                    //Position back to inital pos
                    if (IconBank && (Items[i].m_contents[x].m_icon > -1))
                        textRect.UpperLeftCorner.X -= ItemsIconWidth;

                    textRect.UpperLeftCorner.X -= 6;

                    //Calculate new beginning
                    textRect.UpperLeftCorner.X += part_size;
                }
            }
        }

        frameRect.UpperLeftCorner.Y += m_item_height;
        frameRect.LowerRightCorner.Y += m_item_height;
    }
    FontDrawer::endBatching();
#endif
    IGUIElement::draw();
}


//! adds an list item with an icon
u32 CGUIFLUXARA_DRIFTListBox::addItem(const ListItem & item)
{
    Items.push_back(item);
    recalculateItemHeight();
    recalculateIconWidth();
    return Items.size() - 1;
}


void CGUIFLUXARA_DRIFTListBox::setSpriteBank(IGUISpriteBank* bank)
{
    if ( bank == IconBank )
        return;
    if (IconBank)
        IconBank->drop();

    IconBank = bank;
    if (IconBank)
        IconBank->grab();
}


void CGUIFLUXARA_DRIFTListBox::recalculateScrollPos()
{
    if (!AutoScroll)
        return;

    const s32 selPos = (Selected == -1 ? TotalItemHeight : Selected * m_item_height) - ScrollBar->getPos();

    if (selPos < 0)
    {
        ScrollBar->setPos(ScrollBar->getPos() + selPos);
    }
    else
    if (selPos > AbsoluteRect.getHeight() - m_item_height)
    {
        ScrollBar->setPos(ScrollBar->getPos() + selPos - AbsoluteRect.getHeight() + m_item_height);
    }
}


void CGUIFLUXARA_DRIFTListBox::setAutoScrollEnabled(bool scroll)
{
    AutoScroll = scroll;
}


bool CGUIFLUXARA_DRIFTListBox::isAutoScrollEnabled() const
{
    _IRR_IMPLEMENT_MANAGED_MARSHALLING_BUGFIX;
    return AutoScroll;
}

void CGUIFLUXARA_DRIFTListBox::recalculateIconWidth()
{
    for(int x = 0; x < (int)Items.getLast().m_contents.size(); ++x)
    {
        s32 icon = Items.getLast().m_contents[x].m_icon;
    if (IconBank && icon > -1 &&
        IconBank->getSprites().size() > (u32)icon &&
        IconBank->getSprites()[(u32)icon].Frames.size())
    {
        u32 rno = IconBank->getSprites()[(u32)icon].Frames[0].rectNumber;
        if (IconBank->getPositions().size() > rno)
        {
            const s32 w = IconBank->getPositions()[rno].getWidth();
            if (w > ItemsIconWidth)
                ItemsIconWidth = w;
        }
    }
    }
}


void CGUIFLUXARA_DRIFTListBox::setCell(u32 row_num, u32 col_num, const wchar_t* text, s32 icon)
{
    if ( row_num >= Items.size() || col_num >= Items[row_num].m_contents.size())
        return;

    Items[row_num].m_contents[col_num].m_text = text;
    Items[row_num].m_contents[col_num].m_icon = icon;
    Items[row_num].m_contents[col_num].m_glyph_layouts.clear();

    recalculateItemHeight();
    recalculateIconWidth();
}

void CGUIFLUXARA_DRIFTListBox::swapItems(u32 index1, u32 index2)
{
    if ( index1 >= Items.size() || index2 >= Items.size() )
        return;

    ListItem dummmy = Items[index1];
    Items[index1] = Items[index2];
    Items[index2] = dummmy;
}


void CGUIFLUXARA_DRIFTListBox::setItemOverrideColor(u32 index, video::SColor color)
{
    for ( u32 c=0; c < EGUI_LBC_COUNT; ++c )
    {
        Items[index].OverrideColors[c].Use = true;
        Items[index].OverrideColors[c].Color = color;
    }
}


void CGUIFLUXARA_DRIFTListBox::setItemOverrideColor(u32 index, EGUI_LISTBOX_COLOR colorType, video::SColor color)
{
    if ( index >= Items.size() || colorType < 0 || colorType >= EGUI_LBC_COUNT )
        return;

    Items[index].OverrideColors[colorType].Use = true;
    Items[index].OverrideColors[colorType].Color = color;
}


void CGUIFLUXARA_DRIFTListBox::clearItemOverrideColor(u32 index)
{
    for (u32 c=0; c < (u32)EGUI_LBC_COUNT; ++c )
    {
        Items[index].OverrideColors[c].Use = false;
    }
}


void CGUIFLUXARA_DRIFTListBox::clearItemOverrideColor(u32 index, EGUI_LISTBOX_COLOR colorType)
{
    if ( index >= Items.size() || colorType < 0 || colorType >= EGUI_LBC_COUNT )
        return;

    Items[index].OverrideColors[colorType].Use = false;
}


bool CGUIFLUXARA_DRIFTListBox::hasItemOverrideColor(u32 index, EGUI_LISTBOX_COLOR colorType) const
{
    if ( index >= Items.size() || colorType < 0 || colorType >= EGUI_LBC_COUNT )
        return false;

    return Items[index].OverrideColors[colorType].Use;
}


video::SColor CGUIFLUXARA_DRIFTListBox::getItemOverrideColor(u32 index, EGUI_LISTBOX_COLOR colorType) const
{
    if ( (u32)index >= Items.size() || colorType < 0 || colorType >= EGUI_LBC_COUNT )
        return video::SColor();

    return Items[index].OverrideColors[colorType].Color;
}


video::SColor CGUIFLUXARA_DRIFTListBox::getItemDefaultColor(EGUI_LISTBOX_COLOR colorType) const
{
    IGUISkin* skin = Environment->getSkin();
    if ( !skin )
        return video::SColor();

    switch ( colorType )
    {
        case EGUI_LBC_TEXT:
            return skin->getColor(EGDC_BUTTON_TEXT);
        case EGUI_LBC_TEXT_HIGHLIGHT:
            return skin->getColor(EGDC_HIGH_LIGHT_TEXT);
        case EGUI_LBC_ICON:
            return skin->getColor(EGDC_ICON);
        case EGUI_LBC_ICON_HIGHLIGHT:
            return skin->getColor(EGDC_ICON_HIGH_LIGHT);
        default:
            return video::SColor();
    }
}

//! set global itemHeight
void CGUIFLUXARA_DRIFTListBox::setItemHeight( s32 height )
{
    m_item_height = height;
    ItemHeightOverride = 1;
}


//! Sets whether to draw the background
void CGUIFLUXARA_DRIFTListBox::setDrawBackground(bool draw)
{
    DrawBack = draw;
}


void CGUIFLUXARA_DRIFTListBox::updateScrollBarSize(s32 size)
{
    if (size != ScrollBar->getRelativePosition().getWidth())
    {
        core::recti r(RelativeRect.getWidth() - size, 0, RelativeRect.getWidth(), RelativeRect.getHeight());
        ScrollBar->setRelativePosition(r);
    }
}


} // end namespace gui
} // end namespace irr

#include "states_screens/fluxara_race_result_screen.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "guiengine/screen.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "karts/abstract_kart.hpp"
#include "modes/world.hpp"
#include "utils/string_utils.hpp"
#include "utils/translation.hpp"

namespace FluxaraResults
{
namespace
{
irr::video::ITexture* art[18] = {};
}
void layout(GUIEngine::Screen* screen)
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"fluxara-again", "fluxara-next"})
        FluxaraUI::rasterHitTarget(screen->getWidget<GUIEngine::ButtonWidget>(id));
    // Figma 19:8: the complete coral action surface is 276 x 99.  The
    // invisible hit target must cover the same area, including its lower
    // rounded portion.
    c.move(screen->getWidget<GUIEngine::ButtonWidget>("fluxara-again"),42,537,276,99);
    c.move(screen->getWidget<GUIEngine::ButtonWidget>("fluxara-next"),42,620,276,99);
}
void init(GUIEngine::Screen* screen)
{
    for (const char* id : {"fluxara-again", "fluxara-next"})
        screen->getWidget(id)->setVisible(true);
    const char* files[] = {"background","trophy","again","next-surface",
        "againicon","star","confetti2","confetti3","confetti4","confetti5",
        "confetti6","confetti7","confetti8","confetti9"};
    for (int i=0;i<14;++i) art[i]=FluxaraUI::texture(std::string("results/")+files[i]);
    art[14]=FluxaraUI::texture("home/icon-next");
    art[15]=FluxaraUI::texture("results/trophy-star");
    layout(screen);
    screen->getWidget("operations")->setVisible(false);
    // A completed circuit should advance the campaign on the ordinary
    // confirm action.  Replaying remains available as the secondary button.
    screen->getWidget<GUIEngine::ButtonWidget>("fluxara-next")
        ->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
}
void draw(GUIEngine::Screen* screen)
{
    const FluxaraUI::Canvas c;
    const auto size=irr_driver->getActualScreenSize();
    GL32_draw2DRectangle(irr::video::SColor(255,12,31,76),
        irr::core::recti(0,0,size.Width,size.Height));
    c.image(art[0],0,0,360,780,true,77);
    // Figma 19:8 confetti/star has its own compact 28pt frame.  It is not
    // the larger trophy-star layer further down the card.
    c.image(art[5],166,35,28,28);
    const float bits[8][4]={{30.93f,104,21.593f,26.54f},{306,108.74f,24.683f,27.164f},
        {70,152.33f,16.373f,21.932f},{275.9f,174,18.398f,25.401f},
        {36,232.6f,19.752f,23.076f},{311.94f,244,17.082f,21.907f},
        {36.88f,330,24.021f,27.409f},{305,328.38f,18.106f,22.358f}};
    for(int i=0;i<8;++i)c.image(art[6+i],bits[i][0],bits[i][1],bits[i][2],bits[i][3]);
    // Figma 19:8 has a separate star layer behind the cup art.  Keeping it
    // separate preserves the supplied transparent layer and its exact bounds.
    c.image(art[15],158,311,45,45);
    c.image(art[1],50,235,259,244);
    auto* world=World::getWorld();
    auto* kart=world ? world->getPlayerKart(0) : nullptr;
    const irr::core::stringw place=kart
        ? irr::core::stringw(L"#")+irr::core::stringw(kart->getPosition()) : L"—";
    auto* font=GUIEngine::getFont();
    const float saved=font->getScale();
    font->setScale(1.0f);
    const auto textSize=font->getDimension(place.c_str());
    const auto sample=font->getDimension(L"M");
    font->setScale(std::min(112*c.scale/std::max(1u,sample.Height),
                           130*c.scale/std::max(1u,textSize.Width)));
    font->draw(place,c.rect(115,102,130,117),irr::video::SColor(255,255,196,43),true,true);
    font->setScale(saved);
    c.label(_C("fluxara", "RACE COMPLETE"),87,486,186,27,22);
    c.image(art[2],42,537,276,99);
    c.image(art[4],90,554,42,46);
    c.label(_C("fluxara", "PLAY AGAIN"),108,565,210,28,22);
    c.image(art[3],42,620,276,99);
    c.image(art[14],112,639,42,46);
    c.label(_C("fluxara", "NEXT"),138,649,134,29,23);
    screen->getWidget("operations")->setVisible(false);
}
}

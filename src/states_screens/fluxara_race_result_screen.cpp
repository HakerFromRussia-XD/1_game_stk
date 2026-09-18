#include "states_screens/fluxara_race_result_screen.hpp"
#include "states_screens/fluxara_ui.hpp"
#include "guiengine/screen.hpp"
#include "guiengine/widgets/button_widget.hpp"
#include "karts/abstract_kart.hpp"
#include "modes/world.hpp"
#include "race/race_manager.hpp"
#include "utils/string_utils.hpp"

namespace FluxaraResults
{
namespace
{
irr::video::ITexture* art[17] = {};
}
void layout(GUIEngine::Screen* screen)
{
    const FluxaraUI::Canvas c;
    for (const char* id : {"fluxara-again", "fluxara-next", "fluxara-list"})
        FluxaraUI::rasterHitTarget(screen->getWidget<GUIEngine::ButtonWidget>(id));
    c.move(screen->getWidget<GUIEngine::ButtonWidget>("fluxara-again"),42,537,276,83);
    c.move(screen->getWidget<GUIEngine::ButtonWidget>("fluxara-next"),42,620,276,99);
    c.move(screen->getWidget<GUIEngine::ButtonWidget>("fluxara-list"),76,729,208,38);
}
void init(GUIEngine::Screen* screen)
{
    for (const char* id : {"fluxara-again", "fluxara-next", "fluxara-list"})
        screen->getWidget(id)->setVisible(true);
    const char* files[] = {"background","trophy","again","next-surface",
        "againicon","star","confetti2","confetti3","confetti4","confetti5",
        "confetti6","confetti7","confetti8","confetti9"};
    for (int i=0;i<14;++i) art[i]=FluxaraUI::texture(std::string("results/")+files[i]);
    art[14]=FluxaraUI::texture("home/icon-next");
    layout(screen);
    screen->getWidget("operations")->setVisible(false);
    screen->getWidget<GUIEngine::ButtonWidget>("fluxara-again")
        ->setFocusForPlayer(PLAYER_ID_GAME_MASTER);
}
void draw(GUIEngine::Screen* screen)
{
    const FluxaraUI::Canvas c;
    const auto size=irr_driver->getActualScreenSize();
    GL32_draw2DRectangle(irr::video::SColor(255,12,31,76),
        irr::core::recti(0,0,size.Width,size.Height));
    c.image(art[0],0,0,360,780,true,77);
    c.image(art[5],162,34,37,36);
    const float bits[8][4]={{30.93f,104,21.593f,26.54f},{306,108.74f,24.683f,27.164f},
        {70,152.33f,16.373f,21.932f},{275.9f,174,18.398f,25.401f},
        {36,232.6f,19.752f,23.076f},{311.94f,244,17.082f,21.907f},
        {36.88f,330,24.021f,27.409f},{305,328.38f,18.106f,22.358f}};
    for(int i=0;i<8;++i)c.image(art[6+i],bits[i][0],bits[i][1],bits[i][2],bits[i][3]);
    c.image(art[1],50,235,259,244);
    auto* world=World::getWorld();
    auto* kart=world ? world->getPlayerKart(0) : nullptr;
    auto* race=RaceManager::get();
    const irr::core::stringw place=kart
        ? irr::core::stringw(L"#")+irr::core::stringw(kart->getPosition()) : L"—";
    auto* font=GUIEngine::getTitleFont();
    const float saved=font->getScale();
    font->setScale(1.0f);
    const auto textSize=font->getDimension(place.c_str());
    const auto sample=font->getDimension(L"M");
    font->setScale(std::min(112*c.scale/std::max(1u,sample.Height),
                           160*c.scale/std::max(1u,textSize.Width)));
    font->draw(place,c.rect(100,102,160,117),irr::video::SColor(255,255,196,43),true,true);
    font->setScale(saved);
    c.label(L"RACE COMPLETE",87,486,186,27,22);
    const float elapsed = kart && kart->getFinishTime() > 0.0f
        ? kart->getFinishTime() : (world ? world->getTime() : 0.0f);
    irr::core::stringw details=world
        ? StringUtils::utf8ToWide(StringUtils::timeToString(elapsed)) : L"—";
    if(race->modeHasLaps())
        details+=irr::core::stringw(L"  ·  ")+irr::core::stringw(race->getNumLaps())+L" LAPS";
    details+=L"  ·  "; details+=race->getDifficultyName(race->getDifficulty());
    c.label(details,24,514,312,21,13);
    c.image(art[2],42,537,276,99);
    c.image(art[4],90,554,42,46);
    c.label(L"PLAY AGAIN",137,565,156,28,22);
    c.image(art[3],42,620,276,99);
    c.image(art[14],112,639,42,46);
    c.label(L"NEXT",158,649,114,29,23);
    c.label(L"CAMPAIGN",76,729,208,38,17);
    screen->getWidget("operations")->setVisible(false);
}
}

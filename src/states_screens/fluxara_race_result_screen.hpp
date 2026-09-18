#ifndef HEADER_FLUXARA_RACE_RESULT_SCREEN_HPP
#define HEADER_FLUXARA_RACE_RESULT_SCREEN_HPP
namespace GUIEngine { class Screen; }
namespace FluxaraResults
{
void init(GUIEngine::Screen* screen);
void layout(GUIEngine::Screen* screen);
void draw(GUIEngine::Screen* screen);
}
#endif

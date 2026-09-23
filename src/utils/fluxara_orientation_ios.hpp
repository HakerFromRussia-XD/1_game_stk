#ifndef HEADER_FLUXARA_ORIENTATION_IOS_HPP
#define HEADER_FLUXARA_ORIENTATION_IOS_HPP

// Must run before SDL creates its iOS window, so its first framebuffer has the
// same orientation as the initial Fluxara screen.
void fluxaraPrepareInitialOrientation(bool portrait);

// Read by the Irrlicht SDL device immediately before SDL_Init.  This is the
// final orientation hint, after the engine's platform defaults are applied.
bool fluxaraInitialOrientationIsPortrait();

// Called at the route boundary. UIKit geometry is submitted immediately on its
// main thread before the destination screen is built.
void fluxaraRequestPortraitMenu(bool portrait);

// UIKit applies geometry asynchronously.  Until Irrlicht has recreated its
// render target for that geometry, portrait art must not be drawn through the
// previous landscape framebuffer.
bool fluxaraOrientationTransitionPending();
void fluxaraNotifyRenderTargetSize(unsigned int width, unsigned int height);

// Results are a portrait in-game menu.  When it is popped straight into the
// portrait campaign, suppress exactly the intermediate GAME/landscape request.
void fluxaraPreservePortraitForNextGameState();
bool fluxaraPreservePortraitDuringState(bool destination_is_menu);

#endif

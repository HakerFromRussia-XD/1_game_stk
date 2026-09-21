#ifndef HEADER_FLUXARA_ORIENTATION_IOS_HPP
#define HEADER_FLUXARA_ORIENTATION_IOS_HPP

// Must run before SDL creates its iOS window, so its first framebuffer has the
// same orientation as the initial Fluxara screen.
void fluxaraPrepareInitialOrientation(bool portrait);

// Read by the Irrlicht SDL device immediately before SDL_Init.  This is the
// final orientation hint, after the engine's platform defaults are applied.
bool fluxaraInitialOrientationIsPortrait();

// Called by the game state manager. UIKit work is dispatched to the main queue.
void fluxaraRequestPortraitMenu(bool portrait);

#endif

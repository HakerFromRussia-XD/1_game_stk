#include "utils/fluxara_orientation_ios.hpp"
#include <SDL.h>
#import <UIKit/UIKit.h>

namespace
{
bool g_fluxara_orientation_initialized = false;
bool g_fluxara_orientation_portrait = true;
// The initial SDL hint is consumed before UIKit has a view controller that
// can receive a geometry request.  Remember whether the current orientation
// has subsequently been requested from the foreground scene as well.
bool g_fluxara_geometry_requested = false;
// FLUXARA_DRIFT constructs its initial menu stack while an immediate race is still
// loading.  That transient MENU state must not overwrite a landscape hint
// that was supplied before SDL created its iOS window.
bool g_fluxara_initial_race_pending = false;
bool g_fluxara_geometry_transition_pending = false;
// A result screen is technically an in-game menu.  Its pop temporarily puts
// StateManager into GAME before the campaign restores MENU.  Preserve portrait
// across that one internal state only; every normal GAME transition remains
// landscape.
bool g_fluxara_preserve_portrait_for_next_game_state = false;

void setSDLOutputOrientation(bool portrait)
{
    SDL_SetHint(SDL_HINT_ORIENTATIONS,
                portrait ? "Portrait" : "LandscapeLeft LandscapeRight");
}
}

void fluxaraPrepareInitialOrientation(bool portrait)
{
    // SDL reads this hint while creating its UIKit view controller.  Setting
    // it later rotates UIKit without rotating the already-created renderer.
    g_fluxara_orientation_initialized = true;
    g_fluxara_orientation_portrait = portrait;
    g_fluxara_initial_race_pending = !portrait;
    g_fluxara_geometry_requested = false;
    g_fluxara_geometry_transition_pending = false;
    g_fluxara_preserve_portrait_for_next_game_state = false;
    setSDLOutputOrientation(portrait);
}

bool fluxaraInitialOrientationIsPortrait()
{
    return g_fluxara_orientation_portrait;
}

void fluxaraRequestPortraitMenu(bool portrait)
{
    // A direct race briefly visits MENU during FLUXARA_DRIFT's bootstrap.  Ignoring only
    // that one portrait request keeps SDL's first framebuffer landscape.  The
    // first GAME request clears the guard, so results and every later menu
    // still restore portrait normally.
    if (g_fluxara_initial_race_pending && portrait)
        return;
    if (!portrait)
        g_fluxara_initial_race_pending = false;
    const bool orientation_changed =
        !g_fluxara_orientation_initialized ||
        g_fluxara_orientation_portrait != portrait;

    if (g_fluxara_orientation_initialized &&
        !orientation_changed &&
        g_fluxara_geometry_requested)
        return;

    g_fluxara_geometry_requested = true;
    g_fluxara_orientation_initialized = true;
    g_fluxara_orientation_portrait = portrait;
    // A same-orientation request at startup must not hide Fluxara's canvas.
    // Only a real portrait <-> landscape transition needs to wait for the
    // SDL/Irrlicht render target to receive its new dimensions.
    g_fluxara_geometry_transition_pending =
        g_fluxara_geometry_transition_pending || orientation_changed;
    void (^apply_orientation)(void) = ^{
        // SDL's view controller consults this hint for its supported mask.
        setSDLOutputOrientation(portrait);
        const UIInterfaceOrientationMask mask = portrait
            ? UIInterfaceOrientationMaskPortrait : UIInterfaceOrientationMaskLandscape;
        UIApplication* application = [UIApplication sharedApplication];
        [UIView performWithoutAnimation:^{
            if (@available(iOS 16.0, *))
            {
                for (UIScene* scene in application.connectedScenes)
                {
                    if (![scene isKindOfClass:[UIWindowScene class]] ||
                        scene.activationState != UISceneActivationStateForegroundActive)
                        continue;
                    UIWindowScene* windowScene = (UIWindowScene*)scene;
                    for (UIWindow* window in windowScene.windows)
                    {
                        if (!window.isKeyWindow) continue;
                        UIViewController* controller = window.rootViewController;
                        [controller setNeedsUpdateOfSupportedInterfaceOrientations];
                        while (controller.presentedViewController)
                        {
                            controller = controller.presentedViewController;
                            [controller setNeedsUpdateOfSupportedInterfaceOrientations];
                        }
                    }
                    UIWindowSceneGeometryPreferencesIOS* preferences =
                        [[UIWindowSceneGeometryPreferencesIOS alloc]
                            initWithInterfaceOrientations:mask];
                    [windowScene requestGeometryUpdateWithPreferences:preferences
                        errorHandler:^(NSError* error) {
                            NSLog(@"Fluxara orientation request failed: %@", error);
                        }];
#if !__has_feature(objc_arc)
                    [preferences release];
#endif
                }
            }
            else
            {
                // Older iOS uses the SDL controller's newly narrowed supported mask.
                [UIViewController attemptRotationToDeviceOrientation];
            }
        }];
    };
    // Geometry updates must be submitted in the transition that requested
    // them, not appended behind later menu work.  That prevents the visible
    // landscape → portrait → portrait sequence on NEXT.
    if ([NSThread isMainThread])
        apply_orientation();
    else
        dispatch_sync(dispatch_get_main_queue(), apply_orientation);
}

bool fluxaraOrientationTransitionPending()
{
    return g_fluxara_geometry_transition_pending;
}

void fluxaraNotifyRenderTargetSize(unsigned int width, unsigned int height)
{
    if (g_fluxara_geometry_transition_pending &&
        (height >= width) == g_fluxara_orientation_portrait)
    {
        g_fluxara_geometry_transition_pending = false;
    }
}

void fluxaraPreservePortraitForNextGameState()
{
    g_fluxara_preserve_portrait_for_next_game_state = true;
}

bool fluxaraPreservePortraitDuringState(bool destination_is_menu)
{
    if (!g_fluxara_preserve_portrait_for_next_game_state)
        return false;
    // The result menu may visit more than one non-MENU state while the race
    // world is destroyed.  Keep the actual device portrait throughout all of
    // them, then release the hold only when the campaign has taken ownership.
    if (destination_is_menu)
    {
        g_fluxara_preserve_portrait_for_next_game_state = false;
        return false;
    }
    return true;
}

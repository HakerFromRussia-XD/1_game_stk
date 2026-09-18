#include "utils/fluxara_orientation_ios.hpp"
#include <SDL.h>
#import <UIKit/UIKit.h>

void fluxaraRequestPortraitMenu(bool portrait)
{
    dispatch_async(dispatch_get_main_queue(), ^{
        // SDL's view controller consults this hint for its supported mask.
        SDL_SetHint(SDL_HINT_ORIENTATIONS,
                    portrait ? "Portrait" : "LandscapeLeft LandscapeRight");
        const UIInterfaceOrientationMask mask = portrait
            ? UIInterfaceOrientationMaskPortrait : UIInterfaceOrientationMaskLandscape;
        UIApplication* application = [UIApplication sharedApplication];
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
    });
}

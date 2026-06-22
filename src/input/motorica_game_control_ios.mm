//  SuperTuxKart - a fun racing game with go-kart

#ifdef IOS_STK

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <dispatch/dispatch.h>

#include "input/motorica_game_control.hpp"
#include "main_loop.hpp"
#include "utils/log.hpp"

namespace
{
    NSString* const kAppGroup = @"group.com.motorica.gamecontrol";
    NSString* const kSnapshotKey = @"snapshot";
    NSString* const kInstalledGameKey = @"installedGame.stk";
    NSString* const kSeqKey = @"seq";
    NSString* const kTimestampKey = @"timestampMs";
    NSString* const kOpenLevelKey = @"openLevel";
    NSString* const kCloseLevelKey = @"closeLevel";
    NSString* const kConnectedKey = @"connected";
    NSString* const kBundleIdKey = @"bundleId";
    NSString* const kVersionNameKey = @"versionName";
    NSString* const kVersionCodeKey = @"versionCode";
    NSString* const kUpdatedAtMsKey = @"updatedAtMs";

    dispatch_source_t g_poll_timer = nil;
    uint64_t g_last_seq = 0;
    bool g_logged_app_group_error = false;
    bool g_logged_waiting_snapshot = false;
    UIAlertController* g_connection_lost_alert = nil;

    int clampLevel(NSInteger value)
    {
        if (value < 0)
            return 0;
        if (value > 255)
            return 255;
        return (int)value;
    }

    UIViewController* getRootViewController()
    {
        UIWindow* key_window = nil;
        for (UIScene* scene in UIApplication.sharedApplication.connectedScenes)
        {
            if (scene.activationState != UISceneActivationStateForegroundActive ||
                ![scene isKindOfClass:UIWindowScene.class])
            {
                continue;
            }

            UIWindowScene* window_scene = (UIWindowScene*)scene;
            for (UIWindow* window in window_scene.windows)
            {
                if (window.isKeyWindow)
                {
                    key_window = window;
                    break;
                }
            }

            if (key_window != nil)
                break;
        }

        if (key_window == nil)
            key_window = UIApplication.sharedApplication.windows.firstObject;

        UIViewController* root = key_window.rootViewController;
        while (root.presentedViewController != nil)
            root = root.presentedViewController;
        return root;
    }
}

void writeMotoricaGameVersionIOS()
{
    NSUserDefaults* defaults = [[NSUserDefaults alloc]
        initWithSuiteName:kAppGroup];
    if (defaults == nil)
    {
        Log::warn("MotoricaGameControl",
            "[BLE stk-game debug] ios app group unavailable while writing game version: %s",
            [kAppGroup UTF8String]);
        return;
    }

    NSDictionary* info = NSBundle.mainBundle.infoDictionary;
    NSString* bundle_id = NSBundle.mainBundle.bundleIdentifier;
    if (bundle_id == nil || bundle_id.length == 0)
        bundle_id = @"com.motorica.games.stk";

    NSString* version_name = info[@"CFBundleShortVersionString"];
    if (version_name == nil)
        version_name = @"";

    NSString* build_number = info[@"CFBundleVersion"];
    if (build_number == nil)
        build_number = @"0";

    long long version_code = [build_number longLongValue];
    long long updated_at_ms = (long long)(NSDate.date.timeIntervalSince1970 *
        1000.0);
    NSDictionary* installed_game = @{
        kBundleIdKey: bundle_id,
        kVersionNameKey: version_name,
        kVersionCodeKey: @(version_code),
        kUpdatedAtMsKey: @(updated_at_ms),
    };
    [defaults setObject:installed_game forKey:kInstalledGameKey];
    [defaults synchronize];

    Log::info("MotoricaGameControl",
        "[BLE stk-game debug] ios wrote game version bundle=%s versionName=%s versionCode=%lld",
        [bundle_id UTF8String], [version_name UTF8String], version_code);
}

void showMotoricaConnectionLostDialogIOS()
{
    dispatch_async(dispatch_get_main_queue(), ^{
        if (g_connection_lost_alert != nil)
            return;

        UIViewController* root = getRootViewController();
        if (root == nil)
        {
            Log::warn("MotoricaGameControl",
                "[BLE stk-game debug] ios connection lost dialog root unavailable");
            return;
        }

        UIAlertController* alert = [UIAlertController
            alertControllerWithTitle:@"Связь потеряна"
            message:@"Данные управления не поступают из приложения Motorica Start. Игра продолжится автоматически после восстановления связи."
            preferredStyle:UIAlertControllerStyleAlert];
        UIAlertAction* exit_action = [UIAlertAction
            actionWithTitle:@"Выйти из игры"
            style:UIAlertActionStyleDestructive
            handler:^(__unused UIAlertAction* action) {
                if (main_loop != nullptr)
                    main_loop->requestAbort();
            }];
        [alert addAction:exit_action];
        g_connection_lost_alert = alert;
        [root presentViewController:alert animated:YES completion:nil];
        Log::info("MotoricaGameControl",
            "[BLE stk-game debug] ios connection lost dialog shown");
    });
}

void dismissMotoricaConnectionLostDialogIOS()
{
    dispatch_async(dispatch_get_main_queue(), ^{
        if (g_connection_lost_alert == nil)
            return;
        UIAlertController* alert = g_connection_lost_alert;
        g_connection_lost_alert = nil;
        [alert dismissViewControllerAnimated:YES completion:nil];
        Log::info("MotoricaGameControl",
            "[BLE stk-game debug] ios connection lost dialog dismissed");
    });
}

void startMotoricaGameControlIOS()
{
    if (g_poll_timer != nil)
        return;

    dispatch_queue_t queue = dispatch_queue_create(
        "com.motorica.games.stk.gamecontrol", DISPATCH_QUEUE_SERIAL);
    g_poll_timer = dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER, 0, 0,
                                          queue);
    dispatch_source_set_timer(g_poll_timer, dispatch_time(DISPATCH_TIME_NOW, 0),
                              33ull * NSEC_PER_MSEC, 5ull * NSEC_PER_MSEC);
    dispatch_source_set_event_handler(g_poll_timer, ^{
        @autoreleasepool
        {
            NSUserDefaults* defaults = [[NSUserDefaults alloc]
                initWithSuiteName:kAppGroup];
            if (defaults == nil)
            {
                if (!g_logged_app_group_error)
                {
                    g_logged_app_group_error = true;
                    Log::warn("MotoricaGameControl",
                        "[BLE stk-game debug] ios app group unavailable: %s",
                        [kAppGroup UTF8String]);
                }
                return;
            }

            NSDictionary* snapshot = [defaults dictionaryForKey:kSnapshotKey];
            if (snapshot == nil)
            {
                if (!g_logged_waiting_snapshot)
                {
                    g_logged_waiting_snapshot = true;
                    Log::info("MotoricaGameControl",
                        "[BLE stk-game debug] ios waiting for game control snapshot");
                }
                return;
            }

            NSNumber* seq_number = snapshot[kSeqKey];
            if (seq_number == nil)
                return;
            uint64_t seq = [seq_number unsignedLongLongValue];
            if (seq == g_last_seq)
                return;
            g_last_seq = seq;

            int open_level = clampLevel([snapshot[kOpenLevelKey] integerValue]);
            int close_level = clampLevel([snapshot[kCloseLevelKey] integerValue]);
            bool connected = [snapshot[kConnectedKey] boolValue];
            uint64_t timestamp_ms =
                [snapshot[kTimestampKey] unsignedLongLongValue];

            if (!connected || seq <= 3 || seq % 30 == 0)
            {
                Log::info("MotoricaGameControl",
                    "[BLE stk-game debug] ios read seq=%llu open=%d close=%d connected=%d timestamp=%llu",
                    (unsigned long long)seq, open_level, close_level,
                    connected ? 1 : 0, (unsigned long long)timestamp_ms);
            }

            MotoricaGameControl::get()->updateSnapshot(open_level, close_level,
                connected, timestamp_ms, seq);
        }
    });
    dispatch_resume(g_poll_timer);

    Log::info("MotoricaGameControl",
        "[BLE stk-game debug] ios game control poller started");
}

#endif

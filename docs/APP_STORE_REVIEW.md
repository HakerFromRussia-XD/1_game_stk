# Motorica Kart — App Store review record for 1.0 (28)

## Review Notes — paste into App Store Connect

Motorica Kart opens as Motorica Signal Lab when launched from its app icon.
Motorica Signal Lab is a complete standalone training game and can be reviewed
without an account, network connection, Bluetooth device, Motorica Start, or
any external hardware.

The standalone experience contains three original exercises:

- Precision — navigate the Signal Lab course through twelve target gates;
- Reaction — respond to twenty left/right direction commands;
- Signal Hold — maintain ten requested signal ranges for the required time.

Each exercise calculates a score from 0 to 1000 and presents detailed training
metrics. The app stores the latest twenty results locally in Training History.
No account or personal data is used for these results.

Before starting an exercise, the reviewer can select either:

1. Touch and gyroscope; or
2. Motorica Signal Demonstration.

Motorica Signal Demonstration is a permanent user feature and requires no
hardware. Select "Scripted demonstration" to see the complete sequence:
virtual connection, calibration, signal control, signal loss, automatic pause,
connection recovery, continuation, and the final training result.

Recommended review path:

1. Launch Motorica Kart directly from its app icon.
2. Select Precision, Reaction, or Signal Hold.
3. Set Control source to "Motorica Signal Demonstration".
4. Set Demonstration mode to "Scripted demonstration".
5. Tap "Start Training" and complete or observe the exercise.
6. On the result screen, use Repeat or Return to Motorica Hub.
7. Open Training History to inspect the locally saved result.

Motorica Signal Lab has its own hub, exercise flow, scoring system, local
history, Signal Lab course, visual identity, and Motorica Signal Pilot vehicle.
The standard SuperTuxKart menus, track selection, kart selection, championships
and progression are not exposed in the standalone experience.

The application uses the open-source SuperTuxKart engine. Upstream licenses,
authors, and the complete corresponding source code are disclosed under
"About and Open Source". The full upstream game asset catalog is not bundled
with the standalone application.

An optional integration allows customers with compatible Motorica hardware to
launch additional device-controlled game modes through the separately
distributed Motorica Start app. This integration is not required to review or
use Motorica Signal Lab, and all standalone functionality described above is
available from the app icon.

Source code: https://github.com/HakerFromRussia-XD/1_game_stk

Support: https://hakerfromrussia-xd.github.io/1_game_stk/support/stk/

Privacy: https://hakerfromrussia-xd.github.io/1_game_stk/privacy/stk/

## Response to the previous Guideline 4.3(a) rejection

Thank you for the previous review. We have substantially redesigned the app in
response to Guideline 4.3(a). Build 28 is not a resubmission with only metadata
or cosmetic changes.

The complete upstream SuperTuxKart asset catalog has been removed from the app
bundle. Direct launch now presents Motorica Signal Lab, a standalone training
product with three original exercises, a dedicated Signal Lab course, an
original Motorica Signal Pilot vehicle, two independent input systems, a
fully-featured hardware-free signal simulation, exercise-specific scoring, and
local training history.

SuperTuxKart remains credited as the open-source engine on which the product is
built. Its licenses, authors, and our corresponding source code are available
inside the app and at the source URL above. We respectfully request a new
review of the substantially changed standalone experience in build 28.

## Internal Russian reference

Motorica Kart при прямом запуске открывает законченный самостоятельный
тренажёр Motorica Signal Lab. Для проверки не нужны аккаунт, сеть, Bluetooth,
Motorica Start или внешнее оборудование.

Ревьюверу нужно выбрать одно из трёх упражнений, установить источник управления
«Демонстрация сигналов Motorica», выбрать «Автоматический сценарий» и нажать
«Начать тренировку». Сценарий показывает подключение, калибровку, управление,
потерю сигнала, паузу, восстановление соединения, продолжение и результат.

## Release identity and binary/data boundary

- App Store version: `1.0`.
- Build: `28`.
- Bundle ID: `com.motorica.games.stkttt`.
- Team: `R7M384QD5A` — MOTORICA RESEARCH LLC.
- App Group: `group.com.motorica.start.gamecontrolll`.
- URL scheme: `motorica-stk`.
- App Group is resolved from the single Xcode build setting
  `MOTORICA_GAME_CONTROL_APP_GROUP` in the Info.plist, entitlements, and runtime.
- The standalone app bundle includes `motorica_signal_lab`,
  `motorica_signal_pilot`, and the three Motorica exercise challenges.
- The optional full data package is pinned to `ios-assets-1.0-build28`; it
  contains no executable code, frameworks, dynamic libraries, JavaScript,
  WebAssembly, or AngelScript.

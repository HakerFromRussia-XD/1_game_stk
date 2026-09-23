# Motorica Kart

This repository contains the Motorica-maintained distribution of
[Fluxara Drift](https://github.com/fluxaradrift/fluxara_drift-code), adapted by
**MOTORICA RESEARCH LLC** for integration with the Motorica Start application.

It is a modified, unofficial Fluxara Drift build. This repository and the
applications built from it are not produced, affiliated with, or endorsed by
the Fluxara Drift development team.

## Purpose

The iOS application has two permanent, documented product modes:

- a direct Home Screen launch opens **Motorica Training Hub**, containing the
  Motorica Night Island, Motorica Kiki, and the Motorica Signal Circuit race;
- a valid `motorica-fluxara_drift://` launch from Motorica Start enables local
  game-control snapshots from a compatible Motorica device and the optional
  full Fluxara Drift content catalog;
- Motorica Start and the game exchange control state locally through an Apple
  App Group. The App Group identifier is supplied to entitlements, Info.plist,
  and runtime code from one Xcode build setting to prevent configuration drift.

The full catalog is downloaded only after the user confirms the displayed
size. It contains game data only; executable code and scripts remain in the
reviewed application binary. Direct launches never scan the downloaded full
catalog and work offline without Motorica Start or a Motorica device.

## iOS release identity

| Field | Value |
| --- | --- |
| Product | Motorica Kart |
| Maintainer | MOTORICA RESEARCH LLC |
| App Store version | 1.0 (build 28) |
| Bundle identifier | `com.motorica.games.fluxara_driftttt` |
| Apple team | `R7M384QD5A` |
| App Group | `group.com.motorica.start.gamecontrolll` |
| Motorica Start integration | local App Group and `motorica-fluxara_drift` URL scheme |
| Full asset package | tag `ios-assets-1.0-build28` |

The App Group identifier is intentionally documented without treating it as a
secret. It does not grant access by itself; access is controlled by Apple's
signed entitlements and provisioning profiles.

## Source and release correspondence

The App Store source snapshot and the immutable data release are documented in
[the App Store review record](docs/APP_STORE_REVIEW.md). The `main` branch may
contain later development.

- [Motorica modifications](MODIFICATIONS.md)
- [iOS build instructions](docs/BUILDING_IOS.md)
- [App Store review notes and test flows](docs/APP_STORE_REVIEW.md)
- [Third-party and asset notices](THIRD_PARTY_NOTICES.md)
- [Names and trademark notice](TRADEMARKS.md)
- [Full GPL text and asset-license overview](COPYING)
- [Fluxara Drift credits](data/CREDITS)

## Licensing

The Fluxara Drift program code, including Motorica's modifications in this
repository, is distributed under the GNU General Public License, version 3 or
any later version. See [COPYING](COPYING).

Game data and third-party libraries use several licenses. Their original
license and attribution files remain in `data/` and `lib/`; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for an index.

## Support and privacy

- [Support page](https://hakerfromrussia-xd.github.io/1_game_fluxara_drift/support/fluxara_drift/)
- [Privacy policy](https://hakerfromrussia-xd.github.io/1_game_fluxara_drift/privacy/fluxara_drift/)
- [Motorica website](https://motorica.org/)

## Upstream project

For the official, unmodified game, releases, community support, and general
cross-platform build instructions, visit:

- <https://github.com/fluxaradrift/fluxara_drift-code>
- <https://fluxaradrift.net/>

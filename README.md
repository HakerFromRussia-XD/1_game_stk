# SuperTuxKart for Motorica

This repository contains the Motorica-maintained distribution of
[SuperTuxKart](https://github.com/supertuxkart/stk-code), adapted by
**MOTORICA RESEARCH LLC** for integration with the Motorica Start application.

It is a modified, unofficial SuperTuxKart build. This repository and the
applications built from it are not produced, affiliated with, or endorsed by
the SuperTuxKart development team.

## Purpose

The iOS application is a companion game module for Motorica Start:

- when opened from Motorica Start, it receives local game-control snapshots
  from a compatible Motorica device;
- when opened directly from the Home Screen, it can be reviewed and played
  using the standard touchscreen and motion controls;
- Motorica Start and the game exchange control state locally through an Apple
  App Group. The App Group identifier is supplied to entitlements, Info.plist,
  and runtime code from one Xcode build setting to prevent configuration drift.

The App Store build is intended for unlisted distribution through a direct
link supplied by Motorica Start.

## iOS release identity

| Field | Value |
| --- | --- |
| Product | SuperTuxKart for Motorica |
| Maintainer | MOTORICA RESEARCH LLC |
| Marketing version | 1.0.15 |
| Bundle identifier | `com.motorica.games.stkttt` |
| Apple team | `R7M384QD5A` |
| Motorica Start integration | local App Group and `motorica-stk` URL scheme |
| Corresponding source | tag `ios-appstore-1.0.15` |

The App Group identifier is intentionally documented without treating it as a
secret. It does not grant access by itself; access is controlled by Apple's
signed entitlements and provisioning profiles.

## Source and release correspondence

The preferred source for the App Store version is the immutable
[`ios-appstore-1.0.15`](https://github.com/HakerFromRussia-XD/1_game_stk/tree/ios-appstore-1.0.15)
tag. The `main` branch may contain later development.

- [Motorica modifications](MODIFICATIONS.md)
- [iOS build instructions](docs/BUILDING_IOS.md)
- [Third-party and asset notices](THIRD_PARTY_NOTICES.md)
- [Names and trademark notice](TRADEMARKS.md)
- [Full GPL text and asset-license overview](COPYING)
- [SuperTuxKart credits](data/CREDITS)

## Licensing

The SuperTuxKart program code, including Motorica's modifications in this
repository, is distributed under the GNU General Public License, version 3 or
any later version. See [COPYING](COPYING).

Game data and third-party libraries use several licenses. Their original
license and attribution files remain in `data/` and `lib/`; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for an index.

## Support and privacy

- [Support page](https://hakerfromrussia-xd.github.io/1_game_stk/support/stk/)
- [Privacy policy](https://hakerfromrussia-xd.github.io/1_game_stk/privacy/stk/)
- [Motorica website](https://motorica.org/)

## Upstream project

For the official, unmodified game, releases, community support, and general
cross-platform build instructions, visit:

- <https://github.com/supertuxkart/stk-code>
- <https://supertuxkart.net/>

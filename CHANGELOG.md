# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.3] - Not released yet
### Added
- many additions thanks to [@Phoenyx65535](https://github.com/Phoenyx65535) - _cf._ [PR #29](https://github.com/Lucas-C/undying-dusk/pull/29)
### Fixed
- display final end cut-scene - _cf._ [PR #15](https://github.com/Lucas-C/undying-dusk/pull/15)
- more than 45 typos, thanks to [@Phoenyx65535](https://github.com/Phoenyx65535) - _cf._ [issue #20](https://github.com/Lucas-C/undying-dusk/issues/20)
- broken path to abyss secret in a specific case - _cf._ [PR #24](https://github.com/Lucas-C/undying-dusk/pull/24)
- missing image assets for some tiles - _cf._ [issue #16](https://github.com/Lucas-C/undying-dusk/issues/16). Most new image assets were provided by [@Phoenyx65535](https://www.reddit.com/user/Phoenyx65535/)
- hidden `CTRL G` hint in a book in the Mausoleum - _cf._ [issue #21](https://github.com/Lucas-C/undying-dusk/issues/21)
- reducer over-optimization: this broke the trick to climb over the Mausoleum roof, and was due to `.bonus_atk` not being rendered on some pages. - _cf._ [issue #19](https://github.com/Lucas-C/undying-dusk/issues/19)
- overlapping link to [JourneyToTheEastRocks.ogg](https://chezsoi.org/lucas/undying-dusk/music/AlexandrZhelanov-JourneyToTheEastRocks.ogg) - _cf._ [issue #17](https://github.com/Lucas-C/undying-dusk/issues/17)

## [1.0.2] - 2021-05-12
### Fixed
- abyss secret could not be reached due to a page ID assignment bug
- wrong message about portal when first visiting sage Therel
- visual residual glitch (PAGE UP hint) after taking shortcut over the fire

## [1.0.1] - 2021-05-04
### Added
- extra visual puzzles hints for _portal-activation_ & _shortcut-to-Mausoleum-entrance_ enigmas
- historical map in a book, to help with ballad enigma
### Changed
- text of the _The ballad of the first king_, to better hint at the directions, that have changed

## [1.0.0] - 2021-04-24
### Added
- SFX for spells

### Fixed
- full rewrite of the warp portals system that had glitches

## [0.9.7] - 2021-03-13
### Changed
- made secret path in the woods easier to figure out
- slightly reworked the ending

## [0.9.6] - 2021-03-07
### Fixed
- rendering glitch when facing the well in the woods with both crucifix & empty bottle
- a missing newline during "Seamus through bars" dialog

## [0.9.5] - 2021-03-05
### Added
- new monster & puzzle to defeat it : the Gorgon!
- new books-based rotating-lever puzzle to leave the Mausoleum
- Cauldron fire boost is displayed more explicitly
- Displaying water on minimap
- More helpful hints than _"Trust your instinct: no need to go back for now"_
- 3 distinct hit zones during Storm Dragon battle
- phase 2 of the final boss battle

### Changed
- Improved hints in Zuruth plain, for bottle & hidden chest
- Tried to make fish-on-a-stick puzzle funnier & simpler, in Mausoleum
- Made mimics more diverse

### Fixed
- secrets were incorrectly reported to the Hall of Fame, due to a pages count over-optimization
- Removed useless message in village when portal is not open yet (_"Trust your instinct: no need to go back for now"_)

### Removed
- boulder on Cedar Village exit, no more needed thanks to the gorgon

## [0.9.4] - 2020-11-03
Special thanks to Maxime Lemanach for the detailed feedbacks that helped me
improve the game a lot in this new release!

### Added
- hint in templar library on treasure hidden behind boulder trap
- hint after polishing the sword:
> No creature of darkness can match this weapon!
- Sage Therel new dialog line
- made goblin & fish enigma lengthier & funnier (hopefully)
- SFXs for last 2 enemies attacks
- GIF trailer (& script to generate it)

### Changed
- blocked Templar Academy entrance once player has > 30 gold || great sword

### Fixed
- _Mido Sesame_ password destination fix
- made enigma to pass over Mausoleum easier to figure out

## [0.9.3] - 2020-10-18
### Added
- now also releasing a ZIP file including Sumatra PDF and a `.bat` launcher
- Platino sprite on victory screen with 4 secrets
- URL on victory page pointing to the new [hall of fame](https://chezsoi.org/lucas/undying-dusk/hall-of-fame) page
- extra hint on the Monastery Trail:
> The whispering wind tells you that demons fear blessed liquids.
- Seamus now provides an extra hint in the Zuruth Plains:
> The Empress castle stands further behind the canal. Go look if you can see it despite the darkness.
### Changed
- base music URL now is <https://chezsoi.org/lucas/undying-dusk/music/>
### Fixed
- `HP drain` can no longer bring a monster HP above its maximum

## [0.9.2] - 2020-10-08
### Added
- Now mentioning more largely supported _ALT+🡄_ pdf reader shortcut, instead of _backspace_ only supported by Sumatra
### Fixed
- message when shadow soul dodged the crucifix erroneously mentioned an imp

## [0.9.1] - 2020-10-08
### Added
- link to [SubReddit](https://www.reddit.com/r/UndyingDuskPdfGame/) in credits
### Fixed
- arrows navigation in "HOW TO PLAY" section - fix [#1](https://github.com/Lucas-C/undying-dusk/issues/1) & [#2](https://github.com/Lucas-C/undying-dusk/issues/2) - thanks @Anaguiros for reporting those !

## [0.9.0] - 2020-10-07
First version published on GitHub.
Pre-release aimed at playtesters.

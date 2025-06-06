# Pipeline Changelog
All changes to the pipeline will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Version numbering follows the `MAJOR.MINOR.PATCH` (ex: `1.11.3`) syntax:

- `MAJOR`: for big changes, like inner architecture
- `MINOR`: for new functionalities, like adding hardware and corresponding servers and clients.
- `PATCH`: when fixing bugs or adding very small details for previous MINOR functionality.

Unreleased version holds ongoing changes towards next version and will be numbered
`MAJOR.MINOR.PATCH-dev` (ex: `1.12.0-dev`)

Changes are kept under subsections:

- `New` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

Only major refactoring improvements or functional changes should be noted.

--------------------------------------------------------------------------------
## [8.4] - 2025-03-14 - Fix previous year bug
#### Fixed
- Also substitute current_year-1

## [8.3] - 2025-02-07 - Fix errors from bulk
#### Fixed
- empty entities bug
- empty timespan bug
- remove unparsable patterns
- 24:00:00 parsing bug
#### Changes
- refactored SUTime filters

## [8.1] - 2025-01-13 - Pipeline Optimizations
#### Fixed
- remove duplicated now really removes 
#### Changes
#### New

## [7.9] - 2024-12-31 - Pipeline Optimizations
#### Fixed
- fixed prevdate bug 
- dash issues
- nearest_year regexp
- shortdate expanding
#### Changed
- added SolarOrbiter synonyms
- short date to month duration
- more DataBanks timespans
#### New
- more interval detection rules

## [6.1] - 2024-09-11 - Confidence Index
#### Fixed
- added 'D' to struct: "conf" is fixed
- added 'R' to struct: from duration_to_mission()
#### Changed
- added DEMETER instruments and region
- find the closest mission from duration changed with rank
- de-normalize 'conf' indices

## [5.2] - 2024-08-28 - August changes
#### Changed
- Inserted more synonyms and instruments
- Keep '/' in text to keep 'EUI/HRI'

## [5.1] - 2024-07-05 - Remove duplicated events, and timespan inconsistency
#### Fixed
- swapped entities steps 5 and 6: syns before instr recog
#### Changed
#### New
- add one step to remove duplicated events 
- add one step to clean events out of timespan

## [4.5] - 2024-06-28 - Fix Duration/Mission linking
#### Fixed
- missing instruments at step 7
- missing DURATION type at step 16

## [4.4] - 2024-06-25 - Fix step 16
#### Fixed
- no previous date bug
- missing region type
#### New
- tiny method to extract struct from list

## [4.3] - 2024-06-20 -
#### Fixed
- recognise trailing quotes
- remove PVO
#### Changed
- set duration to previous date

## [4.1] - 2024-06-18 - Remove overlapping missions
#### Fixed
- fix empty sutime struct bug
#### Changed
- overlapped missions becomes uniq

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

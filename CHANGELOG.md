# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Version numbering will follow those principles:
- MAJOR: for big changes, like inner architecture
- MINOR: for new functionalities, like adding hardware and corresponding servers and clients.
- PATCH: when fixing bugs or adding very small details for previous MINOR functionality.

`Unreleased` version holds ongoing changes.

Changes are kept under subsections:
- `New` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

Should be noted only functional changes,
or major refactoring improvements.

## [M.m.p] - yyyy-mm-dd - Global description of changes
### Fixed
### Changed
### New

--------------------------------------------------------------------------------

## [0.3.0] - - 2023-03-01 - Jobs displayed - Minor Release
### Changed
- More style enhancement
### New
- Del papers
- Add (all) from istex
- Functional tests with Selenium
- Jobs status displayed

## [0.3.0-pre.3] - - 2023-02-17 - Get from Istex
### Changed
- New buttons style (Orange)
### New
- Istex requests update table of articles
- Istex paper uploadable

## [0.3.0-pre.2] - - 2023-02-15 - Add download from url field
### Changed
- All tests done with pytest and fixtures
### New
- Upload_from_url field
- Add TestConfig with sqlite in-memory

## [0.3.0-pre.1] - 2023-02-10 - CI/CD Enhancements
### Changed
- Removed *jpg and other results from git repo
- Updated files formats
### New
- Added github actions for tests and deploy
- Added precommit checks

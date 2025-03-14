# Main BibHelioTech Changelog
All notable changes to this project will be documented in this file.

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
## [2.0.0] - 2025-03-14 - Refactor DB
#### Fixed
- tests now all run
#### Change
- new links between paper and hp_event

## [1.7.3] - 2025-03-10 - Fixes before bulk import
#### New
- bulk add from subset
- add sutime server

#### Changed
- catalog file header
- catalogs/page front design
- move events stats
- empty instr. becomes single space 
- insert http://doi.org link in catalogs

## [1.6.0] - 2025-02-20 - Enhance Display
#### Changed
- Pages with many events load faster
- New catalog format more AMDA compliant
- Download catalog through POST and modal dialog

## [1.5.2] - 2025-02-13 - Stats reports
#### New
- Plot NConf distribution
- Plot Events distribution
- Cached data mechanism

## [1.4.2] - 2025-02-10 - Refactor Events Requests
#### Changed
- NConf calculation optimized
- Missions sorting on catalogs page

## [1.3.3] - 2025-02-07 - Partial bulk by CLI
#### Fixed
- Status display
#### Changed
- Pipeline refactoring
- Web status refactoring
#### New
- Filtering by status
- Add pagination for many pages

## [1.2.0] - 2025-01-22 - First Bulk prototype
#### Fixed
- pipeline bugs
#### New
- cli commands bulk run pipeline on files
- allow partial pipeline through web

## [1.0.0] - 2025-01-14 - Latest Pipeline changes
#### Fixed
- remove duplicated

## [0.20.1] - 2024-12-31 - Pipeline changes
#### Fixed
#### Changed
- raw files cleaner keeps normal raws
#### New
- Upgraded web interface
- Sutime DURATION analysis
- More Sutime rules, see PIPELINE_CHANGELOG


## [0.19.2] - 2024-10-09 - Post Filtering Form
#### Changed
- Catalogs page is now form
#### New
- Download button on events search page (/catalogs)
- Events form/filtering by duration and NConf
- Events datatables/sorting
- Admin page adds catalogs to db

## [0.18.0] - 2024-09-27 - Pipeline optimizations
#### Fixed
- Catalog bugs, see pipeline changes
#### Changed
- Force db add after new pipeline
#### New
- NConf now normalised on whole db
- More CLI cmd: clean/updates events

## [0.17.4] - 2024-09-11  - Confidence Index
#### Fixed
- Add catalog to db fixed 
#### New
- Events displayed in sortable table
- Conf index is normalized on the whole DB

## [0.16.0] - 2024-08-28  - August tasks
#### Fixed
- Fix sutime indexes in web pipeline visu
#### Changed
- Moved catalogs dir from docker mounted volume
- Ignore DATA/ and move databank files 
- Docker files doesn't use USER_UID/GID anymore
#### New
- CLI shows databank content

## [0.15.0] - 2024-08-12  - Run pipeline through CLI 
#### Changed
- Dynamically update pipeline version
#### New
- Cli command runs pipeline
- Cli command cleans papers' raw files

## [0.14.0] - 2024-07-17  - Post filter events
#### Fixed
- Swap steps 5 and 6
#### Changed
- Post filter events
#### New

## [0.13.0] - 2024-07-01  - New Duration/Mission linking
#### Fixed
- fix empty sutime struct bug
- overlapped missions becomes uniq
#### Changed
- new link from Duration to Mission
- rewrite pipeline methods
#### New
- show changelog


## [0.12.0] - 2024-06-13 Enhance Pipeline Analysis
#### Fixed
- Empty catalog bug
#### Changed
- Mission to Event detection
- Pipeline analysis refactoring (json dumping)
#### New
- Cli papers tools (clone, change)
- Show all Entities Steps in analysis

## [0.11.0] - 2024-05-28 Fix mission detection
#### Fixed
- Detect mission into parenthesis
#### Changed
- Refactor catalogs generation methods again
#### New
- Catalog lines formating now align
- Show PipelineVersion on page

## [0.10.0] - 2024-05-27 Insert and show PipelineVersionNum
#### Changed
- Refactor catalogs generation code into rewritten methods
#### New
- Pipeline_Version inserted in db and displayed

## [0.9.0] - 2024-05-14 Fix Sutime Filter (2)
#### Fixed
- Now keep DURATION  without 'timex-value'
#### New
- Refactoring: SutimeTools.py holds analysis methods 

## [0.8.0] - 2024-05-06 Show Multi Mode pipeline
#### New
- new disp_mod in pipeline route
- views raw-json and analysed-json 

## [0.7.0] - 2024-05-03 - Enhance Sutime Presentation
#### Changed
- show whole sutime struct in tooltips
#### New
- request papers by ark
- show analysed json

## [0.6.0] - 2024-04-12 - Fixed Sutime Filter
#### Changed
- Custom english file removed from 

## [0.5.1] - 2024-03-28 - Changed Task display
#### Changed
- Task status update while running

## [0.5.0] - 2024-03-22 - Enhance Task Management
#### Fixed
- Paper path bug

#### Changed
- Paper model embeds more attributes
- Task status management
- Tests rewriting

#### New
- Paper page with links

## [0.4.5] - 2024-02-14 - Show Sutime Pipeline
#### New
- Produce json extraction at pipeline steps
- Display text/html with highlight from json

## [0.4.4] - 2024-01-15 - Enhance Docker
#### Changed
- Simplified Docker container build
#### New
- Allow doi on cli

## [0.4.3] - 2024-01-08 - Bypass Grobid
#### Changed
- Speed up TXT pipeline
- Enhance CLI
- Split Entities Pipeline
- Get Doi from Istex Api

## [0.4.1] - 2023-03-17 - Fix red circle
#### Fixed
- remove red circle when catalogue added
- pre-commit.ci doesnt fail any more

## [0.4.0] - 2023-03-17 - 4th Prototype
#### Fixed
- read bht_env in any case
#### Changed
- IHM enhancements
- index page is catalog now
- store task status and show
#### New
- cli cmd to update db from files
- add global stats
- set htpasswd authentication on the whole site
- add the pre-commit.ci workflow

## [0.4.0-pre.3] - 2023-03-13 - DB Migration
#### New
- db migration with alembic
- logging system

## [0.4.0-pre.2] - 2023-03-11 - Refactor tests structure
#### Changed
- tests tree

## [0.4.0-pre.1] - 2023-03-10 - Build and download Catalog by mission
#### Fixed
- HpEvent hour in date bug
#### New
- Catalogs page allows mission selecting and catalog download
- Mission button with num events
- Catalog models contains hpevents
- Catalog to db and db to Catalog tools
- RESTFull api endpoints

## [0.3.0] - 2023-03-01 - Display jobs statuses
#### Changed
- More style enhancement
#### New
- Del papers
- Add (all) from istex
- Functional tests with Selenium
- Jobs status displayed

## [0.3.0-pre.3] - 2023-02-17 - Get from Istex
#### Changed
- New buttons style (Orange)
#### New
- Istex requests update table of articles
- Istex paper uploadable

## [0.3.0-pre.2] - 2023-02-15 - Add download from url field
#### Changed
- All tests done with pytest and fixtures
#### New
- Upload_from_url field
- Add TestConfig with sqlite in-memory

## [0.3.0-pre.1] - 2023-02-10 - CI/CD Enhancements
#### Changed
- Removed *jpg and other results from git repo
- Updated files formats
#### New
- Added github actions for tests and deploy
- Added precommit checks

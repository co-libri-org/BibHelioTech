# BibHelioTech

![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/RichardHitier/BibHelioTech?label=Version)
[![DOI](https://zenodo.org/badge/599997124.svg)](https://zenodo.org/badge/latestdoi/599997124)
[![License](https://img.shields.io/github/license/ADablanc/BibHelioTech.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/RichardHitier/BibHelioTech/main.svg)](https://results.pre-commit.ci/latest/github/RichardHitier/BibHelioTech/main)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/RichardHitier/BibHelioTech/unittest_ci.yml?label=Tests)
![GitHub repo size](https://img.shields.io/github/repo-size/RichardHitier/BibHelioTech)

## BibHelioTech project description

BibHelioTech is a program for the recognition of temporal expressions and entities (satellites, instruments, regions)
extracted from scientific articles in the field of heliophysics.

It was developed at IRAP (Institut de Recherche en Astrophysique et Planétologie, Toulouse https://www.irap.omp.eu/) in
the frame of an internship by A. Dablanc supervised by V. Génot.

Its main purpose is to retrieve events of interest which have been studied and published, and associate them with the
full context of the observations. It produces standardized catalogues of events (time intervals, satellites,
instruments, regions, metrics) which can then be exploited in space physics visualization tools such as
AMDA (http://amda.cdpp.eu/).

## Manual Installation

Runs with python3.12

### Dependencies

Make sure to fulfill any dependency first:

    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install wheel
    pip install -r requirements.txt

### Install sutime dependencies and update language file

on the linux system

    sudo apt install -y openjdk-8-jdk openjdk-8-jre maven zip
    sudo update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java

on the pip venv

    mvn dependency:copy-dependencies -DoutputDirectory=./jars -f $(python -c 'import importlib.util; import pathlib; print(pathlib.Path(importlib.util.find_spec("sutime").origin).parent / "pom.xml")')
    cd ./resources
    zip -u ../venv/lib/python3.12/site-packages/sutime/jars/stanford-corenlp-4.0.0-models.jar   edu/stanford/nlp/models/sutime/english.sutime.txt

you should see the following message, which is ok

```shell
        zip warning: Local Entry CRC does not match CD: edu/stanford/nlp/models/sutime/english.sutime.txt
 (deflated 78%)
 
updating: edu/stanford/nlp/models/sutime/english.sutime.txt
```



## Quick run

configuration:

    cp resources/bht-config.yml-dist bht-config.yml
    $(EDITOR) bht-config.yml

    sudo apt-get install apache2-utils
    htpasswd -c .htpasswd the_user_name

    python manage.py create_db

run website only:

    FLASK_DEBUG=true FLASK_APP=web flask run --host=0.0.0.0

run with pipeline capabilities:

    docker run --rm --name redis_for_bht -d -p 6379:6379 redis
    python manage.py run_worker

more over, for bulk purpose, run a Sutime Server

    uvicorn fastapi_sutime:app --host 0.0.0.0 --port 8000

but if multi processes is needed

    uvicorn --workers 4 fastapi_sutime:app --host 0.0.0.0 --port 8000

or for high load production server

    gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 fastapi_sutime:app



## Docker Install

Please, use a recent docker compose plugin version: https://docs.docker.com/compose/install/linux/

After first install (git clone),

1. add 2 files
    * `htpasswd -b -c .htpasswd 'user' 'passwd'`
    * `cp resources/bht-config.yml-dist bht-config.yml`
1. build and run:
    * `docker compose build`
    * `docker compose up -d`
1. or you may want to listen to another port than :80:
   * `WEB_PORT=8085 docker compose up -d`

Then make sure you have created the database:

    docker compose exec web python manage.py create_db

### Web interface

We use docker compose for the link between bibheliotech and dependency containers.

build it first

    docker compose build

then run all

    docker compose up --detach

- will launch all services
- and flask application

access web interface through `http://localhost` , or any domainname reverse proxying to the host.

If you'd better run on another port, set the WEB_PORT environment variable:

    WEB_PORT=8080 docker compose up -d

### Dev mode

An override compose file is available in root dir

    cp .env.bht-dist .env
    $(EDITOR) .env    # to set you own UID and GID from `id -u` `id -g`
    docker compose down
    cp docker-compose.override.yml-dist docker-compose.override.yml
    docker compose build
    docker compose up -d

Bibheliotech docker container is then linked with the current `DATA/` directory.

Current web dir is also mounted as volume so you can change python code without rebuild.

Mainly runs flask in debug mode (skipping gunicorn), and
linking host files to container for live update.

#### FLASK_ENV

This environment variable is deprecated. We wont use it.
The FLASK_DEBUG var can be set through cli option:

    BHT_ENV=development flask --debug --app bht_web run

But we could also want to run the application in development or testing mode.
For that, you can trigger the create_app() passing it the BHT_ENV variable:

    BHT_ENV=development flask --debug --app bht_web run

BHT_ENV can take 3 possible values:

- 'production' (default)
- 'development'
- 'testing'

### Password protection with flask-htpasswd

If you wish to run the application on the production mode, please make sure you have created the file:

    apt-get install apache2-utils
    htpasswd -c .htpasswd the_user_name

### Running files treatment under ./DATA/

This will compute all `*pdf` papers in `./DATA/` directory

run from your host directory

    docker compose run --rm web python bht

or run inside container itself

    docker compose run --rm web bash

on single file:

    PYTHON_PATH=. python bht -f test-upload/angeo-28-233-2010.pdf

or on the whole DATA/ directory:

    PYTHON_PATH=. python bht

## Continuous integration and deployment

### db migration

In order to make sure we use the latest db structure on distant deployed versions,
we recommend the usage of the SqlAlchemy migration tool, Alembic, provided by flask-migrate.

It needs the environment variable FLASK_APP to be set.

After db structure was changed, you can save a migration script on development side:

    FLASK_APP=web flask db migrate
    git add migrations
    git commit -m "Db migration V-xx.xx"

troubleshooting:

if you get the `ERROR [flask_migrate] Error: Target database is not up to date.`

then try

    FLASK_APP=web flask db stamp head

then, again

    FLASK_APP=web flask db migrate

and follow with `git add/commit`

Then, after deployment on server side, change database on the fly:

    FLASK_APP=web flask db upgrade

If the app is running through docker then try

    docker compose run FLASK_APP=web flask db upgrade

Also see https://flask-migrate.readthedocs.io/en/latest/

### flake8 linter

flake8, along with its pep8-naming plugin allow to make sure our code is properly formated before commitinge.
give it a try:

    cp resources/flake8 ./.flake8
    flake8

### pre-commit

    cp resources/pre-commit-config.ymal  .pre-commit-config.yaml
    pip install pre-commit
    pre-commit install

then any commit will run the plugins to check files format, and python style.

As a first try, you can

    pre-commit run --all-files

it also embeds calls to flake8 and black plugin.

To make sure you follow those formats, you can install plugins.
For pycharm:

https://black.readthedocs.io/en/stable/integrations/editors.html
https://pypi.org/project/flake8-for-pycharm/

### tests

To be run from your workdir with venv activated, assuming requirements have been installed.

Make sure to launch grobid and redis through docker first:

    docker compose -f docker-compose.tests.yml up -d
    cp resources/bht-config.yml-dist ./bht-config.yml
    . venv/bin/activate
    python -m pytest tests

see tests/README.md for more info on tests

### GitHub actions

GitHub actions yml files are stored in the `.github/workflows/` directory.

- one for deployment to the ovh dev server
- one for running integration tests

usage tips:

    git push -f origin HEAD:ovh-deploy
    git push -f origin HEAD:test

### ovh-deploy: see above

## BHT User guide

First Follow previous instruction for

python environment and dependencies

follow 'manual installation' section, STEP 1 and STEP 2

config files ( ./bht-config.yml,  )

    cp ./resources/grobid-client-config.json-dist ./grobid-client-config.json
    cp resources/bht-config.yml-dist bht-config.yml

Then make sure the GROBID server is running:

    docker compose -f docker-compose.tests.yml up ( --detach )

Copy any Heliophysics articles in pdf format under ./DATA/Papers/

Now look at how the main pipeline works

    PYTHONPATH=. python bht --help

run it on one file,

    cp DATA/Papers-dist/angeo-39-379-2021.pdf  .
    PYTHONPATH=. python bht -f angeo-39-379-2021.pdf

then look at results:

    ls angeo-39-379-2021/

Or may be try it on a whole directory

    cp -r DATA/Papers-dist papers
    PYTHONPATH=. python bht -d papers
    find papers/ -cmin -10  -name \*txt

Optionally if you want to have AMDA catalogues by satellites, you need to run "SATS_catalogue_generator.py".

### Tips, Tricks and logs

Some raw files where created randomly.
A new manager tool is available for that:

    python manage.py clean_raws --no-dry-run 3

`3` being the id of the paper we want to clean.

    for i in {1..15} ;do python manage.py clean_raws --no-dry-run $i; done

to erase all papers' unwanted raw files from id 1 to 15.

## Versioning and git workflows

`VERSION.txt` holds the current project version in a semver model. (Also see `CHANGELOG.md`)

Each delivery stage is tagged `0.X.0` as the `1.0.0` goal will be the first major release that is not already reached.

While going towards a minor release, the project reaches some intermediate steps:
call it an agile sprint, or a git feature branch.

Each of those steps is labelled with the version number, followed by the '.pre' keyword, and a number for the step.

For example, lets say we are heading towards the `0.3.0` goal, and that we're on the fifth sprint after the `0.2.0`
release, the
version number will be `0.3.0.pre-5`

While on a branch, the sprint is not fullfilled, thus `VERSION.txt` should contain `0.3.0.pre-5-dev` .

We're using a basic git branch model, where each feature or sprint is a branch, merged in `main` branch for delivery.

The merges are done with the `--no-ff` option, so the history can show the branch/sprints worklow.

Any VERSION change is git tagged with `v` prepended. In the later example, that will be

    git tag -a v0.3.0.pre-5 -m "v0.3.0.pre-5 Release"
    git push origin --tags

## Manual run (without docker)
### Installation and requirements

1. copy resources/*dist config file to there destination and edit
2. install Sutime java dependencies
3. install pip dependencies
3. insert english-custom.txt to java pip package

### Run each component

1. run nginx
2. run redis
3. run flask app for web
4. run (1,n) flask worker(s) with click cli interface
5. run fastapi embedding Sutime


## Manual installation (the old way)

You would be advised to look at `./Dockerfile` for more tips.

STEP 1: install all dependency

1. install system dependencies
   sudo apt install mvn

1. install pip dependencies

```
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install wheel
    pip install -r requirements.txt
```

1. Install SUTime Java dependencies, more details on: https://pypi.org/project/sutime/
1. Update the `edu/stanford/nlp/models/sutime/english.sutime.txt` under jars/stanford-corenlp-4.0.0-models.jar/

STEP 2: tesseract 5.1.0 installation (Ubuntu example)

    sudo apt update
    sudo add-apt-repository ppa:alex-p/tesseract-ocr-devel
    sudo apt install -y tesseract-ocr
    sudo apt update
    tesseract --version

STEP 3: GROBID (0.7.1) installation

* install GROBID under ../
* Follow install instruction on: https://grobid.readthedocs.io/en/latest/Install-Grobid/
* Make sure you have JVM 8 used by default !

or run a grobid docker container

STEP 4: GROBID python client installation

* pip package should have been installed with requirements.txt
* copy grobid-client-config.json-dist grobid-client-config.json

## Jupyter Notebooks

    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-nb.txt
    jupyter notebook notebooks/

* plot intervals

## License

If you use or contribute to BibHelioTech, you agree to use it or share your contribution following the LICENSE file.

## Authors

* [Axel Dablanc](axel.alain.dablanc@gmail.com)
* [Vincent Génot](vincent.genot@irap.omp.eu)
* [Richard Hitier](hitier.richard@gmail.com)

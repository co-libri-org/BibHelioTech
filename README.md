# BibHelioTech

[![DOI](https://zenodo.org/badge/515186537.svg)](https://zenodo.org/badge/latestdoi/515186537)
[![License](https://img.shields.io/github/license/ADablanc/BibHelioTech.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)


![GitHub repo size](https://img.shields.io/github/repo-size/RichardHitier/BibHelioTech)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/RichardHitier/BibHelioTech/unittest_ci.yml?label=Tests)
![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/RichardHitier/BibHelioTech?label=Version)



## BibHelioTech project description
BibHelioTech is a program for the recognition of temporal expressions and entities (satellites, instruments, regions) extracted from scientific articles in the field of heliophysics.

It was developed at IRAP (Institut de Recherche en Astrophysique et Planétologie, Toulouse https://www.irap.omp.eu/) in the frame of an internship by A. Dablanc supervised by V. Génot.

Its main purpose is to retrieve events of interest which have been studied and published, and associate them with the full context of the observations. It produces standardized catalogues of events (time intervals, satellites, instruments, regions, metrics) which can then be exploited in space physics visualization tools such as AMDA (http://amda.cdpp.eu/).

## Docker image building

Please, use a recent docker compose plugin version: https://docs.docker.com/compose/install/linux/

After first install (git clone), `docker compose build` and `docker compose up -d`,
make sure you have created the database:

    docker compose run -it   web python manage.py create_db

### Web interface

We use docker compose for the link between bibheliotech and dependency containers.


build it first

    docker compose build

then run all

    docker compose up --detach

- will launch all services
- and flask application

access web interface through `http://localhost` , or any domainname reverse proxying to the host.

If you'd better run on another port, edit the nginx service in the `docker-compose.yml` file.

### Dev mode

An override compose file is available in `ressources/` dir

    cp .env-dist .env
    $(EDITOR) .env    # to set you own UID and GID from `id -u` `id -g`
    docker compose down
    cp docker compose.override.yml-dist docker compose.override.yml
    docker compose build
    docker compose up -d

Bibheliotech docker container is then linked with the current `DATA/` directory.

Current web dir is also mounted as volume so you can change python code without rebuild.

Mainly runs flask in debug mode (skipping gunicorn), and
linking host files to container for live update.

### Running files treatement under ./DATA/

This will compute all `*pdf` papers in `./DATA/` directory

run from your host directory

    docker compose run --rm bibheliotech python bht

or run inside container itself

    docker compose run --rm bibheliotech bash
    PYTHON_PATH=. python bht

## Continuous integration and deployment

Make sure to fullfill any dependency first:

    pip install -r requirements-tests.txt

### flake8 linter

flake8, along with its pep8-naming plugin allow to make sure our code is properly formated before commitinge.
give it a try:

    cp ressources/flake8 ./.flake8
    flake8

### pre-commit

    cp ressources/pre-commit-config.ymal  .pre-commit-config.yaml
    pip install pre-commit
    pre-commit install

then any commit will run the plugins to check files format, and python style.

As a first try, you can

    pre-commit run --all-files

it also embeds calls to flake8 and black plugin.

### tests

either run on your workdir, but launch grobid and redis first:

    docker-compose -f docker-compose.tests.yml
    cp ressources/bht-config.yml-dist ./bht-config.yml
    cp ressources/pytest.ini-dist ./pytest.ini
    pytest

or use the whole docker stack

    cp docker-compose.override.yml-dist docker-compose.override.yml
    docker compose up -d --build
    docker compose run web pytest

### github actions

Github actions yml files are stored in  the `.github/workflows/` directory.

- one for deployment to the ovh dev server
- one for running integration tests

usage tips:

    git push -f origin HEAD:ovh-deploy
    git push -f origin HEAD:test

### ovh-deploy: see above

## Manual installation

You would be advised to look at `./docker/Dockerfile` for more tips.

STEP 1: install all dependency

1. install pip dependencies
```
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install -r requirements.txt
```
1. Install SUTime Java dependencies, more details on: https://pypi.org/project/sutime/
1. Update the `edu/stanford/nlp/models/sutime/english.sutime.txt` under  jars/stanford-corenlp-4.0.0-models.jar/


STEP 2: tesseract 5.1.0 installation (Ubuntu exemple)

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

## User guide
Make sure the GROBID server is running

Copy any Heliophysics articles in pdf format under ./DATA/Papers/

Now run the main pipeline:

    python bht

Optionally if you want to have AMDA catalogues by satellites, you need to run "SATS_catalogue_generator.py".

## Versionning and git workflows

`VERSION.txt` holds the current project version in a semver model. (Also see `CHANGELOG.md`)

Each delivery stage is tagged `0.X.0` as the `1.0.0` goal will be the first major release that is not already reached.

While going towards a minor release, the project reaches some intermediate steps:
call it an agile sprint, or a git feature branch.

Each of those steps is labelled with the version number, followed by the '.pre' keyword, and a number for the step.

For example, lets say we are heading towards the `0.3.0` goal, and that we're on the fifth sprint after the `0.2.0` release, the
version number will be `0.3.0.pre-5`

While on a branch, the sprint is not fullfilled, thus `VERSION.txt` should contain `0.3.0.pre-5-dev` .

We're using a basic git branch model, where each feature or sprint is a branch, merged in `main` branch for delivery.

The merges are done with the `--no-ff` option, so the history can show the branch/sprints worklow.

Any VERSION change is git tagged with `v` prepended. In the later example, that will be

    git tag -a v0.3.0.pre-5 -m "v0.3.0.pre-5 Release"
    git push origin --tags

## License

If you use or contribute to BibHelioTech, you agree to use it or share your contribution following the LICENSE file.

## Authors
* [Axel Dablanc](axel.alain.dablanc@gmail.com)
* [Vincent Génot](vincent.genot@irap.omp.eu)
* [Richard Hitier](hitier.richard@gmail.com)

# BibHelioTech

[![DOI](https://zenodo.org/badge/515186537.svg)](https://zenodo.org/badge/latestdoi/515186537)
[![License](https://img.shields.io/github/license/ADablanc/BibHelioTech.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)
![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/ADablanc/BibHelioTech)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/ADablanc/BibHelioTech)
![GitHub repo size](https://img.shields.io/github/repo-size/ADablanc/BibHelioTech)
[![GitHub issues](https://img.shields.io/github/issues/ADablanc/BibHelioTech)](https://github.com/ADablanc/BibHelioTech/issues)

## BibHelioTech project description
BibHelioTech is a program for the recognition of temporal expressions and entities (satellites, instruments, regions) extracted from scientific articles in the field of heliophysics.

It was developed at IRAP (Institut de Recherche en Astrophysique et Planétologie, Toulouse https://www.irap.omp.eu/) in the frame of an internship by A. Dablanc supervised by V. Génot.

Its main purpose is to retrieve events of interest which have been studied and published, and associate them with the full context of the observations. It produces standardized catalogues of events (time intervals, satellites, instruments, regions, metrics) which can then be exploited in space physics visualization tools such as AMDA (http://amda.cdpp.eu/).

## Docker image building

### Web interface

We use docker-compose for the link between bibheliotech and grobid containers.


build it first

    cp .env-dist .env
    $(EDITOR) .env    # to set you own UID and GID from `id -u` `id -g`
    docker-compose build

run all

    docker-compose up --detach

- will launch grobid server
- and flask application

access web interface through `localhost:8000` (edit docker-compose.yml in case)

### Volumes

bibheliotech docker container is linked with the current `DATA/` directory, that you can populate
and `run bht` on your own datas.

First make sure there are pdf document in `DATA/Papers/` before running.

It is also possible to link current dir as volume so you can change python code without rebuild.
To do so, change the volume instruction in `docker-compose.yml`.


### Running files treatement under ./DATA/

This will compute all `*pdf` papers in `./DATA/` directory

run from your host directory

    docker-compose run --rm bibheliotech python bht

or run inside container itself

    docker-compose run --rm bibheliotech bash
    python bht

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

## License

If you use or contribute to BibHelioTech, you agree to use it or share your contribution following the LICENSE file.

## Authors
* [Axel Dablanc](axel.alain.dablanc@gmail.com)
* [Vincent Génot](vincent.genot@irap.omp.eu)
* [Richard Hitier](hitier.richard@gmail.com)

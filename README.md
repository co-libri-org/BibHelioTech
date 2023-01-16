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

## Installation guide

You would be advised to look at `./docker/Dockerfile` for more tips.

STEP 1: install all dependency

* On your shell, run: `pip install -r requirements.txt`
* Install SUTime Java dependencies, more details on: https://pypi.org/project/sutime/ 
* Put the "english.sutime.txt" under sutime install directory, jars/stanford-corenlp-4.0.0-models.jar/edu/stanford/nlp/models/sutime/


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

STEP 4: GROBID python client installation

* install GROBID python client under ../
* Follow install instruction on: https://github.com/kermitt2/grobid_client_python 

## User guide
Put Heliophysics articles in pdf format under BibHelio_Tech/DATA/Papers.

You just have to run "MAIN.py".

Optionally if you want to have AMDA catalogues by satellites, you need to run "SATS_catalogue_generator.py".

## License

If you use or contribute to BibHelio_Tech, you agree to use it or share your contribution following the LICENSE file.

## Authors
* [Axel Dablanc](axel.alain.dablanc@gmail.com)
* [Vincent Génot](vincent.genot@irap.omp.eu)

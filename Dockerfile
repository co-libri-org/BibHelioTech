FROM ubuntu:23.10 as bht-prod
LABEL maintainer="Benjamin Renard <benjamin.renard@irap.omp.eu>,\
                  Richard Hitier <hitier.richard@gmail.com>"

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
#    curl \
#    git \
    maven \
    openjdk-8-jdk \
    openjdk-8-jre \
    poppler-utils \
#    python3 \
#    python3-pip \
    python3-venv \
    software-properties-common \
    unzip \
#    vim \
#    wget \
    zip && \
    rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:alex-p/tesseract-ocr && \
    apt install -y tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java

ARG USER_UID
ARG USER_GID

RUN userdel -r ubuntu
RUN groupadd --gid $USER_GID bibheliotech && \
    useradd --uid $USER_UID --gid $USER_GID -ms /bin/bash bibheliotech

WORKDIR /home/bibheliotech

ENV VIRTUAL_ENV=/home/bibheliotech/venv
RUN python3 -m venv $VIRTUAL_ENV &&\
    . ./venv/bin/activate &&\
    pip install --upgrade pip
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install -U pip sutime && \
    mvn dependency:copy-dependencies -DoutputDirectory=./jars -f $(python -c 'import importlib; import importlib.util; import pathlib; print(pathlib.Path(importlib.util.find_spec("sutime").origin).parent / "pom.xml")')

# RUN git clone https://github.com/ADablanc/BibHelioTech.git
WORKDIR /home/bibheliotech/BibHelioTech
COPY ./requirements.txt ./requirements.txt
RUN pip install wheel && pip install -r requirements.txt

COPY ./resources ./resources
WORKDIR /home/bibheliotech/BibHelioTech/resources
RUN jar uf $VIRTUAL_ENV/lib/python3.11/site-packages/sutime/jars/stanford-corenlp-4.0.0-models.jar \
           edu/stanford/nlp/models/sutime/english.sutime.txt

WORKDIR /home/bibheliotech/BibHelioTech
COPY . .
RUN cp ./resources/grobid-client-config.json-dist ./grobid-client-config.json &&\
    cp ./resources/bht-config.yml-dist ./bht-config.yml

RUN chown -R bibheliotech:bibheliotech /home/bibheliotech/
USER bibheliotech

FROM bht-prod AS bht-test
ENV PYTHONPATH="/home/bibheliotech/BibHelioTech:$PYTHONPATH"
RUN cp ./resources/flake8-dist ./.flake8 && \
    cp resources/bht-config.yml-dist ./bht-config.yml && \
    cp resources/pytest.ini-dist ./pytest.ini
RUN pip install -r requirements-tests.txt

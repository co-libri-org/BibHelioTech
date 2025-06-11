# syntax=docker/dockerfile:1.7-labs
# so we can use COPY --parents
FROM ubuntu:24.04


RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /home/bibheliotech

# Virtualenv Python
ENV VIRTUAL_ENV=/home/bibheliotech/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .

# Installations Python and Java (sutime + deps maven)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# Finally set application files
WORKDIR /home/bibheliotech/BibHelioTech

COPY --parents \
     LICENSE \
     VERSION.txt \
     requirements.txt \
     bht_config.py \
     bht_web.py \
     manage.py \
     migrations/ \
     resources/ \
     tools/ \
     web/ \
     bht/ \
     ./

COPY .htpasswd  ./
COPY bht-config.yml ./


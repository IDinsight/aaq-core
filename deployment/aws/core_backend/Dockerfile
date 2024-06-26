# The is the Dockerfile for the core_backend for AWS. It is used to build the Docker
# image for any deployment environment on AWS.
# It gets secrets from AWS secrets manager and sets them as environment variables.
FROM python:3.10-slim-buster
LABEL maintainer="IDinsight"

ARG BOOTSTRAP_FILE
ENV BOOTSTRAP_FILE=$BOOTSTRAP_FILE

ARG NAME=aaq_backend
ARG PORT=8000
ARG HOME_DIR=/usr/src/${NAME}
RUN apt-get update && apt-get install -y \
    gcc libpq-dev python3-dev jq dnsutils

RUN pip install --upgrade pip \
    && pip install --no-cache-dir awscli

COPY add_users_to_db.py /add_users_to_db.py

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
RUN useradd -ms /bin/bash -d ${HOME_DIR} container_user
RUN chown -R container_user: ${HOME_DIR}

RUN mkdir /tmp/prometheus
RUN chown -R container_user: /tmp/prometheus

WORKDIR ${HOME_DIR}

COPY . ${HOME_DIR}
COPY ${BOOTSTRAP_FILE} /bootstrap.sh

RUN chmod +x /bootstrap.sh
RUN ["chmod", "+x", "startup.sh"]

ENV PYTHONPATH "${PYTHONPATH}:${HOME_DIR}"
ENV PORT ${PORT}
EXPOSE ${PORT}

ENTRYPOINT [ "/bootstrap.sh" , "./startup.sh"]

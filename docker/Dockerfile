FROM python:3.8-slim
LABEL maintainer="support@taiga.io"

# Avoid prompting for configuration
ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER=1

# Use a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Get the code
COPY . /taiga-back
WORKDIR /taiga-back

ENV LOGS_DIR=/srv/logs
ENV LOG_FILE=/srv/logs/gunicorn.log
ENV ACCESS_LOGFILE=/srv/logs/access.log

# Install dependencies, compile locales, delete unneeded files
RUN apt-get update \
    && apt-get install -y \
       build-essential \
       gettext \
       net-tools \
       procps \
    && python -m pip install --upgrade pip \
    && python -m pip install wheel \
    && python -m pip install -r requirements.txt \
    && python manage.py compilemessages \
    && chmod +x docker/entrypoint.sh \
    # remove
    && apt-get purge -y \
       build-essential \
       gettext \
    && apt-get autoremove -y \
    && rm requirements.txt \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache \
    && find . -name '__pycache__' -exec rm -r '{}' + \
    && find . -name '*pyc' -exec rm -r '{}' + \
    && find . -name '*po' -exec rm -r '{}' + \
    # create useful files and directories
    && mkdir ${LOGS_DIR} \
    && touch ${LOG_FILE} \
    && touch ${ACCESS_LOGFILE}

ENTRYPOINT ["./docker/entrypoint.sh"]

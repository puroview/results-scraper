## Build from latest Python 3.7 base
FROM python:3.7-slim-buster

## Run in app folder
WORKDIR /usr/src/app

## Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

## Copy in files
COPY ["scraper.py", "db.py", "notifier.py", "./"]

## Run scraper
ENTRYPOINT [ "python", "./scraper.py"]
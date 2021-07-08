## Build from latest Python 3.7 base
FROM python:3.8-slim-buster

## Run in app folder
WORKDIR /usr/src/app

## Install dependencies
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --deploy --ignore-pipfile

## Copy in files
COPY . .

## Run scraper
ENTRYPOINT ["pipenv", "run", "python3", "scraper"]
CMD ["--results"]
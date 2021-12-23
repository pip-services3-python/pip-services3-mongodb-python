FROM python:3.10-slim-buster

# set working directory
WORKDIR /usr/src/app

# copy project file
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy all project
COPY . .
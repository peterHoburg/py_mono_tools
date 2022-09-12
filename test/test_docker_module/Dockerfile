FROM python:3.8-slim
ARG USER_UID=1000
WORKDIR /opt

COPY requirements.txt  .
RUN pip3 install -r requirements.txt

COPY . .

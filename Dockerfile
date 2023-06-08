FROM python:3.9.16-alpine3.17

WORKDIR /app

COPY requirements.txt /app
COPY start.sh /app
COPY eth0.py /etc/periodic/15min
COPY month.py /etc/periodic/monthly

RUN pip install --no-cache-dir -r requirements.txt
RUN apk add gcc python3-dev linux-headers musl-dev openrc
RUN pip install psutil
RUN mkdir -p /run/openrc && mkdir /run/openrc/exclusive
RUN touch /run/openrc/softlevel

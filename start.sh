#!/bin/sh

# start cron and bot
/usr/sbin/crond -f -l 8 &
python3 /app/dockerbot.py /app/token.txt /app/user.txt

#!/usr/bin/env python3
import requests
import eth0

text = eth0.reply
x = requests.post('https://api.telegram.org/bot[TOKEN]?chat_id=[chatID]&text='+str(text))
print(x.text)

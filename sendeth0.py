#!/usr/bin/env python3
import requests
import eth0

text = eth0.reply
x = requests.post('https://api.telegram.org/bot6220437234:AAHPzY6Ajdy0j6WHmpuNmLBV8Wa-Q-3f0HQ/sendMessage?chat_id=1358508532&text='+str(text))
print(x.text)

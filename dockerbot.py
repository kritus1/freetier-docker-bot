#!/usr/bin/python3
import telebot
import subprocess
import psutil
from datetime import datetime

bot = telebot.TeleBot("TOKEN")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hi! I'm a docker bot. Just send me one of the commands: /servstat, /dockerstart, /dockerstatus")

@bot.message_handler(commands=['servstat'])
def def_size(message):
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boottime = datetime.fromtimestamp(psutil.boot_time())
    now = datetime.now()
    timedif = "Online for: %.1f Hours" % (((now - boottime).total_seconds()) / 3600)
    memtotal = "Total memory: %.2f GB " % (memory.total / 1000000000)
    memavail = "Available memory: %.2f GB" % (memory.available / 1000000000)
    memuseperc = "Used memory: " + str(memory.percent) + " %"
    diskused = "Disk used: " + str(disk.percent) + " %"
    netio = psutil.net_io_counters(pernic=True)

    f = open('/home/ubuntu/ar/eth0.txt', 'r')
    d = open('/home/ubuntu/ar/delta.txt', 'r')
    p = open('/home/ubuntu/ar/foryear.txt', 'r')
    fromfilestr = f.read()
    foryearstr = p.read()
    deltastr = d.read()
    f.close()
    d.close()
    p.close()
    if int(netio['eth0'][0]) >= int(fromfilestr): # if system works without reboot
            f = open('/home/ubuntu/ar/eth0.txt', 'w')
            f.write(str(int(netio['eth0'][0]) - int(foryearstr)) + '\n')
            fromfilenew = str(int(netio['eth0'][0]) - int(foryearstr)) + '\n'
            f.close()
    else: # if system reboot happened
            d = open('/home/ubuntu/ar/delta.txt', 'w')
            f = open('/home/ubuntu/ar/eth0.txt', 'w')
            f.write(str(int(fromfilestr) + int(netio['eth0'][0]) - int(deltastr)) + '\n')
            d.write(str(netio['eth0'][0]))
            fromfilenew = str(int(fromfilestr) + int(netio['eth0'][0]) - int(deltastr)) + '\n'
            f.close()
            d.close()

    reply = timedif + "\n" + \
            memtotal + "\n" + \
            memavail + "\n" + \
            memuseperc + "\n" + \
            diskused + "\n\n" + \
            'Network usage in this month: ' + str("%.2f" % (int(fromfilenew) / 1024 / 1024)) + ' MB'
#    print(reply)
    bot.reply_to(message, reply)

#@bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
#def command_handle_document(message):
#    bot.reply_to(message, "Document received, sir!")

@bot.message_handler(commands=['dockerstart'])
def def_vpnstart(message):
	cmd = subprocess.Popen(('docker', 'start', 'ca2517b4310c'), stdout=subprocess.PIPE)
	result2 = cmd.communicate()[0]
	bot.reply_to(message, result2)

@bot.message_handler(commands=['dockerstatus'])
def def_vpnstatus(message):
	status = subprocess.Popen(("docker", "inspect", "--format='{{.State.Status}}'", "ca2517b4310c"), stdout=subprocess.PIPE)
	result3 = status.communicate()[0]
	bot.reply_to(message, result3)

bot.polling()

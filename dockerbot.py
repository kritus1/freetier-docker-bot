#!/usr/bin/env python3
import logging
from dataclasses import dataclass, fields
from argparse import ArgumentParser
from datetime import datetime, timezone
from functools import partial
import psutil
import docker
from telegram import Update, BotCommandScopeChat, BotCommandScopeDefault, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
# as_logger = logging.getLogger('apscheduler')
# as_logger.setLevel(logging.WARNING)
field_names = lambda DC: ', '.join(f.name for f in fields(DC))


class FileDataType:

    def __init__(self, type, mode='r'):
        self.mode = mode
        self.type = type

    def __call__(self, file_name):
        with open(file_name, self.mode) as file:
            data = file.read().strip()

        return self.type(data)
        

@dataclass
class LogArgs:
    container_name: str
    tail_number: int = 5

    def __post_init__(self):
        self.tail_number = int(self.tail_number)


@dataclass
class ListArgs:
    limit: int = 15
    all: bool = False

    def __post_init__(self):
        if isinstance(self.all, bool):  # Default value, no input
            return

        str_to_bool = {'t': True,
                       'f': False} 
        self.all = str_to_bool[self.all.lower()]


@dataclass
class RestartArgs:
    container_name: str
    timeout: int = 10

    def __post_init__(self):
        self.timeout = int(self.timeout)


@dataclass
class EchoArgs:
    text: str = None


class DockerHandler(CommandHandler):

    def __init__(self, command, callback, args_class, **kwargs):
        wrapped_cbk = self._wrapp_callback(command, callback, args_class)
        super().__init__(command, wrapped_cbk, **kwargs)
     
    def _wrapp_callback(self, command, callback, args_class):

        async def wrapped_callback(update, context):
            logging.info('Command %s', update.message.text)

            try:
                cbk_args = args_class(*context.args)
            except Exception:
                error = f'Wrong arguments of {args_class}'
                logging.error(error)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=error)
                return

            docker_client = docker.from_env()
            return await callback(update, context, cbk_args, docker_client)

        return wrapped_callback


def reply_fabric(message_text, text) -> str:       
    now = datetime.now(timezone.utc).isoformat(sep=' ', timespec='seconds')
    
    header = f'_command_ `{message_text}`'

    body = '\n\n'
    body += escape_markdown(text, version=2)
    body += '\n' if text.endswith('\n') else '\n\n'

    footer = f'_replied_ `{now}`'

    reply = header + body + footer
    return reply


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE, args: EchoArgs, docker_client):
    text = 'echo' if args.text is None else args.text
    reply = reply_fabric(update.message.text, text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                   parse_mode=ParseMode.MARKDOWN_V2)


async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f'{update.effective_user} \n {update.effective_chat}'
    reply = reply_fabric(update.message.text, text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                   parse_mode=ParseMode.MARKDOWN_V2)

    
async def net_io(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    f = open('/app/eth0.txt', 'r')
    d = open('/app/delta.txt', 'r')
    p = open('/app/month.txt', 'r')
    fromfilestr = f.read()
    foryearstr = p.read()
    deltastr = d.read()
    f.close()
    d.close()
    p.close()
    if int(netio['eth0'][0]) >= int(fromfilestr):
            f = open('/app/eth0.txt', 'w')
            f.write(str(int(netio['eth0'][0]) - int(foryearstr)) + '\n')
            fromfilenew = str(int(netio['eth0'][0]) - int(foryearstr)) + '\n'
            f.close()
    else:
            d = open('/app/delta.txt', 'w')
            f = open('/app/eth0.txt', 'w')
            f.write(str(int(fromfilestr) + int(netio['eth0'][0]) - int(deltastr)) + '\n')
            d.write(str(netio['eth0'][0]))
            fromfilenew = str(int(fromfilestr) + int(netio['eth0'][0]) - int(deltastr)) + '\n'
            f.close()
            d.close()

    text  = timedif + "\n" + \
            memtotal + "\n" + \
            memavail + "\n" + \
            memuseperc + "\n" + \
            diskused + "\n\n" + \
            'Network usage in this month: ' + str("%.2f" % (int(fromfilenew) / 1024 / 1024)) + ' MB'
    reply = reply_fabric(update.message.text, text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                   parse_mode=ParseMode.MARKDOWN_V2)


async def list_containers(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          args: ListArgs, docker_client):
    c_list = docker_client.containers.list(all=args.all, limit=args.limit)

    text = ''
    for c in c_list:
        text += f'{c.name} {c.status}\n'

    reply = reply_fabric(update.message.text, text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                   parse_mode=ParseMode.MARKDOWN_V2)


async def get_container_logs(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             args: LogArgs, docker_client):
    c = docker_client.containers.get(args.container_name)

    logs = c.logs(tail=args.tail_number).decode()
    
    reply = reply_fabric(update.message.text, logs)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                   parse_mode=ParseMode.MARKDOWN_V2)


async def restart_container(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            args: RestartArgs, docker_client):
    c = docker_client.containers.get(args.container_name)
    
    reply = reply_fabric(update.message.text, 'restarting...')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                   parse_mode=ParseMode.MARKDOWN_V2)

    # At the end to avoid cycling restarts
    async def restart():
        c.restart(timeout=args.timeout)
        reply = reply_fabric(update.message.text, 'restarted.')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=reply,
                                       parse_mode=ParseMode.MARKDOWN_V2)
    context.application.create_task(restart())


async def set_commands(commands_map, application):
    for Scope, scope_data in commands_map.items():
        scope = Scope() if not scope_data.get('args') else Scope(*scope_data['args'])

        await application.bot.set_my_commands(scope_data['commands'], scope=scope)

        cmd_names = ', '.join(bc.command for bc in scope_data['commands'])
        logging.info('Commands have been set: %s[%s]', Scope.__name__, cmd_names)


async def send_healthcheck(chat_id):
   pass 

     
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('token', type=FileDataType(str), help='Absolute path to a text file with a bot token in.')
    parser.add_argument('userid', type=FileDataType(int), help='Absolute path to a text file with an allowed user id number.')
    args = parser.parse_args()

    info_cmd = BotCommand('info', 'User and chat information')
    netio_cmd = BotCommand('netio', 'Docker server statistics')
    echo_cmd = BotCommand('echo', f'Resend you typed text or echoing. Params: {field_names(EchoArgs)}')
    list_cmd = BotCommand('list', f'List containers. Params: {field_names(ListArgs)}')
    logs_cmd = BotCommand('logs', f'Return logs of a container. Params: {field_names(LogArgs)}')
    restart_cmd = BotCommand('restart', f'Restart a container. Params: {field_names(RestartArgs)}')

    pub_commands = (
        info_cmd,
        netio_cmd,
    )
    priv_commands = pub_commands + (
        info_cmd,
        echo_cmd,
        list_cmd,
        logs_cmd,
        restart_cmd
    )
    commands_map = {
        BotCommandScopeDefault: {'commands': pub_commands},
        BotCommandScopeChat: {'commands': priv_commands,
                              'args': (args.userid, )}
    }
    post_init = partial(set_commands, commands_map)
    application = ApplicationBuilder().token(args.token).post_init(post_init).build()

    application.add_handlers([
        CommandHandler(info_cmd.command, user_info),
        CommandHandler(netio_cmd.command, net_io),
        DockerHandler(echo_cmd.command, echo, EchoArgs, filters=filters.User(user_id=args.userid)),
        DockerHandler(list_cmd.command, list_containers, ListArgs, filters=filters.User(user_id=args.userid)),
        DockerHandler(logs_cmd.command, get_container_logs, LogArgs, filters=filters.User(user_id=args.userid)),
        DockerHandler(restart_cmd.command, restart_container, RestartArgs, filters=filters.User(user_id=args.userid))
    ])
    application.run_polling(allowed_updates=['message'], drop_pending_updates=True)

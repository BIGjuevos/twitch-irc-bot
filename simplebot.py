#!/usr/bin/env python3

# simpleircbot.py - A simple IRC-bot written in python
#
# Copyright (C) 2015 : Niklas Hempel - http://liq-urt.de
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
import datetime
import time

import dateutil.parser
import json
import os
import http.client
import http.server
import logging
import re
import signal
import socket
import sys
import threading

log = logging.getLogger()
log.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')

# create file handler which logs even debug messages
fh = logging.FileHandler('logs/twitch-irc-bot.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

# --------------------------------------------- Start Settings ----------------------------------------------------
HOST = os.getenv('T_HOST',"irc.chat.twitch.tv")
PORT = os.getenv('T_POST', 6667)
CHAN = os.getenv('T_CHAN')
NICK = os.getenv('T_NICK')
PASS = os.getenv('T_PASS')
API_KEY = os.getenv('T_API_KEY')
# --------------------------------------------- End Settings -------------------------------------------------------


# --------------------------------------------- Start Functions ----------------------------------------------------
def send_pong(msg):
    b = bytes('PONG %s\r\n' % msg, 'UTF-8')
    log.info(f"I > {b}")
    con.send(b)


def send_message(chan, msg):
    b = bytes('PRIVMSG #%s :[BOT] %s\r\n' % (chan, msg), 'UTF-8')
    log.info(f"I > {b}")
    con.send(b)


def send_nick(nick):
    b = bytes('NICK %s\r\n' % nick, 'UTF-8')
    log.info(f"I > {b}")
    con.send(b)


def send_pass(password):
    b = bytes('PASS %s\r\n' % password, 'UTF-8')
    log.info(f"I > {b}")
    con.send(b)


def join_channel(chan):
    b = bytes('JOIN #%s\r\n' % chan, 'UTF-8')
    log.info(f"I > {b}")
    con.send(b)


def part_channel(chan):
    b = bytes('PART #%s\r\n' % chan, 'UTF-8')
    log.info(f"I > {b}")
    con.send(b)


# --------------------------------------------- End Functions ------------------------------------------------------


# --------------------------------------------- Start Helper Functions ---------------------------------------------
def get_sender(msg):
    result = ""
    for char in msg:
        if char == "!":
            break
        if char != ":":
            result += char
    return result


def get_message(msg):
    result = ""
    i = 3
    length = len(msg)
    while i < length:
        result += msg[i] + " "
        i += 1
    result = result.lstrip(':')
    return result


def parse_message(msg, sent_by):
    if len(msg) >= 1:
        msg = msg.split(' ')
        options = {'!ping': command_ping,
                   "!uptime": command_uptime,
                   '!route': command_route,
                   '!help': command_help,
                   '!discord': command_discord,
                   '!predict': command_predict}
        if msg[0] in options:
            try:
                options[msg[0]](msg[1], sent_by)
            except Exception:
                log.exception("Something went wrong calling {msg[0]}")


# --------------------------------------------- End Helper Functions -----------------------------------------------


# --------------------------------------------- Start Command Functions --------------------------------------------
def command_ping(msg, sent_by):
    send_message(CHAN, 'pong')


def command_help(msg, sent_by):
    send_message(CHAN, 'Available Commands: !route, !predict, !ping, !discord, !help, !uptime')


def command_discord(msg, sent_by):
    send_message(CHAN, 'Discord is at: https://discord.gg/RdGnarY')


def command_uptime(msg, sent_by):
    conn = http.client.HTTPSConnection("api.twitch.tv")

    url = "/helix/streams/?user_login=" + NICK
    conn.request("GET", url, headers={
        'Client-ID': API_KEY
    })

    res = conn.getresponse()
    data = res.read()

    info = json.loads(data)

    if len(info['data']) is 0:
        send_message(CHAN, 'Not currently streaming. Thanks for asking though.')
        return

    info = info['data'][0]
    started = dateutil.parser.parse(info['started_at'])
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - started

    running = "Uptime: " + str(datetime.timedelta(seconds=diff.total_seconds()))

    send_message(CHAN, running)


def command_route(msg, sent_by):
    conn = http.client.HTTPConnection("twitch-briefer.service.consul", 5556)

    headers = {
        'cache-control': "no-cache",
    }

    conn.request("GET", "/data?thing=rte", headers=headers)

    res = conn.getresponse()
    data = res.read()

    data = data.strip(b'\" \n\r')
    data = data.replace(b'\\n', b' ')

    url = "https://skyvector.com/?chart=304&fpl=%20" + data.decode("utf-8").replace(" ", "%20")

    send_message(CHAN, "Current Route: " + data.decode("utf-8") + f" URL: {url}")


def command_predict(msg, sent_by):
    try:
        speed = int(msg)
    except ValueError:
        send_message(CHAN, f"{sent_by}: You must provide a number.")
        return

    if speed >= 0:
        send_message(CHAN, f"{sent_by}: {msg} is not a valid vertical speed. Whole numbers below zero only please.")
        return

    conn = http.client.HTTPConnection("twitch-briefer.service.consul", port=5556)

    conn.request("GET", f"/guess?username={sent_by}&speed={msg}")

    send_message(CHAN, f"{sent_by}: You have guessed {msg} fpm. Good Luck!")

    pass


# --------------------------------------------- End Command Functions ----------------------------------------------

if __name__ == '__main__':
    sys.stderr = open('logs/errors.log', 'a')
    sys.stdout = open('logs/errors.log', 'a')

    con = socket.socket()
    con.connect((HOST, PORT))

    send_pass(PASS)
    send_nick(NICK)
    join_channel(CHAN)

    data = ""

    log.info("Setting up the health check")

    class MyHandler(http.server.BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

        def do_GET(self):
            log.info(f"H < GET {self.path}")
            if self.path.startswith("/winner"):
                name = self.path.split("/")[2]
                speed = self.path.split("/")[3]
                actual = self.path.split("/")[4]
                send_message(CHAN, f"We've landed at {actual} fpm! Congratulations to {name} with the closest correct guess of {speed} -fpm.")

            self._set_headers()

    server_address = ('', 9999)
    httpd = http.server.HTTPServer(server_address, MyHandler)
    status_thread = threading.Thread(target=httpd.serve_forever)
    status_thread.start()

    def sigterm_handler(s, frame):
        # save the state here or do whatever you want
        log.info("Asked to exit, doing so")
        httpd.shutdown()
        log.info("server shut down")
        httpd.server_close()
        log.info("socket closed")
        status_thread.join()
        log.info("thread joined, exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, sigterm_handler)

    log.info("Entering main bot loop")
    start = time.time()
    restart_time = start + 3600

    while True:
        try:
            data = data + con.recv(1024).decode('UTF-8')

            data_split = re.split(r"[~\r\n]+", data)
            data = data_split.pop()

            for line in data_split:
                line = str.rstrip(line)
                log.info(f"I < {line}")
                line = str.split(line)

                if len(line) >= 1:
                    if line[0] == 'PING':
                        send_pong(line[1])

                    if line[1] == 'PRIVMSG':
                        sender = get_sender(line[0])
                        message = get_message(line)
                        parse_message(message, sender)

        except socket.timeout:
            log.exception("Socket timeout")

        except socket.error:
            log.exception("Socket died")

        if time.time() >= restart_time:
            log.info("Our life is up, die so someone can spawn a new one of us.")
            sigterm_handler(None, None)

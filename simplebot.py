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


def parse_message(msg):
    if len(msg) >= 1:
        msg = msg.split(' ')
        options = {'!ping': command_ping,
                   '!route': command_route}
        if msg[0] in options:
            options[msg[0]]()


# --------------------------------------------- End Helper Functions -----------------------------------------------


# --------------------------------------------- Start Command Functions --------------------------------------------
def command_ping():
    send_message(CHAN, 'pong')


def command_route():
    conn = http.client.HTTPConnection("maria.ryannull.com")

    headers = {
        'cache-control': "no-cache",
    }

    conn.request("GET", "/twitch/data.php?thing=rte", headers=headers)

    res = conn.getresponse()
    data = res.read()

    send_message(CHAN, "Current Route: " + data.decode("utf-8"))


# --------------------------------------------- End Command Functions ----------------------------------------------

if __name__ == '__main__':
    sys.stderr = open('logs/errors.log', 'w')

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
            self._set_headers()

    server_address = ('', 8000)
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
                        parse_message(message)

                        print(sender + ": " + message)

        except socket.timeout:
            print("Socket timeout")

        except socket.error:
            print("Socket died")

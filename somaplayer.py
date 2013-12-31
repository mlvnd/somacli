#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import subprocess
import fcntl
import signal
from datetime import datetime
from threading import Timer

configuration_file = "config.json"


class Somaplayer:

    def __init__(self, configuration_file):
        configuration = self.load_configuration(configuration_file)

        self.stations = configuration["stations"]
        self.base_url = configuration["baseurl"]

        self.player_process = None
        self.timer = None
        self.call_back = None
        self.current_title = ""
        self.history = []


    def load_configuration(self, path):
        if not os.path.isfile(path):
            sys.stderr.write("Configuration file not found.\n")
            sys.exit(1)

        configuration_file = open(path)
        configuration = json.load(configuration_file)
        configuration_file.close()
        return configuration


    def get_url(self, station_index):
        feedname = self.stations[station_index]['feed']
        url = "{0}{1}.pls".format(self.base_url, feedname)
        return url


    def is_playing(self):
        return self.player_process != None


    def stop(self):
        player = self.player_process
        if player != None:
            os.killpg(player.pid, signal.SIGQUIT)
            player = None
        if self.timer:
            self.timer.cancel()
            self.timer = None


    def play(self, station_index):
        if self.is_playing():
            self.stop()

        url = self.get_url(station_index)

        # Start sub-process, redirect stdout and stderr
        cmd = ['/usr/bin/mplayer', '-quiet', '-playlist', url]
        player = subprocess.Popen(cmd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

        # Change file descriptor to be non-blocking
        fl = fcntl.fcntl(player.stdout, fcntl.F_GETFL)
        fcntl.fcntl(player.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.player_process = player
        self.history.append("*** {0} ***".format(self.stations[station_index]['name']))
        self.update_current_title()


    def update_current_title(self):
        player = self.player_process
        while True:
            try:
                line = player.stdout.readline()
                if line.startswith('ICY Info:'):
                    match = re.search(r"StreamTitle='(.*)';StreamUrl=", line)
                    self.current_title = match.group(1)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    self.history.append("{0}: {1}".format(timestamp, self.current_title))
                    self.call_call_back()
            except IOError:
                break
        if self.is_playing:
            self.timer = Timer(1.0, self.update_current_title)
            self.timer.start()

    def set_call_back(self, call_back):
        self.call_back = call_back

    def call_call_back(self):
        if self.call_back:
            self.call_back()

if __name__ == "__main__":
    player = Somaplayer(configuration_file) 
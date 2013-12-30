#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import re
import subprocess
import fcntl
import curses
from time import sleep
from datetime import datetime


configuration_file = "config.json"
player = {}

class Somaplayer:

    def __init__(self, configuration_file):
        configuration = self.load_configuration(configuration_file)

        self.stations = configuration["stations"]
        self.base_url = configuration["baseurl"]

        self.player_process = None
        self.current_station_index = None
        self.current_title = ""


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
            player.kill()
            player = None


    def play(self, station_index):
        if self.is_playing():
            self.stop()

        self.current_station_index = station_index
        url = self.get_url(station_index)

        # Start sub-process, redirect stdout and stderr
        cmd = ['/usr/bin/mplayer', '-quiet', '-playlist', url]
        player = subprocess.Popen(cmd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)

        # Change file descriptor to be non-blocking
        fl = fcntl.fcntl(player.stdout, fcntl.F_GETFL)
        fcntl.fcntl(player.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.player_process = player


    def update_current_title(self):
        player = self.player_process
        has_changed = False
        while True:
            try:
                line = player.stdout.readline()
                if line.startswith('ICY Info:'):
                    match = re.search(r"StreamTitle='(.*)';StreamUrl=", line)
                    self.current_title = match.group(1)
                    has_changed = True
            except IOError:
                break
        return has_changed


def main(stdscr):
    global player
    stdscr.clear()
    curses.curs_set(0)
 
    stations = player.stations
    max_y, max_x = stdscr.getmaxyx()
    player.play(3)

    y = 0
    stdscr.nodelay(True)
    while True:
        if player.update_current_title():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            label = "{0}: {1}".format(timestamp, player.current_title)
            stdscr.addstr(y, 0, label)
            y += 1
            if y > max_y:
                stdscr.clear()
                y = 0
                label = "*** {0} ***".format(player.stations[player.current_station_index]['name'])
                stdscr.addstr(y, 0, label)
                y += 1
                stdscr.addstr(y, 0, player.current_title)

    
        key = stdscr.getch()
        if key == -1:
            sleep(0.1)
            continue

        elif key == ord('s'):
            if player.is_playing():
                player.stop()

        elif key == ord('p'):
            player.play(3)

        elif key == ord('c'):
            station = select_station(stdscr, stations)
            if station:
                stdscr.clear()
                y = 0
                label = "*** {0} ***".format(player.stations[station]['name'])
                stdscr.addstr(y, 0, label)
                y += 1
                stdscr.addstr(y, 0, player.current_title)
                player.play(station)

        elif key == ord('q'):
            player.stop()
            return

        else:
            pass

def select_station(stdscr, stations):
    max_y, max_x = stdscr.getmaxyx()
    station_pad = curses.newpad(len(stations), max_x)
    station_pad.nodelay(False)
    station_pad.keypad(True)
    position = 0
    while True:
        for index, station in enumerate(stations):
            if index == position:
                mode = curses.A_REVERSE
            else:
                mode = curses.A_NORMAL

            label = "{0}. {1}".format(index, station['name'])
            station_pad.addstr(index, 0, label, mode)

        station_pad.refresh(0, 0, 0, 0, max_y - 1, max_x - 1)

        key = station_pad.getch()

        if key in [curses.KEY_ENTER, ord('\n')]: 
            stdscr.clear()
            return position

        elif key in [27, ord('q')]:
            stdscr.clear()
            return None

        elif key in [curses.KEY_UP, ord('j')]: 
            position = max(position - 1, 0)

        elif key in [curses.KEY_DOWN, ord('k')]: 
            position = min(position + 1, len(stations) - 1)

        else:
            pass




if __name__ == "__main__":
    if (len(sys.argv) == 1) & (sys.argv[0] == 'soma.py'):
        player = Somaplayer(configuration_file)
    else:
        # Change path to directory of script.
        os.chdir(os.path.dirname(sys.argv[0]))
        player = Somaplayer(configuration_file)
        try:
            curses.wrapper(main)
            if player.is_playing():
                player.stop()
        except KeyboardInterrupt:
            pass

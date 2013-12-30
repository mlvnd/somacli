#!/usr/bin/python
import curses
from somaplayer import Somaplayer
from time import sleep
from datetime import datetime

configuration_file = "config.json"

msgs = []
def log(msg):
    msgs.append(msg)


class Content:
    def __init__(self):
        self.offset = 0
        self.selected = 0
        self.data = []

    def set_data(self, data):
        self.data = data

    def offset_add(self, vector):
        self.offset += vector
        if self.offset < 0:
            self.offset = 0
        elif self.offset > len(self.data) - 1:
            self.offset = len(self.data) - 1

    def selected_add(self, vector):
        self.selected += vector
        if self.selected < 0:
            self.selected = 0
        elif self.selected > len(self.data) - 1:
            self.selected = len(self.data) - 1


class Window:
    def pad_string(self, text):
        return text.ljust(self.width," ")[:self.width]

    def set_text(self, text, line, mode=curses.A_NORMAL):
        self.window.addstr(line, 0, text[:self.width], mode)

    def refresh(self):
        self.window.refresh()

    def getch(self):
        return self.window.getch()


class TitleWindow(Window):
    def __init__(self, parent):
        self.width = parent.width
        self.window = parent.create_window(1, self.width, 0, 0)

    def set_text(self, text):
        Window.set_text(self, self.pad_string(text), 0, curses.A_REVERSE | curses.A_BOLD)


class FooterWindow(Window):
    def __init__(self, parent):
        self.width = parent.width
        self.window = parent.create_window(1, self.width, parent.height - 1, 0)

    def set_text(self, text):
        Window.set_text(self, self.pad_string(text), 0, curses.A_REVERSE)


class ContentWindow(Window):
    def __init__(self, parent):
        self.width = parent.width
        self.height = parent.height - 2
        self.window = parent.create_window(self.height, self.width, 1, 0)
        self.window.keypad(True)
        self.window.nodelay(True)

    def render_content(self, content):
        self.window.clear()

        if content.selected - content.offset > self.height - 1:
            content.offset = content.selected - self.height + 1
        elif content.selected - content.offset <= 0:
            content.offset = content.selected 

        start = content.offset
        end = start + self.height

        for line_no, line in enumerate(content.data[start:end]):
            if line_no + start  == content.selected:
                mode = curses.A_REVERSE
            else:
                mode = curses.A_NORMAL
            Window.set_text(self, self.pad_string(line[:self.width]), line_no, mode)


class SomaUI:
    def create_window(self, height, width, x, y):
        return curses.newwin(height, width + 1, x, y)

    def main(self, stdscr, player):
        self.player = player
        curses.curs_set(False)
        self.height, self.width = stdscr.getmaxyx()

        title = TitleWindow(self)
        footer = FooterWindow(self)
        main = ContentWindow(self)

        title.set_text("PYSOMA: The CLI Soma FM streamplayer (with Python & mplayer)")
        footer.set_text("c:select channel, j/k: move up/down, q:quit, s:stop, p:play")

        data = [station['name'] for station in player.stations]

        content = Content()
        content.set_data(data)

        main.render_content(content)
        title.refresh()
        main.refresh()
        footer.refresh()

        while True:

            key = main.getch()
            #log("Key: " + str(key))
            if key == -1: # No input
                sleep(0.1)
                continue

            elif key in [curses.KEY_ENTER, ord('\n')]: # Select
                index = content.selected
                stations = player.stations
                log("{0}. {1}".format(index, stations[index]['name']))
                title.set_text("{0}: {1}".format(stations[index]['name'], stations[index]['description']))
                player.play(index)

            elif key in [curses.KEY_UP, ord('j')]: # Up
                content.selected_add(-1)
                main.render_content(content)
            
            elif key in [curses.KEY_DOWN, ord('k')]: # Down
                content.selected_add(1)
                main.render_content(content)
            
            elif key in [337, ord('J')]: # Shift up
                content.offset_add(-1)
                main.render_content(content)
            
            elif key in [336, ord('K')]: # Shift down
                content.offset_add(1)
                main.render_content(content)
            
            elif key in [565, ord('J')]: # Control up
                content.offset_add(-main.height)
                main.render_content(content)
            
            elif key in [524, ord('K')]: # Control down
                content.offset_add(main.height)
                main.render_content(content)
        
            elif key == ord('p'):
                data.append(str(len(data)))
                content.set_data(data)
                main.render_content(content)

            elif key in (27, ord('q')): # Quit
                player.stop()
                break

            title.refresh()
            main.refresh()
            footer.refresh()

        return

try:
    ui = SomaUI()
    player = Somaplayer(configuration_file)
    curses.wrapper(ui.main, player)

except KeyboardInterrupt:
    pass

finally:
    if len(msgs) > 0:
        print "*" * 80
        print 
        for msg in msgs:
            print msg
        print
        print "*" * 80
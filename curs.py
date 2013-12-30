import curses

def main(stdscr):
    pad = curses.newpad(100, 100)
    pad.addstr(0,0, curses.longname())
    for i in range(1, 10):
        pad.addstr(i,0, str(i))

    coord = 0, 0, 8, 10
    pad.refresh(0, 0, *coord)

    KEY_UP, KEY_DOWN = 'AB'
    y = 0
    for c in iter(pad.getkey, 'q'):
        if c in '\x1b\x5b': continue # skip escape seq
        y -= (c == KEY_UP)
        y += (c == KEY_DOWN)
        y = min(max(y, 0), 9)
        pad.refresh(y, 0, *coord)

curses.wrapper(main)
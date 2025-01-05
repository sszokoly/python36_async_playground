import curses
import os

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    try:
        for i in range(0, 255):
            stdscr.addstr(str(i), curses.color_pair(i))
    except curses.ERR:
        # End of screen reached
        pass
    stdscr.addstr(7, 0, "COLOR", curses.color_pair(3))
    stdscr.addstr(8, 0, "COLOR LIGHT", curses.color_pair(11))
    stdscr.addstr(9, 0, "COLOR HARSH", curses.color_pair(48))
    stdscr.getch()

def change_terminal(to_type="xterm-256color"):
    types = os.popen("toe -a").read().splitlines()
    if any(x for x in types if x.startswith(to_type)):
        os.environ["TERM"] = to_type

term = os.environ.get("TERM")
change_terminal("xterm-256color")   
curses.wrapper(main)
if term:
    os.environ["TERM"] = term
else:
    del os.environ["TERM"]
import atexit
import asyncio
import functools
import _curses, curses, curses.ascii, curses.panel
import os
import time
import sys
from abc import ABC, abstractmethod
from itertools import islice
from utils import asyncio_run

class Confirmation:
    def __init__(self, stdscr, body=None, attr=None, yoffset=-1, margin=1,
    ) -> None:
        self.stdscr = stdscr
        self.body = body or "Do you confirm (Y/N)?"
        self.attr = attr or curses.color_pair(0)
        self.yoffset = yoffset
        self.margin = margin
        
        maxy, maxx = self.stdscr.getmaxyx()
        nlines = 3 + (2 * self.margin)
        ncols = len(self.body) + (2 * self.margin) + 2
        begin_y = maxy // 2 + self.yoffset - (self.margin + 1)
        begin_x = maxx // 2 - (len(self.body) // 2) - (self.margin + 1)
        self.win = curses.newwin(nlines, ncols, begin_y, begin_x)
        curses.panel.new_panel(self.win)
        self.win.attron(self.attr)
        self.win.nodelay(True)
    
    async def draw(self):
        self.win.box()
        self.win.addstr(self.margin + 1, self.margin + 1, self.body, self.attr)
        self.win.refresh()
        while True:
            char = self.win.getch()
            if char in (ord('y'), ord('Y')):
                return True
            elif char in (ord('n'), ord('N')):
                return False
            else:
                await asyncio.sleep(0.1)

    def erase(self):
        self.win.erase()
        self.win.refresh()

def change_terminal(to_type="xterm-256color"):
    old_term = os.environ.get("TERM")
    types = os.popen("toe -a").read().splitlines()
    if any(x for x in types if x.startswith(to_type)):
        os.environ["TERM"] = to_type
    return old_term

def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    stdscr.resize(24, 80)
    stdscr.nodelay(True)
    done = False
    stdscr.box()
    asyncio_run(run(stdscr))

async def run(stdscr):
    while True:
        confirmation = Confirmation(stdscr)
        result = await confirmation.draw()
        if result:
            return
        else:
            confirmation.erase()
            await asyncio.sleep(1)

def startup():
    print("Starting up")
    orig_term = change_terminal()
    print(f"Old TERM: {orig_term}")
    orig_stty = os.popen("stty -g").read().strip()
    atexit.register(shutdown, orig_term, orig_stty)

def shutdown(term, stty):
    print("Shutting down")
    _ = change_terminal(term)
    os.system(f"stty {stty}")

if __name__ == "__main__":
    startup()
    curses.wrapper(main)
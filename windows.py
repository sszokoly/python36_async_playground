import atexit
import _curses, curses, curses.ascii
import os
import time
import sys
from abc import ABC, abstractmethod
from itertools import islice



def start():
    time.sleep(1)

def stop():
    time.sleep(1)


class Menubar:
    def __init__(self, stdscr, nlines=1, xoffset=0, buttons=None) -> None:
        self._stdscr = stdscr
        self._xoffset = xoffset
        self._buttons = buttons if buttons else []
        self._button_chars = [x.char for x in self._buttons]
        self._button_offset = 20
        self._color_pair = curses.color_pair(0)|curses.A_REVERSE
        self.maxy = nlines
        self.maxx = self._stdscr.getmaxyx()[1]
        self.win = self._stdscr.subwin(nlines, self.maxx,
            self._stdscr.getmaxyx()[0] - nlines, xoffset)

    def draw(self):
        try:
            self.win.addstr(0, 0, " " * (self.maxx),
                self._color_pair|curses.A_REVERSE)
        except _curses.error:
            pass
        self._draw_buttons()
        self.win.refresh()
    
    def _draw_buttons(self):
        offset = self._button_offset
        for idx, button in enumerate(self._buttons):
            self.win.addstr(0, offset, str(button), self._color_pair)
            offset += len(str(button)) + 3

    def register_button(self, button):
        self._buttons.append(button)
        self._button_chars.append(button.char)
        self._width = max(len(str(x)) for x in self._buttons)

    def handle_char(self, char):
        char = chr(char)
        if char in self._button_chars:
            idx = self._button_chars.index(char)
            self._buttons[idx].press()
            self.draw()


class Button:
    def __init__(self, char) -> None:
        self.char = char
        self.state_idx = 0
        self.state_labels = ["Start", "Stop"]
        self.state_callbacks = [start, stop]
        self.status_labels = ["Running", "Stopped"]
        self.status_color_pairs = [curses.color_pair(1), curses.color_pair(2)]
        self.status_temp = "Starting"
        self.status_temp_color_pair = curses.color_pair(3)

    def press(self):
        self.state_idx = (self.state_idx + 1) % len(self.state_labels)

    def status(self):
        return (self.status_labels[self.state_idx],
                self.status_color_pairs[self.state_idx])

    def __str__(self):
        return f"{self.char}={self.state_labels[self.state_idx]}"


def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    stdscr.nodelay(True)
    done = False
    stdscr.box()

    while not done:

        menu = Menubar(stdscr)
        menu.register_button(Button("s"))
        menu.draw()

        while not done:
            char = stdscr.getch()
            if char == curses.ERR:
                time.sleep(0.1)
            elif char == curses.KEY_RESIZE:
                stdscr.erase()
                break
            elif chr(char) == "q":
                sys.exit()
            else:
                menu.handle_char(char)

def change_terminal(to_type="xterm-256color"):
    old_term = os.environ.get("TERM")
    types = os.popen("toe -a").read().splitlines()
    if any(x for x in types if x.startswith(to_type)):
        os.environ["TERM"] = to_type
    return old_term

def startup():
    print("Starting up")
    orig_term = change_terminal()
    print(f"Old TERM: {orig_term}")
    orig_stty = os.popen("stty -g").read().strip()
    atexit.register(shutdown, orig_term, orig_stty)
    curses.wrapper(main)

def shutdown(term, stty):
    print("Shutting down")
    _ = change_terminal(term)
    os.system(f"stty {stty}")


if __name__ == "__main__":
    startup()
    curses.wrapper(main)
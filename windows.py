import atexit
import _curses, curses, curses.ascii
import os
import time
import sys
from abc import ABC, abstractmethod
from itertools import islice


def start():
    time.sleep(2)
    return True

def stop():
    time.sleep(2)
    return True

def filter():
    time.sleep(0.2)
    return True

class Menubar:
    def __init__(
        self,
        stdscr,
        nlines=1,
        xoffset=0,
        buttons=None,
        button_offset=20,
        status_width=10,
    ) -> None:
        self._stdscr = stdscr
        self._xoffset = xoffset
        self._buttons = buttons if buttons else []
        self._button_offset = button_offset
        self._status_width = status_width
        self._button_chars = [x.char for x in self._buttons]
        self._button_width = 3
        self._color_pair = curses.color_pair(0)|curses.A_REVERSE
        self.maxy = nlines
        self.maxx = self._stdscr.getmaxyx()[1]
        self.win = self._stdscr.subwin(nlines, self.maxx,
            self._stdscr.getmaxyx()[0] - nlines, xoffset)
        self.color_pairs = self.init_color_pairs()

    def draw(self):
        try:
            self.win.addstr(0, 0, " " * (self.maxx),
                self._color_pair|curses.A_REVERSE)
        except _curses.error:
            pass
        self._draw_status_bar()
        self._draw_buttons()
        self.win.refresh()

    def _draw_status_bar(self):
        offset = 1
        for b in self._buttons:
            label, cpair = b.status()
            if not label:
                continue
            label = f"│{label:^{self._status_width}}│"
            self.win.addstr(0, offset, label, cpair)
            offset += len(label)
    
    def _draw_buttons(self, gap=3):
        offset = self._button_offset
        for b in self._buttons:
            label = f"{str(b):{self._button_width}}"
            self.win.addstr(0, offset, label, self._color_pair)
            offset += len(label) + gap

    def register_button(self, button):
        self._buttons.append(button)
        self._button_chars.append(button.char)
        self._button_width = max(len(l) for b in self._buttons for l in b.labels) + 2
        self._status_width = max(len(l) for b in self._buttons for l in
                                 b.status_labels + b.temp_status_labels)

    def handle_char(self, char):
        char = chr(char)
        if char in self._button_chars:
            idx = self._button_chars.index(char)
            self._buttons[idx].press()
            self.draw()

    @classmethod
    def init_color_pairs(cls):
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        
        return {
            "RED": curses.color_pair(2),
            "RED_LIGHT": curses.color_pair(197),
            "GREEN": curses.color_pair(42),
            "GREEN_LIGHT": curses.color_pair(156),
            "YELLOW": curses.color_pair(12),
            "YELLOW_LIGHT": curses.color_pair(230),
        }

class Button:
    def __init__(
        self,
        char,
        labels,
        funcs,
        callback=None,
        status_labels=[],
        status_color_pairs=[],
        temp_status_labels=[],
        temp_status_color_pairs=[],
    ) -> None:
        self.char = char
        self.labels = labels
        self.funcs = funcs
        self.callback = callback
        self.status_labels = status_labels
        if status_color_pairs:
            self.status_color_pairs = status_color_pairs
        else:
            self.status_color_pairs = [
                curses.color_pair(3)|curses.A_REVERSE,
                curses.color_pair(197)|curses.A_REVERSE]
        self.temp_status_labels = temp_status_labels
        if temp_status_color_pairs:
            self.temp_status_color_pairs = temp_status_color_pairs
        else:
            self.temp_status_color_pairs = [
                curses.color_pair(4)|curses.A_REVERSE,
                curses.color_pair(4)|curses.A_REVERSE]
        self.state_idx = 0
        self._status_label = None if not self.status_labels else status_labels[self.state_idx]
        self._status_color_pairs = self.status_color_pairs[self.state_idx]

    def press(self):
        if self.temp_status_labels:
            self._status_label = self.temp_status_labels[self.state_idx]
            self._status_color_pairs = self.temp_status_color_pairs[self.state_idx]
            self.callback()
        if self.funcs[self.state_idx]():
            self.state_idx = (self.state_idx + 1) % len(self.labels)
        if self.temp_status_labels:
            self._status_label = self.status_labels[self.state_idx]
            self._status_color_pairs = self.status_color_pairs[self.state_idx]
            self.callback()
        curses.flushinp()

    def __str__(self):
        return f"{self.char}={self.labels[self.state_idx]}"

    def status(self):
        return self._status_label, self._status_color_pairs


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
        menu.register_button(
            Button("s", labels=["Start", "Stop"],
                    funcs=[start, stop],
                    callback=menu.draw,
                    status_labels=["Loop", "Loop"],
                    temp_status_labels=["Starting", "Stopping"]))
        menu.register_button(
            Button("f", labels=["Filter"],
                    funcs=[filter],
                    callback=menu.draw))
        
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

def shutdown(term, stty):
    print("Shutting down")
    _ = change_terminal(term)
    os.system(f"stty {stty}")


if __name__ == "__main__":
    startup()
    curses.wrapper(main)
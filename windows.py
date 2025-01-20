import atexit
import functools
import _curses, curses, curses.ascii, curses.panel
import os
import time
import sys
from abc import ABC, abstractmethod
from itertools import islice


class MyPanel:
    def __init__(
        self,
        stdscr,
        body,
        attr=None,
        offset_y=1,
        offset_x=1,
        margin=1,
    ) -> None:
        self.stdscr = stdscr
        self.body = body
        self.attr = attr
        self.offset_y = offset_y
        self.offset_x = offset_x
        self.margin = margin
        self._initialize()

    def _initialize(self):
        maxy, maxx = self.stdscr.getmaxyx()
        nlines = maxy - (2 * self.margin)
        ncols = maxx - (2 * self.margin)
        begin_y = self.offset_y
        begin_x = self.offset_x
        self.win = curses.newwin(nlines, ncols, begin_y, begin_x)
        self.panel = curses.panel.new_panel(self.win)
        self.panel.top()
        self.attr = self.attr if self.attr else curses.color_pair(0)

    def draw(self):
        self.win.box()
        self.win.addstr(self.margin, self.margin, self.body, self.attr)
        self.win.refresh()

    def erase(self):
        self.win.erase()
        self.win.refresh()

class Popup:
    def __init__(
        self,
        stdscr,
        message,
        attr=None,
        offset_y=-1,
        margin=1,
    ) -> None:
        self.stdscr = stdscr
        self.message = message
        self.attr = attr
        self.offset_y = offset_y
        self.margin = margin
        self._initialize()
    
    def draw(self):
        self.win.refresh()

    def erase(self):
        self.win.erase()
        self.win.refresh()

    def _initialize(self):
        maxy, maxx = self.stdscr.getmaxyx()
        nlines = 3 + (2 * self.margin)
        ncols = len(self.message) + (2 * self.margin) + 2
        begin_y = maxy // 2 + self.offset_y - (self.margin + 1)
        begin_x = maxx // 2 - (len(self.message) // 2) - (self.margin + 1)
        self.win = curses.newwin(nlines, ncols, begin_y, begin_x)
        curses.panel.new_panel(self.win)
        
        attr = self.attr if self.attr else curses.color_pair(0)
        self.win.attron(attr)
        self.win.box()
        self.win.addstr(self.margin + 1, self.margin + 1, self.message, attr)

class Menubar:
    def __init__(
        self,
        stdscr,
        buttons=None,
        button_offset=20,
        button_gap=1,
        nlines=1,
        offset_x=0,
        status_width=10,
        attr=None,
    ) -> None:
        self.stdscr = stdscr
        self.buttons = buttons if buttons else []
        self.button_offset = button_offset
        self.button_gap = button_gap
        self.nlines = nlines
        self.offset_x = offset_x
        self.status_width = status_width
        self.attr = attr
        self._initialize()

    def draw(self):
        try:
            self.win.addstr(0, 0, " " * (self.maxx), self.attr)
        except _curses.error:
            pass
        self._draw_status_bar()
        self._draw_buttons()
        self.win.refresh()

    def _draw_status_bar(self):
        offset = 1
        for b in self.buttons:
            label, button_attr = b.status()
            if not label:
                continue
            label = f"│{label:^{self.status_width}}│"
            self.win.addstr(0, offset, label, button_attr)
            offset += len(label)
    
    def _draw_buttons(self):
        offset = self.button_offset
        for b in self.buttons:
            label = f"{str(b):{self._button_width}}"
            self.win.addstr(0, offset, label, self.attr)
            offset += len(label) + self.button_gap

    def register_button(self, button):
        self.buttons.append(button)
        self._button_chars.append(button.char)
        self._button_width = max(len(l) for b in self.buttons
            for l in b.labels) + 2
        self.status_width = max(len(l) for b in self.buttons
            for l in b.status_labels + b.tempstatus_labels)

    def handle_char(self, char):
        char = chr(char)
        if char in self._button_chars:
            idx = self._button_chars.index(char)
            self.buttons[idx].press()
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

    def _initialize(self):
        self.maxy = nlines = self.nlines
        self.maxx = ncols = self.stdscr.getmaxyx()[1]
        begin_y = self.stdscr.getmaxyx()[0] - nlines
        begin_x = self.offset_x
        self._button_chars = [x.char for x in self.buttons]
        self.attr = self.attr or curses.color_pair(0)|curses.A_REVERSE
        self.color_pairs = self.init_color_pairs()
        self.win = self.stdscr.subwin(nlines, ncols, begin_y, begin_x)

class Button:

    button_map = {"d": "🅳 ", "f": "🅵 ", "s": "🆂 "}
    
    def __init__(
        self,
        stdscr,
        char,
        labels,
        funcs,
        callback=None,
        status_labels=[],
        status_attrs=[],
        tempstatus_labels=[],
        temp_attrs=[],
    ) -> None:
        self.stdscr = stdscr
        self.char = char
        self.labels = labels
        self.funcs = funcs
        self.callback = callback
        self.status_labels = status_labels
        self.status_attrs = status_attrs
        self.tempstatus_labels = tempstatus_labels
        self.temp_attrs = temp_attrs
        self._initialize()

    def _initialize(self):
        self.state_idx = 0
        
        self.status_attrs = self.status_attrs or [
                curses.color_pair(3)|curses.A_REVERSE,
                curses.color_pair(197)|curses.A_REVERSE]
        
        self.temp_attrs = self.temp_attrs or [
                curses.color_pair(4)|curses.A_REVERSE,
                curses.color_pair(4)|curses.A_REVERSE]

        if self.status_labels:
            self.status_label = self.status_labels[self.state_idx]
        else:
            self.status_label = None

        if self.tempstatus_labels:
            self.tempstatus_label = self.tempstatus_labels[self.state_idx]
        else:
            self.tempstatus_label = None

        self.status_attr = self.status_attrs[self.state_idx]

    def press(self):
        pop = Popup(self.stdscr, message="Please wait")
        pop.draw()
        
        if self.tempstatus_labels:
            self.status_label = self.tempstatus_labels[self.state_idx]
            self.status_attr = self.temp_attrs[self.state_idx]
            self.callback()
        
        if self.funcs[self.state_idx]():
            self.state_idx = (self.state_idx + 1) % len(self.labels)
        
        if self.tempstatus_labels:
            self.status_label = self.status_labels[self.state_idx]
            self.status_attr = self.status_attrs[self.state_idx]
            self.callback()
        
        pop.erase()
        del pop
        curses.flushinp()

    def __str__(self):
        char = self.button_map.get(self.char, self.char)
        return f"{char}={self.labels[self.state_idx]}"

    def status(self):
        return self.status_label, self.status_attr


def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    stdscr.resize(24, 80)
    stdpanel =  curses.panel.new_panel(stdscr)
    done = False
    stdscr.box()
    maxy, maxx = stdscr.getmaxyx()
    ypos = 0
    rtppanel = None

    def draw_maxyx():
        nonlocal stdscr, maxy, maxx, ypos
        text = f"{maxy}x{maxx} ypos={ypos}"
        attr = curses.color_pair(3)
        stdscr.addstr(maxy // 2, maxx // 2 - 6, (len(text)+2) * " ", attr)
        stdscr.addstr(maxy // 2, maxx // 2 - 6, text, attr)
        stdscr.refresh()

    def start():
        time.sleep(2)
        return True

    def stop():
        time.sleep(2)
        return True

    def draw_rtppanel():
        nonlocal stdscr, ypos, rtppanel, stdpanel
        rtppanel = MyPanel(stdscr, body="whatever")
        time.sleep(0.2)
        rtppanel.draw()
        curses.panel.update_panels()
        return True

    def erase_rtppanel():
        nonlocal ypos, rtppanel, stdpanel
        time.sleep(0.2)
        rtppanel.erase()
        return True

    while not done:

        menu = Menubar(stdscr)
        menu.register_button(
            Button(stdscr, "s", labels=["Start", "Stop"],
                    funcs=[start, stop],
                    callback=menu.draw,
                    status_labels=["EventLoop", "EventLoop"],
                    tempstatus_labels=["Starting", "Stopping"]))
        menu.register_button(
            Button(stdscr, "d", labels=["Details", "Details"],
                    funcs=[draw_rtppanel, erase_rtppanel],
                    callback=menu.draw))
        
        menu.draw()
        draw_maxyx()

        while not done:
            char = stdscr.getch()
            if char == curses.ERR:
                time.sleep(0.1)
            elif char == curses.KEY_RESIZE:
                stdscr.erase()
                break
            elif chr(char) == "q":
                sys.exit()
            elif char == curses.KEY_DOWN:
                ypos = ypos + 1 if ypos < maxy - 1 else ypos
                draw_maxyx()
            elif char == curses.KEY_UP:
                ypos = ypos - 1 if ypos > 0 else 0
                draw_maxyx()
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
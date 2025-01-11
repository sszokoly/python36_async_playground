import atexit
import _curses, curses, curses.ascii
import os
import time
import sys
from abc import ABC, abstractmethod
from bgw import BGW
from storage import SlicableOrderedDict

bgws = [
    BGW(host="10.10.48.1", gw_name='gw1', gw_number='001', show_running_config='Model : g430\nFW Vintage : 1\nrtp-stat-service', show_faults='No Fault Messages'),
    BGW(host="10.10.48.2", gw_name='gw12', gw_number='002', show_running_config='Model : g450\nFW Vintage : 3\n', show_faults='Error'),
]


storage = SlicableOrderedDict(items={
    "2025-01-10,10:51:36,001,00001": {
        "gw_number": "001",
        "session_id": "00001",
        "start_time": "2025-01-10,10:51:36",
        "end_time": "10:52:48",
        "local_addr": "10.10.48.1",
        "local_port": "2048",
        "remote_addr": "192.168.148.191",
        "remote_port": "33634",
        "qos":  "ok",
        "codec": "G711U",
    },
    "2025-01-10,10:53:36,001,00002": {
        "gw_number": "001",
        "session_id": "00001",
        "start_time": "2025-01-10,10:53:36",
        "end_time": "10:59:38",
        "local_addr": "10.10.48.1",
        "local_port": "2052",
        "remote_addr": "10.10.48.2",
        "remote_port": "2064",
        "qos":  "ok",
        "codec": "G711U",
    },
    "2025-01-10,10:53:36,002,00012": {
        "gw_number": "002",
        "session_id": "00001",
        "start_time": "2025-01-10,10:53:36",
        "end_time": "10:59:38",
        "local_addr": "10.10.48.2",
        "local_port": "2064",
        "remote_addr": "10.10.48.1",
        "remote_port": "2052",
        "qos":  "Faulted",
        "codec": "G711U",
    },
})

row_iterator = list(storage.values())
col_iterator = lambda c: [
    c.get('start_time'), c.get('end_time'), c.get('gw_number'),
    c.get('local_addr'), c.get('local_port'), c.get('remote_addr'),
    c.get('remote_port'), c.get('codec'), c.get('qos')]



class Workspace():
    def __init__(self,
        stdscr,
        col_attrs,
        col_widths=None,
        col_names=None,
        menu_window=None,
        yoffset=2,
        xoffset=0,
        row_iterator=None,
        col_iterator=None,
        color_pair=None,
    ):
        self._stdscr = stdscr
        self._col_attrs = col_attrs
        self._col_widths = col_widths if col_widths else list(
            map(len, col_attrs))
        self._col_names = col_names if col_names else col_attrs
        self._menuwin = menu_window
        self._yoffset = yoffset
        self._xoffset = xoffset
        self._row_iterator = row_iterator
        self._col_iterator = col_iterator
        self._cursy = 0
        self.color_pair = color_pair if color_pair else curses.color_pair(0)
        self.maxy = self._stdscr.getmaxyx()[0] - yoffset
        self.maxx = sum(x + 1 for x in self._col_widths) + 1
        self.title = stdscr.subwin(3, self.maxx, yoffset, xoffset)
        self.body = stdscr.subwin(self.maxy - 3, self.maxx, yoffset + 3, xoffset)
        self.footer = stdscr.subwin(1, self.maxx, self.maxy, xoffset)
        self.draw()

    def draw(self):
        self._draw_title()
        self._draw_body()
        self._draw_footer()

    
    def _draw_title(self):
        self.title.box()
        offset = 0
        for idx, (col_name, col_width) in enumerate(zip(self._col_names, self._col_widths)):
            col_name = f"│{col_name:^{col_width}}"
            xpos = self._xoffset if idx == 0 else offset
            offset = xpos + len(col_name)
            self.title.addstr(1, xpos, col_name, self.color_pair)
            if idx > 0:
                self.title.addstr(0, xpos, "┬", self.color_pair)
                self.title.addstr(2, xpos, "┼", self.color_pair)
        try:
            self.title.addstr(2, self._xoffset, "├", self.color_pair)
            self.title.addstr(2, self.maxx - 1, "┤", self.color_pair)
        except curses.error:
            pass
        self.title.refresh()

    def _draw_body(self):
        for ridx, row in enumerate(self._row_iterator[self._cursy:  self._cursy + self.maxy - 3]):
            offset = 0
            for cidx, (item, width) in enumerate(zip(self._col_iterator(row), self._col_widths)):
                xpos = self._xoffset if cidx == 0 else offset
                item = f"│{item[-width:]:>{width}}"
                offset = xpos + len(item)
                self.body.addstr(ridx, xpos, item, self.color_pair)
            self.body.addstr(ridx, xpos + len(item), "│", self.color_pair)
            self.body.refresh()

    def _draw_footer(self):
        self.footer.addstr(0, 0, " " * (self.maxx - 1), self.color_pair|curses.A_REVERSE)
        self.footer.refresh()

def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    stdscr.nodelay(True)
    done = False

    while not done:
    
        ws = Workspace(
            stdscr,
            col_attrs=["start_time", "stop_time", "gw_number",
                "local_address", "local_port", "remote_address",
                "remote_port", "codec", "qos"],
            col_widths=[8, 8, 3, 15, 5, 15, 5, 5, 3],
            col_names=["Start", "Stop", "BGW", "Local-Address",
                "LPort", "Remote-Address", "RPort", "Codec", "QoS"],
            row_iterator=row_iterator,
            col_iterator=col_iterator,
        )
        while not done:
            char = stdscr.getch()
            if char == curses.ERR:
                time.sleep(0.1)
            elif char == curses.KEY_RESIZE:
                stdscr.erase()
                break
            elif chr(char) == "q":
                sys.exit()

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
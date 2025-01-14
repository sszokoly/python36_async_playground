import _curses, curses, curses.ascii
from abc import ABC, abstractmethod
import time

class Display(ABC):
    def __init__(self,
        stdscr: "_curses._CursesWindow",
        miny: int = 24,
        minx: int = 80,
        workspaces = None,
        tabwin = None,
    ) -> None:
        self._stdscr = stdscr
        self.miny = miny
        self.minx = minx
        self.workspaces = workspaces if workspaces else []
        self.tabwin = tabwin
        self.done: bool = False
        self.posx = 1
        self.posy = 1
        self.maxy, self.maxx = self._stdscr.getmaxyx()
        self.active_ws_idx = 0
        self.color_pairs = self.init_color_pairs()
        curses.noecho()
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)

    @abstractmethod
    def make_display(self) -> None:
        pass

    @abstractmethod
    def handle_char(self, char: int) -> None:
        pass

    def set_exit(self) -> None:
        self.done = True

    def run(self) -> None:
        self._stdscr.nodelay(True)
        
        while not self.done:

            while self.must_resize():
                char = self._stdscr.getch()
                if char == curses.ERR:
                    time.sleep(0.1)
                elif char == curses.KEY_RESIZE:
                    self.maxy, self.maxx = self._stdscr.getmaxyx()
                    self._stdscr.erase()
                elif chr(char) in ("q", "Q"):
                    self.set_exit()
                    break
        
            if not self.done:
                self.make_display()
            
            while not self.done:
                char = self._stdscr.getch()
                if char == curses.ERR:
                    time.sleep(0.1)
                elif char == curses.KEY_RESIZE:
                    self.maxy, self.maxx = self._stdscr.getmaxyx()
                    if self.maxy >= self.miny and self.maxx >= self.minx:
                        self.make_display()
                    else:
                        self._stdscr.erase()
                        break
                else:
                    self.handle_char(char)
    
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
            "BLUE": curses.color_pair(13),
            "BLUE_LIGHT": curses.color_pair(34),
            "MAGENTA": curses.color_pair(6),
            "MAGENTA_LIGHT": curses.color_pair(14),
            "CYAN": curses.color_pair(46),
            "CYAN_LIGHT": curses.color_pair(15),
            "GREY": curses.color_pair(246),    
            "GREY_LIGHT": curses.color_pair(252),        
            "ORANGE": curses.color_pair(203),
            "ORANGE_LIGHT": curses.color_pair(209),
            "PINK": curses.color_pair(220),
            "PINK_LIGHT": curses.color_pair(226),
            "PURPLE": curses.color_pair(135),
            "PURPLE_LIGHT": curses.color_pair(148),
        }

    def must_resize(self):
        msg1 = f"Resize screen to {self.miny}x{self.minx}"
        msg2 = f"Current size     {self.maxy}x{self.maxx}"
        self._stdscr.addstr(int(self.maxy / 2) - 2,
            int((self.maxx - len(msg1)) / 2), msg1)
        self._stdscr.addstr(int(self.maxy / 2) - 1,
            int((self.maxx - len(msg2)) / 2), msg2)
        
        msg2 = "Press 'q' to exit"
        self._stdscr.addstr(
            int(self.maxy / 2) + 1,
            int((self.maxx - len(msg2)) / 2),
            msg2,
            curses.color_pair(255))
        
        self._stdscr.box()
        self._stdscr.refresh()
        
        if self.maxy < self.miny or self.maxx < self.minx:
            return True
        return False

class Tab:
    def __init__(self,
        stdscr,
        tab_names,
        nlines=2,
        yoffset=0,
        xoffset=0,
        color_pair=None,
    ):
        self._stdscr = stdscr
        self._tab_names = tab_names
        self._tab_width = max(len(x) for x in self._tab_names) + 2
        self._yoffset = yoffset
        self._xoffset = xoffset
        self._color_pair = color_pair if color_pair else curses.color_pair(0)
        self._active_tab_idx = 0
        self.maxy = nlines
        self.maxx = self._stdscr.getmaxyx()[1]
        self.win = self._stdscr.subwin(nlines, self.maxx, yoffset, xoffset)

    def draw(self):
        xpos = self._xoffset
        for idx, tab_names in enumerate(self._tab_names):
            active = bool(idx == self._active_tab_idx)
            self._draw_tab(tab_names, self._yoffset, xpos, active)
            xpos += self._tab_width + 2
        self.win.refresh()

    def _draw_tab(self, tab_name, ypos, xpos, active):
        border1 = "╭" + self._tab_width * "─" + "╮"
        border2 = "│" + " " * self._tab_width + "│"
        self.win.addstr(ypos, xpos, border1, self._color_pair)
        for linen in range(1, self.maxy - 1):
            self.win.addstr(ypos + linen, xpos, border2, self._color_pair)
        text = tab_name.center(self._tab_width)
        if not active:
            text_color_pair = self._color_pair
        else:
            text_color_pair = self._color_pair|curses.A_REVERSE
        self.win.addstr(ypos + 1, xpos+1, text, text_color_pair)

    def handle_char(self, char):
        if chr(char) == "\t":
            if self._active_tab_idx < len(self._tab_names) - 1:
                self._active_tab_idx += 1
            else:
                self._active_tab_idx = 0
            self.draw()

class Workspace:
    def __init__(self,
        stdscr,
        column_attrs,
        column_names=None,
        column_widths=None,
        storage=None,
        menu_window=None,
        color_pair=None,
        yoffset=2,
        xoffset=0,
    ):
        self._stdscr = stdscr
        self._column_attrs = column_attrs
        self._column_names = column_names if column_names else column_attrs
        self._column_widths = column_widths if column_widths else [
            len(x) for x in column_attrs]
        self._storage = storage if storage else []
        self._menuwin = menu_window
        self._yoffset = yoffset
        self._xoffset = xoffset
        self._color_pair = color_pair if color_pair else curses.color_pair(0)
        self.posy = 0
        self.posx = 0
        self.row_pos = 0
        self.maxy = self._stdscr.getmaxyx()[0] - yoffset
        self.maxx = sum(x + 1 for x in self._column_widths) + 1
        self.title = self._stdscr.subwin(3, self.maxx, yoffset, xoffset)
        self.body = self._stdscr.subwin(
            self.maxy - 3, self.maxx, yoffset + 3, xoffset)
        self._colors_pairs = Display.init_color_pairs()

    def draw(self):
        self._draw_title()
        self._draw_body()

    def _draw_title(self):
        self.title.attron(self._color_pair)
        self.title.box()
        self.title.attroff(self._color_pair)
        offset = 0
        for idx, (cname, cwidth) in enumerate(zip(self._column_names,
                                                  self._column_widths)):
            cname = f"│{cname:^{cwidth}}"
            xpos = self._xoffset if idx == 0 else offset
            offset = xpos + len(cname)
            self.title.addstr(1, xpos, cname, self._color_pair)
            if idx > 0:
                self.title.addstr(0, xpos, "┬", self._color_pair)
                self.title.addstr(2, xpos, "┼", self._color_pair)
        try:
            self.title.addstr(2, self._xoffset, "├", self._color_pair)
            self.title.addstr(2, self.maxx - 1, "┤", self._color_pair)
        except curses.error:
            pass
        self.title.refresh()

    def _draw_body(self):
        start_row = self.row_pos
        end_row = min(self.row_pos + (self.maxy - 3), len(self._storage))
        for ridx, row in enumerate(self._storage[start_row:end_row]):
            offset = 0
            try:
                for cidx, (attr, width) in enumerate(zip(self._column_attrs,
                self._column_widths)):
                    xpos = self._xoffset if cidx == 0 else offset
                    if hasattr(row, attr):
                        item = getattr(row, attr)
                    else:
                        item = row.get(attr)
                    item = f"│{str(item)[-width:]:>{width}}"
                    if hasattr(item, "color_pair"):
                        cpair = getattr(row, "color_pair")
                    elif hasattr(item, "get"):
                        cpair = item.get("color_pair", self._color_pair)
                    else:
                        cpair = self._color_pair
                    
                    if ridx == self.posy:
                        cpair = cpair|curses.A_REVERSE
                    offset = xpos + len(item)
                    self.body.addstr(ridx, xpos, item, cpair)
                self.body.addstr(ridx, xpos + len(item), "│", cpair)
            except curses.error:
                pass
        self.body.refresh()

    def handle_char(self, char):
        if char == curses.KEY_DOWN:
            self.row_pos = self.row_pos + 1 if self.posy == (self.maxy - 4) and self.row_pos + 1 <= len(self._storage) - (self.maxy - 3) else self.row_pos
            self.posy = self.posy + 1 if self.posy < (self.maxy - 4) and len(self._storage) - 1 > self.posy else self.posy
        elif char == curses.KEY_UP:
            self.row_pos = self.row_pos - 1 if self.row_pos > 0 and self.posy == 0 else self.row_pos
            self.posy =  self.posy - 1 if self.posy > 0 else self.posy
        elif char == curses.KEY_HOME:
            self.row_pos = 0
            self.posy = 0
        elif char == curses.KEY_END:
            self.posy = min(self.maxy - 4, len(self._storage) - 1)
            self.row_pos = max(0, len(self._storage) - (self.maxy - 3))
        elif char == curses.KEY_NPAGE:
            self.row_pos = min(self.row_pos + (self.maxy - 3), max(0, len(self._storage) - (self.maxy - 3)))
            self.posy = 0 if self.row_pos + (self.maxy - 3) <= len(self._storage) - 1 else min(len(self._storage) - 1, (self.maxy - 3) - 1)
        elif char == curses.KEY_PPAGE:
            self.posy = 0
            self.row_pos = max(self.row_pos - (self.maxy - 3), 0)
        self._draw_body()

class MyDisplay(Display):
    
    def make_display(self):
        self.maxy, self.maxx = self._stdscr.getmaxyx()
        self._stdscr.erase()  
        if self.tabwin:
            self.tabwin.draw()
        self.workspaces[self.active_ws_idx].draw()

    def handle_char(self, char: int) -> None:
        if chr(char) in ("q", "Q"):
            self.set_exit()
        elif chr(char) == "\t":
            self.active_ws_idx = (self.active_ws_idx + 1) % len(self.workspaces)
            self._stdscr.erase()
            self.workspaces[self.active_ws_idx].draw()
            self.tabwin.handle_char(char)
        else:
            self.workspaces[self.active_ws_idx].handle_char(char)

if __name__ == "__main__":
    bgw_storage = [
        {
            "host": "10.10.48.1",
            "gw_name": 'gw1',
            "gw_number": '001',
            "model": "g430",
            "firmware": "42.11.0",
            "hw": "1A",
            "slamon": "192.123.111.1",
            "rtp_stat": "enabled",
            "faults": "none"
        },
        {
            "host": "10.10.48.2",
            "gw_name": 'gw2',
            "gw_number": '002',
            "model": "g450",
            "firmware": "41.11.0",
            "hw": "4A",
            "slamon": "192.123.111.1",
            "rtp_stat": "disabled",
            "faults": "exists"
        },
    ]

    rtp_storage = [
        {
            "gw_number": "001",
            "session_id": "00001",
            "start_time": "2025-01-10,10:00:01",
            "end_time": "10:10:01",
            "local_addr": "10.10.48.1",
            "local_port": "2048",
            "remote_addr": "192.168.148.191",
            "remote_port": "33634",
            "qos":  "ok",
            "codec": "G711U",
        },
        {
            "gw_number": "002",
            "session_id": "00001",
            "start_time": "2025-01-10,10:00:02",
            "end_time": "10:10:02",
            "local_addr": "10.10.48.2",
            "local_port": "2052",
            "remote_addr": "10.10.48.4",
            "remote_port": "2064",
            "qos":  "ok",
            "codec": "G711U",
        },
        {
            "gw_number": "003",
            "session_id": "00001",
            "start_time": "2025-01-10,10:00:03",
            "end_time": "10:10:03",
            "local_addr": "10.10.48.3",
            "local_port": "2064",
            "remote_addr": "10.10.48.1",
            "remote_port": "2052",
            "qos":  "nok",
            "codec": "G711U",
        },
    ]

    def main(stdscr):
        curses.use_default_colors()

        ws1 = Workspace(
            stdscr,
            column_attrs=[
                "start_time", "end_time", "gw_number",
                "local_addr", "local_port", "remote_addr",
                "remote_port", "codec", "qos",
            ],
            column_names=[
                "Start", "End", "BGW", "Local-Address", "LPort",
                "Remote-Address", "RPort", "Codec", "QoS",
            ],
            column_widths=[8, 8, 3, 15, 5, 15, 5, 5, 3],
            storage = rtp_storage,
        )       
        ws2 = Workspace(
            stdscr,
            column_attrs=[
                "gw_number", "model", "firmware", "hw",
                "host", "slamon", "rtp_stat", "faults",
            ],
            column_names=[
                "BGW", "Model", "Firmware", "HW", "LAN IP",
                "SLAMon IP", "RTP-Stat", "Faults",
            ],
            column_widths=[3, 5, 8, 2, 15, 15, 8, 6],
            storage = bgw_storage,
        )
        tab = Tab(
            stdscr,
            tab_names=["RTP Stats", "Inventory"],
        )
        display = MyDisplay(stdscr, workspaces=[ws1, ws2], tabwin=tab)
        display.run()

    curses.wrapper(main)

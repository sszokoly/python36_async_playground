import asyncio
import _curses, curses, curses.ascii
from abc import ABC, abstractmethod
from utils import asyncio_run
import time
import os

class Display(ABC):
    def __init__(self, stdscr: "_curses._CursesWindow", minx: int = 80, miny: int = 24) -> None:
        self.stdscr = stdscr
        self.done: bool = False
        self.posx = 1
        self.posy = 1
        self.minx = minx
        self.miny = miny
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        curses.noecho()
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)
        self.init_color_pairs()

    @abstractmethod
    def make_display(self) -> None:
        pass

    @abstractmethod
    def handle_char(self, char: int) -> None:
        pass

    def set_exit(self) -> None:
        self.done = True

    async def run(self) -> None:
        self.stdscr.nodelay(True)
        
        while not self.done:

            while self.must_resize():
                char = self.stdscr.getch()
                if char == curses.ERR:
                    await asyncio.sleep(0.1)
                elif char == curses.KEY_RESIZE:
                    self.maxy, self.maxx = self.stdscr.getmaxyx()
                    self.stdscr.erase()
                elif chr(char) == "q":
                    self.set_exit()
                    break
        
            if not self.done:
                self.make_display()
            
            while not self.done:
                char = self.stdscr.getch()
                if char == curses.ERR:
                    await asyncio.sleep(0.1)
                elif char == curses.KEY_RESIZE:
                    self.maxy, self.maxx = self.stdscr.getmaxyx()
                    if self.maxy >= self.miny and self.maxx >= self.minx:
                        self.make_display()
                    else:
                        self.stdscr.erase()
                        break
                else:
                    self.handle_char(char)
    
    def init_color_pairs(self):
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        
        self.color_pairs = {
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
        self.stdscr.addstr(int(self.maxy / 2) - 2,
            int((self.maxx - len(msg1)) / 2), msg1)
        self.stdscr.addstr(int(self.maxy / 2) - 1,
            int((self.maxx - len(msg2)) / 2), msg2)
        
        msg2 = "Press 'q' to exit"
        self.stdscr.addstr(
            int(self.maxy / 2) + 1,
            int((self.maxx - len(msg2)) / 2),
            msg2,
            curses.color_pair(255))
        
        self.stdscr.box()
        self.stdscr.refresh()
        
        if self.maxy < self.miny or self.maxx < self.minx:
            return True
        return False

class Window(ABC):
    def __init__(self):
        self.colors_pairs = {
            "normal": curses.color_pair(0),
            "reversed": curses.color_pair(0)|curses.A_REVERSE,
            "standout": curses.color_pair(8),
            "address": curses.color_pair(124),
            "port": curses.color_pair(224),
            "codec": curses.color_pair(84),
            "title": curses.color_pair(255),
            "dimmmed": curses.color_pair(0)|curses.A_DIM,
            "ok": curses.color_pair(48),
            "fault": curses.color_pair(10),
            "active": curses.color_pair(215),
            "ended": curses.color_pair(250),
        }

class MyDisplay(Display):

    def make_display(self) -> None:

        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.stdscr.erase()

        #self.stdscr.addstr(0, 0, f'{self.maxx}x{self.maxy}')
        #curses.setsyx(self.posy, self.posx)

        #ypos = 3
        #for k,v in self.color_pairs.items():
        #    self.stdscr.addstr(ypos, 1, f"{k}", v)
        #    ypos += 1

        #self.stdscr.box()
        self.stdscr.addstr(0, 0, "╭─────────╮", curses.color_pair(0))
        self.stdscr.addstr(1, 0, "│         │", curses.color_pair(0))
        self.stdscr.addstr(2, 0, "╰─────────╯", curses.color_pair(0))
        self.stdscr.addstr(1, 1, "RTP Stats", curses.color_pair(221))
        self.stdscr.addstr(0, 11, "╭─────────╮", curses.color_pair(0))
        self.stdscr.addstr(1, 11, "│         │", curses.color_pair(0))
        self.stdscr.addstr(2, 11, "╰─────────╯", curses.color_pair(0))
        self.stdscr.addstr(1, 13, "Systems", curses.color_pair(221))
        self.stdscr.addstr(0, 22, "╭─────────╮", curses.color_pair(0))
        self.stdscr.addstr(1, 22, "│         │", curses.color_pair(0))
        self.stdscr.addstr(2, 22, "╰─────────╯", curses.color_pair(0))
        self.stdscr.addstr(1, 23, "Util/Temp", curses.color_pair(221))
        self.stdscr.refresh()
        self.menu = MenuWindow()
        self.header = HeaderWindow(
            col_names=[
                "  Start ","   End  ", "BGW",
                " Local-Address ", "LPort",
                " Remote-Address", "RPort",
                "Codec", "QoS", "Cp"])


    def handle_char(self, char: int) -> None:
        if chr(char) == "q":
            self.set_exit()
        elif char in (curses.ascii.CR, curses.ascii.LF, curses.KEY_ENTER):
            self.set_exit()
        elif char == curses.KEY_RIGHT:
            self.posx = self.posx + 1 if self.posx < self.maxx - 1 else self.posx
            curses.setsyx(self.posy, self.posx)
        elif char == curses.KEY_LEFT:
            self.posx = self.posx - 1 if self.posx > 0 else self.posx
            curses.setsyx(self.posy, self.posx)
        elif char == curses.KEY_UP:
            self.posy = self.posy - 1 if self.posy > 0 else self.posy
            curses.setsyx(self.posy, self.posx)
        elif char == curses.KEY_DOWN:
            self.posy = self.posy + 1 if self.posy < self.maxy -1 else self.posy
            curses.setsyx(self.posy, self.posx)
        curses.doupdate()

class MenuWindow(Window):
    def __init__(self, nlines=1, xstart=10):
        super().__init__()
        mcols, mlines = os.get_terminal_size()
        self.buttons = ["s", "c", "e", "t"]
        self.xstart = xstart
        self.win = curses.newwin(nlines, mcols, mlines-nlines, 1)
        self.maxy, self.maxx = self.win.getmaxyx()
        self.draw()

    def draw(self):
        self.win.addstr(0, 0, ' ' * (self.maxx - 1), self.colors_pairs["reversed"])
        for idx, button in enumerate(self.buttons):
            xpos = (len(self.buttons[idx-1]) + offset + 1) if idx > 0 else self.xstart
            self.win.addstr(0, xpos, button, self.colors_pairs["reversed"])
            offset = xpos
        self.win.refresh()

    def handle_char(self, char):        
        pass


class HeaderWindow(Window):
    def __init__(self, nlines=1, col_names=None, separator=True):
        super().__init__()
        self.separator = separator
        mcols, _ = os.get_terminal_size()
        self.col_names = col_names if col_names else []
        self.win = curses.newwin(nlines + 2, mcols, 3, 0)
        self.maxy, self.maxx = self.win.getmaxyx()
        self.draw()

    def draw(self):
        self.win.box()
        offset = 0
        for idx, col_name in enumerate(self.col_names):
            xpos = (len(self.col_names[idx-1]) + offset + 1) if idx > 0 else 0
            if self.separator:
                col_name = f"{col_name}│"
                topsep = "┬" if xpos else "┌"
                botsep = "┴" if xpos else "├"
                self.win.addstr(0, xpos, topsep, self.colors_pairs["normal"])
                self.win.addstr(2, xpos, botsep, self.colors_pairs["normal"])
            self.win.addstr(1, xpos+1, col_name, self.colors_pairs["normal"])
            offset = xpos
        if self.separator:
            xpos = offset + len(self.col_names[-1]) + 1
            topsep = "┬" if xpos < self.maxx - 1 else "┐"
            botsep = "┴" if xpos < self.maxx - 1 else "┤"
            self.win.addstr(0, xpos, topsep, self.colors_pairs["normal"])
            #self.win.addstr(2, xpos, botsep, self.colors_pairs["normal"])
        self.win.refresh()


async def display_main(stdscr):
    display = MyDisplay(stdscr)
    await display.run()


def change_terminal(to_type="xterm-256color"):
    types = os.popen("toe -a").read().splitlines()
    if any(x for x in types if x.startswith(to_type)):
        os.environ["TERM"] = to_type

def main(stdscr) -> None:
    """Main entry point to run the asynchronous tasks.

    Args:
        host (str): The host to connect to.
        port (int): The port to connect to.
    """
    asyncio_run(display_main(stdscr))

if __name__ == "__main__":
    term = os.environ.get("TERM")
    change_terminal("xterm-256color")   
    curses.wrapper(main)
    if term:
        os.environ["TERM"] = term
    else:
        del os.environ["TERM"]
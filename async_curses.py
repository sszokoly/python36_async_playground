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
        self.initcolors()

    @abstractmethod
    def make_display(self) -> None:
        pass

    @abstractmethod
    def handle_char(self, char: int) -> None:
        pass

    def set_exit(self) -> None:
        self.done = True

    async def run(self) -> None:
        curses.curs_set(1)
        self.stdscr.nodelay(True)

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
            else:
                self.make_display()

                while not self.done:
                    char = self.stdscr.getch()
                    if char == curses.ERR:
                        await asyncio.sleep(0.1)
                    elif char == curses.KEY_RESIZE:
                        #self.make_display()
                        break
                    else:
                        self.handle_char(char)
    
    def initcolors(self):
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


class MyDisplay(Display):

    def make_display(self) -> None:

        colors = {
            "normal": curses.color_pair(0),
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


        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.stdscr.erase()
        self.stdscr.box()

        self.stdscr.addstr(0, 0, f'{self.maxx}x{self.maxy}')
        curses.setsyx(self.posy, self.posx)

        ypos = 3
        for k,v in self.color_pairs.items():
            self.stdscr.addstr(ypos, 1, f"{k}", v)
            ypos += 1
        self.stdscr.refresh()
        self.menuwin = MenuWindow()
        self.headerwin = HeaderWindow()


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

class MenuWindow():
    def __init__(self, nlines=1, ncols=None):
        mcols, mlines = os.get_terminal_size()
        self.win = curses.newwin(nlines, mcols, mlines-nlines, 0)
        self.maxy, self.maxx = self.win.getmaxyx()
        self.win.addstr(0, 1, f"{' ':>{self.maxx-2}}", curses.A_REVERSE)
        self.win.refresh()


class HeaderWindow():
    def __init__(self, nlines=2, ncols=None):
        mcols, mlines = os.get_terminal_size()
        self.header = curses.newwin(nlines, mcols, 1, 0)
        self.maxy, self.maxx = self.header.getmaxyx()
        self.header.addstr(0, 1, f"{' ':>{self.maxx-2}}", curses.A_REVERSE)
        self.header.refresh()


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
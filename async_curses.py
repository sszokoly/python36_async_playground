import asyncio
import _curses, curses
from abc import ABC, abstractmethod
from utils import asyncio_run

class Display(ABC):
    def __init__(self, stdscr: "_curses._CursesWindow"):
        self.stdscr = stdscr
        self.done: bool = False
        self.posx = 1
        self.posy = 1

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

        self.make_display()

        while not self.done:
            char = self.stdscr.getch()
            if char == curses.ERR:
                await asyncio.sleep(0.05)
            elif char == curses.KEY_RESIZE:
                self.make_display()
            else:
                self.handle_char(char)

class MyDisplay(Display):
    def make_display(self) -> None:
        msg1 = "Resize at will"
        msg2 = "Press 'q' to exit"

        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.stdscr.erase()

        self.stdscr.box()
        self.stdscr.addstr(
            int(self.maxy / 2) - 1, int((self.maxx - len(msg1)) / 2), msg1
        )
        self.stdscr.addstr(
            int(self.maxy / 2) + 1, int((self.maxx - len(msg2)) / 2), msg2
        )

        self.stdscr.addstr(
            0, 0, f'{self.maxx}x{self.maxy}'
        )

        curses.setsyx(self.posy, self.posx)
        self.stdscr.refresh()

    def handle_char(self, char: int) -> None:
        if chr(char) == "q":
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

async def display_main(stdscr):
    display = MyDisplay(stdscr)
    await display.run()


def main(stdscr) -> None:
    """Main entry point to run the asynchronous tasks.

    Args:
        host (str): The host to connect to.
        port (int): The port to connect to.
    """
    asyncio_run(display_main(stdscr))

if __name__ == "__main__":
    curses.wrapper(main)
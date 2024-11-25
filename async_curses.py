import asyncio
import _curses, curses, curses.ascii
from abc import ABC, abstractmethod
from utils import asyncio_run
from session import iter_session_detailed_attrs, cmds_to_session_dicts, stdout_to_cmds

class Display(ABC):
    def __init__(self, stdscr: "_curses._CursesWindow"):
        self.stdscr = stdscr
        self.done: bool = False
        self.posx = 1
        self.posy = 1
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

        self.make_display()

        while not self.done:
            char = self.stdscr.getch()
            if char == curses.ERR:
                await asyncio.sleep(0.05)
            elif char == curses.KEY_RESIZE:
                self.make_display()
            else:
                self.handle_char(char)
    
    def initcolors(self):
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        curses.init_pair(255, 21, 245)

        self.colors = {
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

class MyDisplay(Display):
    def make_display(self) -> None:
        msg1 = "Resize at will"
        msg2 = "Press 'q' to exit"

        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.stdscr.erase()

        self.stdscr.box()
        #self.stdscr.addstr(q
        #    int(self.maxy / 2) - 1, int((self.maxx - len(msg1)) / 2), msg1, 
        #    curses.COLOR_RED
        #)
        #self.stdscr.addstr(
        #    int(self.maxy / 2) + 1, int((self.maxx - len(msg2)) / 2), msg2,
        #    curses.COLOR_BLUE
        #)

        #for y, x, text, color in iter_session_detailed_attrs(session_dict):
        #    self.stdscr.addstr(y, x, text, self.colors[color])

        self.stdscr.addstr(
            0, 0, f'{self.maxx}x{self.maxy}'
        )

        curses.setsyx(self.posy, self.posx)
        self.stdscr.refresh()

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
    stdout = '''#BEGIN\nshow rtp-stat detailed 00001\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Faulted, EngineId: 10\r\nStart-Time: 2024-11-20,16:07:30, End-Time: 2024-11-21,07:17:48\r\nDuration: 15:10:18\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.110:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 3718873098 (0)\r\nSamples: 10923 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 54626.390sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 2731505, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 41, DSCP 0, L2Pri 0, RTCP 10910, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10927, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #10902, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    print(stdout)
    session_dicts = cmds_to_session_dicts(stdout_to_cmds(stdout))
    for id, session_dict in session_dicts.items():
        print(session_dict)
        for y, x, text, attrs in iter_session_detailed_attrs(session_dict):
            print(y, x, text, attrs)
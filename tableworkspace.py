import _curses, curses, curses.ascii
import asyncio
import time
import sys
import re
from utils import asyncio_run
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set

BGWS = []

SYSTEM_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'gw_name',
        'column_name': 'Name',
        'column_color': 'normal',
        'column_fmt_spec': '>13',
        'column_xpos': 5,
    },
    {
        'column_attr': 'host',
        'column_name': 'LAN IP',
        'column_color': 'normal',
        'column_fmt_spec': '>15',
        'column_xpos': 19,
    },
    {
        'column_attr': 'mac',
        'column_name': 'LAN MAC',
        'column_color': 'normal',
        'column_fmt_spec': '>12',
        'column_xpos': 35,
    },
    {
        'column_attr': 'uptime',
        'column_name': 'Uptime',
        'column_color': 'normal',
        'column_fmt_spec': '>13',
        'column_xpos': 48,
    },
    {
        'column_attr': 'model',
        'column_name': 'Model',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 62,
    },
    {
        'column_attr': 'hw',
        'column_name': 'HW',
        'column_color': 'normal',
        'column_fmt_spec': '>2',
        'column_xpos': 68,
    },
    {
        'column_attr': 'fw',
        'column_name': 'Firmware',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

class Button:
    def __init__(self, *chars_int: int,
        win: "_curses._CursesWindow",
        y: Optional[int] = 0,
        x: Optional[int] = 0,
        char_alt: Optional[str] = None,
        label_off: Optional[str] = None,
        label_on: Optional[str] = None,
        color_scheme = None,
        exec_func_on: Optional[Callable[[], None]] = None,
        exec_func_off: Optional[Callable[[], None]] = None,
        done_callback_on: Optional[Callable[[], None]] = None,
        done_callback_off: Optional[Callable[[], None]] = None,
        status_label: Optional[str] = None,
        status_attr_on: Optional[int] = None,
        status_attr_off: Optional[int] = None,
        **kwargs: Any) -> None:
        """
        Initialize a Button.

        Parameters
        ----------
        chars_int : int
            A list of integer values of characters to listen for.
        win : _curses._CursesWindow
            The curses window where the button is displayed.
        y : int, optional
            The y-coordinate of the button. Defaults to 0.
        x : int, optional
            The x-coordinate of the button. Defaults to 0.
        char_alt : str, optional
            An alternative character to display instead of the first character
            in chars_int. Defaults to None.
        label_on : str, optional
            The label to display when the button is on. Defaults to "On ".
        label_off : str, optional
            The label to display when the button is off. Defaults to "Off" if
            not label_on else label_on.
        exec_func_on : Callable[[], None], optional
            The function to call when the button is turned on. Defaults to None.
        exec_func_off : Callable[[], None], optional
            The function to call when the button is turned off. Defaults to None.
        done_callback_on : Callable[[], None], optional
            The function to call when the on action is completed. Defaults to
            None.
        done_callback_off : Callable[[], None], optional
            The function to call when the off action is completed. Defaults to
            None.
        status_label : str, optional
            The label to display in the status bar when the button is on.
            Defaults to "".
        status_attr_on : int, optional
            The curses attribute to use when the button is on in the status bar.
            Defaults to the attribute_on value.
        status_attr_off : int, optional
            The curses attribute to use when the button is off in the status
            bar. Defaults to the attribute_off value.
        **callback_kwargs : Any
            Additional keyword arguments to pass to the callbacks.

        Returns
        -------
        None
        """

        self.chars_int = chars_int
        self.win = win
        self.y = y
        self.x = x
        self.char_alt = char_alt
        self.label_off = label_off or ("On" if not label_on else label_on)
        self.label_on = label_on or "Off"
        self.color_scheme = color_scheme or {"normal": 0, "standout": 65536}
        self.attr = self.color_scheme.get("standout", 65536)
        self.exec_func_on = exec_func_on
        self.exec_func_off = exec_func_off
        self.done_callback_on = done_callback_on
        self.done_callback_off = done_callback_off
        self.status_label = status_label if status_label else ""
        self.status_attr_on = status_attr_on or self.color_scheme.get("status_on", self.attr)
        self.status_attr_off = status_attr_off or self.color_scheme.get("status_off", self.attr)
        self.kwargs = {**{"button": self}, **(kwargs if kwargs else {})}
        self.state = False if exec_func_off else True
        self.exec_func_on_task = None
        self.exec_func_off_task = None

    def draw(self) -> None:
        """
        Draw the button on the given curses window.

        Returns
        -------
        None
        """
        if self.char_alt:
            char = self.char_alt
        elif any(chr(c).isalnum() for c in self.chars_int):
            char = next(c for c in self.chars_int if chr(c).isalnum())
        else:
            char = repr(chr(self.chars_int[0]))

        label = self.label_on if self.state else self.label_off

        try:
            self.win.addstr(self.y, self.x, f"{char}={label}", self.attr)
        except curses.error:
            pass

        self.win.refresh()

    def toggle(self) -> None:
        """
        Toggle the button state.

        Returns
        -------
        None
        """
        if self.exec_func_off: 
            self.state = not self.state

    def press(self) -> None:
        """
        Handle a button press synchronously:
         - Toggle the state.
         - Schedule the appropriate callback onto the event loop.

        Returns
        -------
        None
        """
        self.toggle()

        if self.state:
            if self.exec_func_on:
                if asyncio.iscoroutinefunction(self.exec_func_on):
                    self.exec_func_on_task: asyncio.Task = create_task(
                        self.exec_func_on(**self.kwargs),
                        name=f"{self.exec_func_on.__name__}")
                    if self.done_callback_on:
                        self.exec_func_on_task.add_done_callback(
                            self.done_callback_on)
                else:
                    self.exec_func_on(**self.kwargs)
        else:
            if self.exec_func_off:
                if asyncio.iscoroutinefunction(self.exec_func_off):
                    self.exec_func_off_task: asyncio.Task = create_task(
                        self.exec_func_off(**self.kwargs),
                        name=f"{self.exec_func_off.__name__}")
                    if self.done_callback_off:
                        self.exec_func_off_task.add_done_callback(
                            self.done_callback_off)
                else:
                    self.exec_func_off(**self.kwargs)
                
                if self.exec_func_on_task and not self.exec_func_on_task.done():
                    self.exec_func_on_task.remove_done_callback(
                        self.done_callback_on)
                    self.exec_func_on_task = None

    async def handle_char(self, char: int) -> None:
        """
        Process a keypress.

        Parameters
        ----------
        key : int
            The character code of the key that was pressed.

        Returns
        -------
        None
        """
        if char in self.chars_int:
            logger.info(f"Button.handle_char({repr(chr(char))})")
            self.press()

    def status(self) -> str:
        """
        Get the current label of the button.

        Returns
        -------
        str
            The label of the button.
        """
        attr = self.status_attr_on if self.state else self.status_attr_off
        return self.status_label, attr


class Workspace:
    def __init__(self, stdscr,
        column_attrs,
        column_names=None,
        column_fmt_specs=None,
        column_colors=None,
        column_xposes=None,
        *,
        menubar=None,
        name=None,
        storage=None,
        panels=None,
        yoffset=2,
        xoffset=0,
        title_width=3,
        color_scheme=None,
        **kwargs,
    ):
        self.stdscr = stdscr
        self.column_attrs = column_attrs
        self.column_names = column_names or column_attrs
        self.column_fmt_specs = column_fmt_specs or [
            f"^{len(x)}" for x in column_names]
        self.column_colors = column_colors or [None for x in column_names]
        self.column_xposes = column_xposes or [None for x in column_names]
        self.menubar = menubar
        self.name = name
        self.storage = storage if storage is not None else []
        self.yoffset = yoffset
        self.xoffset = xoffset
        self.color_scheme = color_scheme or {"normal": 0, "standout": 65536}
        self.title_width = title_width
        self.bodywin_posy = 0
        self.bodywin_posx = 0
        self.storage_idx = 0
        self.attr = self.color_scheme["normal"]
        self.maxy = self.stdscr.getmaxyx()[0] - yoffset
        self.maxx = self.stdscr.getmaxyx()[1]
        self.titlewin = stdscr.subwin(title_width, self.maxx,
            yoffset, xoffset)
        self.bodywin = self.stdscr.subwin(
            self.maxy - title_width - menubar.maxy, self.maxx,
            yoffset + title_width, xoffset)
        self.panel = curses.panel.new_panel(self.bodywin)

    def iter_attrs(self, obj: object, xoffset: int = 0) -> Iterator[Tuple[int, str, str]]:
        """
        Iterate over the attributes of the given object.

        - `xpos`: The x position of the attribute
        - `attr_value`: The value of the attribute, formatted with `fmt_spec`
        - `color`: The color of the attribute as a string

        :param obj: The object whose attributes are to be iterated over
        :param xoffset: An x offset as an integer that is added to the x position
        """
    
        offset = 1
        
        params = zip(self.column_attrs, self.column_names,
            self.column_fmt_specs, self.column_colors, self.column_xposes)
        
        for attr, name, fmt_spec, color, xpos in params:
            _len = len(name)

            if hasattr(obj, attr):
                attr_value = getattr(obj, attr)
            elif hasattr(obj, "__getitem__"):
                attr_value = obj.get(attr, attr)
            else:
                attr_value = attr

            if isinstance(attr_value, int) or isinstance(attr_value, float):
                attr_value = str(attr_value)

            if fmt_spec:
                m = re.search(r"([<>^]?)(\d+)", fmt_spec)
                _len = int(m.group(2)) if m else _len
                if m.group(1) in ("<", "^"):
                    attr_value = f"{attr_value[:_len]:{fmt_spec}}"
                elif m.group(1) == ">":
                    attr_value = f"{attr_value[-_len:]:{fmt_spec}}"
            
            if isinstance(attr_value, str):
                attr_value = f"{attr_value[:_len]}"

            if not xpos:
                xpos = offset
            
            yield xpos + xoffset, attr_value, color
            offset += len(attr_value) + 1

    def iter_column_names(self, xoffset: int = 0) -> Iterator[Tuple[int, str, str]]:
        """
        Iterate over the column names with formatting, color, and x position.

        :param xoffset: An integer that is added to the x position
        :return: An iterator of tuples with x position, name and color
        """
        offset = 1

        params = zip(self.column_names, self.column_fmt_specs,
            self.column_colors, self.column_xposes)

        for name, fmt_spec, color, xpos in params:
            _len = len(name)

            if fmt_spec:
                m = re.search(r"[<>^](\d+)", fmt_spec)
                _len = int(m.group(1)) if m else _len
            
            name = f"{name:^{_len}}"

            if not xpos:
                xpos = offset

            yield xpos + xoffset, name, color
            offset += len(name) + 1

    def draw(self):
        if not self.panel.hidden():
            self.draw_titlewin()
            self.draw_bodywin()
            self.draw_menubar()

    def draw_titlewin(self):
        self.titlewin.attron(self.attr)
        self.titlewin.box()
        self.titlewin.attroff(self.attr)
  
        for idx, (xpos, name, color) in enumerate(self.iter_column_names()):
            attr = self.color_scheme.get(color, 0)
            if idx > 0:
                self.titlewin.addstr(1, xpos - 1, "│", attr)
                self.titlewin.addstr(0, xpos - 1, "┬", attr)
                self.titlewin.addstr(2, xpos - 1, "┼", attr)
            self.titlewin.addstr(1, xpos, name, attr)
            self.titlewin.refresh()

        try:
            self.titlewin.addstr(2, self.xoffset, "├", attr)
            self.titlewin.addstr(2, self.maxx - 1, "┤", attr)
        except curses.error:
            pass
        self.titlewin.refresh()

    def draw_bodywin(self):
        start_row = self.storage_idx
        end_row = min(self.storage_idx + (self.maxy - 3), len(self.storage))
        
        for ridx, obj in enumerate(self.storage[start_row:end_row]):
            try:
                for xpos, attr_value, color in self.iter_attrs(obj, self.xoffset):
                    if ridx == self.bodywin_posy:
                        attr = self.color_scheme.get(color, 0)|curses.A_STANDOUT
                    else:
                        attr = self.color_scheme.get(color, 0)
                    self.bodywin.addstr(
                        ridx, xpos - 1, "│" + attr_value + "│", attr
                    )
            except curses.error:
                pass
        
        if not self.panel.hidden():
            self.bodywin.refresh()

    def draw_menubar(self):
        if self.menubar:
            self.menubar.draw()

    async def handle_char(self, char):
        if char == curses.KEY_DOWN:
            if ((self.bodywin_posy == (self.maxy - (self.title_width + 2))) and
                (self.storage_idx + 1 <= (len(self.storage) -
                                          (self.maxy - self.title_width)))):
                self.storage_idx += 1
            if ((self.bodywin_posy < (self.maxy - (self.title_width + 2))) and
                (len(self.storage) - 1 > self.bodywin_posy)):
                self.bodywin_posy += 1

        elif char == curses.KEY_UP:
            if self.storage_idx > 0 and self.bodywin_posy == 0:
                self.storage_idx -= 1
            if self.bodywin_posy > 0:
                self.bodywin_posy -= 1

        elif char == curses.KEY_HOME:
            self.storage_idx = 0
            self.bodywin_posy = 0

        elif char == curses.KEY_END:
            self.bodywin_posy = min(
                self.maxy - (self.title_width + 2),
                len(self.storage) - 1
            )
            self.storage_idx = max(
                0,
                len(self.storage) - (self.maxy - self.title_width)
            )

        elif char == curses.KEY_NPAGE:
            self.storage_idx = min(
                self.storage_idx + (self.maxy - self.title_width - 1),
                max(0, len(self.storage) - (self.maxy - self.title_width))
            )
            if self.storage_idx + (self.maxy - self.title_width + 1) <= len(self.storage):
                self.bodywin_posy = 0
            else:
                self.bodywin_posy = min(len(self.storage) - 1,
                    self.maxy - self.title_width - 2)

        elif char == curses.KEY_PPAGE:
            self.bodywin_posy = 0
            self.storage_idx = max(
                self.storage_idx - (self.maxy - self.title_width), 0)
        
        else:
            await self.menubar.handle_char(char)

        if not self.panel.hidden():
            self.draw_bodywin()

class Tab:
    def __init__(self,
        stdscr,
        tab_names,
        yoffset=0,
        xoffset=0,
        color_scheme=None,
    ):
        self.stdscr = stdscr
        self.tab_names = tab_names
        self.yoffset = yoffset
        self.xoffset = xoffset
        self.color_scheme = color_scheme or {"normal": 0, "standout": 65536}
        self.attr = self.color_scheme.get("normal", 0)
        self.attr_standout = self.color_scheme.get("standout", 65536)
        self.tab_width = max(len(x) for x in self.tab_names)
        self.active_tab_idx = 0
        self.win = self.stdscr.subwin(2, self.stdscr.getmaxyx()[1] - xoffset,
            yoffset, xoffset)

    def draw(self):
        xpos, ypos = self.xoffset, self.yoffset
        for idx, tab_names in enumerate(self.tab_names):
            
            try:
                self.win.addstr(ypos, xpos,
                    "╭" + "─" * self.tab_width + "╮", self.attr)
                self.win.addstr(ypos + 1, xpos,
                    "│" + " " * self.tab_width + "│", self.attr)
                
                if idx == self.active_tab_idx:
                    self.win.addstr(ypos + 1, xpos + 1,
                        tab_names.center(self.tab_width), self.attr_standout)
                else:    
                    self.win.addstr(ypos + 1, xpos + 1,
                        tab_names.center(self.tab_width), self.attr)
            except _curses.error:
                pass

            xpos += self.tab_width + 2
        self.win.refresh()

    async def handle_char(self, char):
        if char in (ord("\t"), curses.KEY_RIGHT):
            self.active_tab_idx = (self.active_tab_idx + 1) % len(self.tab_names)
        elif char in (curses.KEY_LEFT, curses.KEY_BACKSPACE):
            self.active_tab_idx = (self.active_tab_idx - 1) % len(self.tab_names)
        self.draw()


class MyDisplay():
    def __init__(self,
        stdscr: "_curses._CursesWindow",
        miny: int = 24,
        minx: int = 80,
        workspaces = None,
        tab = None,
    ) -> None:
        self.stdscr = stdscr
        self.miny = miny
        self.minx = minx
        self.workspaces = workspaces
        self.tab = tab
        self.confirmation = None
        self.done: bool = False
        self.bodywin_posx = 1
        self.bodywin_posy = 1
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.active_ws_idx = 0
        self.color_pairs = self.init_color_pairs()

    def set_exit(self) -> None:
        self.done = True

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

    async def run(self) -> None:
        self.stdscr.nodelay(True)
        self.make_display()
        
        while not self.done:
            char = self.stdscr.getch()
            if char == curses.ERR:
                await asyncio.sleep(0.05)
            elif char == curses.KEY_RESIZE:
                self.maxy, self.maxx = self.stdscr.getmaxyx()
                if self.maxy >= self.miny and self.maxx >= self.minx:
                    self.make_display()
                else:
                    self.stdscr.erase()
                    break
            else:
                await self.handle_char(char)

    def make_display(self):
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.stdscr.erase()  
        if self.tab:
            self.tab.draw()
        self.workspaces[self.active_ws_idx].draw()

    async def handle_char(self, char: int) -> None:
        if chr(char) in ("q", "Q"):
            self.set_exit()
        elif char in (ord("\t"), curses.KEY_RIGHT,
                      curses.KEY_BACKSPACE, curses.KEY_LEFT):
            if char in (ord("\t"), curses.KEY_RIGHT):
                self.active_ws_idx = (self.active_ws_idx + 1) % len(self.workspaces)
            else:
                self.active_ws_idx = (self.active_ws_idx - 1) % len(self.workspaces)
        
            self.stdscr.erase()
            self.workspaces[self.active_ws_idx].draw()
            await self.tab.handle_char(char)
        else:
            await self.workspaces[self.active_ws_idx].handle_char(char)

    def draw_maxyx(self, stdscr, maxy, maxx, ypos):
            text = f"{maxy}x{maxx} ypos={ypos}"
            attr = curses.color_pair(3)
            stdscr.addstr(maxy // 2, maxx // 2 - 6, (len(text)+2) * " ", attr)
            stdscr.addstr(maxy // 2, maxx // 2 - 6, text, attr)
            stdscr.refresh()

    @property
    def active_workspace(self):
        return self.workspaces[self.active_ws_idx]

def main(stdscr, miny: int = 24, minx: int = 80):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.start_color()
    curses.noecho()

    #stdscr.resize(24, 80)
    
    ws1 = Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in SYSTEM_ATTRS],
            column_names=[x['column_name'] for x in SYSTEM_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in SYSTEM_ATTRS],
            column_colors=[x['column_color'] for x in SYSTEM_ATTRS],
            column_xposes=[x['column_xpos'] for x in SYSTEM_ATTRS],
            color_scheme=None,
            storage=BGWS,
            name="System",
        )
    
    tab = Tab(stdscr, tab_names=[ws1.name])
    mydisplay = MyDisplay(stdscr, workspaces=[ws1], tabwin=tab)
    asyncio_run(mydisplay.run())

curses.wrapper(main)
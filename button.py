
import _curses, curses, curses.ascii, curses.panel
import asyncio
from utils import asyncio_run
import functools
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set, Coroutine, Callable

GATEWAYS = {}

def create_task(
    coro: Coroutine[Any, Any, Any],
    name: Optional[str] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> asyncio.Task:
    """Patched version of create_task that assigns a name to the task.

    Parameters
    ----------
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop to create the task in.
    coro : Coroutine[Any, Any, Any]
        The coroutine to run in the task.
    name : Optional[str], optional
        The name to assign to the task. Defaults to None.

    Returns
    -------
    asyncio.Task
        The newly created task.
    """
    loop = loop if loop else asyncio.get_event_loop()
    task = asyncio.ensure_future(coro, loop=loop)
    task.name = name
    return task

def ungetch_done_callback(char, fut):
    try:
        fut.result()  # Will raise CancelledError if the task was cancelled.
    except asyncio.CancelledError:
        # If cancelled, leave self.state True.
        return
    except Exception:
        # Optionally log or handle exceptions here.
        return
    curses.ungetch(char)

class ProgressBar:
    def __init__(self, stdscr: "_curses._CursesWindow",
        fraction: float = 0,
        width: int = 21,
        attr_fg: Optional[int] = None,
        attr_bg: Optional[int] = None,
        offset_y: int = 0) -> None:
        """
        Initialize the progress bar.

        Parameters
        ----------
        stdscr : _curses._CursesWindow
            The curses window that the progress bar should be drawn on.
        fraction : float, optional
            The fraction of the bar that should be filled. Defaults to 0.
        width : int, optional
            The width of the progress bar. Defaults to 21.
        attr_fg : Optional[int], optional
            The curses attribute to use for the foreground. Defaults to
            curses.color_pair(221)|curses.A_REVERSE.
        attr_bg : Optional[int], optional
            The curses attribute to use for the background. Defaults to
            curses.color_pair(239)|curses.A_REVERSE.
        offset_y : int, optional
            The y offset of the progress bar. Defaults to 0.
        """
        self.stdscr = stdscr
        self.fraction = fraction
        self.width = width
        self.attr_fg = attr_fg or curses.color_pair(221)|curses.A_REVERSE
        self.attr_bg = attr_bg or curses.color_pair(239)|curses.A_REVERSE
        maxy, maxx = stdscr.getmaxyx()
        begin_y = maxy // 2 + offset_y
        begin_x = maxx // 2 - (width // 2)
        self.win = curses.newwin(1, width, begin_y, begin_x)
        curses.panel.new_panel(self.win)
        self.win.attron(self.attr_bg)

    def draw(self, fraction: Optional[float] = None) -> "ProgressBar":
        """
        Draw the progress bar on the screen.

        Parameters
        ----------
        fraction : Optional[float], optional
            The fraction of the bar that should be filled. Defaults to None.

        Returns
        -------
        ProgressBar
            The same instance.
        """
        if fraction:
            self.win.erase()
            self.fraction = fraction
        
        filled_width = int(self.fraction * self.width)
        remaining_width = self.width - filled_width
        
        try:
            self.win.addstr(0, 0, " " * filled_width, self.attr_fg)
            self.win.addstr(0, filled_width, " " * remaining_width, self.attr_bg)
        except _curses.error:
            pass
        
        self.win.refresh()
        return self

    def erase(self) -> "ProgressBar":
        """
        Erase the progress bar from the screen.

        Returns
        -------
        ProgressBar
            The same instance.
        """
        self.win.erase()
        self.win.refresh()

class Button:
    def __init__(self, *chars_int: int,
        win: "_curses._CursesWindow",
        y: Optional[int] = 0,
        x: Optional[int] = 0,
        char_alt: Optional[str] = None,
        label_on: Optional[str] = None,
        label_off: Optional[str] = None,
        attr_on: Optional[int] = None,
        attr_off: Optional[int] = None,
        callback_on: Optional[Callable[[], None]] = None,
        callback_off: Optional[Callable[[], None]] = None,
        done_callback_on: Optional[Callable[[], None]] = None,
        done_callback_off: Optional[Callable[[], None]] = None,
        status_label: Optional[str] = None,
        status_attr_on: Optional[int] = None,
        status_attr_off: Optional[int] = None,
        **callback_kwargs: Any) -> None:
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
        attr_on : int, optional
            The curses attribute to use when the button is on. Defaults to
            curses.A_REVERSE.
        attr_off : int, optional
            The curses attribute to use when the button is off. Defaults to
            curses.A_NORMAL.
        callback_on : Callable[[], None], optional
            The function to call when the button is turned on. Defaults to None.
        callback_off : Callable[[], None], optional
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
        self.label_on = label_on or "Off"
        self.label_off = label_off or ("On" if not label_on else label_on)
        self.attr_on = attr_on or curses.A_REVERSE
        self.attr_off = attr_off or curses.A_REVERSE
        self.callback_on = callback_on
        self.callback_off = callback_off
        self.done_callback_on = done_callback_on
        self.done_callback_off = done_callback_off
        self.status_label = status_label if status_label else ""
        self.status_attr_on = status_attr_on or self.attr_on
        self.status_attr_off = status_attr_off or self.attr_off
        self.callback_kwargs = callback_kwargs or {}
        self.callback_kwargs = {**self.callback_kwargs, **{"button": self}}
        self.state = False
        self.callback_on_task = None
        self.callback_off_task = None

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
        attr = self.attr_on if self.state else self.attr_off

        try:
            self.win.addstr(self.y, self.x, f"{char}={label}", attr)
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
            if self.callback_on:
                if asyncio.iscoroutinefunction(self.callback_on):
                    self.callback_on_task: asyncio.Task = create_task(
                        self.callback_on(**self.callback_kwargs),
                        name="callback_on")
                    if self.done_callback_on:
                        self.callback_on_task.add_done_callback(
                            self.done_callback_on)
                else:
                    self.callback_on(**self.callback_kwargs)
        else:
            if self.callback_off:
                if asyncio.iscoroutinefunction(self.callback_off):
                    self.callback_off_task: asyncio.Task = create_task(
                        self.callback_off(**self.callback_kwargs),
                        name="callback_off")
                    if self.done_callback_off:
                        self.callback_off_task.add_done_callback(
                            self.done_callback_off)
                else:
                    self.callback_off(**self.callback_kwargs)
                
                if self.callback_on_task and not self.callback_on_task.done():
                    self.callback_on_task.remove_done_callback(
                        self.done_callback_on)
                    self.callback_on_task = None

    async def handle_char(self, key: int) -> None:
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
        if key in self.chars_int:
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

class Menubar:
    def __init__(self, stdscr: "_curses._CursesWindow",
        nlines: Optional[int] = 1,
        attr: Optional[int] = None,
        offset_x: Optional[int] = 0,
        status_bar_width: Optional[int] = 20,
        buttons: List[Button] = None) -> None:
        """
        Initialize the menubar.

        Parameters
        ----------
        stdscr : _curses._CursesWindow
            The curses window that the menubar will be drawn on.
        nlines : int, optional
            The number of lines the menubar should use. Defaults to 1.
        attr : int, optional
            The curses attribute to use when drawing the menubar. Defaults to
            curses.A_REVERSE.
        offset_x : int, optional
            The x offset of the menubar. Defaults to 0.
        status_bar_width : int, optional
            The width of the status bar. Defaults to 20.
        buttons : List[Button], optional
            A list of Button objects that should be used to populate the
            menubar. Defaults to an empty list.
        """
        self.stdscr = stdscr
        self.nlines = nlines
        self.attr = attr or curses.color_pair(0)|curses.A_REVERSE
        self.buttons = buttons if buttons else []
        self.offset_x = offset_x
        self.status_bar_width = status_bar_width
        maxy, ncols = stdscr.getmaxyx()
        begin_y, begin_x = maxy - nlines, offset_x
        self.win = stdscr.subwin(nlines, ncols, begin_y, begin_x)
        self.maxy, self.maxx = self.win.getmaxyx()

    def draw(self) -> None:
        """
        Draw the menubar.

        Returns
        -------
        None
        """
        for y in range(0, self.maxy):
            try:
                self.win.addstr(y, 0, " " * (self.maxx), self.attr)
            except _curses.error:
                pass
        
        self.draw_status_bar()
        self.draw_buttons()
        self.win.refresh()

    def draw_status_bar(self, offset: int = 0) -> None:
        """
        Draw the status bar for all buttons in the menubar.

        Parameters
        ----------
        offset : int, optional
            The x offset for the status bar. Defaults to 0.

        Returns
        -------
        None
        """
        labels, attrs = zip(*[b.status() for b in self.buttons])
        labels, attrs = list(labels), list(attrs)
        visible_labels = [l for l in labels if l]
        nseparators = max(0, len(visible_labels) - 1)
        width = (self.status_bar_width - nseparators) // len(visible_labels)
        noffset = offset
        
        for label, attr in zip(labels, attrs):
            if label:
                if nseparators and noffset > offset:
                    self.win.addstr(0, noffset, "│", self.attr)
                    noffset += 1
                label = f"{label[:width]:^{width}}"
                self.win.addstr(0, noffset, label, attr)
                noffset += len(label)

    def draw_buttons(self) -> None:
        """
        Draw all buttons in the list.

        Returns
        -------
        None
        """
        for button in self.buttons:
            button.draw()

    async def handle_char(self, char: int) -> None:
        """
        Process a keypress for one of the buttons in the menubar.

        Parameters
        ----------
        char : int
            The character code of the key that was pressed.

        Returns
        -------
        None
        """
        chars_list = [b.chars_int for b in self.buttons]
        for idx, chars in enumerate(chars_list):
            if char in chars:
                await self.buttons[idx].handle_char(char)
                self.draw()
                break

async def discovery_on_callback(progressbar, *args, **kwargs):
    try:
        for i in range(1, progressbar.width):
            progressbar.draw(i / 20)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        return

async def discovery_off_callback(progressbar, *args, **kwargs):
    for task in asyncio.Task.all_tasks():
        if hasattr(task, "name") and task.name == "callback_on":
            task.cancel()
            await task
            break
    progressbar.erase()

class Workspace:
    def __init__(self, stdscr, column_attrs, *,
        column_names=None,
        column_widths=None,
        menubar=None,
        name=None,
        storage=None,
        attr=None,
        offset_y=2,
        offset_x=0,
        title_width=3,
        colors_pairs=None,
    ):
        self.stdscr = stdscr
        self.column_attrs = column_attrs
        self.column_names = column_names or column_attrs
        self.column_widths = column_widths or [len(x) for x in column_attrs]
        self.menubar = menubar
        self.name = name
        self.storage = storage or []
        self.attr = attr or curses.color_pair(0)
        self.offset_y = offset_y
        self.offset_x = offset_x
        self.colors_pairs = colors_pairs
        self.title_width = title_width
        self.posy = 0
        self.posx = 0
        self.row_pos = 0
        self.maxy = self.stdscr.getmaxyx()[0] - offset_y
        self.maxx = sum(x + 1 for x in self.column_widths) + 1
        self.titlewin = stdscr.subwin(title_width, self.maxx,
            offset_y, offset_x)
        self.bodywin = self.stdscr.subwin(
            self.maxy - title_width, self.maxx, offset_y + title_width,
            offset_x)

    def draw(self):
        self.draw_titlewin()
        self.draw_bodywin()
        self.draw_menubar()

    def draw_titlewin(self):
        self.titlewin.attron(self.attr)
        self.titlewin.box()
        self.titlewin.attroff(self.attr)
        offset = 0
        for idx, (cname, cwidth) in enumerate(zip(self.column_names,
                                                self.column_widths)):
            cname = f"│{cname:^{cwidth}}"
            xpos = self.offset_x if idx == 0 else offset
            offset = xpos + len(cname)
            self.titlewin.addstr(1, xpos, cname, self.attr)
            if idx > 0:
                self.titlewin.addstr(0, xpos, "┬", self.attr)
                self.titlewin.addstr(2, xpos, "┼", self.attr)
        try:
            self.titlewin.addstr(2, self.offset_x, "├", self.attr)
            self.titlewin.addstr(2, self.maxx - 1, "┤", self.attr)
        except curses.error:
            pass
        self.titlewin.refresh()

    def draw_bodywin(self):
        start_row = self.row_pos
        end_row = min(self.row_pos + (self.maxy - 3), len(self.storage))
        for ridx, row in enumerate(self.storage[start_row:end_row]):
            offset = 0
            try:
                for cidx, (attr, width) in enumerate(zip(self.column_attrs,
                                                         self.column_widths)):
                    xpos = self.offset_x if cidx == 0 else offset
                    
                    if hasattr(row, attr):
                        item = getattr(row, attr)
                    else:
                        item = row.get(attr)
                    item = f"│{str(item)[-width:]:>{width}}"
                    
                    if hasattr(item, "attr"):
                        cpair = getattr(row, "attr")
                    elif hasattr(item, "get"):
                        cpair = item.get("attr", self.attr)
                    else:
                        cpair = self.attr
                    if ridx == self.posy:
                        cpair = cpair|curses.A_REVERSE
                    
                    offset = xpos + len(item)
                    self.bodywin.addstr(ridx, xpos, item, cpair)
                self.bodywin.addstr(ridx, xpos + len(item), "│", cpair)
            except curses.error:
                pass
        self.bodywin.refresh()

    def draw_menubar(self):
        if self.menubar:
            self.menubar.draw()

    async def handle_char(self, char):
        if char == curses.KEY_DOWN:
            self.row_pos = self.row_pos + 1 if self.posy == (self.maxy - (self.title_width + 1)) and self.row_pos + 1 <= len(self.storage) - (self.maxy - self.title_width) else self.row_pos
            self.posy = self.posy + 1 if self.posy < (self.maxy - (self.title_width + 1)) and len(self.storage) - 1 > self.posy else self.posy
        elif char == curses.KEY_UP:
            self.row_pos = self.row_pos - 1 if self.row_pos > 0 and self.posy == 0 else self.row_pos
            self.posy =  self.posy - 1 if self.posy > 0 else self.posy
        elif char == curses.KEY_HOME:
            self.row_pos = 0
            self.posy = 0
        elif char == curses.KEY_END:
            self.posy = min(self.maxy - (self.title_width + 1), len(self.storage) - 1)
            self.row_pos = max(0, len(self.storage) - (self.maxy - self.title_width))
        elif char == curses.KEY_NPAGE:
            self.row_pos = min(self.row_pos + (self.maxy - self.title_width), max(0, len(self.storage) - (self.maxy - self.title_width)))
            self.posy = 0 if self.row_pos + (self.maxy - self.title_width) <= len(self.storage) - 1 else min(len(self.storage) - 1, (self.maxy - self.title_width) - 1)
        elif char == curses.KEY_PPAGE:
            self.posy = 0
            self.row_pos = max(self.row_pos - (self.maxy - self.title_width), 0)
        else:
            await self.menubar.handle_char(char)
        self.draw_bodywin()

# Example usage within an asynchronous curses application:
async def main(stdscr):
    # Initialize curses settings: hide the cursor and set non-blocking input.
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    stdscr.clear()
    stdscr.nodelay(True)

    menubar = Menubar(stdscr)
    # Define separate callbacks for the "on" and "off" states.
    button_d = Button(ord("d"), ord("D"),
        win=menubar.win,
        y=0, x=25,
        char_alt="🄳 ",
        label_on="Discovery Stop ",
        label_off="Discovery Start",
        callback_on=discovery_on_callback,
        callback_off=discovery_off_callback,
        done_callback_on=functools.partial(ungetch_done_callback, ord("d")),
        status_label="Discovery",
        status_attr_on=curses.color_pair(42)|curses.A_REVERSE,
        status_attr_off=curses.color_pair(2)|curses.A_REVERSE,
        stdscr=stdscr,
        progressbar=ProgressBar(stdscr)
    )

    button_c = Button(ord("c"), ord("C"),
        win=menubar.win,
        y=0, x=45,
        char_alt="🄲 ",
        label_on="Clear",
    )

    menubar.buttons = [button_d, button_c]

    workspace = Workspace(
            stdscr,
            column_attrs = [
                "gw_number", "model", "firmware", "hw",
                "host", "slamon", "rtp_stat", "faults",
            ],
            column_names = [
                "BGW", "Model", "FW", "HW", "LAN IP",
                "SLAMon IP", "RTP-Stat", "Faults",
            ],
            column_widths = [3, 5, 8, 2, 15, 15, 8, 6],
            menubar = menubar,
            storage = GATEWAYS,
            name = "Systems",
        )

    workspace.draw()
    stdscr.refresh()

    # Main event loop: process key events and update the button accordingly.
    while True:
        try:
            key = stdscr.getch()
            if key != -1:
                if key == ord('q'):
                    break
                await workspace.handle_char(key)
                workspace.draw()
                stdscr.refresh()
            await asyncio.sleep(0.05)
        except KeyboardInterrupt:
            break

def run_curses_app():
    asyncio_run(curses.wrapper(main))

if __name__ == '__main__':
    run_curses_app()
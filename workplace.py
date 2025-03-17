import curses

def init_attrs():
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    return {
        "RED": curses.attr(2),
        "RED_LIGHT": curses.attr(197),
        "GREEN": curses.attr(42),
        "GREEN_LIGHT": curses.attr(156),
        "YELLOW": curses.attr(12),
        "YELLOW_LIGHT": curses.attr(230),
        "BLUE": curses.attr(13),
        "BLUE_LIGHT": curses.attr(34),
        "MAGENTA": curses.attr(6),
        "MAGENTA_LIGHT": curses.attr(14),
        "CYAN": curses.attr(46),
        "CYAN_LIGHT": curses.attr(15),
        "GREY": curses.attr(246),
        "GREY_LIGHT": curses.attr(252),
        "ORANGE": curses.attr(203),
        "ORANGE_LIGHT": curses.attr(209),
        "PINK": curses.attr(220),
        "PINK_LIGHT": curses.attr(226),
        "PURPLE": curses.attr(135),
        "PURPLE_LIGHT": curses.attr(148),
    }


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
        self.attr = attr or curses.attr(0)
        self.offset_y = offset_y
        self.offset_x = offset_x
        self.colors_pairs = colors_pairs or init_attrs()
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

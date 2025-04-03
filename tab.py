class Tab:
    def __init__(self,
        stdscr,
        tab_names,
        nlines=2,
        yoffset=0,
        xoffset=0,
        color_scheme=None,
    ):
        self.stdscr = stdscr
        self.tab_names = tab_names
        self.tab_width = max(len(x) for x in self.tab_names)
        self.yoffset = yoffset
        self.xoffset = xoffset
        self.color_scheme = color_scheme or {"normal": 0}
        self.active_tab_idx = 0
        self.maxy = nlines
        self.maxx = self.stdscr.getmaxyx()[1]
        self.win = self.stdscr.subwin(nlines, self.maxx, yoffset, xoffset)

    def draw(self):
        for idx, tab_name in enumerate(self.tab_names):
            self.draw_tab(tab_name, self.yoffset, self.xoffset + idx * (self.tab_width + 2), idx == self.active_tab_idx)
        self.win.refresh()

    def draw_tab(self, tab_name, ypos, xpos, active):
        attr = self.color_scheme["normal"]
        text = tab_name.center(self.tab_width)
        border = " " + "─" * self.tab_width + " "
        if active:
            attr = self.color_scheme.get("standout", 0)
            border = "╭" + "─" * self.tab_width + "╮"
        self.win.addstr(ypos, xpos, border, attr)
        self.win.addstr(ypos + 1, xpos + 1, text, attr)
        self.win.addstr(ypos + 2, xpos, border, attr)

    async def handle_char(self, char):
        if chr(char) == "\t":
            if self.active_tab_idx < len(self.tab_names) - 1: 
                self.active_tab_idx += 1
            else:
                self.active_tab_idx = 0
            self.draw()

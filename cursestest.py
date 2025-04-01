import curses

COLOR_SCHEMES = {
    'default': {
        'normal': 0,        # white
        'bold': 2097152,    # white bold
        'dim': 1048576,     # white dim
        'standout': 65536,  # white standout
    },

    'blue': {
        'normal': 31744,    # blue
        'bold': 2128896,    # blue bold
        'dim': 1080320,     # blue dim
        'standout': 97280,  # blue standout
    },

    'green': {
        'normal': 12288,    # green
        'bold': 2109440,    # green bold
        'dim': 1060864,     # green dim
        'standout': 77824,  # green standout
    },

    'orange': {
        'normal': 53504,    # orange
        'bold': 2150656,    # orange bold
        'dim': 1102080,     # orange dim
        'standout': 119040, # orange standout
    }
}

def main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    colors = COLOR_SCHEMES['orange']

    stdscr.addstr(1, 1, "Hello, World! NORMAL", colors['normal'])
    stdscr.addstr(3, 1, "Hello, World! BOLD", colors['bold'])
    stdscr.addstr(5, 1, "Hello, World! DIM", colors['dim'])
    stdscr.addstr(7, 1, "Hello, World! STANDOUT", colors['standout'])
    stdscr.refresh()
    stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)

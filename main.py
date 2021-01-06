import asyncio
import curses
import itertools
import random
import time

from curses_tools import draw_frame, get_frame_size, read_controls

TIC_TIMEOUT = 0.1
MAX_STARS = 190
MARGIN = 1
DEFAULT_STEP = 15

FRAME_FILE_PATHS = [
  'frames/rocket_frame_1.txt',
  'frames/rocket_frame_2.txt'
]


async def blink(canvas, row, column, offset, symbol='*'):
    while True:
        for _ in range(offset):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas,
               start_row,
               start_column,
               rows_speed=-0.3,
               columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    max_row, max_column = get_max_window_size(canvas)

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def twice_cycle(iterable):
    for item in itertools.cycle(iterable):
        for _ in range(2):
            yield item


async def animate_spaceship(canvas, row, column, frames, step):
    frame_rows, frame_columns = get_frame_size(frames[0])
    max_row, max_column = get_max_window_size(canvas)

    max_y = max_row - frame_rows
    max_x = max_column - frame_columns

    for frame in twice_cycle(frames):
        rows_direction, columns_direction, _ = read_controls(
            canvas)

        rows_step = row + rows_direction * step
        columns_step = column + columns_direction * step

        row = max(1, min(rows_step, max_y))
        column = max(1, min(columns_step, max_x))

        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


def read_frame(path):
    with open(path, 'r') as frame_file:
        return frame_file.read()


def get_symbol():
    return random.choice(['+', '*', '.', ':'])


def get_max_window_size(canvas):
    # getmaxyx() return height and width of the window, bun less by one
    rows, columns = canvas.getmaxyx()
    return rows - 1, columns - 1


def get_window_center(canvas):
    """Return a tuple (height, width) of the halfs height and width of the window."""
    height, width = canvas.getmaxyx()
    return height // 2, width // 2


def get_random_star_params(canvas):
    """Return a tuple (y, x, z) of the row, column, offset."""
    rows, columns = get_max_window_size(canvas)
    return (
      random.randint(1, rows - MARGIN),
      random.randint(1, columns - MARGIN),
      random.randint(10, 20)
    )


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    half_height, half_width = get_window_center(canvas)

    frames = [read_frame(path) for path in FRAME_FILE_PATHS]

    coroutines = []

    for _ in range(MAX_STARS):
        row, column, offset = get_random_star_params(canvas)
        coroutines.append(
          blink(canvas, row, column, offset, get_symbol())
        )

    gun_shot = fire(canvas, half_height - 1, half_width + 2)
    coroutines.append(gun_shot)

    spaceship = animate_spaceship(
      canvas, half_height, half_width, frames, DEFAULT_STEP
    )
    coroutines.append(spaceship)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)

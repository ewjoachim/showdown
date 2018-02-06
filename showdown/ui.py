import curses
import queue
import time
import threading

from showdown import game


DRAWINGS = dict(zip(
    "shoot dodge reload stand bang click bullet eye eye-dead initial".split(),
    (s.strip() for s in r"""
__M__
(  o)
 (i)_;=
 u u

__M__
(  o) /===\
 (i)  |===|
 u u  \===/

 __M__
.(o  )
=; (i)
   u u

__M__
(  o)
 (i)
 u u

!BANG!

.click.

-

o

x

i
""".split("\n\n"))))

CHARACTER_SIZE = max(len(l)
                     for character in "shoot dodge reload stand".split()
                     for l in DRAWINGS[character].splitlines())

DRAWINGS["clocks"] = [s.strip() for s in r"""
o-----o
|  |  |
|     |
o-----o

o-----o
|   / |
|     |
o-----o

o-----o
|   _ |
|     |
o-----o

o-----o
|     |
|   \ |
o-----o

o-----o
|     |
|  |  |
o-----o

o-----o
|     |
| /   |
o-----o

o-----o
| _   |
|     |
o-----o

o-----o
| \   |
|     |
o-----o
""".split("\n\n")]

REFRESH_TIME = 0.02
TURN_DURATION = 1.


def ui(states_queue):
    curses.wrapper(loop, states_queue)


def loop(window, states_queue):
    window.keypad(False)
    window.leaveok(True)

    curses.curs_set(0)
    window.nodelay(True)

    state = states_queue.get()
    while draw_state(state=state, window=window):
        state = states_queue.get()


def draw_state(state, window):
    begin = time.time()
    turn_step = 0.
    while turn_step < 1.:
        draw_step(turn_step, state, window)
        time.sleep(REFRESH_TIME)
        turn_step = (time.time() - begin) / TURN_DURATION
    if "winner_key" in state:
        draw_step(0, state, window, end=True)
        time.sleep(3)
        return False
    else:
        return True


def mirror_character(drawing_lines):
    tmp_char = "@"
    result = []
    for line in drawing_lines:
        rev = "".join(reversed(line))

        rev = rev.replace("(", tmp_char)
        rev = rev.replace(")", "(")
        rev = rev.replace(tmp_char, ")")

        rev = rev.replace("/", tmp_char)
        rev = rev.replace("\\", "/")
        rev = rev.replace(tmp_char, "\\")

        rev = " " * (CHARACTER_SIZE - len(rev)) + rev
        result.append(rev)
    return result


def draw(window, x, y, drawing):
    for i, line in enumerate(drawing):
        spaces = len(line) - len(line.lstrip())
        window.addstr(y + i, x + spaces, line.lstrip())


def draw_step(turn_step, state, window, end=False):
    window.erase()
    total_height, total_width = window.getmaxyx()

    # Clock
    clock = DRAWINGS["clocks"][int(turn_step * len(DRAWINGS["clocks"]))]
    clock_lines = clock.splitlines()
    clock_x = (total_width - len(clock_lines[0])) // 2
    clock_y = 2

    draw(window, clock_x, clock_y, clock_lines)

    # Characters
    command_a = state["a"]["command"]
    command_b = state["b"]["command"]

    drawing_a = DRAWINGS[command_a].replace(
        DRAWINGS["initial"], state["a"]["name"][0])
    drawing_b = DRAWINGS[command_b].replace(
        DRAWINGS["initial"], state["b"]["name"][0])

    if end:
        if state["winner_key"] == "a":
            drawing_b = drawing_b.replace(
                DRAWINGS["eye"], DRAWINGS["eye-dead"])
        else:
            drawing_a = drawing_a.replace(
                DRAWINGS["eye"], DRAWINGS["eye-dead"])

    drawing_lines_a = drawing_a.splitlines()
    drawing_lines_b = mirror_character(drawing_b.splitlines())

    distance = 40
    a_x = ((total_width - distance) // 2)  - CHARACTER_SIZE
    a_y = total_height - 5 - len(drawing_lines_b)

    draw(window, a_x, a_y, drawing_lines_a)

    b_x = int((total_width + distance) // 2)
    b_y = a_y

    draw(window, b_x, b_y, drawing_lines_b)

    description = state["description"]
    description_x = (total_width - len(description)) // 2
    description_y = total_height - 2

    draw(window, description_x, description_y, [description])

    shoot_a = state["a"]["command"] == "shoot"
    shoot_b = state["b"]["command"] == "shoot"

    if not end:
        bullet_y = a_y + 2

        if shoot_a:
            bullet_ax = a_x + CHARACTER_SIZE + int(distance * turn_step)
            if not (turn_step > 0.5 and shoot_b):
                draw(window, bullet_ax, bullet_y, [DRAWINGS["bullet"]])

        if shoot_b:
            bullet_ax = b_x - int(distance * turn_step)
            if not (turn_step > 0.5 and shoot_a):
                draw(window, bullet_ax, bullet_y, [DRAWINGS["bullet"]])

    window.refresh()
    curses.update_lines_cols()

def main():
    state_queue = queue.Queue()

    thread = threading.Thread(
            target=ui,
            args=(state_queue,))

    state = {}
    try:
        state = game.setup()
        thread.start()
        while True:
            cont = game.loop(state, state_queue)
            if not cont:
                game.finish(state, state_queue)
            game.write_to_ui_queue(state, state_queue)
            if not cont:
                break
    finally:
        game.clean(state)

    thread.join()

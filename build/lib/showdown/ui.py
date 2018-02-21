import curses
import queue
import time
import threading
import sys

from showdown import game


DRAWINGS = dict(
    e.split("\n", 1)
    for e in r"""
shoot
__M__
(  o)
 (i)_;=
 u u

dodge
__M__
(  o) /===\
 (i)  |===|
 u u  \===/

reload
 __M__
.(o  )
=; (i)
   u u

stand
__M__
(  o)
 (i)
 u u

bang
!BANG!

click
.click.

bullet
-

eye
o

eye-dead
x

initial
i

stacked-bullet
|
""".strip().split("\n\n"))

DRAWINGS["shoot_no_bullet"] = DRAWINGS["shoot"]

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
TURN_TIME = 1.
ENDING_TIME = 3.

DISTANCE = 40

def ui(states_queue):
    curses.wrapper(loop, states_queue)


def loop(window, states_queue):
    """
    Main loop. Will draw every state decribed in
    the states_queue.
    """
    window.keypad(False)
    window.leaveok(True)

    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    window.nodelay(True)

    for __ in draw_states(states_queue=states_queue,
                          window=window):
        window.refresh()
        curses.update_lines_cols()
        time.sleep(REFRESH_TIME)
        window.erase()
        if get_keypress(window) == "q":
            sys.exit(0)


def draw_states(states_queue, window):
    while True:
        state = states_queue.get()
        for __ in draw_state(state=state, window=window):
            yield

        if "winner_key" in state:
            begin = time.time()
            while time.time() - begin < ENDING_TIME:
                draw_step(window, 0, state, end=True)
                yield
            break


def draw_state(state, window):
    """
    Generator (one may say coroutine...)
    that at each call draws one frame,
    and in globality draws a whole state
    """
    begin = time.time()
    turn_step = 0.
    while turn_step < 1.:
        draw_step(window, turn_step, state)
        yield
        turn_step = (time.time() - begin) / TURN_TIME

def get_keypress(window):
    try:
        keypress = window.getkey()
    except curses.error:
        keypress = None

    # it seems OSX has a problem with the escape codes.
    if keypress == "\x1b":
        keypress = {
            "[D": curses.KEY_LEFT, "[C": curses.KEY_RIGHT,
            "[B": curses.KEY_DOWN, "[A": curses.KEY_UP,
        }.get(window.getkey() + window.getkey(), None)

    return keypress


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

def draw_box(window, x1, y1, x2, y2,
             horizontal="-", vertical="|", corner="+"):  # pylint: disable=unbalanced-tuple-unpacking
    draw(window, x1 + 1, y1, [horizontal * (x2 - x1 - 1)])
    draw(window, x1 + 1, y2, [horizontal * (x2 - x1 - 1)])
    draw(window, x1, y1 + 1, [vertical] * (y2 - y1 - 1))
    draw(window, x2, y1 + 1, [vertical] * (y2 - y1 - 1))
    draw(window, x1, y1, [corner])
    draw(window, x1, y2, [corner])
    draw(window, x2, y1, [corner])
    draw(window, x2, y2, [corner])

def draw_step(window, turn_step, state, end=False):
    total_height, total_width = window.getmaxyx()

    a_x = ((total_width - DISTANCE) // 2)  - CHARACTER_SIZE
    b_x = int((total_width + DISTANCE) // 2)

    characters_y = total_height - 5 - DRAWINGS["shoot"].count("\n")

    command_a = state["a"]["command"]
    command_b = state["b"]["command"]

    draw_clock(window=window,
               turn_step=turn_step,
               total_width=total_width)
    draw_characters(window=window,
                    state=state,
                    end=end,
                    command_a=command_a,
                    command_b=command_b,
                    a_x=a_x,
                    b_x=b_x,
                    characters_y=characters_y)
    draw_description(window=window,
                     state=state,
                     total_width=total_width,
                     total_height=total_height)
    draw_bullets(window=window,
                 turn_step=turn_step,
                 command_a=command_a,
                 command_b=command_b,
                 a_x=a_x,
                 b_x=b_x,
                 characters_y=characters_y,
                 end=end)
    draw_noises(window=window,
                turn_step=turn_step,
                command_a=command_a,
                command_b=command_b,
                a_x=a_x,
                b_x=b_x,
                characters_y=characters_y,
                end=end)
    draw_boxes(window=window,
               state=state,
               total_width=total_width)
    draw_turns(window=window,
               state=state,
               total_width=total_width)


def draw_clock(window, turn_step, total_width):
    # Clock
    clock = DRAWINGS["clocks"][int(turn_step * len(DRAWINGS["clocks"]))]
    clock_lines = clock.splitlines()
    clock_x = (total_width - len(clock_lines[0])) // 2
    clock_y = 2

    draw(window=window, x=clock_x, y=clock_y, drawing=clock_lines)


def draw_characters(window, state, end, command_a, command_b,
                    a_x, b_x, characters_y):
    # Characters

    drawing_a = DRAWINGS[command_a].replace(
        DRAWINGS["initial"], state["a"]["name"][0])
    drawing_b = DRAWINGS[command_b].replace(
        DRAWINGS["initial"], state["b"]["name"][0])

    # Eyes
    if end:
        if state["winner_key"] == "a":
            drawing_b = drawing_b.replace(
                DRAWINGS["eye"], DRAWINGS["eye-dead"])
        else:
            drawing_a = drawing_a.replace(
                DRAWINGS["eye"], DRAWINGS["eye-dead"])

    drawing_lines_a = drawing_a.splitlines()
    drawing_lines_b = mirror_character(drawing_b.splitlines())

    draw(window=window,
         x=a_x,
         y=characters_y,
         drawing=drawing_lines_a)

    draw(window=window,
         x=b_x,
         y=characters_y,
         drawing=drawing_lines_b)


def draw_description(window, state, total_width, total_height):
    # Description
    description = state["description"]
    description_x = (total_width - len(description)) // 2
    description_y = total_height - 2

    draw(window=window,
         x=description_x,
         y=description_y,
         drawing=[description])


def draw_bullets(window, turn_step, command_a, command_b,
                 a_x, b_x, characters_y, end):
    shoot_a = command_a == "shoot"
    shoot_b = command_b == "shoot"

    # Flying bullets
    if not end:
        bullet_y = characters_y + 2

        if shoot_a:
            bullet_ax = a_x + CHARACTER_SIZE + int(DISTANCE * turn_step)
            if not (turn_step > 0.5 and shoot_b):
                draw(window=window,
                     x=bullet_ax, y=bullet_y,
                     drawing=[DRAWINGS["bullet"]])

        if shoot_b:
            bullet_ax = b_x - int(DISTANCE * turn_step)

            if not (turn_step > 0.5 and shoot_a):
                draw(window=window,
                     x=bullet_ax, y=bullet_y,
                     drawing=[DRAWINGS["bullet"]])


def draw_noises(window, turn_step, command_a, command_b,
                a_x, b_x, characters_y, end):
    # Noises
    noisy_commands = "shoot shoot_no_bullet reload".split()
    if not end and turn_step < 0.5:
        if command_a in noisy_commands:
            if command_a == "shoot":
                draw(window=window,
                     x=a_x + CHARACTER_SIZE - 2, y=characters_y + 1,
                     drawing=[DRAWINGS["bang"]])
            elif command_a == "shoot_no_bullet":
                draw(window=window,
                     x=a_x + CHARACTER_SIZE - 2, y=characters_y + 1,
                     drawing=[DRAWINGS["click"]])
            else:  # reload
                draw(window=window,
                     x=a_x +  - 2 - len(DRAWINGS["click"]), y=characters_y + 1,
                     drawing=[DRAWINGS["click"]])

        if command_b in noisy_commands:
            if command_b == "shoot":
                draw(window=window,
                     x=b_x + 2 - len(DRAWINGS["bang"]), y=characters_y + 1,
                     drawing=[DRAWINGS["bang"]])
            elif command_b == "shoot_no_bullet":
                draw(window=window,
                     x=b_x + 2 - len(DRAWINGS["click"]), y=characters_y + 1,
                     drawing=[DRAWINGS["click"]])
            else:  # reload
                draw(window=window,
                     x=b_x + CHARACTER_SIZE + 2, y=characters_y + 1,
                     drawing=[DRAWINGS["click"]])


def draw_boxes(window, state, total_width):
    # Boxes with info at the top
    draw_box(window=window,
             x1=total_width // 6, y1=2,
             x2=total_width // 2 - 6, y2=7)
    draw_box(window=window,
             x1=total_width // 2 + 4, y1=2,
             x2=(5 * total_width) // 6, y2=7)

    # Names in the boxes
    draw(window=window,
         x=total_width // 2 - 8 - len(state["a"]["name"]),
         y=4,
         drawing=[state["a"]["name"]])

    draw(window=window,
         x=total_width // 2 + 6,
         y=4,
         drawing=[state["b"]["name"]])

    # Bullets left
    draw(window=window,
         x=total_width // 2 - 8 - state["a"]["bullets"],
         y=5,
         drawing=[DRAWINGS["stacked-bullet"] * state["a"]["bullets"]])

    draw(window=window,
         x=total_width // 2 + 6,
         y=5,
         drawing=[DRAWINGS["stacked-bullet"] * state["b"]["bullets"]])


def draw_turns(window, state, total_width):
    # Turns
    draw(window=window,
         x=total_width // 2 - 2,
         y=6,
         drawing=[f"{state['num_turn']:03}"])

def write_to_ui_queue(state, state_queue):
    a = state["a"]
    b = state["b"]
    if "description" in state:
        description = state["description"]
    else:
        description = f"{a.description} {b.description}"

    new_state = {
        "num_turn": state["num_turn"],
        "description": description,
        "a": {
            "name": a.name,
            "bullets": a.num_bullets,
            "command": a.latest_command.value,
            "num_dodges": a.num_dodges
        },
        "b": {
            "name": b.name,
            "bullets": b.num_bullets,
            "command": b.latest_command.value,
            "num_dodges": b.num_dodges
        },
    }

    if "winner_key" in state:
        new_state["winner_key"] = state["winner_key"]

    state_queue.put(new_state)


def run_game_ui(call_args_a, call_args_b):
    state_queue = queue.Queue()

    thread = threading.Thread(
            target=ui,
            args=(state_queue,))

    state = {}
    try:
        state = game.setup(call_args_a, call_args_b)
        thread.start()
        while True:
            cont = game.loop(state)
            if not cont:
                game.finish(state)
            write_to_ui_queue(state, state_queue)
            if not cont:
                break
    finally:
        game.clean(state)

    thread.join()

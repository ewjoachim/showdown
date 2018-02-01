#!/usr/bin/env python
import curses
import enum
import errno
import io
import logging
import os
import sys

import sh
import time

logger = logging.getLogger(__file__)


DRAWINGS = dict(zip(
    "shoot dodge reload stand bang click bullet eye eye-dead initial".split(),
    (s.strip() for s in r"""
__M__
(  o)
 (i)_;=
 u u

__M__  ___
(  o) / | \
 (i)  | | |
 u u  \_|_/

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

DRAWINGS["clocks"] = [s.strip() for s in r"""
 ___
/ | \
\   /
 ¯¯¯

 ___
/  /\
\   /
 ¯¯¯

 ___
/  _\
\   /
 ¯¯¯

 ___
/   \
\  \/
 ¯¯¯

 ___
/   \
\ | /
 ¯¯¯

 ___
/   \
\/  /
 ¯¯¯

 ___
/_  \
\   /
 ¯¯¯

 ___
/\  \
\   /
 ¯¯¯
""".split("\n\n")]

REFRESH_TIME = 0.02
TURN_TIME = 0.5
STARTUP_TIME = 10
TURN_MAX_WAIT_TIME = 3
TOTAL_TURNS = 15
MAX_BULLETS = 6

class Commands(enum.Enum):
    STAND = "stand"
    SHOOT = "shoot"
    DODGE = "dodge"
    RELOAD = "reload"
    SHOOT_NO_BULLET = "shoot_no_bullet"
    GAME_OVER = "game_over"

def usage():
    print(f"Usage: {sys.argv[0]} program_a args -- program_b args")
    sys.exit(1)

def main():
    state = setup()
    while loop(state):
        pass
    finish(state)

def setup():
    state = {
        "turn": 0,
    }

    args = sys.argv[1:]
    try:
        index = args.index("--")
    except IndexError:
        usage()

    program_call_a = args[:index]
    program_call_b = args[index + 1:]

    state["a"] = setup_one(program_call_a)
    state["b"] = setup_one(program_call_b)
    setup_logging(state["a"]["name"], state["b"]["name"])
    if any("exited" in state[key] for key in "ab"):
        sys.exit(1)
    return state

def setup_one(program_call):
    state = {"program_call": program_call}

    try:
        state["stdin"] = io.StringIO()
        state["program"] = sh.Command(program_call[0])(
            *program_call[1:], _iter_noblock=True,
            _bg_exc=False, _in=state["stdin"])
    except sh.CommandNotFound:
        state["exited"] = True
        print(f"Command '{program_call[0]}' not found")
        return state

    begin = time.time()
    try:
        for contestant in state["program"]:
            if contestant != errno.EWOULDBLOCK:
                break

            if time.time() - begin > STARTUP_TIME:
                state["exited"] = True
                print(f"{' '.join(program_call)} took more than {STARTUP_TIME}"
                      " seconds to output its name")
                return state

            time.sleep(REFRESH_TIME)

        else:
            state["exited"] = True
            print(f"{' '.join(program_call)} exited before it gave its name")
            return state

    except sh.ErrorReturnCode as exc:
        state["exited"] = True
        print(f"{' '.join(program_call)} crashed before it gave its name")
        print(f"exit code: {exc.exit_code}")
        print(f"stdout: {exc.stdout}")
        print(f"stderr: {exc.stderr}")

        return state

    contestant = contestant.strip()

    state.update({
        "name": contestant,
        "bullets": 1,
        "num_dodges": 0,

    })
    print(f"Contestant: {contestant}")

    return state

def setup_logging(name_a, name_b):
    hdlr = logging.FileHandler(f"{name_a}-vs-{name_b}.log")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    logger.info(f"Starting new showdown: {name_a} vs {name_b}")

def loop(state):
    logger.info(f"Turn {state['turn']} begins")
    command_a = ask(state["a"])
    command_b = ask(state["b"])
    if Commands.GAME_OVER in (command_a, command_b):
        winner = list("ab")
        if command_a == Commands.GAME_OVER:
            print(f"{state['a']['name']} took more than {TURN_MAX_WAIT_TIME} to respond")
            winner.remove("a")
        if command_b == Commands.GAME_OVER:
            print(f"{state['b']['name']} took more than {TURN_MAX_WAIT_TIME} to respond")
            winner.remove("b")
        state["winner"] = next(iter(winner), None)
        return False

    print(f"{state['a']['name']}: {command_a.value}")
    print(f"{state['b']['name']}: {command_b.value}")
    unprotected = [Commands.SHOOT_NO_BULLET, Commands.RELOAD, Commands.STAND]
    if command_a == Commands.SHOOT and command_b in unprotected:
        state["winner"] = "a"
        logger.info(f"{state['a']['name']} shot {state['b']['name']}")
        return False
    if command_b == Commands.SHOOT and command_a in unprotected:
        state["winner"] = "b"
        logger.info(f"{state['b']['name']} shot {state['a']['name']}")
        return False

    # tell(state["a"], command_b)
    # tell(state["b"], command_a)

    state["turn"] += 1

    if state["turn"] >= TOTAL_TURNS:
        return False

    time.sleep(TURN_TIME)

    return True

def finish(state):
    print(state.get("winner"))

def ask(program):
    command = Commands.STAND
    name = program['name']
    try:
        command = next(program["program"])
        if command == errno.EWOULDBLOCK:
            logger.warning(f"{name} took too long")
            command = Commands.STAND

            # We still need the program to output its command
            # But we will ignore it.
            # If it takes more than 3 seconds, game over
            begin = time.time()
            for ignored in program["program"]:
                if ignored != errno.EWOULDBLOCK:
                    break
                if time.time() - begin > TURN_MAX_WAIT_TIME:
                    logger.error(f"{name} took more than {TURN_MAX_WAIT_TIME}s")
                    return Commands.GAME_OVER
            else:
                return Commands.GAME_OVER

        if command == errno.EAGAIN:
            logger.info(f"{name} had already crashed")
            return "stand"
    except StopIteration:
        logger.warning(f"{name} exited")
    except sh.ErrorReturnCode:
        logger.warning(f"{name} crashed")
        logger.warning(f"  exit code: {exc.exit_code}")
        logger.warning(f"  stdout: {exc.stdout}")
        logger.warning(f"  stderr: {exc.stderr}")

    try:
        command = Commands(command.strip())
    except ValueError:
        command = Commands.STAND

    if command not in [Commands.SHOOT, Commands.DODGE, Commands.RELOAD]:
        command = Commands.STAND

    if command == Commands.SHOOT:
        if program["bullets"]:
            program["bullets"] -= 1
        else:
            command = Commands.SHOOT_NO_BULLET

    if command == Commands.RELOAD:
        if program["bullets"] == MAX_BULLETS:
            logger.info(f"{program['name']} reloaded but already full")
        else:
            program["bullets"] += 1
    logger.info(f"{program['name']} command: {command}")
    return command

if __name__ == '__main__':
    main()

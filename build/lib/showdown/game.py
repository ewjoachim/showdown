#!/usr/bin/env python
import enum
import logging
import queue
import random
import subprocess
import sys
import time
import threading

logger = logging.getLogger(__file__)
logging.basicConfig(level="INFO")

STARTUP_TIME = 10
TURN_TIME = 1
TOTAL_TURNS = 100
MAX_BULLETS = 6


def run_game(call_args_a, call_args_b):
    state = {}
    try:
        state = setup(call_args_a, call_args_b)
        while loop(state):
            pass
        finish(state)
    finally:
        clean(state)

    return state


class Commands(enum.Enum):
    STAND = "stand"
    SHOOT = "shoot"
    DODGE = "dodge"
    RELOAD = "reload"
    SHOOT_NO_BULLET = "shoot_no_bullet"
    GAME_OVER = "game_over"


def enqueue_output(contestant):
    try:
        for line in iter(contestant.process.stdout.readline, b''):
            contestant.stdout_queue.put(line)
    except ValueError:
        pass

    contestant.process.stdout.close()


class Contestant:
    def __init__(self, call_args):
        self.call_args = call_args
        self.exited = False
        self.start()
        if self.exited:
            return
        self.contestant_name = self.read_name()
        self.num_bullets = 1
        self.num_dodges = 0
        self.latest_command = None

    @property
    def name(self):
        return getattr(self, "contestant_name",
                       " ".join(self.call_args))

    @property
    def description(self):
        if self.latest_command == Commands.SHOOT:
            return f"{self.name} shoots."
        elif self.latest_command == Commands.RELOAD:
            return f"{self.name} reloads."
        elif self.latest_command == Commands.DODGE:
            return f"{self.name} hides behind a barrel."
        elif self.latest_command == Commands.STAND:
            return f"{self.name} issues an invalid command."

    def start(self):
        try:
            self.process = subprocess.Popen(
                self.call_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0, close_fds=True)
        except PermissionError:
            self.exited = True
            print(f"Command '{self.name}': Permission denied")
            return
        except FileNotFoundError:
            self.exited = True
            print(f"Command '{self.name}' not found")
            return

        self.stdout_queue = queue.Queue(maxsize=1 + TOTAL_TURNS)
        self.stdout_thread = threading.Thread(
            target=enqueue_output,
            args=(self,))

        # thread dies with the program
        self.stdout_thread.daemon = True
        self.stdout_thread.start()

    def read_name(self):
        time.sleep(0.1)
        try:
            name = self.read(timeout=STARTUP_TIME)

        except EOFError:
            self.exited = True
            logger.warning(f"{self.name} exited")
            logger.warning(f"{self.name} stderr: {self.process.stderr.read()}")
            logger.warning(f"{self.name} exit code: {self.process.poll()}")

            return None
        except TimeoutError:
            self.exited = True
            logger.warning(
                f"{self.name} took more than {STARTUP_TIME}"
                f" seconds to output its name")
            self.kill()

            return None

        if not name:
            logger.warning(f"{self.name} didn't send its name")
            self.exited = True

        return name

    def read(self, timeout):
        if self.process.poll() is not None:
            raise EOFError
        try:
            line = self.stdout_queue.get(timeout=timeout)
            return line.decode("utf-8").strip()
        except queue.Empty:
            raise TimeoutError

    def is_alive(self):
        return not self.exited and self.process.poll() is None

    def ask(self):
        command = Commands.STAND

        # Check if process is alive
        if not self.is_alive():
            logger.warning(
                f"{self.name} has terminated ({self.process.returncode})")
            return Commands.STAND

        # Read stdout, with a hard timeout
        try:
            command = self.read(timeout=TURN_TIME)
        except EOFError:
            logger.warning(
                f"{self.name} has exited.")
            return Commands.STAND
        except TimeoutError:
            logger.warning(
                f"{self.name} took more than {TURN_TIME} "
                f"seconds to answer.")
            return Commands.GAME_OVER

        # Check for valid command
        try:
            command = Commands(command.strip())
        except ValueError:
            logger.warning(f"{self.name} issued invalid command {command}")

            return Commands.STAND

        if command not in [Commands.SHOOT, Commands.DODGE, Commands.RELOAD]:
            logger.warning(
                f"{self.name} issued invalid command {command.value}")

            return Commands.STAND

        # Update internal state for shoot
        if command == Commands.SHOOT:
            if self.num_bullets:
                self.num_bullets -= 1
            else:
                logger.info(f"{self.name} shot but without bullets")

                return Commands.SHOOT_NO_BULLET

        # Update internal state for reload
        if command == Commands.RELOAD:
            if self.num_bullets == MAX_BULLETS:
                logger.info(f"{self.name} reloaded but already full")
            else:
                self.num_bullets += 1

        # Update internal state for reload
        if command == Commands.DODGE:
            self.num_dodges += 1

        logger.info(f"{self.name} command: {command.value}")
        return command

    def tell(self, command):
        logger.debug(f"Telling {self.name} that opponent did: "
                     f"{command.value}")
        self.process.stdin.write(
            command.value.encode("utf-8") + b"\n")
        self.process.stdin.flush()


    def kill(self):
        logger.info(f"Killing {self.name}")
        self.exited = True
        try:
            self.process.stdin.close()
            self.process.stdout.close()
            self.process.stderr.close()
            self.process.kill()
        except AttributeError:
            pass
        logger.info(f"{self.name} exit code: {self.process.poll()}")


def setup(call_args_a, call_args_b):
    state = {
        "num_turn": 0,
    }

    state["a"] = Contestant(call_args_a)
    state["b"] = Contestant(call_args_b)
    if any(not state[key].is_alive() for key in "ab"):
        sys.exit(1)
    setup_logging(state["a"].name, state["b"].name)
    return state


def setup_logging(name_a, name_b):
    hdlr = logging.FileHandler(f"{name_a}-vs-{name_b}.log")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.info(f"Starting new showdown: {name_a} vs {name_b}")


def loop(state):
    state["num_turn"] += 1
    logger.info(f"Turn {state['num_turn']} begins")
    command_a = state["a"].ask()
    state["a"].latest_command = command_a
    command_b = state["b"].ask()
    state["b"].latest_command = command_b
    if Commands.GAME_OVER in (command_a, command_b):
        winners = list("ab")
        descriptions = []
        if command_a == Commands.GAME_OVER:
            winners.remove("a")
            descriptions.append(
                f"{state['a'].name} takes too long to answer.")
        if command_b == Commands.GAME_OVER:
            winners.remove("b")
            descriptions.append(
                f"{state['b'].name} takes too long to answer.")
        state["description"] = " ".join(descriptions)
        logger.info(state["description"])
        winner_key = next(iter(winners), None)
        if winner_key:
            state["winner_key"] = winner_key

        return False

    unprotected = [Commands.SHOOT_NO_BULLET, Commands.RELOAD, Commands.STAND]
    if command_a == Commands.SHOOT and command_b in unprotected:
        state["winner_key"] = "a"
        description = f"{state['a'].name} shoots {state['b'].name}"
        logger.info(description)
        state["description"] = description

        return False
    if command_b == Commands.SHOOT and command_a in unprotected:
        state["winner_key"] = "b"
        description = f"{state['b'].name} shoots {state['a'].name}"
        logger.info(description)
        state["description"] = description
        return False

    state["a"].tell(command_b)
    state["b"].tell(command_a)

    if state["num_turn"] >= TOTAL_TURNS:
        return False

    return True


def finish(state):
    winner_key = state.get('winner_key')

    if not winner_key:
        logger.info(f"{state['a'].name} dodged {state['a'].num_dodges} times")
        logger.info(f"{state['b'].name} dodged {state['b'].num_dodges} times")
        diff_dodges = state["a"].num_dodges - state["b"].num_dodges
        if diff_dodges:
            if diff_dodges < 0:
                winner_key = "a"
            elif diff_dodges > 0:
                winner_key = "b"
            description = ("{winner.name} wins by having dodged "
                           "{abs(diff_dodges)} times less")
        else:
            winner_key = random.choice("ab")
            description = "Toss a coin: {winner.name} wins."

        state['description'] = description.format(
            winner=state[winner_key])

    state['winner_key'] = winner_key
    logger.info(state['description'])


def clean(state):
    try:
        state["a"].kill()
    except KeyError:
        pass
    try:
        state["b"].kill()
    except KeyError:
        pass

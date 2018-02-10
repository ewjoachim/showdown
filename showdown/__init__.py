import os
import pathlib
import sys

from showdown.ui import run_game_ui
from showdown.bulk import run_game_bulk


def usage():
    print(f"Usage:")
    print(f"  Run the contest once with graphical output")
    print(f"       {sys.argv[0]} ui program_a args -vs- program_b args")
    print(f"  Run the contest num times and print results")
    print(f"       {sys.argv[0]} bulk {{num}} program_a args -vs- program_b args")
    print(f"  List example implementations")
    print(f"       {sys.argv[0]} example -l")
    print(f"  Launch an example implementation")
    print(f"       {sys.argv[0]} example name [arg, ...]")
    sys.exit(1)


def split_args(args):
    try:
        index = args.index("-vs-")
    except ValueError:
        print("Could not find '-vs-' in arguments")
        usage()

    return args[:index], args[index + 1:]


def ui():
    call_args_a, call_args_b = split_args(sys.argv[1:])
    run_game_ui(call_args_a, call_args_b)


def bulk():
    try:
        n = int(sys.argv.pop(1))
    except ValueError:
        print(f"n should be an integer")
        usage()

    call_args_a, call_args_b = split_args(sys.argv[1:])
    run_game_bulk(n, call_args_a, call_args_b)


def example():

    dirname = pathlib.Path(__file__).parent / "examples"
    if sys.argv[1] in ["-l", "--list"]:
        for line in os.listdir(dirname):
            if not line.startswith("_"):
                print(line[:-3])
        sys.exit(0)
    name, *args = sys.argv[1:]
    filename = os.path.join(dirname, name + ".py")
    args = [filename, *args]
    os.execv(filename, args)


def main():
    command = sys.argv.pop(1)
    try:
        {
            "ui": ui,
            "bulk": bulk,
            "example": example,
        }[command]()
    except KeyError:
        print(f"Unrecognized command {command}")
        usage()


if __name__ == '__main__':
    main()

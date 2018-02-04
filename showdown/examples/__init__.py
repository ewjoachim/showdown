import os
import sys

def main():
    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: showdown-example -l")
        print("Usage: showdown-example name [arg, ...]")
        sys.exit(1)
    dirname = os.path.dirname(__file__)
    if sys.argv[1] in ["-l", "--list"]:
        for line in os.listdir(dirname):
            if not line.startswith("_"):
                print(line[:-3])
        sys.exit(0)
    name, *args = sys.argv[1:]
    filename = os.path.join(dirname, name + ".py")
    args = [filename, *args]
    os.execv(filename, args)


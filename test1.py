#!/usr/bin/env python
import random
import sys

name = sys.argv[1]
print(name)

try:
    with open(name + ".log", "w") as f:
        while True:
            print(random.choice("shoot dodge reload".split()))
            f.write("internal" + name + sys.stdin.readline() + "\n")
except KeyboardInterrupt:
    pass

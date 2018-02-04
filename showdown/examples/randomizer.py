#!/usr/bin/env python
import random
import sys

name = sys.argv[1]
print(name)

while True:
    print(random.choice("shoot dodge reload".split()))
    action = input()

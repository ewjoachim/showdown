#!/usr/bin/env python
"""
Greetsdlfnj, I'm the Randomizer !
Usage: showdown-example randomizer name

I play randomly shoot, dodge and reload
with equal probability.
"""
import random
import sys

name = sys.argv[1]
print(name)

while True:
    print(random.choice("shoot dodge reload".split()))
    action = input()

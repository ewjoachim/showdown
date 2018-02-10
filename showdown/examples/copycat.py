#!/usr/bin/env python
"""
Meow, I'm the Copycat.
Usage: showdown-example copycat name first

I will do the action you give me as first action
and then I will repeat my opponent's action
"""
import sys

name, first = sys.argv[1:]  # pylint: disable=unbalanced-tuple-unpacking
print(name)

print(first)
ok = set("shoot dodge reload".split())
while True:
    their_action = input()
    print(their_action if their_action in ok else first)

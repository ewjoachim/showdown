#!/usr/bin/env python
"""
lHeol, I'm the Shuffler !
Usage: showdown-example shiffler name n

I will do 2 cycles of n turns alternatively:
["dodge", "dodge", "dodge", "shoot"].shuffle()
<--------n times -------->
then
["dodge", "dodge", "dodge", "reload"].shuffle()
<--------n times -------->

It's a safe strategy, but I dodge a lot, so if
I miss my shots, I probably lose in the end.
"""
import random
import sys

name, n = sys.argv[1:]  # pylint: disable=unbalanced-tuple-unpacking
print(name)
n = int(n)
k = n + 1

while True:
    for action in random.sample(
            ["dodge"] * n + ["shoot"], k=k):
        print(action)
        input()
    for action in random.sample(
            ["dodge"] * n + ["reload"], k=k):
        print(action)
        input()

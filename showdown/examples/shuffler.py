#!/usr/bin/env python
import random
import sys

name, n = sys.argv[1:]
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

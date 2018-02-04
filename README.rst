Showdown
========

    This town is not big enough for both of our bots

What is this?
-------------

Showdown is a game for two bots (and for the people to write those bots)

The rules
---------

.. image:: https://nerdist.com/wp-content/uploads/2016/08/Good-Bad-Ugly-Trio.jpg
   :alt: Showdown (mexican standoff) from The Good, the Bad and the Ugly. (image from https://nerdist.com/)

Basics
^^^^^^

This game is played by 2 bots (a.k.a players), implemented as 2 different command line programs.

Each bot represents an opponent in a western movie style showdown. They both have a 6-bullet Colt, and start with one loaded bullet. The aim is to kill the opponent by shooting them while they are vulnerable.

Player play at the same time by issuing one of the 3 allowed commands : ``shoot``, ``dodge``, ``reload``. Then, if both player survive, they see what their opponent did, and start over, etc.

Who dies ?
^^^^^^^^^^

- If A shoots and B reloads, B dies
- If A and B both shoot but B has no more bullets, B dies
- If A shoots and B issues an invalid command or their program has exited, B dies
- If A shoots and B issues a command in more than 500ms, B dies
- If B has not issued a command within 3s, B dies

In all other cases, the game continues.

Ammunition
^^^^^^^^^^

Each player start with 1 bullet in their gun. Shooting always removes a bullet from your gun (except if it's already empty). Reloading always adds a bullet to your gun (except if it already has 6 bullets and is full)


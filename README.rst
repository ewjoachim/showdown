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

(A and B can be any of the 2 players)

- If A shoots while B reloads, B dies
- If A and B both shoot but B has no more bullets, B dies
- If A shoots while B issues an invalid command or their program has exited, B dies
- If B has not issued a command within one second (but their program is still running), B dies. This rule is to avoid bots that will slow the game at each and every turn.

In all other cases, the game continues.

Ammunition
^^^^^^^^^^

Each player start with 1 bullet in their gun. Shooting always removes a bullet from your gun (except if it's already empty). Reloading always adds a bullet to your gun (except if it already has 6 bullets and is full)

Turns & victory
^^^^^^^^^^^^^^^

The game stops when an opponent is dead, or when at least one opponent takes more than one second to give its intructions, or after 100 turns.

If there is no winner, the winner will be selected as the one who dodged the least frequently. If both opponent dodged the same amount of time, a winner is randomly selected.

Inputs, outputs, timings
^^^^^^^^^^^^^^^^^^^^^^^^

Here, ``print`` means write in stdout, followed by a newline (`\n`), and ``read``means read from stdin until newline.

The program should print its name (within 10 seconds after the start of the process)

Then, as long as the game is on, the program should loop over the two following action.

The program should print its action for the current turn among ``shoot``, ``dodge`` and ``reload``.
Then, the program may read the action the opponent did. The action may be ``shoot``, ``dodge``, ``reload``, ``shoot_no_bullet`` if the opponent shot bu had no bullet left, ``stand`` if the opponent sent an invalid command.

A program has one second after it receives the opponent's action to print its own action, otherwise the game will be terminated.

The program
-----------

.. code::bash

    showdown first command with args -vs- second command with args

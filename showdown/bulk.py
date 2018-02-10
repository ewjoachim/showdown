from showdown.game import run_game


def run_game_bulk(n, call_args_a, call_args_b):
    a_victories = 0
    b_victories = 0
    for __ in range(n):
        state = run_game(call_args_a, call_args_b)
        if state["winner_key"] == "a":
            a_victories += 1
            print("a", end="", flush=True)
        elif state["winner_key"] == "b":
            b_victories += 1
            print("b", end="", flush=True)

    print(f"a: {a_victories} / b: {b_victories}")

import multiprocessing

from showdown.game import run_game


def process(call_args_a, call_args_b):
    state = run_game(call_args_a, call_args_b)
    return state["winner_key"]

def run_game_bulk(n, call_args_a, call_args_b):
    a_victories = 0
    b_victories = 0

    with multiprocessing.Pool() as pool:
        future_results = [
            pool.apply_async(process, (call_args_a, call_args_b))
            for __ in range(n)]
        for f in future_results:
            winner_key = f.get()
            if winner_key == "a":
                a_victories += 1
                print("a", end="", flush=True)
            elif winner_key == "b":
                b_victories += 1
                print("b", end="", flush=True)

    print(f"a: {a_victories} / b: {b_victories}")


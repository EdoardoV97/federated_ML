from mimetypes import init
import time
from z3 import *
import math

"""
Create a variable representing each charachter of the flag string (23, seen from the read on ghidra).
Add all the constraints seen with Ghidra.
Add the constraints to be printable charachters.
Print the value for the found model.
"""


def get_j_rew_coeff(j, K_PRIME):
    return (K_PRIME - 2 * j + 1) / (K_PRIME - 1)


def main():
    z3.set_option(rational_to_decimal=True)
    z3.set_option(precision=5)
    for N in range(5, 20, 5):
        for W in range(N * 10, N * 100, N * 1):
            K_PRIME = W / N
            for BEST_K in range(
                math.floor((K_PRIME + 1) / 2) - 1,
                math.floor((K_PRIME + 1) / 2),  # +1 for the classic formula
            ):
                fee = z3.Real("fee")
                r1 = z3.Real("r1")
                bounty = z3.Real("bounty")

                solver = z3.Solver()

                coeffs = [1]
                for i in range(2, BEST_K + 1):
                    coeffs.append(get_j_rew_coeff(i, K_PRIME))

                solver.add(bounty >= 0, fee >= 0, r1 >= 0)
                solver.add(fee < (((K_PRIME - 2 * BEST_K + 1) / (K_PRIME - 1))) * r1)
                solver.add(fee >= (r1 / (K_PRIME / 2 + 2)))
                # solver.add(r1 == B / (sum(coeffs) * N - W / (K_PRIME / 2 + 2)))
                r = sum(coeffs) * r1
                solver.add(r * N == bounty + fee * W)

                checked = solver.check()
                print(f"{N} rounds {W} workers {K_PRIME} w/r {BEST_K} best_k:{checked}")
                m = solver.model()
                print(m)


if __name__ == "__main__":
    before = time.time()
    main()
    after = time.time()
    # print("Time elapsed: {}".format(after - before))

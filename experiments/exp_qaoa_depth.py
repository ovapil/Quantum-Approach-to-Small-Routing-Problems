import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"
EXPERIMENT_DIR = PROJECT_ROOT / "experiments"

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(EXPERIMENT_DIR))


from experiment_runner import (
    run_single_experiment,
    save_experiment_csv,
)


DEPTHS = [
    1,
    2,
    3,
]

SEEDS = [
    0,
    1,
    2,
    3,
    4,
]


def main():

    print("=" * 70)
    print("WEEK 5 - EXPERIMENT B: QAOA DEPTH")
    print("=" * 70)

    results = []

    for p in DEPTHS:

        print(
            f"\n{'=' * 70}"
        )

        print(
            f"DEPTH p = {p}"
        )

        print(
            f"{'=' * 70}"
        )

        for seed in SEEDS:

            print(
                f"\nRunning p={p}, "
                f"seed={seed}"
            )

            result = run_single_experiment(
                p=p,
                penalty=3.0,
                shots=2048,
                seed=seed,
                maxiter=150,
            )

            result["experiment"] = (
                "qaoa_depth"
            )

            results.append(
                result
            )

            print(
                "Feasibility rate:",
                f"{result['feasibility_rate']:.4f}"
            )

            print(
                "Optimal probability:",
                f"{result['optimal_solution_probability']:.4f}"
            )

            print(
                "Best feasible cost:",
                result["best_feasible_cost"]
            )

            print(
                "Optimality gap:",
                result["optimality_gap"]
            )

            print(
                "Runtime:",
                f"{result['runtime_seconds']:.6f}s"
            )

    output_path = (
        PROJECT_ROOT
        / "experiments"
        / "results"
        / "qaoa_depth.csv"
    )

    save_experiment_csv(
        results,
        output_path
    )

    print(
        "\n" + "=" * 70
    )

    print(
        f"[PASS] CSV created: {output_path}"
    )

    print(
        f"Total runs: {len(results)}"
    )

    print(
        "ALL QAOA DEPTH EXPERIMENTS COMPLETED!"
    )


if __name__ == "__main__":
    main()
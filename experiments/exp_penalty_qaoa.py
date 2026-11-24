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


TOPOLOGIES = ["topology_6", "topology_8"]
PENALTY_KS = [0.8, 1.0, 1.2, 1.5, 2.0, 4.0]

SEEDS = [
    0,
    1,
    2,
    3,
    4,
]


def main():

    print("=" * 70)
    print("EXPERIMENT C: PENALTY COEFFICIENT (A = k * c_UB / 2)")
    print("=" * 70)

    results = []

    for topology in TOPOLOGIES:
        for k in PENALTY_KS:

            print(f"\n{'=' * 70}\n{topology} | k = {k}\n{'=' * 70}")

            for seed in SEEDS:

                result = run_single_experiment(
                    topology_name=topology,
                    p=1,
                    penalty=None,
                    penalty_k=k,
                    shots=2048,
                    seed=seed,
                )

                result["experiment"] = "penalty"
                results.append(result)

                print(
                    f"  seed={seed}"
                    f" | A={result['penalty_A']:.2f}"
                    f" | feas={result['feasibility_rate']:.4f}"
                    f" | P_opt={result['optimal_solution_probability']:.4f}"
                    f" | gain={result['optimal_prob_gain']:.2f}"
                    f" | top1={result['match_optimal']}"
                )

    output_path = (
        PROJECT_ROOT / "experiments" / "results" / "qaoa_penalty.csv"
    )

    save_experiment_csv(results, output_path)

    print(f"\n[PASS] CSV created: {output_path}")
    print(f"Total runs: {len(results)}")
if __name__ == "__main__":
    main()
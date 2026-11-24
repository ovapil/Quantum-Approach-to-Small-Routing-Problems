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

SHOTS_LIST = [
    256,
    512,
    1024,
    2048,
    4096,
]

SEEDS = [
    0,
    1,
    2,
    3,
    4,
]
TOPOLOGIES = ["topology_6", "topology_8"]

def main():

    print("=" * 70)
    print("EXPERIMENT D: NUMBER OF SHOTS")
    print("=" * 70)

    results = []

    for topology in TOPOLOGIES:
        for shots in SHOTS_LIST:

            print("\n" + "=" * 70)
            print(f"{topology} | SHOTS = {shots}")
            print("=" * 70)

            for seed in SEEDS:

                print(f"\nRunning {topology}, shots={shots}, seed={seed}")

                result = run_single_experiment(
                    topology_name=topology,
                    p=1,
                    shots=shots,
                    seed=seed,
                )

                result["experiment"] = "shots"
                results.append(result)

                print(
                    f"  feas={result['feasibility_rate']:.4f}"
                    f" | P_opt={result['optimal_solution_probability']:.4f}"
                    f" | gain={result['optimal_prob_gain']:.2f}"
                    f" | top1={result['match_optimal']}"
                    f" | {result['runtime_seconds']:.2f}s"
                )

    output_path = (
        PROJECT_ROOT / "experiments" / "results" / "qaoa_shots.csv"
    )

    save_experiment_csv(results, output_path)

    print("\n" + "=" * 70)
    print(f"[PASS] CSV created: {output_path}")
    print(f"Total runs: {len(results)}")

if __name__ == "__main__":
    main()
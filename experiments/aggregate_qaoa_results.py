import csv
from pathlib import Path
from statistics import mean, stdev


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULT_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "results"
)


# ============================================================
# Helpers
# ============================================================

def load_csv(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


def to_float(value):
    if value in (
        None,
        "",
        "None",
    ):
        return None

    return float(value)


def to_bool(value):
    return str(value).lower() in (
        "true",
        "1",
        "yes",
    )


def safe_mean(values):
    values = [
        value
        for value in values
        if value is not None
    ]

    if not values:
        return None

    return mean(values)


def safe_stdev(values):
    values = [
        value
        for value in values
        if value is not None
    ]

    if len(values) < 2:
        return 0.0

    return stdev(values)


# ============================================================
# Aggregate one experiment
# ============================================================

def aggregate_rows(
    rows,
    experiment_name,
    group_column,
):
    groups = {}

    for row in rows:

        group_value = (row["topology"], row[group_column])

        groups.setdefault(
            group_value,
            []
        ).append(row)

    output = []

    for group_value, group_rows in groups.items():

        feasibility_rates = [
            to_float(
                row["feasibility_rate"]
            )
            for row in group_rows
        ]

        optimal_probabilities = [
            to_float(
                row[
                    "optimal_solution_probability"
                ]
            )
            for row in group_rows
        ]

        optimality_gaps = [
            to_float(
                row["optimality_gap"]
            )
            for row in group_rows
        ]

        runtimes = [
            to_float(
                row["runtime_seconds"]
            )
            for row in group_rows
        ]

        mean_feasible_costs = [
            to_float(
                row["mean_feasible_cost"]
            )
            for row in group_rows
        ]

        expectation_values = [
            to_float(
                row["expectation_value"]
            )
            for row in group_rows
        ]

        match_flags = [
            to_bool(
                row["match_optimal"]
            )
            for row in group_rows
        ]

        optimization_successes = [
            to_bool(
                row[
                    "optimization_success"
                ]
            )
            for row in group_rows
        ]

        match_rate = (
            sum(match_flags)
            / len(match_flags)
        )

        optimization_success_rate = (
            sum(
                optimization_successes
            )
            / len(
                optimization_successes
            )
        )

        summary = {
            "experiment":
                experiment_name,

            "parameter":
                group_column,

            "topology": group_value[0],
            "value": group_value[1],
            "mean_optimal_prob_gain": safe_mean(
                [to_float(r["optimal_prob_gain"]) for r in group_rows]
            ),
            "mean_random_optimal_prob": safe_mean(
                [to_float(r["random_optimal_prob"]) for r in group_rows]
            ),

            "runs":
                len(group_rows),

            "mean_feasibility_rate":
                safe_mean(
                    feasibility_rates
                ),

            "std_feasibility_rate":
                safe_stdev(
                    feasibility_rates
                ),

            "mean_optimal_probability":
                safe_mean(
                    optimal_probabilities
                ),

            "std_optimal_probability":
                safe_stdev(
                    optimal_probabilities
                ),

            "match_rate":
                match_rate,

            "mean_optimality_gap":
                safe_mean(
                    optimality_gaps
                ),

            "mean_feasible_cost":
                safe_mean(
                    mean_feasible_costs
                ),

            "mean_expectation_value":
                safe_mean(
                    expectation_values
                ),

            "mean_runtime_seconds":
                safe_mean(
                    runtimes
                ),

            "std_runtime_seconds":
                safe_stdev(
                    runtimes
                ),

            "optimization_success_rate":
                optimization_success_rate,
        }

        output.append(
            summary
        )

    return output


# ============================================================
# Save summary
# ============================================================

def save_summary(
    rows,
    output_path
):

    if not rows:
        raise ValueError(
            "No summary rows to save"
        )

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# Main
# ============================================================

def main():

    depth_file = (
        RESULT_DIR
        / "qaoa_depth.csv"
    )

    penalty_file = (
        RESULT_DIR
        / "qaoa_penalty.csv"
    )

    shots_file = (
        RESULT_DIR
        / "qaoa_shots.csv"
    )

    depth_rows = load_csv(
        depth_file
    )

    penalty_rows = load_csv(
        penalty_file
    )

    shots_rows = load_csv(
        shots_file
    )

    summaries = []

    summaries.extend(
        aggregate_rows(
            depth_rows,
            experiment_name="qaoa_depth",
            group_column="p",
        )
    )

    summaries.extend(
        aggregate_rows(
            penalty_rows,
            experiment_name="penalty",
            group_column="penalty_A",
        )
    )

    summaries.extend(
        aggregate_rows(
            shots_rows,
            experiment_name="shots",
            group_column="shots",
        )
    )

    output_file = (
        RESULT_DIR
        / "qaoa_summary.csv"
    )

    save_summary(
        summaries,
        output_file
    )

    print("=" * 80)
    print(
        "WEEK 5 - QAOA EXPERIMENT SUMMARY"
    )
    print("=" * 80)

    for row in summaries:

        print(
            f"\n"
            f"{row['experiment']} | "
            f"{row['parameter']}="
            f"{row['value']}"
        )

        print(
            "Runs:",
            row["runs"]
        )

        print(
            "Mean feasibility rate:",
            f"{row['mean_feasibility_rate']:.4f}"
        )

        print(
            "Mean optimal probability:",
            f"{row['mean_optimal_probability']:.4f}"
        )

        print(
            "Match rate:",
            f"{row['match_rate']:.4f}"
        )

        print(
            "Mean optimality gap:",
            f"{row['mean_optimality_gap']:.4f}"
        )

        print(
            "Mean runtime:",
            f"{row['mean_runtime_seconds']:.6f}s"
        )

    print(
        "\n" + "=" * 80
    )

    print(
        f"[PASS] Summary CSV created: "
        f"{output_file}"
    )

    print(
        f"Total summary rows: "
        f"{len(summaries)}"
    )


if __name__ == "__main__":
    main()
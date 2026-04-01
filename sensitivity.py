#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sensitivity.py — Sobol sensitivity analysis over seven agent/model parameters.
 
Uses SALib to generate a Saltelli sample, runs the ABM with replicates for
each parameter set, and performs first- and total-order Sobol decomposition
on two outputs: mean eco_state and fraction of gardening agents.
 
Results are written to ``sensitivity_outputs.csv`` and printed to the console.
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import numpy as np
from SALib.sample import saltelli
from SALib.analyze import sobol
from tqdm import tqdm
import csv

from neighborhood import Neighborhood
from cell import cell_factory

# ======== Sensitivity Analysis Setup ========

problem = {
    "num_vars": 7,
    "names": [
        "gardener_fraction",
        "gardening_years_min",
        "gardening_years_max",
        "turnover_rate",
        "inherit_weight",
        "base_adopt",
        "peer_influence"
    ],
    "bounds": [
        [0.0, 0.3],    # gardener_fraction
        [3, 10],       # gardening_years_min
        [10, 25],      # gardening_years_max
        [0.0, 0.1],    # turnover_rate
        [0.0, 1.0],    # inherit_weight
        [0.01, 0.2],   # base_adopt
        [0.0, 0.5],    # peer_influence
    ]
}

# Output file
METRICS_CSV = "sensitivity_outputs.csv"

# Number of base samples (Total runs = N * (2D + 2))
N = 512

# Replicates per parameter set
REPLICATES = 3


# ============ ABM Wrapper ============

def run_abm_with_params(params):
    (
        gardener_fraction,
        gardening_years_min,
        gardening_years_max,
        turnover_rate,
        inherit_weight,
        base_adopt,
        peer_influence
    ) = params

    # Build neighborhood
    neighborhood = Neighborhood(
        width=50,
        height=50,
        cell_factory=cell_factory
    )

    # Inject parameters
    neighborhood.turnover_rate = turnover_rate
    neighborhood.inherit_weight = inherit_weight
    neighborhood.newcomer_gardener_fraction = gardener_fraction
    neighborhood.gardening_year_range = (int(gardening_years_min), int(gardening_years_max))
    neighborhood.base_adopt = base_adopt
    neighborhood.adoption_check_rate = 0.25
    neighborhood.adopt_scale = 0.30
    neighborhood.benefit_threshold = 0.03

    # Update agent peer influence
    for row in neighborhood.grid:
        for cell in row:
            if cell.agent:
                cell.agent.peer_influence = peer_influence

    # Seed gardeners
    neighborhood.seed_gardeners(
        gardener_fraction=gardener_fraction,
        gardening_year_range=(int(gardening_years_min), int(gardening_years_max))
    )

    # Run model
    for _ in range(50):
        neighborhood.step()

    # Collect outputs
    cells = [c for row in neighborhood.grid for c in row]
    mean_eco = np.mean([c.eco_state for c in cells])
    frac_gardening = np.mean([
        1 if c.agent and c.agent.gardening else 0
        for c in cells
    ])
    return mean_eco, frac_gardening


def run_with_replicates(params, n=REPLICATES):
    results = [run_abm_with_params(params) for _ in range(n)]
    return np.mean(results, axis=0)


# ========= Run Simulation & Collect Data ==========

if __name__ == "__main__":
    print("Generating samples...")
    param_values = saltelli.sample(problem, N=N, calc_second_order=True)

    print(f"Total simulations: {len(param_values)} × {REPLICATES} replicates")
    Y_eco = []
    Y_gardening = []

    with open(METRICS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        header = problem["names"] + ["mean_eco", "frac_gardening"]
        writer.writerow(header)

        for params in tqdm(param_values):
            mean_eco, frac_gardening = run_with_replicates(params)
            Y_eco.append(mean_eco)
            Y_gardening.append(frac_gardening)

            writer.writerow(list(params) + [mean_eco, frac_gardening])

    print("Simulation complete. Results written to:", METRICS_CSV)

    # ========== Sobol Analysis ==========

    print("\nAnalyzing variance (mean eco_state)...")
    Si_eco = sobol.analyze(problem, np.array(Y_eco), calc_second_order=True, print_to_console=True)

    print("\nAnalyzing variance (frac gardening)...")
    Si_garden = sobol.analyze(problem, np.array(Y_gardening), calc_second_order=True, print_to_console=True)

    # Optional: print key results
    def print_summary(Si, title):
        print(f"\n=== {title} ===")
        for name, s1, st in zip(problem["names"], Si["S1"], Si["ST"]):
            print(f"{name:<25}  S1: {s1:.3f}   ST: {st:.3f}")

    print_summary(Si_eco, "Mean Eco State")
    print_summary(Si_garden, "Fraction Gardeners")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Entry point for a single model run.
 
Initializes the neighborhood, seeds gardeners, runs the simulation for the
configured number of years, and optionally writes metrics (CSV) and spatial
snapshots (NPZ) to disk.
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import csv
import numpy as np

from neighborhood import Neighborhood
from cell import cell_factory
from visualize import plot_neighborhood, plot_metrics, plot_atlas_timeline


# =================
# Model Parameters
# =================

GRID_WIDTH = 50
GRID_HEIGHT = 50
YEARS = 50

# Gardening
GARDENER_FRACTION = 0.10  # (0 - 1)
GARDENING_YEARS = (5, 15)  # inclusive duration range


# # Random seed
# RANDOM_SEED = 14
# random.seed(RANDOM_SEED)
# np.random.seed(RANDOM_SEED)


# =========================
# Data logging / diagnostics
# =========================

SAVE_METRICS_CSV = True
METRICS_PATH = "run_metrics.csv"

SAVE_SNAPSHOTS = True
SNAPSHOT_EVERY = 5          # save grids every N years
SNAPSHOT_PATH = "snapshots.npz"


# =========================
# Helpers for logging
# =========================

def iter_cells(neighborhood):
    for row in neighborhood.grid:
        for cell in row:
            yield cell


def collect_metrics(neighborhood, year):
    cells = list(iter_cells(neighborhood))

    eco = np.array([c.eco_state for c in cells], dtype=float)
    bias = np.array([c.regen_bias for c in cells], dtype=float)
    birds = np.array([c.bird_index for c in cells], dtype=float)

    # Agent-derived
    agents = [c.agent for c in cells if c.agent is not None]
    n_agents = len(agents)
    gardeners = [a for a in agents if a.gardening == 1]
    n_gardeners = len(gardeners)

    if n_agents > 0:
        frac_control = sum(1 for a in agents if a.practice == 0) / n_agents
        frac_permit = sum(1 for a in agents if a.practice == 1) / n_agents
        frac_gardening = n_gardeners / n_agents
        mean_habit = sum(a.habit for a in agents) / n_agents

        # Gardener-only practice diagnostics
        if gardeners:
            frac_permit_gardeners = sum(1 for a in gardeners if a.practice == 1) / len(gardeners)
            frac_control_gardeners = 1.0 - frac_permit_gardeners
        else:
            frac_permit_gardeners = float("nan")
            frac_control_gardeners = float("nan")
    else:
        frac_control = frac_permit = frac_gardening = mean_habit = float("nan")
        frac_permit_gardeners = frac_control_gardeners = float("nan")

    # Threshold / regime signals
    frac_degraded = float(np.mean(eco < 0.1))
    frac_recoverable = float(np.mean(bias > 0.0))      # recovery uses max(0, regen_bias)
    frac_birds_gt_0p3 = float(np.mean(birds > 0.3))    # proxy for bird-feedback gate

    return {
        "year": int(year),
        "mean_eco": float(np.mean(eco)),
        "var_eco": float(np.var(eco)),
        "mean_bias": float(np.mean(bias)),
        "var_bias": float(np.var(bias)),
        "mean_birds": float(np.mean(birds)),
        "var_birds": float(np.var(birds)),
        "frac_degraded_eco_lt_0p1": frac_degraded,
        "frac_regen_bias_gt_0": frac_recoverable,
        "frac_birds_gt_0p3": frac_birds_gt_0p3,
        "frac_control": float(frac_control),
        "frac_permit": float(frac_permit),
        "frac_gardening": float(frac_gardening),
        "mean_habit": float(mean_habit),
        "frac_permit_gardeners": float(frac_permit_gardeners),
        "frac_control_gardeners": float(frac_control_gardeners),
        "n_gardeners": int(n_gardeners)
    }


def snapshot_grids(neighborhood):
    h, w = neighborhood.height, neighborhood.width
    eco = np.zeros((h, w), dtype=float)
    bias = np.zeros((h, w), dtype=float)
    birds = np.zeros((h, w), dtype=float)
    gardening = np.zeros((h, w), dtype=int)
    practice = np.zeros((h, w), dtype=int)  # 0 control, 1 permit

    for y in range(h):
        for x in range(w):
            c = neighborhood.grid[y, x]
            eco[y, x] = c.eco_state
            bias[y, x] = c.regen_bias
            birds[y, x] = c.bird_index

            if c.agent is not None:
                gardening[y, x] = 1 if c.agent.gardening == 1 else 0
                practice[y, x] = 1 if c.agent.practice == 1 else 0
            else:
                gardening[y, x] = 0
                practice[y, x] = 0

    return eco, bias, birds, gardening, practice


def bird_feedback_active(cell):
    return (
        cell.eco_state > 0.7 and
        cell.bird_index > 0.5 and
        cell.bird_memory > 6
    )


# ===============
# Run Simulation
# ===============

def run(
    gardener_fraction,
    gardening_years,
    years,
    save_outputs=False,
    record_feedback=False
):


    # ----------
    # Initialize 
    # ----------

    neighborhood = Neighborhood(
        width=GRID_WIDTH,
        height=GRID_HEIGHT,
        cell_factory=cell_factory
    )

    # Structural parameters (world, not experiment)
    neighborhood.turnover_rate = 0.02
    neighborhood.inherit_weight = 0.6

    # Gardening parameters 
    neighborhood.newcomer_gardener_fraction = gardener_fraction
    neighborhood.gardening_year_range = gardening_years

    # Seed initial gardeners
    neighborhood.seed_gardeners(
        gardener_fraction=gardener_fraction,
        gardening_year_range=gardening_years
    )

    if save_outputs:
        gardeners_at_start = sum(
            1
            for row in neighborhood.grid
            for cell in row
            if cell.agent is not None and cell.agent.gardening == 1
        )
        print("Gardeners at start:", gardeners_at_start)

    # -----------------
    # Logging containers
    # -----------------

    metrics_rows = []

    snap_years = []
    snap_eco = []
    snap_bias = []
    snap_birds = []
    snap_gardening = []
    snap_practice = []
    bird_feedback_ts = [] if record_feedback else None


    # -----------------
    # Baseline (year 0)
    # -----------------

    metrics_rows.append(collect_metrics(neighborhood, year=0))

    if save_outputs and SAVE_SNAPSHOTS and (0 % SNAPSHOT_EVERY == 0):
        e, b, bd, g, p = snapshot_grids(neighborhood)
        snap_years.append(0)
        snap_eco.append(e)
        snap_bias.append(b)
        snap_birds.append(bd)
        snap_gardening.append(g)
        snap_practice.append(p)

    # -----------------
    # Main simulation loop
    # -----------------

    for year in range(1, years + 1):
        neighborhood.step()
        if record_feedback:
            cells = [c for row in neighborhood.grid for c in row]
            frac_feedback = np.mean([
                1 if bird_feedback_active(c) else 0
                for c in cells
                ])
            bird_feedback_ts.append(frac_feedback)


        metrics_rows.append(collect_metrics(neighborhood, year=year))

        if save_outputs and SAVE_SNAPSHOTS and (year % SNAPSHOT_EVERY == 0):
            e, b, bd, g, p = snapshot_grids(neighborhood)
            snap_years.append(year)
            snap_eco.append(e)
            snap_bias.append(b)
            snap_birds.append(bd)
            snap_gardening.append(g)
            snap_practice.append(p)

        if save_outputs and (year - 1) in [0, 10, 20, 30, 40, 49]:
            plot_neighborhood(neighborhood, title=f"Year {year - 1}")

    # -------------
    # Write outputs
    # -------------

    if save_outputs and SAVE_METRICS_CSV:
        fieldnames = list(metrics_rows[0].keys())
        with open(METRICS_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(metrics_rows)
        print("Wrote metrics to:", METRICS_PATH)

    if save_outputs and SAVE_SNAPSHOTS:
        np.savez_compressed(
            SNAPSHOT_PATH,
            years=np.array(snap_years, dtype=int),
            eco=np.stack(snap_eco, axis=0),
            bias=np.stack(snap_bias, axis=0),
            birds=np.stack(snap_birds, axis=0),
            gardening=np.stack(snap_gardening, axis=0),
            practice=np.stack(snap_practice, axis=0),
        )
        print("Wrote snapshots to:", SNAPSHOT_PATH)

    if record_feedback:
        return neighborhood, bird_feedback_ts
    else:
        return neighborhood



if __name__ == "__main__":
    run(
        gardener_fraction=GARDENER_FRACTION,
        gardening_years=GARDENING_YEARS,
        years=YEARS,
        save_outputs=True
    )


    # Only visualize after outputs exist
    if SAVE_METRICS_CSV:
        plot_metrics(METRICS_PATH)

    if SAVE_SNAPSHOTS:
        plot_atlas_timeline("snapshots.npz", every=4)






    
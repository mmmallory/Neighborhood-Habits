#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
monte_carlo_analysis.py — Monte Carlo ensemble near the ecological/social tipping region.
 
Sweeps gardener fraction from 5% to 15% across 30 stochastic replicates and
measures two outcomes:
 
  - Functional ecological recovery: whether the bird–ecosystem feedback loop
    activates in a sufficient fraction of cells for a sustained period.
  - Social practice shift: whether permit-practice agents reach dominance
    (>50%) by the final year.
 
Results are written to ``monte_carlo_dual_outcomes.csv``.
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import numpy as np
import csv
from tqdm import tqdm

from main import run   # uses run(..., record_feedback=True)

# ====================
# Configuration
# ====================

NUM_REPLICATES = 30
FRACTIONS_TO_TEST = np.linspace(0.05, 0.15, 11)
YEARS = 100
GARDENING_YEARS = (5, 15)

# Social threshold
PERMIT_DOMINANCE_THRESHOLD = 0.50

# Functional bird recovery thresholds
FEEDBACK_FRAC_THRESHOLD = 0.2   # ≥5% of cells
FEEDBACK_PERSIST_YEARS = 10       # for ≥5 consecutive years

OUTPUT_CSV = "monte_carlo_dual_outcomes.csv"

# ====================
# Helper: functional recovery test
# ====================

def functional_bird_recovery(feedback_ts):
    """
    Birds are functionally recovered if the bird–ecosystem feedback
    is active in ≥ FEEDBACK_FRAC_THRESHOLD of cells for
    ≥ FEEDBACK_PERSIST_YEARS consecutive years.
    """
    count = 0
    for frac in feedback_ts:
        if frac >= FEEDBACK_FRAC_THRESHOLD:
            count += 1
            if count >= FEEDBACK_PERSIST_YEARS:
                return True
        else:
            count = 0
    return False


# ====================
# Monte Carlo Loop
# ====================

results = []

for frac in tqdm(FRACTIONS_TO_TEST, desc="Monte Carlo sweep", ncols=100):

    for rep in range(NUM_REPLICATES):

        # ---- run model (steps internally) ----
        neighborhood, bird_feedback_ts = run(
            gardener_fraction=frac,
            gardening_years=GARDENING_YEARS,
            years=YEARS,
            save_outputs=False,
            record_feedback=True
        )

        # ---- ecological outcome (functional) ----
        bird_functional = functional_bird_recovery(bird_feedback_ts)
        max_feedback_frac = max(bird_feedback_ts)
        final_feedback_frac = bird_feedback_ts[-1]

        # ---- social outcome (final state) ----
        cells = [
            c for row in neighborhood.grid for c in row
            if c.agent is not None
        ]

        if cells:
            frac_permit_final = np.mean([
                1 if c.agent.practice == 1 else 0
                for c in cells
            ])
        else:
            frac_permit_final = np.nan

        permit_dominant = frac_permit_final > PERMIT_DOMINANCE_THRESHOLD

        # ---- record results ----
        results.append({
            "gardener_fraction": frac,
            "replicate": rep,

            # ecological (functional)
            "bird_functional_recovery": int(bird_functional),
            "max_bird_feedback_frac": float(max_feedback_frac),
            "final_bird_feedback_frac": float(final_feedback_frac),

            # social
            "permit_dominant_final": int(permit_dominant),
            "frac_permit_final": float(frac_permit_final),
        })

# ====================
# Write CSV
# ====================

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\n✅ Monte Carlo complete. Results saved to '{OUTPUT_CSV}'")

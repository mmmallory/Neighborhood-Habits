#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visualize.py — Visualization utilities for the neighborhood ABM.
 
Provides static snapshots, 2×2 panel atlases, time-series plots, and
animations of spatial fields saved to NPZ snapshot files.
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from matplotlib.patches import Patch


# -------
# Helpers
# -------

def _format_ax(ax, title=None):
    ax.set_xticks([])
    ax.set_yticks([])
    if title:
        ax.set_title(title)


def _overlay_gardeners(ax, gardening_grid):
    """Overlay gardener cells as red rectangles."""
    if gardening_grid is None:
        return
    h, w = gardening_grid.shape
    for y in range(h):
        for x in range(w):
            if gardening_grid[y, x] == 1:
                rect = patches.Rectangle(
                    (x - 0.5, y - 0.5),
                    1, 1,
                    linewidth=1.2,
                    edgecolor="red",
                    facecolor="none"
                )
                ax.add_patch(rect)


def _add_practice_legend(ax):
    """Legend for practice meaning + gardener overlay."""
    handles = [
        Patch(facecolor="none", edgecolor="none", label="practice: 0=control, 1=permit"),
        Patch(edgecolor="red", facecolor="none", linewidth=1.2, label="gardener (red outline)")
    ]
    ax.legend(handles=handles, loc="upper right", frameon=True)


# -------------------
# RGB snapshot
# -------------------

def plot_neighborhood(neighborhood, title=None):
    """Original RGB composite snapshot (eco in RG, birds in B) with gardener outlines."""
    h, w = neighborhood.height, neighborhood.width
    img = np.zeros((h, w, 3), dtype=float)

    for y in range(h):
        for x in range(w):
            cell = neighborhood.grid[y, x]
            eco = cell.eco_state
            birds = cell.bird_index
            img[y, x, :] = [0.6 * eco, 0.9 * eco, birds]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(img, vmin=0, vmax=1)

    for y in range(h):
        for x in range(w):
            cell = neighborhood.grid[y, x]
            if cell.agent is not None and cell.agent.gardening == 1:
                rect = patches.Rectangle(
                    (x - 0.5, y - 0.5),
                    1, 1,
                    linewidth=1.5,
                    edgecolor="red",
                    facecolor="none"
                )
                ax.add_patch(rect)

    _format_ax(ax, title)
    plt.tight_layout()
    plt.show()


# ------------------
# Static 2x2 atlas
# ------------------

def plot_neighborhood_atlas(neighborhood, title=None):
    """
    2x2 panel snapshot at the CURRENT state of the neighborhood:
    - eco_state
    - bird_index
    - regen_bias
    - practice (0 control, 1 permit) + gardener overlay
    """
    h, w = neighborhood.height, neighborhood.width

    eco = np.zeros((h, w), dtype=float)
    birds = np.zeros((h, w), dtype=float)
    bias = np.zeros((h, w), dtype=float)
    gardening = np.zeros((h, w), dtype=int)
    practice = np.zeros((h, w), dtype=int)

    for y in range(h):
        for x in range(w):
            c = neighborhood.grid[y, x]
            eco[y, x] = c.eco_state
            birds[y, x] = c.bird_index
            bias[y, x] = c.regen_bias
            if c.agent is not None:
                gardening[y, x] = 1 if c.agent.gardening == 1 else 0
                practice[y, x] = 1 if c.agent.practice == 1 else 0

    fig, axs = plt.subplots(2, 2, figsize=(10, 9))

    im0 = axs[0, 0].imshow(eco, vmin=0.0, vmax=1.0)
    _format_ax(axs[0, 0], "eco_state")

    im1 = axs[0, 1].imshow(birds, vmin=0.0, vmax=1.0)
    _format_ax(axs[0, 1], "bird_index")

    im2 = axs[1, 0].imshow(bias, vmin=-1.0, vmax=1.0)
    _format_ax(axs[1, 0], "regen_bias")

    im3 = axs[1, 1].imshow(practice, vmin=0.0, vmax=1.0)
    _overlay_gardeners(axs[1, 1], gardening)
    _format_ax(axs[1, 1], "practice + gardeners")
    _add_practice_legend(axs[1, 1])

    if title:
        fig.suptitle(title)

    # colorbars
    cb0 = fig.colorbar(im0, ax=axs[0, 0], fraction=0.046, pad=0.04)
    cb1 = fig.colorbar(im1, ax=axs[0, 1], fraction=0.046, pad=0.04)
    cb2 = fig.colorbar(im2, ax=axs[1, 0], fraction=0.046, pad=0.04)
    cb3 = fig.colorbar(im3, ax=axs[1, 1], fraction=0.046, pad=0.04)
    cb3.set_ticks([0, 1])
    cb3.set_ticklabels(["control (0)", "permit (1)"])

    plt.tight_layout()
    plt.show()


# ----------------
# Metrics plotting
# ----------------

def plot_metrics(csv_path):
    years = []
    mean_eco = []
    mean_bias = []
    mean_birds = []
    frac_control = []
    frac_permit = []
    frac_gardening = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            years.append(int(row["year"]))
            mean_eco.append(float(row["mean_eco"]))
            mean_bias.append(float(row["mean_bias"]))
            mean_birds.append(float(row["mean_birds"]))
            frac_control.append(float(row["frac_control"]))
            frac_permit.append(float(row["frac_permit"]))
            frac_gardening.append(float(row["frac_gardening"]))

    plt.figure()
    plt.plot(years, mean_eco)
    plt.xlabel("Year")
    plt.ylabel("Mean eco_state")
    plt.title("Mean ecological viability")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.plot(years, mean_bias)
    plt.xlabel("Year")
    plt.ylabel("Mean regen_bias")
    plt.title("Mean regenerative regime")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.plot(years, mean_birds)
    plt.xlabel("Year")
    plt.ylabel("Mean bird_index")
    plt.title("Mean bird index")
    plt.tight_layout()
    plt.show()

    plt.figure()
    plt.plot(years, frac_control, label="control")
    plt.plot(years, frac_permit, label="permit")
    plt.plot(years, frac_gardening, label="gardening")
    plt.xlabel("Year")
    plt.ylabel("Fraction of agents")
    plt.title("Practices over time")
    plt.legend()
    plt.tight_layout()
    plt.show()


# -------------------------
# Animations from snapshots.npz
# -------------------------

def animate_field(npz_path, field="eco", interval=200, overlay_gardening=False):
    """
    Animate a single field from snapshots.npz.
    Supported fields: "eco", "bias", "birds", "gardening", "practice"
    """
    data = np.load(npz_path)
    years = data["years"]
    grids = data[field]

    # fixed ranges per field
    if field in ("eco", "birds"):
        vmin, vmax = 0.0, 1.0
    elif field == "bias":
        vmin, vmax = -1.0, 1.0
    else:
        vmin, vmax = 0.0, 1.0

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(grids[0], vmin=vmin, vmax=vmax)
    _format_ax(ax, f"{field} — year {years[0]}")

    def update(i):
        ax.clear()
        im2 = ax.imshow(grids[i], vmin=vmin, vmax=vmax)
        _format_ax(ax, f"{field} — year {years[i]}")
        if overlay_gardening and "gardening" in data.files:
            _overlay_gardeners(ax, data["gardening"][i])
        return (im2,)

    ani = animation.FuncAnimation(fig, update, frames=len(years), interval=interval, blit=False)
    plt.tight_layout()
    plt.show()
    return ani


def animate_delta(npz_path, field="eco", interval=200):
    """
    Animate Δfield between consecutive snapshots.
    Computed from saved snapshots (no model changes needed).
    """
    data = np.load(npz_path)
    years = data["years"]
    grids = data[field]

    deltas = grids[1:] - grids[:-1]
    delta_years = years[1:]

    vmax = float(np.max(np.abs(deltas)))
    vmin = -vmax

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(deltas[0], vmin=vmin, vmax=vmax)
    _format_ax(ax, f"Δ{field} — year {delta_years[0]}")

    def update(i):
        im.set_data(deltas[i])
        ax.set_title(f"Δ{field} — year {delta_years[i]}")
        return (im,)

    ani = animation.FuncAnimation(fig, update, frames=len(delta_years), interval=interval, blit=False)
    plt.tight_layout()
    plt.show()
    return ani


def animate_atlas(npz_path, interval=250):
    """
    Animate a 2x2 atlas through saved snapshot years:
    - eco, birds, bias, practice (with gardener overlay)
    Requires snapshots to include: eco, birds, bias, practice, gardening
    """
    data = np.load(npz_path)
    years = data["years"]

    eco = data["eco"]
    birds = data["birds"]
    bias = data["bias"]
    practice = data["practice"]
    gardening = data["gardening"] if "gardening" in data.files else None

    fig, axs = plt.subplots(2, 2, figsize=(10, 9))

    im0 = axs[0, 0].imshow(eco[0], vmin=0.0, vmax=1.0)
    _format_ax(axs[0, 0], "eco_state")

    im1 = axs[0, 1].imshow(birds[0], vmin=0.0, vmax=1.0)
    _format_ax(axs[0, 1], "bird_index")

    im2 = axs[1, 0].imshow(bias[0], vmin=-1.0, vmax=1.0)
    _format_ax(axs[1, 0], "regen_bias")

    im3 = axs[1, 1].imshow(practice[0], vmin=0.0, vmax=1.0)
    _format_ax(axs[1, 1], "practice + gardeners")
    _add_practice_legend(axs[1, 1])

    # gardener overlay frame 0
    if gardening is not None:
        _overlay_gardeners(axs[1, 1], gardening[0])

    fig.suptitle(f"Year {years[0]}")

    # colorbars (fixed ranges)
    fig.colorbar(im0, ax=axs[0, 0], fraction=0.046, pad=0.04)
    fig.colorbar(im1, ax=axs[0, 1], fraction=0.046, pad=0.04)
    fig.colorbar(im2, ax=axs[1, 0], fraction=0.046, pad=0.04)

    cb3 = fig.colorbar(im3, ax=axs[1, 1], fraction=0.046, pad=0.04)
    cb3.set_ticks([0, 1])
    cb3.set_ticklabels(["control (0)", "permit (1)"])

    def update(i):
        im0.set_data(eco[i])
        im1.set_data(birds[i])
        im2.set_data(bias[i])
        im3.set_data(practice[i])
        fig.suptitle(f"Year {years[i]}")

        if gardening is not None:
            _overlay_gardeners(axs[1, 1], gardening[i])

        return (im0, im1, im2, im3)

    ani = animation.FuncAnimation(fig, update, frames=len(years), interval=interval, blit=False)
    plt.tight_layout()
    plt.show()
    return ani

def plot_saved_atlas(npz_path, year_index):
    d = np.load(npz_path)
    years = d["years"]

    eco = d["eco"][year_index]
    birds = d["birds"][year_index]
    bias = d["bias"][year_index]
    practice = d["practice"][year_index]
    gardening = d["gardening"][year_index]

    fig, axs = plt.subplots(2, 2, figsize=(10, 9))

    axs[0, 0].imshow(eco, vmin=0, vmax=1); axs[0, 0].set_title("eco_state")
    axs[0, 1].imshow(birds, vmin=0, vmax=1); axs[0, 1].set_title("bird_index")
    axs[1, 0].imshow(bias, vmin=-1, vmax=1); axs[1, 0].set_title("regen_bias")
    axs[1, 1].imshow(practice, vmin=0, vmax=1); axs[1, 1].set_title("practice")

    for y in range(gardening.shape[0]):
        for x in range(gardening.shape[1]):
            if gardening[y, x]:
                axs[1, 1].add_patch(
                    plt.Rectangle((x-0.5, y-0.5), 1, 1,
                                  edgecolor="red", facecolor="none", linewidth=1)
                )

    fig.suptitle(f"Year {years[year_index]}")
    for ax in axs.flat:
        ax.set_xticks([]); ax.set_yticks([])

    plt.tight_layout()
    _add_practice_legend(axs[1, 1])
    fig.colorbar(axs[0, 0].images[0], ax=axs[0, 0], fraction=0.046, pad=0.04)
    fig.colorbar(axs[0, 1].images[0], ax=axs[0, 1], fraction=0.046, pad=0.04)
    fig.colorbar(axs[1, 0].images[0], ax=axs[1, 0], fraction=0.046, pad=0.04)
    
    cb = fig.colorbar(axs[1, 1].images[0], ax=axs[1, 1], fraction=0.046, pad=0.04)
    cb.set_ticks([0, 1])
    cb.set_ticklabels(["control (0)", "permit (1)"])

    plt.show()

def plot_atlas_timeline(npz_path, every=1):
    d = np.load(npz_path)
    years = d["years"]

    for i in range(0, len(years), every):
        plot_saved_atlas(npz_path, year_index=i)



# -------------------------
# Backward-compatible wrapper
# -------------------------

def animate_snapshots(npz_path, field="eco", interval=200):
    """
    Backward-compatible alias for older code.
    Equivalent to animate_field(npz_path, field=field, interval=interval).
    """
    return animate_field(npz_path, field=field, interval=interval)



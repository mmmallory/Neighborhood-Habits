# Composting Mathematics ABM

Agent-based model accompanying the paper:

> **Composting Mathematics: Cascading Processes of Composition and Decomposition in an Era of Climate Crisis**

The model simulates a residential neighborhood as a 2-D grid of cells, each occupied by an agent who decides each year whether to control (mow, spray) or permit ecological growth. A subset of agents practice active gardening, which accelerates ecological recovery and gradually shifts the latent regenerative potential of their cell. Bird populations respond slowly to sustained habitat improvement and, under sufficiently healthy conditions, feed back positively into the ecosystem.

---

## Files

- `agent.py` — Agent: perception, habit learning, gardening adoption
- `cell.py` — Grid cell: ecological state, bird dynamics, spatial diffusion
- `neighborhood.py` — Spatial grid: turnover, stepping, gardener seeding
- `main.py` — Single-run entry point: outputs CSV metrics and NPZ snapshots
- `visualize.py` — Static plots, 2×2 atlases, and animations from saved snapshots
- `sensitivity.py` — Sobol sensitivity analysis over seven model parameters; computationally intensive — expect several hours on a standard laptop at default settings
- `monte_carlo_analysis.py` — Monte Carlo ensemble near the tipping region; measures functional ecological recovery and social practice shift across 30 replicates × 11 gardener fractions at 100 years each

---

## Requirements

Python 3.9 or later is recommended.

```bash
pip install -r requirements.txt
```

---

## Running the model

### Single run

```bash
python main.py
```

Model parameters (grid size, years, initial gardener fraction) are set at the top of `main.py`. Running the script writes `run_metrics.csv` and `snapshots.npz`.

### Sobol sensitivity analysis

```bash
python sensitivity.py
```

### Monte Carlo ensemble

```bash
python monte_carlo_analysis.py
```

---

## Citation

If you use this code in your research, please cite:

```bibtex
@article{AUTHOR_YEAR,
  author  = {Mallory Mattimore-Malan},
  title   = {Composting Mathematics: Cascading Processes of Composition
             and Decomposition in an Era of Climate Crisis},
  journal = {},
  year    = {},
  volume  = {},
  pages   = {},
  doi     = {https://doi.org/10.5281/zenodo.19371296}
}
```

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

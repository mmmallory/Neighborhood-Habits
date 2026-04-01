#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cell.py — Grid cell holding ecological state and an optional resident agent.
 
Each cell tracks:
  - eco_state    : current ecological viability [0, 1]
  - regen_bias   : latent regenerative regime (seed banks, soil chemistry,
                   invasive pressure) [-1, 1]
  - bird_index   : local bird population index [0, 1]
  - management   : signal written by the agent each step
                   (-1 control, +1 permit, 0 none)
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import random
from agent import Agent


class Cell:
    def __init__(self, x, y, agent=None):
        self.x = x
        self.y = y
        self.agent = agent
        # Current ecological viability
        self.eco_state = random.uniform(0.2, 0.8)
        # Latent ecological regime (e.g. seed banks, soil chemistry, invasive pressure)
        self.regen_bias = random.uniform(-1.0, 1.0)
        # Change in eco-state
        self.last_eco_state = self.eco_state
        # Bird population index (initial)
        self.bird_index = random.uniform(0.2, 0.5)
        self.bird_memory = 0
        self.management = 0  # -1 control, +1 permit, 0 none

    def is_gardened(self):
        return self.agent is not None and self.agent.gardening == 1

    def agent_step(self, neighborhood):
        if self.agent is not None:
            self.agent.step(self, neighborhood)

    def ecology_step(self):
        """Local ecology dynamics.
        - All cells pay a baseline maintenance cost (decay).
        - All cells can recover contingent on regen_bias (history/potential).
        - Gardening boosts recovery and slowly increases regen_bias (legacy).
        """
        decay_rate = 0.01
        max_recovery = 0.03

        # 1) Decay
        self.eco_state -= decay_rate

        # 2) Management effects
        if self.management == -1:
            self.eco_state += 0.005      # looks tidy (short-term)
            self.regen_bias -= 0.008      # long-term hidden cost
        elif self.management == +1:
            self.regen_bias += 0.003       # slow/latent benefit from permissive practices

        # 3) Gardening
        recovery_multiplier = 1.0
        if self.is_gardened():
            recovery_multiplier *= 1.3
            self.regen_bias += 0.04  # strong - reflects deliberate ecological restoration, not just casual gardening

        if self.eco_state > 0.1:
            recovery = (
                max_recovery
                * recovery_multiplier
                * max(0.0, self.regen_bias)
            )
            self.eco_state += recovery

        # 4) Enforce bounds & reset
        self.eco_state = max(0.0, min(1.0, self.eco_state))
        self.regen_bias = max(-1.0, min(1.0, self.regen_bias))
        self.management = 0

    def bird_step(self):
        """ Birds respond slowly to sustained ecological conditions.
        Gardening increases the probability of improvement.
        """
        # Decay rate based on 25% decline seen across previous 50 years
        baseline_factor = 0.75 ** (1 / 50)  # ~0.99426
        self.bird_index *= baseline_factor

        # Habitat stress from degraded ecosystem
        stress_factor = 1.0
        if self.eco_state < 0.4:
            stress_factor *= (baseline_factor ** 2) / baseline_factor  # approx "double" decline
        self.bird_index *= stress_factor

        # As ecosystems improve, they can accomodate more/diversified birds
        if self.eco_state > self.last_eco_state:  # track changes
            self.bird_memory += 1
        else:
            self.bird_memory = max(0, self.bird_memory - 1)

        # gardening brings about better conditions for birds
        if self.agent and self.agent.gardening:
            self.bird_memory += 0.5

        # probability of increase grows with memory AND habitat quality
        habitat = min(1.0, max(0.0, (self.eco_state - 0.2) / 0.8))
        prob_increase = min(0.05 * self.bird_memory, 0.3) * habitat

        if random.random() < prob_increase:
            self.bird_index += random.uniform(0.02, 0.05)

        # In very healthy ecosystems, birds contribute back to a thriving ecology
        if self.eco_state > 0.7 and self.bird_index > 0.5 and self.bird_memory > 6:
            self.eco_state += 0.005
            self.regen_bias += 0.002

        # Enforce bounds
        self.eco_state = max(0.0, min(1.0, self.eco_state))
        self.regen_bias = max(-1.0, min(1.0, self.regen_bias))
        self.bird_index = max(0.0, min(1.0, self.bird_index))

    def diffusion_step(self, neighbors):
        """ A cell borrows a little ecological viability from its neighbors, but cannot escape its own regime
        """
        if not neighbors:
            return
        diffusion_rate = 0.05  # deliberately small
        neighbor_mean = sum(n.eco_state for n in neighbors) / len(neighbors)
        bias_diffusion = 0.01
        neighbor_bias_mean = sum(n.regen_bias for n in neighbors) / len(neighbors)
        self.regen_bias += bias_diffusion * (neighbor_bias_mean - self.regen_bias)

        # Move slightly toward neighbor mean
        delta = diffusion_rate * (neighbor_mean - self.eco_state)
        self.eco_state += delta

        # Enforce bounds
        self.eco_state = max(0.0, min(1.0, self.eco_state))
        self.regen_bias = max(-1.0, min(1.0, self.regen_bias))

    # debug
    def get_state(self):
        return {
            "x": self.x,
            "y": self.y,
            "eco-state": self.eco_state
        }


def cell_factory(x, y):
    return Cell(x, y, agent=Agent())



   
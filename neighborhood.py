#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
neighborhood.py — Spatial grid managing cells, agents, and simulation stepping.
 
The Neighborhood holds a 2-D grid of Cell objects and coordinates each
annual time step: demographic turnover, agent decisions, ecological dynamics,
bird dynamics, and spatial diffusion.
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import numpy as np
import random


class Neighborhood:
    def __init__(self, width, height, cell_factory):
        self.width = width
        self.height = height
        self.grid = np.empty((height, width), dtype=object)
        self.year = 0

        # Annual probability an agent is replaced (e.g., 0.02 ~ avg 50-year tenure)
        self.turnover_rate = 0.02
        # How strongly a newcomer inherits local norms (0=no inheritance, 1=full)
        self.inherit_weight = 0.6

        # Gardening parameters used for newcomer recruitment (set in main.py)
        self.newcomer_gardener_fraction = 0.05
        self.gardening_year_range = (5, 7)

        # initialize grid
        for y in range(height):
            for x in range(width):
                self.grid[y, x] = cell_factory(x, y)

    def get_neighbors(self, x, y):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append(self.grid[ny, nx])
        return neighbors

    def turnover_step(self):
        """
        Demographic turnover: with probability turnover_rate, replace the agent in a cell.
        The new agent partially inherits norms from neighboring agents (cultural transmission).
        Newcomers can adopt gardening after their first (silent) year via Agent.step().
        """
        # local import avoids circular imports at module load time
        from agent import Agent

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y, x]
                if cell.agent is None:
                    continue

                if random.random() < self.turnover_rate:
                    neighbors = self.get_neighbors(x, y)
                    neighbor_agents = [
                        n.agent for n in neighbors
                        if hasattr(n, "agent") and n.agent is not None
                    ]

                    newcomer = Agent()
                    if neighbor_agents:
                        newcomer.inherit_from_neighbors(neighbor_agents, weight=self.inherit_weight)

                    # Mark as newcomer so they can be recruited into gardening after move-in delay
                    newcomer.is_newcomer = True
                    newcomer.newcomer_gardening_checked = False

                    cell.agent = newcomer

    def step(self):
        # 0 Demographic turnover (people move in/out)
        self.turnover_step()
        
        # 1. Agent decisions
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y, x]
                if cell.agent is not None:
                    cell.agent.step(cell, self)

        # 2. Local ecology and bird dynamics
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y, x].ecology_step()

        for y in range(self.height):
            for x in range(self.width):
                self.grid[y, x].bird_step()

        # 3. Spatial diffusion
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y, x].diffusion_step(self.get_neighbors(x, y))

        # 4. Update last_eco_state at the end of the yearly cycle (after diffusion)
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y, x]
                cell.last_eco_state = cell.eco_state

        self.year += 1

    def seed_gardeners(self, gardener_fraction, gardening_year_range):
        """Randomly assigns a fraction of agents as gardeners (initial condition)."""
        min_years, max_years = gardening_year_range
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y, x]
                if cell.agent is None:
                    continue
                if random.random() < gardener_fraction:
                    cell.agent.gardening = 1
                    cell.agent.gardening_years_remaining = random.randint(min_years, max_years)


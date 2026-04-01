#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent.py — Resident agent with perceptually guided action and emergent habit.
 
Perception:  Agents perceive changes in eco-state, but not perfectly.
Action:      Agents choose to control (mow, spray) or permit growth based on
             perception and sensitivity.
Habit:       Learned bias toward control under perceived worsening.
Gardening:   Seeded in main.py; newcomers are recruited; adoption is driven
             by perceived neighbor benefits.
 
Notes
-----
- Move-in delay: if last_signal is None, the agent records a baseline and
  does not act.
- Newcomer recruitment happens on the first *active* year after move-in delay.
 
Part of: Composting Mathematics: Cascading Processes of Composition and
         Decomposition in an Era of Climate Crisis
Author: M.M-M.
"""

import random


class Agent:
    def __init__(self):
        # -------------------------
        # Core practice + perception
        # -------------------------
        P_CONTROL_INIT = 0.7  # tune: 0.7–0.95 baseline norm for control
        self.practice = 0 if random.random() < P_CONTROL_INIT else 1  # 0=control, 1=permit

        self.sensitivity = random.uniform(0.2, 0.8)   # detection threshold
        self.peer_influence = 0.2                      # probability of copying neighbors per step
        self.last_signal = None                        # perceptual baseline / memory

        # -----------
        # Gardening
        # -----------
        self.gardening = 0
        self.gardening_years_remaining = 0
        self.gardening_permit_bias = 0.10              # gardeners slightly more likely to permit

        # -----------------
        # Habit + learning
        # -----------------
        self.habit = random.uniform(0.6, 0.9)          # P(control | worsening)
        self.learning_rate = 0.05
        self.prev_action = None

        # ----------------
        # Bird perception
        # ----------------
        self.last_bird_signal = None

        # --------------------------
        # Turnover/newcomer tracking
        # --------------------------
        self.is_newcomer = False
        self.newcomer_gardening_checked = False

    # ----------------------------
    # Turnover cultural inheritance
    # ----------------------------
    def inherit_from_neighbors(self, neighbor_agents, weight=0.6):
        """
        Cultural inheritance for demographic turnover.
        weight=0 => newcomer stays random
        weight=1 => newcomer matches local norms (in expectation)
        """
        if not neighbor_agents:
            return

        mean_practice = sum(a.practice for a in neighbor_agents) / len(neighbor_agents)  # frac permit
        mean_habit = sum(a.habit for a in neighbor_agents) / len(neighbor_agents)
        mean_sens = sum(a.sensitivity for a in neighbor_agents) / len(neighbor_agents)

        # Practice: probabilistic adoption of local norm
        if random.random() < weight:
            self.practice = 1 if random.random() < mean_practice else 0

        # Habit: blend toward local mean
        self.habit = (1.0 - weight) * self.habit + weight * mean_habit

        # Sensitivity: mild blending to keep some individual variation
        sens_w = 0.3 * weight
        self.sensitivity = (1.0 - sens_w) * self.sensitivity + sens_w * mean_sens

        # Gardening not inherited
        self.gardening = 0
        self.gardening_years_remaining = 0

        # Reset personal memories (new person)
        self.last_signal = None
        self.prev_action = None
        self.last_bird_signal = None

    # ----------------
    # Perception helpers
    # ----------------
    def perceive_birds(self, cell) -> float:
        """Return perceived change in bird_index since last step."""
        current = cell.bird_index
        if self.last_bird_signal is None:
            self.last_bird_signal = current
            return 0.0
        delta = current - self.last_bird_signal
        self.last_bird_signal = current
        return delta

    # -----------------------------
    # Gardening adoption mechanisms
    # -----------------------------
    def maybe_recruit_newcomer_into_gardening(self, neighborhood):
        """
        Exogenous reseeding mechanism: newcomers have some chance of becoming gardeners
        on their first *active* year after move-in delay.
        """
        if not self.is_newcomer or self.newcomer_gardening_checked:
            return
        self.newcomer_gardening_checked = True

        if self.gardening == 1:
            return

        p = getattr(neighborhood, "newcomer_gardener_fraction", 0.03)
        if random.random() < p:
            self.gardening = 1
            min_years, max_years = getattr(neighborhood, "gardening_year_range", (5, 7))
            self.gardening_years_remaining = random.randint(min_years, max_years)

        # After first active year, they are no longer "new" for recruitment purposes
        self.is_newcomer = False

    def maybe_adopt_gardening_from_neighbors(self, cell, neighborhood, neighbors):
        """
        Endogenous gardening uptake based on perceived neighbor benefit.
        (Optional; keep it conservative.)
        """
        if self.gardening == 1:
            return

        adoption_check_rate = getattr(neighborhood, "adoption_check_rate", 0.25)
        if random.random() > adoption_check_rate:
            return

        gardener_cells = [
            n for n in neighbors
            if getattr(n, "agent", None) is not None and n.agent.gardening == 1
        ]
        if not gardener_cells:
            return

        mean_g_eco = sum(n.eco_state for n in gardener_cells) / len(gardener_cells)
        mean_g_birds = sum(n.bird_index for n in gardener_cells) / len(gardener_cells)

        benefit = 0.7 * (mean_g_eco - cell.eco_state) + 0.3 * (mean_g_birds - cell.bird_index)

        benefit_threshold = getattr(neighborhood, "benefit_threshold", 0.03)
        if benefit <= benefit_threshold:
            return

        base_adopt = getattr(neighborhood, "base_adopt", 0.05)
        scale = getattr(neighborhood, "adopt_scale", 0.30)
        p_adopt = min(base_adopt + scale * benefit, 0.5)

        if random.random() < p_adopt:
            self.gardening = 1
            min_years, max_years = getattr(neighborhood, "gardening_year_range", (10, 20))
            self.gardening_years_remaining = random.randint(min_years, max_years)

    # ----
    # Step
    # ----
    def step(self, cell, neighborhood):
        """
        Perceptually guided action:
        - Sense a noisy signal of local conditions
        - Learn habit from whether last action preceded improvement/worsening
        - Choose practice based on perceived change + habit
        - Optionally imitate neighbors
        - Write management onto the cell (cell applies effects)
        - Update gardening persistence
        - Recruit newcomers and/or adopt gardening from neighbors
        """
        # 1) Perception noise (gardeners slightly more perceptive => less noise)
        noise = 0.01 if self.gardening == 1 else 0.02
        current_signal = cell.eco_state + random.uniform(-noise, noise)

        # Move-in delay: initialize baseline, no action
        if self.last_signal is None:
            self.last_signal = current_signal
            return

        # Gather neighbors once (used for both imitation and optional adoption)
        neighbors = neighborhood.get_neighbors(cell.x, cell.y)
        neighbor_agents = [n.agent for n in neighbors if getattr(n, "agent", None) is not None]

        # 1.5) Gardening pathways
            # Some new residents garden
        self.maybe_recruit_newcomer_into_gardening(neighborhood)

            # Some agents begin gardening based on the perceived benefits to their neighbors
        self.maybe_adopt_gardening_from_neighbors(cell, neighborhood, neighbors)

        perceived_change = current_signal - self.last_signal


        # 2) Habit learning: did my LAST action seem to help?
        if self.prev_action is not None:
            if perceived_change > 0:
                # things improved
                if self.prev_action == 0:   # control
                    self.habit = min(1.0, self.habit + self.learning_rate)
                else:                        # permit
                    self.habit = max(0.0, self.habit - self.learning_rate)
            elif perceived_change < 0:
                # things worsened
                if self.prev_action == 0:   # control
                    self.habit = max(0.0, self.habit - self.learning_rate)
                else:                        # permit
                    self.habit = min(1.0, self.habit + self.learning_rate)

        # 3) Sensitivity threshold
        threshold = self.sensitivity
        if self.gardening == 1:
            threshold *= 1.5  # gardeners tolerate small negative changes

        # 4) Action selection
        if perceived_change < -threshold:
            effective_habit = self.habit
            if self.gardening == 1:
                effective_habit *= 0.7  # gardeners slightly more permissive under worsening
            self.practice = 0 if random.random() < effective_habit else 1

        elif perceived_change > threshold:
            self.practice = 1
        # else inertia

        # 4a) Gardeners slightly more likely to permit
        if self.gardening == 1 and random.random() < self.gardening_permit_bias:
            self.practice = 1

        # 4b) Social diffusion of practice
        if neighbor_agents and random.random() < self.peer_influence:
            p_permit = sum(a.practice for a in neighbor_agents) / len(neighbor_agents)
            self.practice = 1 if random.random() < p_permit else 0

        # 5) Write action into world; applied later by ecology_step()
        cell.management = -1 if self.practice == 0 else +1

        # 6) Gardening countdown + persistence decision
        if self.gardening == 1:
            self.gardening_years_remaining = max(0, self.gardening_years_remaining - 1)
            bird_delta = self.perceive_birds(cell)

            if self.gardening_years_remaining <= 0:
                if bird_delta < -0.02:
                    quit_prob = 0.3
                elif bird_delta > 0.02:
                    quit_prob = 0.05
                else:
                    quit_prob = 0.15

                if random.random() < quit_prob:
                    self.gardening = 0
                    self.gardening_years_remaining = 0

        # 7) Update memories
        self.prev_action = self.practice
        self.last_signal = current_signal



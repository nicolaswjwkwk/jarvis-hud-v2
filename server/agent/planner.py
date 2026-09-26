from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PlannedStep:
    step: int
    action: str
    status: str = 'pending'


class AgentPlanner:
    def __init__(self, goal: str):
        self.goal = goal
        self.steps: List[PlannedStep] = []

    def plan(self, steps: List[str]) -> List[PlannedStep]:
        self.steps = [PlannedStep(step=index + 1, action=item) for index, item in enumerate(steps)]
        return self.steps

    def next(self) -> PlannedStep | None:
        for item in self.steps:
            if item.status == 'pending':
                return item
        return None


def build_default_plan(goal: str) -> List[dict]:
    planner = AgentPlanner(goal)
    return planner.plan([
        'Understand the request and safety constraints',
        'Gather context and memory',
        'Use the allowed tools and compose the answer',
        'Deliver the answer and log the final state',
    ])

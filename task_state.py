from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskStage(str, Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    DONE = "done"
    PAUSED = "paused"


STAGE_ORDER: list[TaskStage] = [
    TaskStage.PLANNING,
    TaskStage.EXECUTION,
    TaskStage.VALIDATION,
    TaskStage.DONE,
]


@dataclass
class TaskState:
    stage: TaskStage = TaskStage.PLANNING
    current_step: int = 0
    expected_action: str = ""
    paused_at_stage: TaskStage | None = None
    paused_at_step: int = 0

    def pause(self) -> None:
        if self.stage == TaskStage.PAUSED:
            return
        self.paused_at_stage = self.stage
        self.paused_at_step = self.current_step
        self.stage = TaskStage.PAUSED

    def resume(self) -> None:
        if self.stage != TaskStage.PAUSED or self.paused_at_stage is None:
            return
        self.stage = self.paused_at_stage
        self.current_step = self.paused_at_step
        self.paused_at_stage = None
        self.paused_at_step = 0

    def advance(self) -> None:
        if self.stage in (TaskStage.PAUSED, TaskStage.DONE):
            return
        idx = STAGE_ORDER.index(self.stage)
        if idx < len(STAGE_ORDER) - 1:
            self.stage = STAGE_ORDER[idx + 1]
            self.current_step = 0

    def to_context_string(self) -> str:
        if self.stage == TaskStage.PAUSED:
            lines = [
                f"Текущий этап задачи: ПАУЗА (возобновить с «{self.paused_at_stage.value}», шаг {self.paused_at_step})"
            ]
        else:
            lines = [
                f"Текущий этап задачи: {self.stage.value.upper()}",
                f"Текущий шаг: {self.current_step}",
            ]
        if self.expected_action:
            lines.append(f"Ожидаемое действие: {self.expected_action}")
        return "\n".join(lines)

    def to_state(self) -> dict:
        return {
            "stage": self.stage.value,
            "current_step": self.current_step,
            "expected_action": self.expected_action,
            "paused_at_stage": (
                self.paused_at_stage.value if self.paused_at_stage else None
            ),
            "paused_at_step": self.paused_at_step,
        }

    @classmethod
    def from_state(cls, data: dict) -> "TaskState":
        raw = data.get("paused_at_stage")
        return cls(
            stage=TaskStage(data.get("stage", "planning")),
            current_step=data.get("current_step", 0),
            expected_action=data.get("expected_action", ""),
            paused_at_stage=TaskStage(raw) if raw else None,
            paused_at_step=data.get("paused_at_step", 0),
        )

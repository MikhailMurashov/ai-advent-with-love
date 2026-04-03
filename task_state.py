from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TaskStage(str, Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    DONE = "done"


STAGE_ORDER: list[TaskStage] = [
    TaskStage.PLANNING,
    TaskStage.EXECUTION,
    TaskStage.VALIDATION,
    TaskStage.DONE,
]

STAGE_CONTRACTS: dict[TaskStage, str] = {
    TaskStage.PLANNING: (
        "Вход: описание задачи или материалы для работы.\n"
        "Задача: проанализировать код, декомпозировать на конкретные шаги, "
        "сформулировать критерии готовности.\n"
        "Выход: нумерованный список шагов, согласованный с пользователем.\n"
        "Не начинай реализацию — только план."
    ),
    TaskStage.EXECUTION: (
        "Вход: согласованный план. Последовательность шагов.\n"
        "Задача: реализовать весь план пошагово, объяснить решение.\n"
        "Выход: готовое решение для плана + очень краткое объяснение действий."
    ),
    TaskStage.VALIDATION: (
        "Вход: результат всех шагов выполнения.\n"
        "Задача: проверить соответствие критериям готовности из плана.\n"
        "Выход: чеклист ✅/❌ по каждому критерию + edge cases для проверки.\n"
        "Не считай задачу завершённой, пока пользователь не подтвердил все пункты.\n"
        "Если хотя бы один критерий ❌ — Предложи вернуться к EXECUTION с конкретным списком исправлений.\n"
    ),
    TaskStage.DONE: (
        "Задача завершена.\n"
        "Задача: подвести итог — что было сделано, какие решения приняты, что стоит учесть в будущем."
    ),
}


class TaskFSM:
    TRANSITIONS: dict[TaskStage, list[TaskStage]] = {
        TaskStage.PLANNING:   [TaskStage.EXECUTION],
        TaskStage.EXECUTION:  [TaskStage.VALIDATION],
        TaskStage.VALIDATION: [TaskStage.DONE, TaskStage.EXECUTION, TaskStage.PLANNING],
        TaskStage.DONE:       [],
    }

    def __init__(self, stage: TaskStage = TaskStage.PLANNING) -> None:
        self.stage = stage

    def can_transition(self, to: TaskStage) -> bool:
        return to in self.TRANSITIONS.get(self.stage, [])

    def transition(self, to: TaskStage) -> None:
        if not self.can_transition(to):
            raise ValueError(
                f"Недопустимый переход: {self.stage.value} → {to.value}"
            )
        self.stage = to

    def allowed(self) -> list[TaskStage]:
        return list(self.TRANSITIONS.get(self.stage, []))


@dataclass
class TaskState:
    stage: TaskStage = TaskStage.PLANNING
    _fsm: TaskFSM = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._fsm = TaskFSM(self.stage)

    def transition(self, to: TaskStage) -> None:
        self._fsm.transition(to)
        self.stage = self._fsm.stage

    def allowed(self) -> list[TaskStage]:
        return self._fsm.allowed()

    def to_context_string(self) -> str:
        lines = [
            f"Текущий этап задачи: {self.stage.value.upper()}",
        ]
        contract = STAGE_CONTRACTS.get(self.stage, "")
        if contract:
            lines.append(f"Контракт этапа:\n{contract}")

        return "\n".join(lines)

    def to_state(self) -> dict:
        return {"stage": self.stage.value}

    @classmethod
    def from_state(cls, data: dict) -> "TaskState":
        stage_value = data.get("stage", "planning")
        return cls(stage=TaskStage(stage_value))

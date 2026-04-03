from __future__ import annotations

import re
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
        "=== ЭТАП: ПЛАНИРОВАНИЕ ===\n"
        "ТЫ СЕЙЧАС ТОЛЬКО ПЛАНИРУЕШЬ. НЕ ПИШИ КОД. НЕ ВЫПОЛНЯЙ ЗАДАЧУ.\n"
        "Написать код или реализовать решение на этом этапе — ОШИБКА.\n"
        "\n"
        "ЧТО ДЕЛАТЬ:\n"
        "1. Разбери задачу на конкретные шаги (нумерованный список).\n"
        "2. Сформулируй критерии готовности — как поймём, что задача выполнена.\n"
        "3. Уточняй у пользователя, пока план не согласован.\n"
        "\n"
        "КАК ЗАКАНЧИВАТЬ КАЖДЫЙ ОТВЕТ:\n"
        "- Если план ещё не согласован: просто задай уточняющий вопрос.\n"
        "- Если пользователь согласился с планом: последняя строка ответа — ровно эти символы, "
        "скопированные без изменений, на латинице, без перевода на русский:\n"
        "[SUGGEST_TRANSITION: execution]\n"
        "Никакого текста после этой строки. Только она — последней строкой.\n"
        "НЕ ПЕРЕВОДИ МАРКЕР НА РУССКИЙ ЯЗЫК."
    ),
    TaskStage.EXECUTION: (
        "=== ЭТАП: ВЫПОЛНЕНИЕ ===\n"
        "ПЛАН УЖЕ СОГЛАСОВАН. ТВОЯ ЗАДАЧА — РЕАЛИЗОВАТЬ ЕГО ПОЛНОСТЬЮ.\n"
        "\n"
        "ЧТО ДЕЛАТЬ:\n"
        "1. Выполни КАЖДЫЙ шаг плана по порядку. Пропускать шаги ЗАПРЕЩЕНО.\n"
        "2. Кратко объясни, что сделал на каждом шаге.\n"
        "3. Дай готовый результат.\n"
        "\n"
        "СТРОГО ЗАПРЕЩЕНО:\n"
        "- Пропускать шаги плана по любой причине.\n"
        "- Писать фразы вида «пропустим этот шаг», «примем за данность», "
        "«несмотря на отсутствие X», «условно считаем выполненным».\n"
        "- Самостоятельно решать, что шаг можно не делать.\n"
        "Если шаг невозможно выполнить — явно сообщи об этом пользователю и жди указаний.\n"
        "\n"
        "КАК ЗАКАНЧИВАТЬ КАЖДЫЙ ОТВЕТ:\n"
        "Последняя строка ответа — ровно эти символы, скопированные без изменений, "
        "на латинице, без перевода на русский:\n"
        "[SUGGEST_TRANSITION: validation]\n"
        "Никакого текста после этой строки. Только она — последней строкой.\n"
        "НЕ ПЕРЕВОДИ МАРКЕР НА РУССКИЙ ЯЗЫК.\n"
        "Это ОБЯЗАТЕЛЬНО в каждом ответе на этом этапе."
    ),
    TaskStage.VALIDATION: (
        "=== ЭТАП: ПРОВЕРКА ===\n"
        "ВЫПОЛНЕНИЕ ЗАВЕРШЕНО. ТВОЯ ЗАДАЧА — ПРОВЕРИТЬ РЕЗУЛЬТАТ ЧЕСТНО.\n"
        "\n"
        "ЧТО ДЕЛАТЬ:\n"
        "1. Возьми критерии готовности из плана.\n"
        "2. По каждому критерию поставь ✅ (выполнено) или ❌ (не выполнено).\n"
        "3. Укажи edge cases — граничные случаи для проверки.\n"
        "\n"
        "СТРОГО ЗАПРЕЩЕНО:\n"
        "- Ставить ✅ там, где проверка не проводилась.\n"
        "- Писать фразы вида «несмотря на отсутствие тестирования», "
        "«принимаем решение о завершении», «условно считаем выполненным», "
        "«в данном контексте проверка невозможна».\n"
        "- Самостоятельно решать, что этап завершён. Это решает ТОЛЬКО пользователь.\n"
        "Если проверка невозможна — явно сообщи об этом и жди решения пользователя.\n"
        "\n"
        "КАК ЗАКАНЧИВАТЬ КАЖДЫЙ ОТВЕТ:\n"
        "Последняя строка — ровно одна из этих строк, скопированная без изменений, "
        "на латинице, без перевода на русский:\n"
        "- Если все критерии ✅ и пользователь явно подтвердил:\n"
        "[SUGGEST_TRANSITION: done]\n"
        "- Если есть ❌ или нужны исправления:\n"
        "[SUGGEST_TRANSITION: execution]\n"
        "Никакого текста после этих строк. Только одна из них — последней строкой.\n"
        "НЕ ПЕРЕВОДИ МАРКЕР НА РУССКИЙ ЯЗЫК.\n"
        "Это ОБЯЗАТЕЛЬНО в каждом ответе на этом этапе."
    ),
    TaskStage.DONE: (
        "=== ЭТАП: ЗАВЕРШЕНО ===\n"
        "ЗАДАЧА ВЫПОЛНЕНА И ПРОВЕРЕНА.\n"
        "\n"
        "ЧТО ДЕЛАТЬ:\n"
        "1. Подведи итог: что было сделано.\n"
        "2. Перечисли ключевые решения, которые были приняты.\n"
        "3. Отметь, что стоит учесть в будущем.\n"
        "\n"
        "Отвечай на вопросы пользователя по результату работы."
    ),
}

_SUGGEST_RE = re.compile(
    r"\[(?:SUGGEST_TRANSITION|Суггест_транзит|СУГГЕСТ_ТРАНЗИТ|suggest.transition):\s*(\w+)\]",
    re.IGNORECASE,
)


_STAGE_ALIASES: dict[str, TaskStage] = {
    "planning": TaskStage.PLANNING,
    "планирование": TaskStage.PLANNING,
    "execution": TaskStage.EXECUTION,
    "выполнение": TaskStage.EXECUTION,
    "реализация": TaskStage.EXECUTION,
    "validation": TaskStage.VALIDATION,
    "проверка": TaskStage.VALIDATION,
    "валидация": TaskStage.VALIDATION,
    "done": TaskStage.DONE,
    "завершено": TaskStage.DONE,
    "готово": TaskStage.DONE,
}


def parse_transition_suggestion(content: str) -> TaskStage | None:
    """Извлекает предложенный этап из маркера [SUGGEST_TRANSITION: stage] в тексте."""
    m = _SUGGEST_RE.search(content)
    if not m:
        return None
    raw = m.group(1).lower()
    return _STAGE_ALIASES.get(raw)


def strip_transition_marker(content: str) -> str:
    """Удаляет маркер [SUGGEST_TRANSITION: ...] из текста перед отображением."""
    return _SUGGEST_RE.sub("", content).strip()


class TaskFSM:
    TRANSITIONS: dict[TaskStage, list[TaskStage]] = {
        TaskStage.PLANNING: [TaskStage.EXECUTION],
        TaskStage.EXECUTION: [TaskStage.VALIDATION],
        TaskStage.VALIDATION: [TaskStage.DONE, TaskStage.EXECUTION, TaskStage.PLANNING],
        TaskStage.DONE: [],
    }

    def __init__(self, stage: TaskStage = TaskStage.PLANNING) -> None:
        self.stage = stage

    def can_transition(self, to: TaskStage) -> bool:
        return to in self.TRANSITIONS.get(self.stage, [])

    def transition(self, to: TaskStage) -> None:
        if not self.can_transition(to):
            raise ValueError(f"Недопустимый переход: {self.stage.value} → {to.value}")
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

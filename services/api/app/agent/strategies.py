from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum


class StrategyType(str, Enum):
    SLIDING_WINDOW_SUMMARY = "sliding_window_summary"
    BRANCHING = "branching"


class BaseStrategy(ABC):
    """Abstract base for all context management strategies."""

    CONTEXT_WINDOW: int = 10

    def __init__(self, system_prompt: str = "") -> None:
        self.system_prompt: str = system_prompt
        self._history: list[dict[str, str]] = []

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    def add_message(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content})

    def get_context(self) -> list[dict[str, str]]:
        """Return messages list ready to send to LLM (without system prompt)."""
        return list(self._history[-self.CONTEXT_WINDOW :])

    def should_summarize(self) -> bool:
        return False

    @abstractmethod
    def to_state(self) -> dict:
        """Serialize strategy-specific state to a plain dict."""

    @classmethod
    @abstractmethod
    def from_state(cls, system_prompt: str, state: dict) -> "BaseStrategy":
        """Restore a strategy instance from a previously serialized state dict."""


class SlidingWindowSummaryStrategy(BaseStrategy):
    """Sliding window with auto-summarization."""

    CONTEXT_WINDOW = 100

    def __init__(
        self, system_prompt: str = "", summarization_enabled: bool = True
    ) -> None:
        super().__init__(system_prompt)
        self._summary: str = ""
        self._summarized_count: int = 0
        self.summarization_enabled: bool = summarization_enabled

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def summarized_count(self) -> int:
        return self._summarized_count

    def should_summarize(self) -> bool:
        return (
            self.summarization_enabled
            and len(self._history) > self.CONTEXT_WINDOW
            and len(self._history) - self._summarized_count > self.CONTEXT_WINDOW
        )

    def get_context(self) -> list[dict[str, str]]:
        return list(self._history[-self.CONTEXT_WINDOW :])

    def get_summary_context(self) -> list[dict[str, str]]:
        """Return messages that need to be summarized."""
        return self._history[self._summarized_count : -self.CONTEXT_WINDOW]

    def apply_summary(self, summary: str) -> None:
        self._summary = summary
        self._summarized_count = len(self._history) - self.CONTEXT_WINDOW

    def build_messages(self, full_system_prompt: str) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if full_system_prompt:
            messages.append({"role": "system", "content": full_system_prompt})
        if self._summary and self.summarization_enabled:
            messages.append(
                {
                    "role": "system",
                    "content": f"Саммари предыдущей беседы:\n{self._summary}",
                }
            )
        messages.extend(self.get_context())
        return messages

    def to_state(self) -> dict:
        return {
            "summary": self._summary,
            "summarized_count": self._summarized_count,
            "history": list(self._history),
            "summarization_enabled": self.summarization_enabled,
        }

    @classmethod
    def from_state(
        cls, system_prompt: str, state: dict
    ) -> "SlidingWindowSummaryStrategy":
        instance = cls(
            system_prompt=system_prompt,
            summarization_enabled=state.get("summarization_enabled", True),
        )
        instance._summary = state.get("summary", "")
        instance._summarized_count = state.get("summarized_count", 0)
        instance._history = list(state.get("history", []))
        return instance


@dataclass
class Branch:
    branch_id: str
    name: str
    checkpoint_index: int
    history: list


class BranchingStrategy(BaseStrategy):
    """Conversation branching: trunk + named branches."""

    CONTEXT_WINDOW = 10

    def __init__(self, system_prompt: str = "", window_size: int = 10) -> None:
        super().__init__(system_prompt)
        self._trunk: list[dict[str, str]] = []
        self._branches: dict[str, Branch] = {}
        self._active_branch_id: str | None = None
        self._window_size: int = window_size

    @property
    def history(self) -> list[dict[str, str]]:
        if self._active_branch_id and self._active_branch_id in self._branches:
            branch = self._branches[self._active_branch_id]
            return list(self._trunk[: branch.checkpoint_index] + branch.history)
        return list(self._trunk)

    def _active_list(self) -> list[dict[str, str]]:
        if self._active_branch_id and self._active_branch_id in self._branches:
            return self._branches[self._active_branch_id].history
        return self._trunk

    def add_message(self, role: str, content: str) -> None:
        self._active_list().append({"role": role, "content": content})

    def get_context(self) -> list[dict[str, str]]:
        return list(self.history[-self._window_size :])

    def build_messages(self, full_system_prompt: str) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if full_system_prompt:
            messages.append({"role": "system", "content": full_system_prompt})
        messages.extend(self.get_context())
        return messages

    def create_branch(self, name: str) -> str:
        branch_id = str(uuid.uuid4())
        branch = Branch(
            branch_id=branch_id,
            name=name,
            checkpoint_index=len(self.history),
            history=[],
        )
        self._branches[branch_id] = branch
        self._active_branch_id = branch_id
        return branch_id

    def switch_branch(self, branch_id: str | None) -> None:
        if branch_id is None or branch_id in self._branches:
            self._active_branch_id = branch_id
        else:
            logging.warning(f"strategies: branch {branch_id!r} not found")

    def delete_branch(self, branch_id: str) -> None:
        self._branches.pop(branch_id, None)
        if self._active_branch_id == branch_id:
            self._active_branch_id = None

    def to_state(self) -> dict:
        return {
            "window_size": self._window_size,
            "trunk": list(self._trunk),
            "branches": {bid: asdict(b) for bid, b in self._branches.items()},
            "active_branch_id": self._active_branch_id,
        }

    @classmethod
    def from_state(cls, system_prompt: str, state: dict) -> "BranchingStrategy":
        instance = cls(
            system_prompt=system_prompt, window_size=state.get("window_size", 10)
        )
        instance._trunk = list(state.get("trunk", []))
        instance._active_branch_id = state.get("active_branch_id")
        for bid, bdata in state.get("branches", {}).items():
            instance._branches[bid] = Branch(
                branch_id=bdata["branch_id"],
                name=bdata["name"],
                checkpoint_index=bdata["checkpoint_index"],
                history=list(bdata.get("history", [])),
            )
        return instance


def make_strategy(
    strategy_type: str,
    system_prompt: str = "",
    state: dict | None = None,
) -> BaseStrategy:
    """Factory: create or restore a strategy instance."""
    if state is not None:
        if strategy_type == StrategyType.SLIDING_WINDOW_SUMMARY:
            return SlidingWindowSummaryStrategy.from_state(system_prompt, state)
        if strategy_type == StrategyType.BRANCHING:
            return BranchingStrategy.from_state(system_prompt, state)

    if strategy_type == StrategyType.SLIDING_WINDOW_SUMMARY:
        return SlidingWindowSummaryStrategy(system_prompt=system_prompt)
    if strategy_type == StrategyType.BRANCHING:
        return BranchingStrategy(system_prompt=system_prompt)

    raise ValueError(f"Unknown strategy type: {strategy_type}")

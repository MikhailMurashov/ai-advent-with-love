import time
from dataclasses import dataclass

import litellm
from config import LLM_MODEL, API_KEY


@dataclass
class ChatResponse:
    content: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    elapsed_s: float
    tool_calls: list | None = None


def chat(
    messages: list[dict[str, str]],
    model: str = LLM_MODEL,
    tools: list | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    max_tokens: int | None = None,
    seed: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    stop: list[str] | None = None,
) -> ChatResponse:
    """Простой чат с lmm.

    Args:
        messages: Список сообщений в контексте с ролью.
        temperature: Насколько «творчески» модель подбирает слова (0.0–2.0).
            При 0.0 ответ почти всегда одинаковый и предсказуемый.
            При 1.0 — стандартное поведение модели.
            При 2.0 — очень разнообразно, но может быть бессвязно.
        top_p: Альтернативный способ контролировать разнообразие (0.0–1.0).
            Модель на каждом шаге выбирает следующее слово из «топа» вариантов,
            пока их суммарная вероятность не достигнет p.
            При 0.1 — только самые очевидные слова, при 1.0 — все варианты.
            Обычно достаточно менять либо temperature, либо top_p, не оба сразу.
        top_k: Жёсткое ограничение: на каждом шаге модель выбирает только из k
            наиболее вероятных следующих слов. При top_k=1 — всегда самое
            вероятное слово (детерминированно). При top_k=50 — из 50 вариантов.
        max_tokens: Максимальная длина ответа в токенах. Токен — это примерно
            0.75 слова (или 3–4 символа). 300 токенов ≈ 200–250 слов.
            Если ответ обрывается на полуслове — увеличьте это значение.
        seed: Целое число для фиксации случайности. При одинаковом seed и
            одинаковых параметрах модель даёт воспроизводимый результат.
            Удобно для отладки или сравнения разных промптов.
        presence_penalty: Штрафует модель за повторное упоминание тем,
            которые уже встречались в тексте (-2.0–2.0).
            Положительные значения (например, 0.5) заставляют модель
            говорить о новом, отрицательные — наоборот, зацикливаться.
        frequency_penalty: Штрафует за повторение конкретных слов пропорционально
            тому, сколько раз они уже использовались (-2.0–2.0).
            Помогает избежать однообразных текстов вида «добавьте, добавьте,
            добавьте». Обычно достаточно значений 0.1–0.5.

    Returns:
        ChatResponse с полями:
          - content (str): текст ответа
          - prompt_tokens (int): число токенов в запросе
          - completion_tokens (int): число токенов в ответе
          - total_tokens (int): суммарное число токенов
          - elapsed_s (float): время выполнения запроса в секундах
    """

    t0 = time.time()
    is_gigachat = model.startswith("gigachat/")
    response = litellm.completion(
        model=model,
        api_key=None if is_gigachat else API_KEY,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_tokens=max_tokens,
        seed=seed,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        stop=stop,
        messages=messages,
        **({"tools": tools} if tools else {}),
        **({"ssl_verify": False} if is_gigachat else {}),
    )
    elapsed_s = time.time() - t0

    msg = response.choices[0].message  # type: ignore[union-attr]
    u = response.usage  # type: ignore[union-attr]
    tool_calls = msg.tool_calls if hasattr(msg, "tool_calls") else None
    return ChatResponse(
        content=msg.content or "",
        prompt_tokens=u.prompt_tokens if u else None,
        completion_tokens=u.completion_tokens if u else None,
        total_tokens=u.total_tokens if u else None,
        elapsed_s=elapsed_s,
        tool_calls=tool_calls or None,
    )

import argparse

from llm_client import generate_recipe


def parse_args():
    parser = argparse.ArgumentParser(
        description="Генератор рецептов на основе ингредиентов"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Температура генерации (0.0–2.0). Контролирует случайность: ниже = детерминированнее.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        help="Nucleus sampling (0.0–1.0). Оставляет только токены с суммарной вероятностью p.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        help="Ограничивает выбор следующего токена топ-k вариантами.",
    )
    parser.add_argument(
        "--max-tokens", type=int, help="Максимальное количество токенов в ответе."
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Фиксирует случайность генерации для воспроизводимости.",
    )
    parser.add_argument(
        "--presence-penalty",
        type=float,
        help="Штраф за повторное упоминание тем (-2.0–2.0).",
    )
    parser.add_argument(
        "--frequency-penalty",
        type=float,
        help="Штраф за повторение токенов по частоте (-2.0–2.0).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    llm_params = {k: v for k, v in vars(args).items() if v is not None}

    print("Генератор рецептов (Ctrl+C для выхода)")
    while True:
        try:
            ingredients = input("\nВведите название блюда или ингредиенты: ").strip()
            if not ingredients:
                continue
            print("\nГенерирую рецепт...\n")
            print(generate_recipe(ingredients, **llm_params))
        except KeyboardInterrupt:
            print("\nДо свидания!")
            break


if __name__ == "__main__":
    main()

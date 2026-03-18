import argparse

from llm_client import chat


def parse_args():
    parser = argparse.ArgumentParser(description="Интерактивный чат с LLM")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--presence-penalty", type=float)
    parser.add_argument("--frequency-penalty", type=float)
    parser.add_argument("--stop", type=str)
    return parser.parse_args()


def main():
    args = parse_args()
    llm_params = {k: v for k, v in vars(args).items() if v is not None}

    system_prompt = input("Системный промпт (оставьте пустым для пропуска): ").strip()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    print("\nЧат начат. Введите пустую строку, 'quit' или 'exit' для выхода.\n")
    while True:
        try:
            user_input = input("Вы: ").strip()
            if not user_input or user_input.lower() in ("quit", "exit"):
                print("До свидания!")
                break
            messages.append({"role": "user", "content": user_input})
            reply = chat(messages, **llm_params)
            print(f"\nАссистент: {reply}\n")
            messages.append({"role": "assistant", "content": reply})
        except KeyboardInterrupt:
            print("\nДо свидания!")
            break


if __name__ == "__main__":
    main()

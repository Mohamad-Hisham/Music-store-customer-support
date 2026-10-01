"""Command-line interface for the customer-support workflow."""

import argparse

from .app import create_support_app, resume_conversation, start_conversation


def main() -> None:
    parser = argparse.ArgumentParser(description="Music store customer support")
    parser.add_argument("question", nargs="?", help="A customer question")
    parser.add_argument("--thread-id", default="terminal-demo")
    args = parser.parse_args()

    app = create_support_app()
    question = args.question or input("Customer: ")
    result = start_conversation(app, question, args.thread_id)
    while result.get("__interrupt__"):
        print(f"Support: {result['__interrupt__'][0].value}")
        result = resume_conversation(app, input("Customer: "), args.thread_id)
    print(f"Support: {result['final_response']}")


if __name__ == "__main__":
    main()
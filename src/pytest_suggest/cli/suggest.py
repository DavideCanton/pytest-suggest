from argparse import ArgumentParser
from pathlib import Path

from pytest_suggest.constants import FILE_NAME
from pytest_suggest.trie import Trie


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()

    subparsers = parser.add_subparsers(dest="action", required=True)

    suggest = subparsers.add_parser("suggest", help="Provide suggestions")
    suggest.add_argument("prefix", type=str, help="Prefix to search for")

    autocompletion = subparsers.add_parser(
        "autocompletion", help="Set autocompletion script"
    )
    autocompletion.add_argument(
        "shell",
        choices=["bash", "powershell"],
        help="The shell type for the autocompletion script",
    )

    return parser


def print_suggestions(prefix: str) -> None:
    with open(FILE_NAME, "rb") as f:
        trie = Trie.load(f)

    for w in sorted(trie.words(prefix)):
        print(w)


def emit_autocomplete_script(shell: str) -> None:
    scripts_folder = Path(__file__).parent.parent / "scripts"

    if shell == "bash":
        file = "pytest-mycompletion.sh"
    elif shell == "powershell":
        file = "pytest-mycompletion.ps1"
    else:
        # should not be reachable
        raise ValueError(f"Unknown shell: {shell}")

    with (scripts_folder / file).open() as f:
        print(f.read())


def main():
    parser = parse_args()
    args = parser.parse_args()

    if args.action == "suggest":
        print_suggestions(args.prefix)
    elif args.action == "autocompletion":
        emit_autocomplete_script(args.shell)

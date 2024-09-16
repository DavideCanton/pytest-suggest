import sys

from pytest_suggest.constants import FILE_NAME
from pytest_suggest.trie import Trie


def main():
    with open(FILE_NAME, "rb") as f:
        trie = Trie.load(f)

    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    for w in sorted(trie.words(prefix)):
        print(w)

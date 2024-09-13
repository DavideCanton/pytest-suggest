import sys

from pytest_suggest.trie import Trie


def main():
    with open("trie.bin", "rb") as f:
        trie = Trie.load(f)

    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    for w in sorted(trie.words(prefix)):
        print(w)

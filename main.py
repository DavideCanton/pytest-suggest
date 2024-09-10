from pytest_suggest.trie import Trie


def main():
    # words = ["casa", "casale", "casino", "casotto", "casinino", "pippo", "pluto"]
    with open("nodeids.txt") as f:
        words = [s.strip() for s in f]

    trie = Trie.from_words(words)

    # print(list(trie.words()))
    print(trie)

    # pp = ["c", "casa", "caso", "casi", "z"]
    # for p in pp:
    #     print(f"{p} ->", list(trie.words(prefix=p)))


main()

import pytest

from pytest_suggest.trie import Node, Trie


class TestNode:
    def test_init(self):
        node = Node("test")

        assert node.word == "test"
        assert node.parent is None
        assert node.word_len == 4
        assert node.children == {}
        assert node.is_end is False

    def test_child(self):
        parent = Node("parent", is_end=True)

        assert parent.is_end
        a = parent.set_child("a", Node("abc"))
        b = parent.set_child("b", Node("bcd"))
        assert a.parent is parent
        assert b.parent is parent
        assert parent.get_child("a") is a
        assert parent.get_child("b") is b
        assert parent.get_child("c") is None

        assert parent["a"] is a
        assert parent["b"] is b

        for k in ("ab", "abc", "bcd", "c"):
            with pytest.raises(KeyError):
                parent[k]

    @pytest.mark.parametrize("childEnd", [True, False])
    def test_merge(self, childEnd):
        parent = Node("parent", is_end=False)
        a = parent.set_child("a", Node("abc", is_end=childEnd))
        b = a.set_child("b", Node("bcd", is_end=True))
        c = a.set_child("c", Node("cde", is_end=False))
        parent.merge_with_child()

        assert parent.is_end == childEnd
        assert parent.word == "parentabc"
        assert parent.word_len == 9
        assert parent.children == a.children
        assert b.parent is parent
        assert c.parent is parent

    def test_merge_multiple_children(self):
        parent = Node("parent", is_end=False)
        parent.set_child("a", Node("abc", is_end=True))
        parent.set_child("b", Node("bcd", is_end=True))

        with pytest.raises(RuntimeError):
            parent.merge_with_child()

    def test_merge_end(self):
        parent = Node("parent", is_end=True)
        parent.set_child("a", Node("abc", is_end=True))

        with pytest.raises(RuntimeError):
            parent.merge_with_child()

    def test_str(self):
        node = Node("test")
        node.set_child("a", Node("abc"))
        node.set_child("b", Node("bcd"))

        assert str(node) == "Node 'test' -> ['a', 'b']"


WORDS = ["casa", "casale", "casino", "casotto", "casinino", "pippo", "pluto"]


class TestTrie:
    def test_build(self):
        trie = Trie.from_words(WORDS)

        root = Node(
            "",
            {
                "c": Node(
                    "cas",
                    {
                        "a": Node(
                            "a",
                            {
                                "l": Node("le", is_end=True),
                            },
                            is_end=True,
                        ),
                        "i": Node(
                            "in",
                            {
                                "o": Node("o", is_end=True),
                                "i": Node("ino", is_end=True),
                            },
                        ),
                        "o": Node("otto", {}, is_end=True),
                    },
                ),
                "p": Node(
                    "p",
                    {"i": Node("ippo", is_end=True), "l": Node("luto", is_end=True)},
                ),
            },
        )

        def _eq(node1, node2):
            assert node1.word == node2.word
            assert node1.word_len == node2.word_len
            assert node1.is_end == node2.is_end
            assert node1.children.keys() == node2.children.keys()

            for k, v in node1.children.items():
                _eq(v, node2.children[k])

        _eq(trie.root, root)

    @pytest.mark.parametrize(
        ("word", "expected"),
        [
            t
            for w in WORDS
            for t in [(w, True), (w + "0", False), (w[:-1], False), (w[1:], False)]
        ]
        + [
            ("foo", False),
            ("bar", False),
            ("baz", False),
        ],
    )
    def test_contains(self, word, expected):
        trie = Trie.from_words(WORDS)
        assert (word in trie) == expected

    def test_words(self):
        trie = Trie.from_words(WORDS)
        assert set(trie.words()) == set(WORDS)
        assert set(trie) == set(WORDS)

    @pytest.mark.parametrize(
        ("prefix", "expected"),
        [
            ("cas", ["casa", "casale", "casino", "casotto", "casinino"]),
            ("casa", ["casa", "casale"]),
            ("case", []),
            ("casi", ["casino", "casinino"]),
            ("p", ["pippo", "pluto"]),
            ("pl", ["pluto"]),
            ("", WORDS),
        ],
    )
    def test_words_prefixes(self, prefix, expected):
        trie = Trie.from_words(WORDS)
        assert set(trie.words(prefix)) == set(expected)

    def test_str(self):
        trie = Trie.from_words(WORDS)
        s = """
 ├cas
   ✓├a
    ✓├le
    ├in
     ✓├ino
     ✓├o
   ✓├otto
 ├p
 ✓├ippo
 ✓├luto"""
        s = s[1:]  # strip leading newline
        assert str(trie) == s

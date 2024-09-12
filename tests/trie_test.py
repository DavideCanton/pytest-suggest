import pytest

from pytest_suggest.trie import Node, Trie


class TestNode:
    def test_init(self):
        node = Node.root("test")

        assert node.parent is None
        assert node.data_len == 4
        assert node.children == {}
        assert node.is_end is False
        assert node.word == "test"

    def test_child(self):
        parent = Node.root("parent", end=True)
        assert parent.is_end

        a = parent.add_child("abc")
        assert a.parent == parent

        b = parent.add_child("bcd")
        assert b.parent == parent

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
        parent = Node.root("root/")

        a = parent.add_child("a/", end=childEnd)
        b = a.add_child("b$", end=childEnd)
        c = a.add_child("c$")
        parent.merge_with_child()

        assert parent.is_end == childEnd
        assert parent.word == "root/a/"
        assert parent.data_len == 7
        assert parent.children == a.children
        assert b.parent is parent
        assert c.parent is parent

    def test_merge_multiple_children(self):
        parent = Node.root("root/")

        parent.add_child("a$", end=True)
        parent.add_child("b$", end=True)

        with pytest.raises(RuntimeError):
            parent.merge_with_child()

    def test_merge_end(self):
        parent = Node.root("root/", end=True)
        parent.add_child("a$", end=True)

        with pytest.raises(RuntimeError):
            parent.merge_with_child()

    def test_str(self):
        node = Node.root("test")
        node.add_child("abc")
        node.add_child("bcd")

        assert str(node) == "Node 'test' -> ['a', 'b']"


WORDS = ["casa", "casale", "casino", "casotto", "casinino", "pippo", "pluto"]


class TestTrie:
    def test_build(self):
        trie = Trie.from_words(WORDS)

        root = Node(
            "",
            0,
            {
                "c": Node(
                    "cas",
                    3,
                    {
                        "a": Node(
                            "casa",
                            1,
                            {"l": Node("casale", 2, is_end=True)},
                            is_end=True,
                        ),
                        "i": Node(
                            "casin",
                            2,
                            {
                                "o": Node("casino", 1, is_end=True),
                                "i": Node("casinino", 3, is_end=True),
                            },
                        ),
                        "o": Node("casotto", 4, is_end=True),
                    },
                ),
                "p": Node(
                    "p",
                    1,
                    {
                        "i": Node("pippo", 4, is_end=True),
                        "l": Node("pluto", 4, is_end=True),
                    },
                ),
            },
        )

        def _eq(node1: Node, node2: Node):
            assert node1.word == node2.word
            assert node1.data_len == node2.data_len
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
        trie = Trie.from_words(sorted(WORDS))
        s = """
 ├cas
   ✓├a [casa]
    ✓├le [casale]
    ├in
     ✓├ino [casinino]
     ✓├o [casino]
   ✓├otto [casotto]
 ├p
 ✓├ippo [pippo]
 ✓├luto [pluto]"""
        s = s[1:]  # strip leading newline
        assert str(trie) == s

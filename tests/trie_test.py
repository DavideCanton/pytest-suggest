import random
import string

import pytest

from pytest_suggest.trie import Node, Trie


def _check_node_eq(node1: Node, node2: Node):
    assert node1.prefix == node2.prefix
    assert node1.part_len == node2.part_len
    assert node1.is_word == node2.is_word
    assert node1.children.keys() == node2.children.keys()

    for k, v in node1.children.items():
        _check_node_eq(v, node2.children[k])


class TestNode:
    root_prefix = pytest.mark.parametrize(
        "root_prefix", (pytest.param("", id="no_prefix"), "root")
    )

    def test_init(self):
        node = Node("prefix", 3, is_word=True)

        assert node.prefix == "prefix"
        assert node.part_len == 3
        assert node.is_word is True
        assert node.children == {}

    def test_root(self):
        node = Node.root()

        assert node.parent is None
        assert node.part_len == 0
        assert node.children == {}
        assert node.is_word is False
        assert node.prefix == ""

    def test_child(self):
        parent = Node.root()

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

    @pytest.mark.parametrize("child_is_word", [True, False])
    def test_merge(self, child_is_word):
        parent = Node.root()

        a = parent.add_child("a/", is_word=child_is_word)
        b = a.add_child("b$", is_word=child_is_word)
        c = a.add_child("c$")
        parent.merge_with_child()

        assert parent.is_word == child_is_word
        assert parent.prefix == "a/"
        assert parent.part_len == 2
        assert parent.children == a.children
        assert b.parent is parent
        assert c.parent is parent

    def test_merge_multiple_children(self):
        parent = Node.root()

        parent.add_child("a$", is_word=True)
        parent.add_child("b$", is_word=True)

        with pytest.raises(RuntimeError):
            parent.merge_with_child()

    def test_merge_end(self):
        parent = Node.root()
        c1 = parent.add_child("a/", is_word=True)
        c1.add_child("b$", is_word=True)

        with pytest.raises(RuntimeError):
            c1.merge_with_child()

    def test_str(self):
        node = Node.root()
        c1 = node.add_child("abc")
        gc1 = c1.add_child("def")
        c2 = node.add_child("bcd")

        assert str(node) == "Node '' -> ['a', 'b']"
        assert str(c1) == "Node 'abc' -> ['d']"
        assert str(c2) == "Node 'bcd' -> []"
        assert str(gc1) == "Node 'abcdef' -> []"

    def test_dict(self):
        node = Node.root()
        c1 = node.add_child("abc")
        c1.add_child("def", is_word=True)
        c2 = node.add_child("bcd", is_word=True)
        c2.add_child("efg", is_word=True)

        exp = {
            "c": {
                "a": {
                    "c": {"d": {"l": 3, "p": "def", "w": True}},
                    "l": 3,
                    "p": "abc",
                    "w": False,
                },
                "b": {
                    "c": {"e": {"l": 3, "p": "efg", "w": True}},
                    "l": 3,
                    "p": "bcd",
                    "w": True,
                },
            },
            "l": 0,
            "p": "",
            "w": False,
        }

        assert node._to_dict() == exp

        loaded = Node._from_dict(exp)
        _check_node_eq(node, loaded)

    @root_prefix
    def test_tree(self, root_prefix):
        root = Node(root_prefix, len(root_prefix))
        c1 = root.add_child("abc", is_word=True)

        c11 = c1.add_child("def", is_word=False)
        c11.add_child("ghi", is_word=True)
        c11.add_child("jk", is_word=True)

        c1.add_child("lk", is_word=True)

        c2 = root.add_child("bcd", is_word=False)
        c21 = c2.add_child("efg", is_word=True)
        c21.add_child("hij", is_word=True)

        c2.add_child("pq", is_word=True)

        f = "root\n├" if root_prefix else "┌"
        s = f"""
{f}─abc *
│ ├─def
│ │ ├─ghi *
│ │ └─jk *
│ └─lk *
└─bcd
  ├─efg *
  │ └─hij *
  └─pq *"""
        # strip first newline
        s = s[1:]

        assert root.tree() == s

    @root_prefix
    def test_tree_only_root(self, root_prefix):
        root = Node(root_prefix, len(root_prefix))
        if root_prefix:
            assert root.tree() == "root"
        else:
            assert root.tree() == ""

    @root_prefix
    @pytest.mark.parametrize("grandchild", (True, False))
    def test_tree_single_child_root(self, root_prefix, grandchild):
        root = Node(root_prefix, len(root_prefix))
        n = root.add_child("abc", is_word=True)

        if grandchild:
            n.add_child("def", is_word=True)

        if root_prefix:
            s = "root\n└"
        else:
            s = "─"

        s += "─abc *"
        if grandchild:
            s += "\n  └─def *"

        assert root.tree() == s


WORDS = ["casa", "casale", "casino", "casotto", "casinino", "pippo", "pluto"]


class TestTrie:
    def test_build(self):
        trie = Trie.from_words(WORDS)
        root = self._build_trie_manually()
        _check_node_eq(trie._root, root)

    def test_save_load(self, tmp_path):
        trie = Trie.from_words(WORDS)
        path = tmp_path / "trie.pkl"

        with path.open("wb") as f:
            trie.save(f)

        with path.open("rb") as f:
            trie2 = Trie.load(f)

        _check_node_eq(trie._root, trie2._root)

    @pytest.mark.slow
    def test_save_load_big(self, tmp_path):
        words = set()
        chars = list(set(string.printable) - set(string.whitespace))

        while len(words) < 10000:
            word = "".join(random.choices(chars, k=20))
            words.add(word)

        trie = Trie.from_words(words)
        path = tmp_path / "trie.pkl"

        with path.open("wb") as f:
            trie.save(f)

        with path.open("rb") as f:
            trie2 = Trie.load(f)

        _check_node_eq(trie._root, trie2._root)

    def _build_trie_manually(self):
        return Node(
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
                            {"l": Node("casale", 2, is_word=True)},
                            is_word=True,
                        ),
                        "i": Node(
                            "casin",
                            2,
                            {
                                "o": Node("casino", 1, is_word=True),
                                "i": Node("casinino", 3, is_word=True),
                            },
                        ),
                        "o": Node("casotto", 4, is_word=True),
                    },
                ),
                "p": Node(
                    "p",
                    1,
                    {
                        "i": Node("pippo", 4, is_word=True),
                        "l": Node("pluto", 4, is_word=True),
                    },
                ),
            },
        )

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
        assert str(trie) == trie._root.tree()

    def test_duplicate_words(self):
        words_with_duplicates = WORDS + WORDS
        trie = Trie.from_words(words_with_duplicates)

        # Ensure duplicates don't affect the trie structure
        assert set(trie.words()) == set(WORDS)
        assert set(trie) == set(WORDS)

        # Ensure the duplicate words are still recognized as valid words
        for word in ["casa", "casino", "pippo"]:
            assert word in trie

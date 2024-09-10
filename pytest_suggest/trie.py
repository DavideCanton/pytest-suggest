from __future__ import annotations

from collections.abc import Generator, Iterable
from dataclasses import dataclass, field


@dataclass(eq=True, slots=True)
class Node:
    word: str
    children: dict[str, Node] = field(default_factory=dict)
    parent: Node | None = field(default=None, repr=False)
    is_end: bool = field(default=False)
    word_len: int = field(init=False, repr=False)

    def __post_init__(self):
        self.word_len = len(self.word)

    def get_child(self, child: str) -> Node | None:
        return self.children.get(child)

    def set_child(self, child: str, node: Node) -> Node:
        self.children[child] = node
        node.parent = self
        return node

    def merge_with_child(self) -> None:
        if self.is_end or len(self.children) != 1:
            raise RuntimeError("Cannot merge end node or with multiple children")

        child = self.children.popitem()[1]

        self.word += child.word
        self.word_len += child.word_len
        self.is_end = child.is_end
        self.children = child.children

        for grandchild in child.children.values():
            grandchild.parent = self

    def __getitem__(self, child: str) -> Node:
        return self.children[child]

    def __str__(self) -> str:
        return f"Node {self.word!r} -> {sorted(self.children)!r}"


class Trie:
    def __init__(self):
        self.root = Node("")

    @staticmethod
    def from_words(words: Iterable[str]) -> Trie:
        words = sorted(words)
        trie = Trie()

        cur_node = trie.root
        cur_word = ""

        for word in words:
            cur_word, cur_node = Trie._insert_word(word, cur_word, cur_node)

        trie._compress()

        return trie

    @staticmethod
    def _insert_word(word: str, cur_word: str, cur_node: Node) -> tuple[str, Node]:
        cur_word, cur_node = Trie._backtrack_word(word, cur_word, cur_node)
        cur_node = Trie._traverse_and_insert(cur_node, word[len(cur_word) :])
        return word, cur_node

    @staticmethod
    def _backtrack_word(
        word: str, current_word: str, current: Node
    ) -> tuple[str, Node]:
        c: Node | None = current

        while word[: len(current_word)] != current_word:
            assert c is not None
            c = c.parent
            current_word = current_word[:-1]

        assert c is not None
        return current_word, c

    @staticmethod
    def _traverse_and_insert(current: Node, word: str) -> Node:
        for char in word:
            if (child := current.get_child(char)) is None:
                child = current.set_child(char, Node(char))

            current = child

        current.is_end = True

        return current

    def _compress(self) -> None:
        stack = [self.root]

        while stack:
            current = stack.pop()
            children = list(current.children.values())

            # don't compress if there are multiple children or if the current node is an end
            if len(children) != 1 or current.is_end:
                stack.extend(children)
                continue

            current.merge_with_child()
            stack.append(current)

    def __contains__(self, word: str) -> bool:
        current = self.root
        cur = 0

        while cur < len(word):
            char = word[cur]
            child = current.get_child(char)
            if child is None:
                return False
            cur += child.word_len
            current = child

        return current.is_end and cur == len(word)

    def words(self, prefix: str = "") -> Generator[str]:
        cur_word: list[str] = []

        if prefix:
            current = self.root
            cur = 0

            while cur < len(prefix):
                char = prefix[cur]
                child = current.get_child(char)
                if child is None:
                    return
                cur += child.word_len
                cur_word.append(child.word)
                current = child

            if current.is_end:
                yield "".join(cur_word)

            stack = [(ch, len(cur_word)) for ch in current.children.values()]
        else:
            stack = [(self.root, 0)]

        while stack:
            current, depth = stack.pop()

            if depth >= 0:
                cur_word = cur_word[:depth]

            if current.word is not None:
                cur_word.append(current.word)

            if current.is_end:
                yield "".join(cur_word)

            for child in current.children.values():
                stack.append((child, depth + 1))

    def __str__(self) -> str:
        parts = []
        self._to_str(self.root, parts, 1)
        return "\n".join(parts)

    def __iter__(self) -> Generator[str]:
        yield from self.words()

    def _to_str(self, node: Node, parts: list[str], depth: int):
        indent = " " * depth
        if node.is_end:
            indent = indent[:-1] + "✓"

        if node.word:
            parts.append(f"{indent}├{node.word}")
        for child in node.children.values():
            self._to_str(child, parts, depth + node.word_len)

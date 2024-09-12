from __future__ import annotations

from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
import weakref


@dataclass(eq=True, slots=True, weakref_slot=True)
class Node:
    word: str
    data_len: int
    children: dict[str, Node] = field(default_factory=dict)
    is_end: bool = False

    parent: Node | None = field(default=None, repr=False, init=False)

    @staticmethod
    def root(_data="", *, end: bool = False) -> Node:
        return Node(data_len=len(_data), word=_data, is_end=end)

    def get_child(self, child: str) -> Node | None:
        return self.children.get(child)

    def add_child(self, data: str, *, end: bool = False) -> Node:
        node = Node(data_len=len(data), word=self.word + data, is_end=end)
        self.children[data[0]] = node
        node.parent = weakref.proxy(self)
        return node

    def merge_with_child(self) -> None:
        if self.is_end or len(self.children) != 1:
            raise RuntimeError("Cannot merge end node or with multiple children")

        child = self.children.popitem()[1]

        self.data_len += child.data_len
        self.word = child.word
        self.children = child.children
        self.is_end = child.is_end

        for grandchild in child.children.values():
            grandchild.parent = self

    def __getitem__(self, child: str) -> Node:
        return self.children[child]

    def __str__(self) -> str:
        return f"Node {self.word!r} -> {sorted(self.children)!r}"


class Trie:
    def __init__(self):
        self.root = Node.root()

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
        # TODO improve this
        cur_word, cur_node = Trie._backtrack_word(word, cur_word, cur_node)
        cur_node = Trie._traverse_and_insert(cur_node, word, len(cur_word))
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
    def _traverse_and_insert(current: Node, word: str, pos: int) -> Node:
        for i in range(pos, len(word)):
            char = word[i]
            last = i == len(word) - 1

            if (child := current.get_child(char)) is None:
                child = current.add_child(char, end=last)

            current = child

        return current

    def __contains__(self, word: str) -> bool:
        if node := self._find_node(word):
            return node.is_end and node.word == word

        return False

    def words(self, prefix: str = "") -> Generator[str]:
        stack: list[Node] = []

        if prefix:
            node = self._find_node(prefix)
            if node is not None:
                stack.append(node)
        else:
            stack.append(self.root)

        while stack:
            current = stack.pop()

            if current.is_end:
                assert current.word is not None
                yield current.word

            for child in current.children.values():
                stack.append(child)

    def __str__(self) -> str:
        parts = []
        self._to_str(self.root, parts, 1)
        return "\n".join(parts)

    def __iter__(self) -> Generator[str]:
        yield from self.words()

    def _find_node(self, prefix: str) -> Node | None:
        current = self.root
        cur = 0

        while cur < len(prefix):
            char = prefix[cur]
            child = current.get_child(char)
            if child is None:
                return None
            cur += child.data_len
            current = child

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

    def _to_str(self, node: Node, parts: list[str], depth: int):
        indent = " " * depth
        if node.is_end:
            indent = indent[:-1] + "✓"
            trailer = f" [{node.word}]"
        else:
            trailer = ""

        data = node.word[-node.data_len :]
        if data:
            parts.append(f"{indent}├{data}{trailer}")
        for child in node.children.values():
            self._to_str(child, parts, depth + node.data_len)

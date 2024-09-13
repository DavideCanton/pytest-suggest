from __future__ import annotations

import pickle
import weakref
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass(slots=True, weakref_slot=True)
class Node:
    """A node in a trie."""

    prefix: str
    """The prefix represented up to this node.
    
    This is the concatenation of the prefixes from the root to this node.
    """
    part_len: int
    """The length of the part represented by this node.
    
    This is the length of the part of the prefix that is represented by this node,
    so for example if the prefix is "abc" and this node represents "ab", then this
    value is 2.
    """
    children: dict[str, Node] = field(default_factory=dict)
    """The children of this node.

    This is a mapping of the first character of the child to the child node.
    """
    is_word: bool = False
    """Whether this node represents a word in the trie or just a prefix."""

    parent: Node | None = field(default=None, repr=False, init=False)
    """The parent of this node.

    This is a weak reference to the parent node.

    The root node has no parent and this value is None.
    """

    @staticmethod
    def root() -> Node:
        """Creates the root node.

        Returns:
            Node: the root node.
        """
        return Node(part_len=0, prefix="", is_word=False)

    def get_child(self, child: str) -> Node | None:
        return self.children.get(child)

    def add_child(self, part: str, *, is_word: bool = False) -> Node:
        node = Node(part_len=len(part), prefix=self.prefix + part, is_word=is_word)
        self.children[part[0]] = node
        node.parent = weakref.proxy(self)
        return node

    def merge_with_child(self) -> None:
        if self.is_word or len(self.children) != 1:
            raise RuntimeError("Cannot merge a word node or with multiple children")

        child = self.children.popitem()[1]

        self.part_len += child.part_len
        self.prefix = child.prefix
        self.children = child.children
        self.is_word = child.is_word

        for grandchild in child.children.values():
            grandchild.parent = self

    def __getitem__(self, child: str) -> Node:
        return self.children[child]

    def __str__(self) -> str:
        return f"Node {self.prefix!r} -> {sorted(self.children)!r}"


class Trie:
    def __init__(self):
        self._root = Node.root()
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    @staticmethod
    def from_words(words: Iterable[str]) -> Trie:
        trie = Trie()

        for word in words:
            cur = trie._root
            for char in word:
                if child := cur.get_child(char):
                    cur = child
                else:
                    cur = cur.add_child(char)
            cur.is_word = True
            trie._size += 1

        trie._compress()

        return trie

    @staticmethod
    def load(from_: BinaryIO) -> Trie:
        return pickle.load(from_)

    def save(self, to: BinaryIO) -> None:
        pickle.dump(self, to)

    def __contains__(self, word: str) -> bool:
        if node := self._find_node(word):
            return node.is_word and node.prefix == word

        return False

    def words(self, prefix: str = "") -> Generator[str]:
        stack: list[Node] = []

        if prefix:
            node = self._find_node(prefix)
            if node is not None:
                stack.append(node)
        else:
            stack.append(self._root)

        while stack:
            current = stack.pop()

            if current.is_word:
                assert current.prefix is not None
                yield current.prefix

            for child in current.children.values():
                stack.append(child)

    def __str__(self) -> str:
        parts = []
        self._to_str(self._root, parts, 1)
        return "\n".join(parts)

    def __iter__(self) -> Generator[str]:
        yield from self.words()

    def _find_node(self, prefix: str) -> Node | None:
        current = self._root
        cur = 0

        while cur < len(prefix):
            char = prefix[cur]
            child = current.get_child(char)
            if child is None:
                return None
            cur += child.part_len
            current = child

        return current

    def _compress(self) -> None:
        stack = [self._root]

        while stack:
            current = stack.pop()
            children = list(current.children.values())

            # don't compress if there are multiple children or if the current node is an end
            if len(children) != 1 or current.is_word or current.part_len == 0:
                stack.extend(children)
                continue

            current.merge_with_child()
            stack.append(current)

    def _to_str(self, node: Node, parts: list[str], depth: int):
        indent = " " * depth
        if node.is_word:
            indent = indent[:-1] + "✓"
            trailer = f" [{node.prefix}]"
        else:
            trailer = ""

        data = node.prefix[-node.part_len :]
        if data:
            parts.append(f"{indent}├{data}{trailer}")
        for child in node.children.values():
            self._to_str(child, parts, depth + node.part_len)

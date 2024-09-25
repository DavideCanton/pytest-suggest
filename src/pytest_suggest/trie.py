from __future__ import annotations

import pickle
import weakref
from collections.abc import Generator, Iterable
from typing import BinaryIO

import bz2


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
    children: dict[str, Node]
    """The children of this node.

    This is a mapping of the first character of the child to the child node.
    """
    is_word: bool
    """Whether this node represents a word in the trie or just a prefix."""

    parent: Node | None
    """The parent of this node.

    This is a weak reference to the parent node.

    The root node has no parent and this value is None.
    """

    __slots__ = ("prefix", "part_len", "children", "is_word", "parent", "__weakref__")

    def __init__(
        self,
        prefix: str,
        part_len: int,
        children: dict[str, Node] | None = None,
        is_word: bool = False,
    ) -> None:
        self.prefix = prefix
        self.part_len = part_len
        self.children = children or {}
        self.is_word = is_word
        self.parent = None

    @staticmethod
    def root() -> Node:
        """Creates the root node.

        Returns:
            Node: the root node.
        """
        return Node(part_len=0, prefix="", is_word=False)

    def get_child(self, child: str) -> Node | None:
        """Returns the child node for the given character, or None if it doesn't exist."""
        return self.children.get(child)

    def add_child(self, part: str, *, is_word: bool = False) -> Node:
        """Adds a child node for the given part.

        Also sets `self` as the parent node for the newly created node.

        Args:
            part (str): the part to add.
            is_word (bool, optional): whether the part is a word. Defaults to False.

        Returns:
            Node: the child node.
        """
        node = Node(part_len=len(part), prefix=self.prefix + part, is_word=is_word)
        self.children[part[0]] = node
        node.parent = weakref.proxy(self)
        return node

    def merge_with_child(self) -> None:
        """Merges this node with its only child.

        Raises:
            RuntimeError: if the node is not a word node or if it has multiple children.
        """
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
        """Returns the child node for the given character."""
        return self.children[child]

    def __str__(self) -> str:
        return f"Node {self.prefix!r} -> {sorted(self.children)!r}"


class Trie:
    """A trie data structure.

    It represents a set of words, and it's optimized for fast lookups based on a prefix.
    """

    def __init__(self):
        """Initializes an empty trie.

        The trie is initialized with an empty root node and a size of 0.
        """
        self._root = Node.root()
        self._size = 0

    @property
    def size(self) -> int:
        """The number of words in the trie."""
        return self._size

    def __len__(self) -> int:
        """The number of words in the trie."""
        return self._size

    @staticmethod
    def from_words(words: Iterable[str]) -> Trie:
        """Creates a trie from a list of words.

        The trie is compressed after the creation by merging nodes that have
        a single child.

        Args:
            words (Iterable[str]): the list of words.

        Returns:
            Trie: the trie.
        """
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
        """Loads a trie from a file.

        The trie is assumed to be compressed using ``bz2.compress``.

        Args:
            from_ (BinaryIO): the file to load from.

        Returns:
            Trie: the loaded trie.
        """
        data = bz2.decompress(from_.read())
        return pickle.loads(data)

    def save(self, to: BinaryIO) -> None:
        """Saves the trie to a file.

        The trie is pickled, then compressed using ``bz2.compress``.

        Args:
            to (BinaryIO): the file to save to.
        """
        data = bz2.compress(pickle.dumps(self))
        to.write(data)

    def __contains__(self, word: str) -> bool:
        """Checks if the given word is in the trie."""
        if node := self._find_node(word):
            return node.is_word and node.prefix == word

        return False

    def words(self, prefix: str = "") -> Generator[str]:
        """Returns all words in the trie that start with the given prefix.

        If the prefix is empty, all words in the trie are returned.

        Args:
            prefix (str, optional): the prefix to search for. Defaults to "".

        Yields:
            Generator[str]: the words in the trie that start with the given prefix.
        """
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
        """Returns a string representation of the trie."""
        parts = []
        self._to_str(self._root, parts, 0, False)
        parts[0] = "┌" + parts[0][1:]
        return "\n".join(parts)

    def __iter__(self) -> Generator[str]:
        """Returns an iterator over all words in the trie."""
        yield from self.words()

    def _find_node(self, prefix: str) -> Node | None:
        """Finds the node for the given prefix."""
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
        """Compresses the trie by merging nodes that have a single child."""
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

    def _to_str(
        self, node: Node, parts: list[str], depth: int, parent_is_last: bool
    ) -> None:
        """Recursively creates a string representation of the trie."""
        children_count = len(node.children)
        for i, child in enumerate(node.children.values()):
            is_last = i == children_count - 1

            if parent_is_last:
                part = ["│ "] * (depth - 1) + ["  "]
            else:
                part = ["│ "] * depth

            if is_last:
                part.append("└")
            else:
                part.append("├")

            part.append("─")
            part.append(child.prefix[-child.part_len :])

            if child.is_word:
                part.append(" *")

            parts.append("".join(part))

            self._to_str(child, parts, depth + 1, is_last)

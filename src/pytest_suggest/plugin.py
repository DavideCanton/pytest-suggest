from pytest import Config, Item, Session, StashKey, hookimpl

from pytest_suggest.constants import FILE_NAME
from pytest_suggest.trie import Trie

KEY = StashKey[Trie]()


def pytest_addoption(parser):
    group = parser.getgroup("suggest")
    group.addoption(
        "--build-suggestion-index",
        action="store_true",
        dest="build_suggestion_index",
        default=False,
        help="Builds the suggestion index to be used by the autocompletion script. It does not run any test.",
    )


def pytest_report_header(config: Config):
    if config.option.build_suggestion_index:
        return "Building test index..."
    return None


def pytest_report_collectionfinish(config: Config, startdir: str, items: list[Item]):
    if config.option.build_suggestion_index:
        trie = config.stash[KEY]
        return f"Built test index of size {len(trie)}"
    return None


def pytest_configure(config: Config):
    if config.option.build_suggestion_index:
        config.option.verbose = -1


@hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]):
    if not config.option.build_suggestion_index:
        return

    trie = Trie.from_words(item.nodeid for item in items)
    config.stash[KEY] = trie

    with open(FILE_NAME, "wb") as f:
        trie.save(f)

    config.hook.pytest_deselected(items=items)
    items.clear()

import pathlib

from pytest import (
    Config,
    ExitCode,
    Item,
    Session,
    Parser,
    StashKey,
    hookimpl,
    version_tuple as pytest_version,
)

from pytest_suggest.constants import FILE_NAME
from pytest_suggest.trie import Trie


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("suggest")
    group.addoption(
        "--build-suggestion-index",
        action="store_true",
        dest="build_suggestion_index",
        default=False,
        help="Builds the suggestion index to be used by the autocompletion script. It does not run any test.",
    )


def pytest_configure(config: Config) -> None:
    if config.option.build_suggestion_index:
        config.option.verbose = -1
        config.pluginmanager.register(SuggestPlugin())


class SuggestPlugin:
    KEY = StashKey[Trie]()

    def pytest_report_header(self, config: Config) -> str:
        return "Building test index..."

    if pytest_version < (8, 0):

        def pytest_report_collectionfinish(  # type: ignore
            self, config: Config, startdir: str, items: list[Item]
        ) -> str:
            return self._collectionfinish(config)

    else:

        def pytest_report_collectionfinish(
            self,
            config: Config,
            start_path: pathlib.Path,
            items: list[Item],
        ) -> str:
            return self._collectionfinish(config)

    def _collectionfinish(self, config: Config) -> str:
        trie = config.stash[self.KEY]
        return f"Built test index of size {len(trie)}"

    @hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(
        self, session: Session, config: Config, items: list[Item]
    ) -> None:
        trie = Trie.from_words(item.nodeid for item in items)
        config.stash[self.KEY] = trie

        with open(FILE_NAME, "wb") as f:
            trie.save(f)

        config.hook.pytest_deselected(items=items)
        items.clear()

    def pytest_sessionfinish(self, session: Session, exitstatus: ExitCode) -> None:
        # avoid reporting "no test collected" when building the index
        if exitstatus == ExitCode.NO_TESTS_COLLECTED:
            session.exitstatus = ExitCode.OK

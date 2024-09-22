from pathlib import Path

import pytest

from pytest_suggest.cli import suggest
from pytest_suggest.trie import Trie


@pytest.fixture
def run_app(monkeypatch):
    def run_app(args):
        monkeypatch.setattr("sys.argv", ["pytest-suggest"] + args)
        suggest.main()

    return run_app


@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_autocompletion(run_app, shell, capsys):
    run_app(["autocompletion", shell])

    captured = capsys.readouterr()
    assert not captured.err

    assert captured.out.rstrip() == read_file(shell)


def test_invalid_shell(run_app, capsys):
    try:
        run_app(["autocompletion", "foo"])
        pytest.fail("Test should have failed")
    except SystemExit:
        captured = capsys.readouterr()
        assert (
            "invalid choice: 'foo' (choose from 'bash', 'powershell')" in captured.err
        )
        assert not captured.out


def test_missing_shell(run_app, capsys):
    try:
        run_app(["autocompletion"])
        pytest.fail("Test should have failed")
    except SystemExit:
        captured = capsys.readouterr()
        assert "the following arguments are required: shell" in captured.err
        assert not captured.out


def test_suggest(run_app, capsys, monkeypatch, tmp_path):
    test_trie = Trie.from_words(["foo", "bar", "foobar"])

    trie_path = tmp_path / "trie.pkl"
    with trie_path.open("wb") as f:
        test_trie.save(f)

    monkeypatch.setattr(suggest, "FILE_NAME", str(trie_path))

    run_app(["suggest", "foo"])

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out.rstrip() == "foo\nfoobar"


def test_missing_prefix(run_app, capsys):
    try:
        run_app(["suggest"])
        pytest.fail("Test should have failed")
    except SystemExit:
        captured = capsys.readouterr()
        assert "the following arguments are required: prefix" in captured.err
        assert not captured.out


def read_file(shell):
    if shell == "bash":
        file = "pytest-mycompletion.sh"
    elif shell == "powershell":
        file = "pytest-mycompletion.ps1"
    else:
        pytest.fail(f"Unknown shell: {shell}")

    scripts_folder = Path(__file__).parent.parent / "src" / "pytest_suggest" / "scripts"
    with (scripts_folder / file).open() as f:
        return f.read().rstrip()

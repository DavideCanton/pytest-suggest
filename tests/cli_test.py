from pathlib import Path

import pytest

from pytest_suggest.cli import suggest
from pytest_suggest.trie import Trie


@pytest.fixture
def run_app(monkeypatch: pytest.MonkeyPatch):
    """Returns a function that, given a list of args, runs the main function."""

    def run_app(args: list[str]) -> int | str | None:
        monkeypatch.setattr("sys.argv", ["pytest-suggest"] + args)
        try:
            suggest.main()
            return 0
        except SystemExit as e:
            return e.code

    return run_app


@pytest.fixture
def check_error(run_app, capsys):
    """Returns a function that, given a list of args, checks that the provided error message is printed."""

    def run(args: list[str], error: str):
        ret = run_app(args)
        if ret == 0:
            pytest.fail("Test should have failed")
        else:
            captured = capsys.readouterr()
            assert error in captured.err
            assert not captured.out

    return run


@pytest.mark.parametrize("shell", ["bash", "powershell"])
def test_autocompletion(run_app, shell, capsys):
    run_app(["autocompletion", shell])

    captured = capsys.readouterr()
    assert not captured.err

    assert captured.out.rstrip() == read_file(shell)


def test_invalid_shell(check_error):
    check_error(
        ["autocompletion", "foo"],
        "invalid choice: 'foo' (choose from 'bash', 'powershell')",
    )


def test_missing_shell(check_error):
    check_error(
        ["autocompletion"],
        "the following arguments are required: shell",
    )


@pytest.mark.parametrize("custom_index_arg", ["no", "short", "long"])
def test_suggest(run_app, capsys, monkeypatch, tmp_path, custom_index_arg: str):
    test_trie = Trie.from_words(["foo", "bar", "foobar"])

    trie_path = tmp_path / "trie.pkl"
    with trie_path.open("wb") as f:
        test_trie.save(f)

    app = ["suggest", "foo"]

    match custom_index_arg:
        case "no":
            monkeypatch.setattr(suggest, "FILE_NAME", str(trie_path))
        case "short":
            app.extend(["-i", str(trie_path)])
        case "long":
            app.extend(["--index", str(trie_path)])

    run_app(app)

    captured = capsys.readouterr()
    assert not captured.err
    assert captured.out.rstrip() == "foo\nfoobar"


def test_missing_prefix(check_error):
    check_error(
        ["suggest"],
        "the following arguments are required: prefix",
    )


def test_index_not_built(run_app, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(suggest, "FILE_NAME", str(tmp_path / "trie.pkl"))
    assert not Path(suggest.FILE_NAME).exists()

    ret = run_app(["suggest", "foo"])

    assert ret == 1
    captured = capsys.readouterr()
    assert not captured.err
    assert not captured.out


def read_file(shell):
    if shell == "bash":
        file = "pytest-mycompletion.bash"
    elif shell == "powershell":
        file = "pytest-mycompletion.ps1"
    else:
        pytest.fail(f"Unknown shell: {shell}")

    scripts_folder = Path(__file__).parent.parent / "src" / "pytest_suggest" / "scripts"
    with (scripts_folder / file).open() as f:
        return f.read().rstrip()

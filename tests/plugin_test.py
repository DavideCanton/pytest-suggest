import pytest

from pytest_suggest.trie import Trie


@pytest.fixture()
def setup_tests(pytester: pytest.Pytester):
    pytester.makepyfile(
        test_1="""
        import pytest

        import os
        print(os.getcwd())

        @pytest.fixture(params=[1,2,3])
        def fixt(request):
            return request.param

        def test_1(fixt):
            pass
            
        def test_foo():
            pass
            
        class TestMoreTests:
            def test_bar_1(self):
                pass
                
            def test_bar_2(self, fixt):
                pass
                
            @pytest.mark.parametrize("n", ['ok', 'ok-no', 'no'])
            @pytest.mark.parametrize("m", ['yes', 'no'])
            def test_baz(self, n, m):
                pytest.fail("fail")
        """,
        test_2="""
        def test_foo():
            pass
            
        def test_foo_2():
            pass
        """,
    )

    pytester.mkpydir("sub")

    pytester.makepyfile(
        **{
            "sub/test_1.py": """
            def test_foo(): pass
            def test_foo_2(): pass
            def test_bar(): pass

            class TestMoar:
                def test_foo(self): pass
            """,
            "sub/test_2.py": """
            def test_foo(): pass
            def test_foo_2(): pass
            def test_bar(): pass
            """,
        }
    )


@pytest.mark.usefixtures("setup_tests")
def test_build_index(pytester: pytest.Pytester):
    result = pytester.runpytest_subprocess("--build-suggestion-index")
    assert result.ret == pytest.ExitCode.OK

    index = pytester.path / ".pytest_suggest_index"
    assert index.exists()

    with index.open("rb") as f:
        trie = Trie.load(f)

    assert len(trie) == 23

    assert sorted(trie.words()) == [
        "sub/test_1.py::TestMoar::test_foo",
        "sub/test_1.py::test_bar",
        "sub/test_1.py::test_foo",
        "sub/test_1.py::test_foo_2",
        "sub/test_2.py::test_bar",
        "sub/test_2.py::test_foo",
        "sub/test_2.py::test_foo_2",
        "test_1.py::TestMoreTests::test_bar_1",
        "test_1.py::TestMoreTests::test_bar_2[1]",
        "test_1.py::TestMoreTests::test_bar_2[2]",
        "test_1.py::TestMoreTests::test_bar_2[3]",
        "test_1.py::TestMoreTests::test_baz[no-no]",
        "test_1.py::TestMoreTests::test_baz[no-ok-no]",
        "test_1.py::TestMoreTests::test_baz[no-ok]",
        "test_1.py::TestMoreTests::test_baz[yes-no]",
        "test_1.py::TestMoreTests::test_baz[yes-ok-no]",
        "test_1.py::TestMoreTests::test_baz[yes-ok]",
        "test_1.py::test_1[1]",
        "test_1.py::test_1[2]",
        "test_1.py::test_1[3]",
        "test_1.py::test_foo",
        "test_2.py::test_foo",
        "test_2.py::test_foo_2",
    ]


@pytest.mark.usefixtures("setup_tests")
def test_run_without_build(pytester: pytest.Pytester):
    result = pytester.runpytest_subprocess()
    assert result.ret == pytest.ExitCode.TESTS_FAILED

    index = pytester.path / ".pytest_suggest_index"
    assert not index.exists()


@pytest.mark.usefixtures("setup_tests")
def test_run_without_plugin(pytester: pytest.Pytester):
    # ensure the plugin is not loaded
    result = pytester.runpytest_subprocess(
        "-p", "no:suggest", "--build-suggestion-index"
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        "*error: unrecognized arguments: --build-suggestion-index*"
    )

    result = pytester.runpytest_subprocess("-p", "no:suggest")
    assert result.ret == pytest.ExitCode.TESTS_FAILED

    index = pytester.path / ".pytest_suggest_index"
    assert not index.exists()

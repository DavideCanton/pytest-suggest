#/usr/bin/env bash
_pytest_suggest_completions() {
    local cur
    _get_comp_words_by_ref -n : cur

    COMPREPLY=($(compgen -W '$(pytest-suggest "$cur")' -- "$cur"))

    __ltrim_colon_completions "$cur"
}

complete -o bashdefault -o default -F _pytest_suggest_completions pytest

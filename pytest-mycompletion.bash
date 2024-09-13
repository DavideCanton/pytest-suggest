#/usr/bin/env bash
_pytest_suggest_completions() {
    local cur
    _get_comp_words_by_ref -n : cur

    # if [ "${#COMP_WORDS[@]}" != "2" ]; then
    #     return
    # fi

    COMPREPLY=($(compgen -W '$(pytest-suggest "$cur")' -- "$cur"))

    __ltrim_colon_completions "$cur"
}

complete -F _pytest_suggest_completions pytest

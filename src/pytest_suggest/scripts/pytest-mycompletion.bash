_check() {
    type -t $1 &>/dev/null
    echo $?
}

# sets __ltrim_colon_completions if not available
# since some shells like mingw don't have this
if [ $(_check "__ltrim_colon_completions") -ne 0 ]; then
    # copied from https://github.com/scop/bash-completion/blob/1.x/bash_completion#L374

    __ltrim_colon_completions() {
        # If word-to-complete contains a colon,
        # and bash-version < 4,
        # or bash-version >= 4 and COMP_WORDBREAKS contains a colon
        if [[ 
            "$1" == *:* && (
            ${BASH_VERSINFO[0]} -lt 4 ||
            (${BASH_VERSINFO[0]} -ge 4 && "$COMP_WORDBREAKS" == *:*)) ]] \
            ; then
            # Remove colon-word prefix from COMPREPLY items
            local colon_word=${1%${1##*:}}
            local i=${#COMPREPLY[*]}
            while [ $((--i)) -ge 0 ]; do
                COMPREPLY[$i]=${COMPREPLY[$i]#"$colon_word"}
            done
        fi
    }
fi

_pytest_suggest_completions() {
    if [[ "${COMP_WORDS[$COMP_CWORD]}" =~ ^[^-].* ]]; then
        local cur
        _get_comp_words_by_ref -n : cur

        # remove \r since compgen in mingw returns \r\n
        COMPREPLY=($(compgen -W '$(pytest-suggest suggest "$cur")' | sed 's/\r//'))

        __ltrim_colon_completions "$cur"
    else
        # use default pytest completion
        _pytest pytest 2> /dev/null
    fi
}

if [ -f "/usr/share/bash-completion/completions/pytest" ]; then
    source /usr/share/bash-completion/completions/pytest
fi

complete -F _pytest_suggest_completions pytest

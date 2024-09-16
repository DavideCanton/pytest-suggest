$scriptblock = {
    param(
        $wordToComplete,
        $commandAst,
        $cursorPosition
    )

    $res = pytest-suggest $wordToComplete
    $res | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new(
            $_, # completionText
            $_, # listItemText
            'ParameterValue', # resultType
            $_                # toolTip
        )
    }
}

Register-ArgumentCompleter -Native -CommandName pytest -ScriptBlock $scriptblock
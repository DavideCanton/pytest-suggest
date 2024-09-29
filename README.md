# pytest-suggest

Pytest plugin for providing autocompletion.

## Installation

```shell
pip install pytest-suggest
```

## Shell integration

### Bash

You can either add the following line to the `.bashrc` or `.bash_profile` file:

```bash
eval "$(pytest-suggest autocompletion bash)"
```

or run the following command:

```bash
echo "$(pytest-suggest autocompletion bash)" >> ~/.bash_completion
```

### PowerShell

Add the following to your `.ps1`:

```powershell
pytest-suggest autocompletion powershell
```

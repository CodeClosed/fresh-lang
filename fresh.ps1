# PowerShell script wrapper for Fresh
$env:PYTHONPATH = "$PSScriptRoot\src;$env:PYTHONPATH"
python -m fresh $args


$ErrorActionPreference = 'Stop'
$env:PATH = "D:\ProgramData\Anaconda3\Library\bin;D:\ProgramData\Anaconda3;" + $env:PATH

& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\manage.py" migrate --noinput
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\manage.py" runserver 127.0.0.1:8000

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "sage_assistant.py"
$requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
if (-not (Test-Path -LiteralPath $scriptPath)) { throw "sage_assistant.py was not found beside this installer." }

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python was not found. Install Python 3.10 or newer, enable 'Add python.exe to PATH', then run this installer again."
}
$pythonCommandPath = $pythonCommand.Source
try {
    $pythonVersion = & $pythonCommandPath --version 2>&1
    if ($LASTEXITCODE -ne 0 -or "$pythonVersion" -notmatch "Python 3\.") { throw "Python did not start successfully." }
    $pythonPath = (& $pythonCommandPath -c "import sys; print(sys.executable)").Trim()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pythonPath)) { throw "Could not locate the Python executable." }
} catch {
    throw "The 'python' command points to a Windows Store alias or a non-working installation. Install Python 3.10 or newer from python.org, enable 'Add python.exe to PATH', open a new PowerShell window, and run this installer again."
}

Write-Host "Installing SAGE dependencies..."
& $pythonPath -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& $pythonPath -m pip install -r $requirementsPath
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Review the pip error above." }

$pythonwPath = Join-Path (Split-Path $pythonPath) "pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonwPath)) { $pythonwPath = $pythonPath }
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "SAGE Voice Assistant.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonwPath
$shortcut.Arguments = "`"$scriptPath`""
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = "Start SAGE voice assistant when you sign in"
$shortcut.Save()

Write-Host "SAGE is installed. It will start when you sign in to Windows."
Write-Host "To start it now, run: `"$pythonPath`" `"$scriptPath`""
Write-Host "To remove startup, delete: $shortcutPath"

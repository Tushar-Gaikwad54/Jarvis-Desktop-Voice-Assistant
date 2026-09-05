# Creates a Clean Desktop and Project Shortcut for J.A.R.V.I.S. (No Background Console Window)
$WScriptShell = New-Object -ComObject WScript.Shell

$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}
$PythonwExe = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$MainPy = Join-Path $ProjectDir "main.py"

if (-not (Test-Path $PythonwExe)) {
    $PythonwExe = "pythonw.exe"
}

# Helper to configure shortcut
function Setup-JarvisShortcut($ShortcutPath) {
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PythonwExe
    $Shortcut.Arguments = "`"$MainPy`""
    $Shortcut.WorkingDirectory = $ProjectDir
    $Shortcut.Description = "J.A.R.V.I.S. Voice Assistant & Computer Agent"
    $Shortcut.IconLocation = "$env:SystemRoot\system32\imageres.dll,109"
    $Shortcut.Save()
}

# 1. Shortcut on Desktop
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
Setup-JarvisShortcut("$DesktopPath\J.A.R.V.I.S.lnk")

# 2. Shortcut in Project folder
Setup-JarvisShortcut("$ProjectDir\J.A.R.V.I.S.lnk")

Write-Host "J.A.R.V.I.S. Clean Shortcuts created successfully!"

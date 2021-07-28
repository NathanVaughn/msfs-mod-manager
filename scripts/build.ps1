param (
    [switch]$debug = $false,
    [switch]$installer = $false
)

Remove-Item build -Recurse -Force -ErrorAction Ignore
Remove-Item dist -Recurse -Force -ErrorAction Ignore

$pyside6_location = python -c "import os, PySide6; print(os.path.dirname(PySide6.__file__))"
$base_command = ("pyinstaller main.py " +
                "--clean " +
                "--noconfirm " +
                "--onedir " +
                "--name=MSFSModManager " +
                "--add-data='app/assets;assets' " +
                "--add-data='$pyside6_location/plugins;plugins' " +
                "--add-data='$pyside6_location/translations;translations' " +
                "--add-data='$pyside6_location/qt.conf;.' " +
                "--icon=app/assets/icon.ico " +
                "--hiddenimport=patoolib.programs " +
                "--hiddenimport=patoolib.programs.p7zip " +
                "--hiddenimport=patoolib.programs.rar " +
                "--hiddenimport=patoolib.programs.unrar " +
                "--hiddenimport=patoolib.programs.zip " +
                "--hiddenimport=patoolib.programs.unzip " +
                "--hiddenimport=patoolib.programs.tar " +
                "--hiddenimport=patoolib.programs.py_bz2 " +
                "--hiddenimport=patoolib.programs.py_echo " +
                "--hiddenimport=patoolib.programs.py_gzip " +
                "--hiddenimport=patoolib.programs.py_lzma " +
                "--hiddenimport=patoolib.programs.py_tarfile " +
                "--hiddenimport=patoolib.programs.py_zipfile ")

if ($debug) {
    $full_command = $base_command + " --console"
} else {
    $full_command = $base_command + " --noconsole"
}

Write-Output "Executing: $full_command"
Invoke-Expression $full_command

#if ($installer) {
#    Write-Output "Building installer"
#    pipenv run fbs installer
#}
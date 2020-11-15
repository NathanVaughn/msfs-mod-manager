param (
    [switch]$debug = $false,
    [switch]$installer = $false
)

Write-Output "Cleaning existing build"
pipenv run fbs clean
cp src\build\settings\base.json src\main\resources\base\base.json

Write-Output "Building exe"
if ($debug) {
    pipenv run fbs freeze --debug
} else {
    pipenv run fbs freeze
}

if ($installer) {
    Write-Output "Building installer"
    pipenv run fbs installer
}
param (
    [switch]$debug = $false,
    [switch]$installer = $false
)

pipenv run fbs clean
cp src\build\settings\base.json src\main\resources\base\base.json

if ($debug) {
    pipenv run fbs freeze --debug
} else {
    pipenv run fbs freeze
}

if ($installer) {
    pipenv run fbs installer
}
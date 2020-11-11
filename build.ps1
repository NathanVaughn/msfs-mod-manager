param (
    [switch]$debug = $false
)

fbs clean
cp src\build\settings\base.json src\main\resources\base\base.json

if ($debug) {
    fbs freeze --debug
} else {
    fbs freeze
}

fbs installer
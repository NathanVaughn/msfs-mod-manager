param (
    [switch]$debug = $false
)

fbs clean

if ($debug) {
    fbs freeze --debug
} else {
    fbs freeze
}

fbs installer
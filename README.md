# MSFS Mod Manager

<img src="src/main/resources/base/icons/icon.png" alt="Bad Logo (I'm not good at graphic design)" width="200"/>

This is a very early external mod manager for the new Microsoft Flight Simulator.

![Main Screen](screenshots/main-1.png)

## Features

### Automatic Installation Detection

The program automatically tries to determine where the sim is installed, for you.
No rooting around inside the `AppData` folder.

![Sim Directory Detection](screenshots/auto-detect.png)

If the program can't automatically find the installation folder (you put it somewhere
non-standard), you can manually select the location that contains `FlightSimulator.CFG`.

![Manual Selection](screenshots/manual-select.png)

This is normally `%USER%\AppData\Roaming\Microsoft Flight Simulator` or
`%USER%\AppData\Local\Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalCache`

### Super Easy Mod Installs

The program will extract an archive, find all mods inside, and install them
inside the correct folder automatically.

![Install Demo](screenshots/install.gif)

### Enable and Disable Mods

Enable and disable mods on the fly without needing to re-download them.

### More To Come

This is still under active development. Pull requests welcome!

## Usage

Just head to the
[releases page](https://github.com/NathanVaughn/msfs-mod-manager/releases)
to download the latest installer. Or, if you want to live life on the edge,
run the code from source, as described below.

Note: If you want extract `.rar` or `.7z` files with the program, you'll need
to have [7zip](https://www.7-zip.org/) installed.

## Running/Building From Source

To run the program from source, first install [Python 3.6](https://www.python.org/downloads/release/python-368/).
Next, install the dependencies:

```bash
python -m pip install pipenv
pipenv install
```

Activate the newly created virtual environment with `pipenv shell`.

To run the program, use `fbs run`.

To build the program, use `fbs freeze` and optionally `fbs installer`.

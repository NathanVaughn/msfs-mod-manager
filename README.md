# MSFS Mod Manager

This is a very early external mod manager for the new Microsoft Flight Simulator.

![Main Screen](screenshots/main-1.png)

## Features

### Automatic Installation Detection

The program automatically tries to determine where the sim is installed, for you.
No rooting around inside the `AppData` folder.

![Sim Directory Detection](screenshots/auto-detect.png)

### Super Easy Mod Installs

The program will extract an archive, find all mods inside, and install them
inside the correct folder automatically.

![Install Demo](screenshots/install.gif)

### Enable and Disable Mods

Enable and disable mods on the fly without needing to re-download them.

### More To Come

This is still under active development. Pull requests welcome!

## Running/Building From Source

To run the program from source, first install Python 3.7.
Next, install the dependencies.

```bash
python -m pip install pipenv
pipenv install
```

To run the program, use `fbs run`.

To build the program, use `fbs freeze`.
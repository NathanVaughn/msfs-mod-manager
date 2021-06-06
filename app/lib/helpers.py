import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

QWIDGETSIZE_MAX = (1 << 24) - 1


def resource_path(path: Path) -> Path:
    """
    Returns path to resource that works for PyInstaller and not.
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS, "assets")  # type: ignore
    else:
        base_path = Path(Path.cwd(), "app", "assets")

    print(base_path.joinpath(path))
    return base_path.joinpath(path)


def max_resize(widget: QWidget, size: QSize) -> None:
    """
    Resizes a widget to the given size while setting limits.
    Takes a widget class, and a QSize.
    """
    # limit max programmatic resize
    widget.setMaximumHeight(700)
    widget.setMaximumWidth(2000)

    # resize
    widget.resize(size)

    # reset max height to default
    widget.setMaximumHeight(QWIDGETSIZE_MAX)
    widget.setMaximumWidth(QWIDGETSIZE_MAX)

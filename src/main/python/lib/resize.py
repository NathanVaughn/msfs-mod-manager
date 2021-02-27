from PySide2.QtCore import QSize
from PySide2.QtWidgets import QWidget

QWIDGETSIZE_MAX = (1 << 24) - 1


def max_resize(widget: QWidget, size: QSize) -> None:
    """Resizes a widget to the given size while setting limits.
    Takes a widget class, and a QSize."""
    # limit max programmatic resize
    widget.setMaximumHeight(700)
    widget.setMaximumWidth(2000)

    # resize
    # pylance doesn't connect to the correct function definition
    widget.resize(size) # type: ignore

    # reset max height to default
    widget.setMaximumHeight(QWIDGETSIZE_MAX)
    widget.setMaximumWidth(QWIDGETSIZE_MAX)

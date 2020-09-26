QWIDGETSIZE_MAX = (1 << 24) - 1


def max_resize(widget, size):
    """Resizes a widget to the given size while setting limits.
    Takes a widget class, and a QSize."""
    # limit max programmatic resize
    widget.setMaximumHeight(700)
    widget.setMaximumWidth(2000)

    # resize
    widget.resize(size)

    # reset max height to default
    widget.setMaximumHeight(QWIDGETSIZE_MAX)
    widget.setMaximumWidth(QWIDGETSIZE_MAX)

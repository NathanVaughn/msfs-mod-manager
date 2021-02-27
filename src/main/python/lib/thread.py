from contextlib import contextmanager
from typing import Callable

import PySide2.QtCore as QtCore
from loguru import logger


class base_thread(QtCore.QThread):
    """Base thread class."""

    activity_update = QtCore.Signal(object)
    percent_update = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, function: Callable) -> None:
        """Initialize the thread."""
        self.function = function
        QtCore.QThread.__init__(self)

    def run(self) -> None:
        """Start thread."""
        logger.debug("Running thread")
        try:
            output = self.function()
            self.finished.emit(output) # type: ignore
        except Exception as e:
            self.failed.emit(e) # type: ignore
        logger.debug("Thread completed")


@contextmanager
def thread_wait(
    finished_signal: QtCore.Signal,
    timeout: int = 600000,
    finish_func: Callable = None,
    failed_signal: QtCore.Signal = None,
    failed_func: Callable = None,
    update_signal: QtCore.Signal = None,
):
    """Prevent the primary event loop from progressing without blocking GUI events.
    This progresses until the given signal is emitted or the timeout reached."""
    # https://www.jdreaver.com/posts/2014-07-03-waiting-for-signals-pyside-pyqt.html
    # create a new event loop
    loop = QtCore.QEventLoop()

    # create a finished quit function
    def finished_quit() -> None:
        loop.quit()
        # stop timer
        if timer:
            timer.stop()

    # connect the finished signal to loop quit
    finished_signal.connect(finished_quit) # type: ignore

    # if an optional finish function is provided, also connect that signal to it
    if finish_func:
        finished_signal.connect(finish_func) # type: ignore

    timer = None

    # create a timeout quit function
    def timeout_quit() -> None:
        loop.exit(1)
        logger.error("Timeout reached")

    if timeout is not None:
        # setup a timeout quit
        timer = QtCore.QTimer()
        timer.timeout.connect(timeout_quit) # type: ignore
        timer.setSingleShot(True)
        timer.start(timeout)

        if update_signal:
            update_signal.connect(lambda: timer.start(timeout)) # type: ignore

    # create a failed quit function
    def failed_quit(err) -> None:
        # exit loop and
        loop.exit(1)
        # stop timer
        if timer:
            timer.stop()
        # call provided failure function
        failed_func(err)

    # if an optional failure function is provided, also connect that signal to it
    if failed_signal and failed_func:
        failed_signal.connect(failed_quit) # type: ignore

    # do
    yield

    # execute the new event loop
    loop.exec_()

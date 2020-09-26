from contextlib import contextmanager

import PySide2.QtCore as QtCore
from loguru import logger


@contextmanager
def thread_wait(
    finished_signal,
    timeout=600000,
    finsh_func=None,
    failed_signal=None,
    failed_func=None,
    update_signal=None,
):
    """Prevent the primary event loop from progressing without blocking GUI events.
    This progresses until the given signal is emitted or the timeout reached."""
    # https://www.jdreaver.com/posts/2014-07-03-waiting-for-signals-pyside-pyqt.html
    # create a new event loop
    loop = QtCore.QEventLoop()

    # create a finished quit function
    def finished_quit():
        loop.quit()
        # stop timer
        if timer:
            timer.stop()

    # connect the finished signal to loop quit
    finished_signal.connect(finished_quit)

    # if an optional finish function is provided, also connect that signal to it
    if finsh_func:
        finished_signal.connect(finsh_func)

    timer = None

    # create a timeout quit function
    def timeout_quit():
        loop.exit(1)
        logger.error("Timeout reached")

    if timeout is not None:
        # setup a timeout quit
        timer = QtCore.QTimer()
        timer.timeout.connect(timeout_quit)
        timer.setSingleShot(True)
        timer.start(timeout)

        if update_signal:
            update_signal.connect(lambda: timer.start(timeout))

    # create a failed quit function
    def failed_quit(err):
        # exit loop and
        loop.exit(1)
        # stop timer
        if timer:
            timer.stop()
        # call provided failure function
        failed_func(err)

    # if an optional failure function is provided, also connect that signal to it
    if failed_signal and failed_func:
        failed_signal.connect(failed_quit)

    # do
    yield

    # execute the new event loop
    loop.exec_()

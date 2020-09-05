from contextlib import contextmanager
from loguru import logger
import PySide2.QtCore as QtCore

@contextmanager
def thread_wait(signal, timeout=600000, finsh_func=None):
    """Prevent the primary event loop from progressing without blocking GUI events,
    until the given signal is emitted or the timeout reached"""
    loop = QtCore.QEventLoop()
    signal.connect(loop.quit)

    if finsh_func:
        signal.connect(finsh_func)

    yield

    def loop_quit():
        loop.quit()
        logger.error("Timeout reached")

    if timeout is not None:
        QtCore.QTimer.singleShot(timeout, loop_quit)

    loop.exec_()

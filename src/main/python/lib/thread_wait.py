from contextlib import contextmanager
import PySide2.QtCore as QtCore

@contextmanager
def thread_wait(signal, timeout=120000, finsh_func=None):
    """Prevent the primary event loop from progressing without blocking GUI events,
    until the given signal is emitted or the timeout reached"""
    loop = QtCore.QEventLoop()
    signal.connect(loop.quit)

    if finsh_func:
        signal.connect(finsh_func)

    yield

    if timeout is not None:
        QtCore.QTimer.singleShot(timeout, loop.quit)

    loop.exec_()

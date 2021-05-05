from typing import Any, Callable, Union

import PySide2.QtCore as QtCore
from loguru import logger


class Thread(QtCore.QThread):
    """
    Base thread class.
    """

    activity_update = QtCore.Signal(object)
    percent_update = QtCore.Signal(object)

    finished = QtCore.Signal(object)
    failed = QtCore.Signal(Exception)

    def __init__(self, function: Callable) -> None:
        self.function = function
        QtCore.QThread.__init__(self)

    def run(self) -> None:
        """
        Start thread.
        """
        logger.debug("Running thread")

        try:
            output = self.function(
                activity_func=self.activity_update.emit,
                percent_func=self.percent_update.emit,
            )
            self.finished.emit(output)  # type: ignore
        except Exception as e:
            self.failed.emit(e)  # type: ignore

        logger.debug("Thread completed")


def wait_for_thread(thread: Thread) -> Any:
    """
    Run a thread in a separate event loop so as not to block the main GUI.
    """

    loop = QtCore.QEventLoop()

    # outputs can only be obtained via connected signals
    # so create some variables for the callback functions to modify
    finished_output: Any = None
    failed_output: Union[None, Exception] = None

    # callback function for finished signal
    def finished_func(thread_output):
        logger.debug("Thread has emitted finished event")

        nonlocal finished_output
        finished_output = thread_output

        # make sure to stop the event loop
        loop.exit(0)

    # callback function for failed signal
    def failed_func(thread_output):
        logger.warning("Thread has emitted failed event")

        nonlocal failed_output
        failed_output = thread_output

        # make sure to stop the event loop
        loop.exit(1)

    # connect the signals
    thread.finished.connect(finished_func)  # type: ignore
    thread.failed.connect(failed_func)  # type: ignore

    # start the thread
    thread.start()

    # execute the event loop
    loop.exec_()

    # return output values
    if failed_output is not None:
        raise failed_output  # type: ignore
    else:
        return finished_output

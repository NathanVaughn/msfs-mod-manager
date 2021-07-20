import sys

from loguru import logger
from PySide6 import QtWidgets

from app.lib.config import config
from app.lib.helpers import max_resize
from app.widgets.main_window import MainWindow


def main() -> None:
    # prepare the logger
    logger.add(
        config.LOG_FILE,
        rotation="1 MB",
        retention="1 week",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    logger.info("---------------------")
    logger.info("Launching application")

    try:
        # start app
        app = QtWidgets.QApplication()

        # create instance of main window
        app_main_window = MainWindow(parent=app, qapp=app)

        # load data
        app_main_window.main_widget.find_sim_path()
        # app_main_window.main_widget.check_version()
        app_main_window.main_widget.refresh(first=True)

        # resize and show
        max_resize(app_main_window, app_main_window.sizeHint())
        app_main_window.show()

        # execute the application
        sys.exit(app.exec())

    except Exception as e:
        if isinstance(e, SystemExit):
            logger.info("System exit requested")
        else:
            logger.exception("Uncaught exception in application")


if __name__ == "__main__":
    main()

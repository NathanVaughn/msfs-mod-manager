import sys

from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger

from lib.config import config
from lib.helpers import max_resize
from widgets.main_window import MainWindow


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
        appctxt = ApplicationContext()
        app = appctxt.app

        # create instance of main window
        app_main_window = MainWindow(parent=app, appctxt=appctxt)

        # load data
        app_main_window.main_widget.find_sim_path()
        # app_main_window.main_widget.check_version()
        app_main_window.main_widget.refresh(first=True)

        # resize and show
        max_resize(app_main_window, app_main_window.sizeHint())
        app_main_window.show()

        # execute the application
        sys.exit(app.exec_())

    except Exception as e:
        if isinstance(e, SystemExit):
            logger.info("System exit requested")
        else:
            logger.exception("Uncaught exception")


if __name__ == "__main__":
    main()

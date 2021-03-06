import sys

from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger

from lib.config import DEBUG_LOG
from lib.resize import max_resize
from widgets.main_window import main_window


def main() -> None:
    # args = sys.argv

    # start app
    appctxt = ApplicationContext()
    app = appctxt.app

    # prepare the logger
    logger.add(
        DEBUG_LOG,
        rotation="1 MB",
        retention="1 week",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    logger.info("-----------------------")
    logger.info("Launching application")

    try:
        # create instance of main window
        app_main_window = main_window(app, appctxt)
        # build the main window
        app_main_window.build()
        app_main_window.set_theme()

        # load data
        app_main_window.main_widget.find_sim()
        app_main_window.main_widget.check_version()
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

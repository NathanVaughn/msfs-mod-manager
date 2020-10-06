import sys

from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger

from lib.config import DEBUG_LOG
from lib.resize import max_resize
from widgets.main_window import main_window

if __name__ == "__main__":
    args = sys.argv

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
        main_window = main_window(app, appctxt)
        # build the main window
        main_window.build()
        main_window.set_theme()

        # load data
        main_window.main_widget.find_sim()
        main_window.main_widget.check_version()
        main_window.main_widget.refresh(first=True)

        # resize and show
        max_resize(main_window, main_window.sizeHint())
        main_window.show()

        # execute the application
        sys.exit(app.exec_())
    except Exception as e:
        if not isinstance(e, SystemExit):
            logger.exception("Uncaught exception")

import sys
import os
from loguru import logger

from fbs_runtime.application_context.PySide2 import ApplicationContext

from lib.config import BASE_FOLDER
from widgets.main_window import main_window

if __name__ == "__main__":
    args = sys.argv

    # start app
    appctxt = ApplicationContext()
    app = appctxt.app

    # prepare the logger
    logger.add(os.path.join(BASE_FOLDER, "debug.log"), rotation="1 MB", backtrace=True, diagnose=True, enqueue=True)
    logger.info("-----------------------")
    logger.info("Launching application")

    # create instance of main window
    main_window = main_window(app, appctxt)
    # build the main window
    main_window.build()
    main_window.set_theme()

    # load data
    main_window.main_widget.find_sim()
    main_window.main_widget.check_version()
    main_window.main_widget.refresh()

    # resize and show
    main_window.resize(main_window.sizeHint())
    main_window.show()

    # execute the application
    sys.exit(app.exec_())

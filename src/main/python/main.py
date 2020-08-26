import sys

from fbs_runtime.application_context.PySide2 import ApplicationContext
from widgets.main_window import main_window

if __name__ == "__main__":
    args = sys.argv

    appctxt = ApplicationContext()
    app = appctxt.app

    # create instance of main window
    main_window = main_window(app, appctxt)
    # build the main window
    main_window.build()

    # load data
    main_window.main_widget.find_sim()
    main_window.main_widget.refresh()

    # resize and show
    main_window.resize(main_window.sizeHint())
    main_window.show()

    # execute the application
    sys.exit(app.exec_())

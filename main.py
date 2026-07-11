import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

import database
import config
from ui.dashboard import Dashboard


def main():
    # 1. Create all database tables (safe to call every run)
    database.create_tables()
    database.ensure_truck_tables()
    database.upgrade_tables()
    database.upgrade_truck_entries()
    try:
        database.init_new_modules()
    except Exception:
        pass
    try:
        database.init_fuel_tracker()
    except Exception:
        pass
    try:
        database.init_land_rent()
    except Exception:
        pass
    try:
        database.init_people_register()
    except Exception:
        pass

    # 2. Backup the database (once per day)
    database.backup_database()

    # 3. Launch the app
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setStyleSheet(config.STYLESHEET)

    # Set window icon if logo exists
    if os.path.exists(config.LOGO_PATH):
        app.setWindowIcon(QIcon(config.LOGO_PATH))

    window = Dashboard()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
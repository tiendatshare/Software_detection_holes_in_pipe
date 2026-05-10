import sys
from PyQt6.QtWidgets import QApplication
from src.utils import language_manager as lm
import src.utils.app_config as app_config

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pipe Defect Inspector")
    lm.set_language(app_config.get("language"))
    from src.ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

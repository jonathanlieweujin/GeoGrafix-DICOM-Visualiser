import sys
from PyQt5 import QtWidgets

from gui_window import GUIWindow
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer, pyqtSlot

from PyQt5.uic import loadUi

class PlaySplashScreen(QtWidgets.QSplashScreen):
    def __init__(self):
        super(PlaySplashScreen, self).__init__()
        loadUi('./src/splash_screen.ui', self)

        self.player_label : QtWidgets.QLabel

        self.setFixedSize(800,450)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.movie = QMovie('./images/opening.gif')
        self.player_label.setMovie(self.movie)
        # layout = QtWidgets.QVBoxLayout(self)
        # layout.setFixedSize(600, 338)
        # layout.addWidget(self.movie_frame)
        # self.setLayout(layout)
        self.movie.start()
        QTimer.singleShot(4700, self.stop_movie)

    @pyqtSlot()
    def stop_movie(self):
        self.movie.stop()
        def initialize():
            import time
            time.sleep(2)
        QTimer.singleShot(0, initialize)
        self.close()
        GUIWindow().show()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen_geometry = app.primaryScreen().geometry()
    splash = PlaySplashScreen()
    x = (screen_geometry.width() - splash.width()) // 2
    y = (screen_geometry.height() - splash.height()) // 2
    splash.move(x, y)
    splash.show()
    splash.movie.start()
    sys.exit(app.exec_())

# pyinstaller --onefile -w --collect-submodules=pydicom --icon=./images/icon.ico src/jonathanlieweujin.py
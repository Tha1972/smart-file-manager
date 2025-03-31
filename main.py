from PyQt5 import QtWidgets
from gui.input_bar import InputBar

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    bar = InputBar()
    bar.show()
    app.exec_()

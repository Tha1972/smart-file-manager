# smart-file-assistant/gui/input_bar.py
from PyQt5 import QtWidgets, QtCore, QtGui
from core.command_executor import parse_instruction, execute_command

class InputBar(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        width = 600
        total_height = 160
        self.setGeometry(
            (screen.width() - width) // 2,
            screen.height() - total_height - 40,
            width,
            total_height
        )

        container = QtWidgets.QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 230);
                border-radius: 20px;
            }
        """)
        container.setGeometry(0, 0, width, total_height)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        self.output_box = QtWidgets.QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.output_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(20, 20, 20, 200);
                border-radius: 12px;
                color: white;
                font-size: 15px;
                padding: 8px;
            }
        """)
        self.output_box.setFixedHeight(80)
        self.output_box.setGraphicsEffect(QtWidgets.QGraphicsOpacityEffect(self.output_box))
        self.output_box.hide()

        input_row = QtWidgets.QHBoxLayout()
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Message Assistant")
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 18px;
            }
        """)
        self.input.returnPressed.connect(self.send_command)

        send_button = QtWidgets.QPushButton("\u27A4")
        send_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #bbbbbb;
                border: none;
                border-radius: 16px;
                font-size: 18px;
                width: 32px;
                height: 32px;
            }
            QPushButton:hover {
                background-color: #999999;
            }
        """)
        send_button.clicked.connect(self.send_command)

        input_row.addWidget(self.input, 1)
        input_row.addWidget(send_button)

        layout.addWidget(self.output_box)
        layout.addLayout(input_row)

        self.animation = QtCore.QPropertyAnimation(
            self.output_box.graphicsEffect(), b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)

    def send_command(self):
        text = self.input.text().strip()
        if text:
            self.input.setEnabled(False)
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            QtCore.QTimer.singleShot(50, lambda: self.process_command(text))

    def process_command(self, text):
        command = parse_instruction(text)
        result = execute_command(command)
        self.input.setEnabled(True)
        QtWidgets.QApplication.restoreOverrideCursor()

        if result:
            self.output_box.setText(result)
            self.output_box.show()
            self.animation.start()
        else:
            self.output_box.hide()

        self.input.clear()
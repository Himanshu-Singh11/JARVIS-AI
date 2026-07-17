from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
)
from PyQt5.QtGui import (
    QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
)
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os

env_vars = dotenv_values('.env')
Assistantname = env_vars.get('Assistantname="JARVIS"') or "JARVIS AI"
current_dir = os.getcwd()
TempDirPath = os.path.join(current_dir, "Data")
DataDirPath = TempDirPath
FilesDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")
old_chat_message = ""

def AnswerModifier(text):
    return text.strip()

def QueryModifier(text):
    return text.strip()

def ensure_file_exists(filepath):
    if not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding='utf-8') as f:
            f.write("")

def GraphicsDirectoryPath(filename):
    return os.path.join(GraphicsDirPath, filename)

def TempDirectoryPath(filename):
    return os.path.join(TempDirPath, filename)

def SetMicrophoneStatus(Command):
    filename = os.path.join(DataDirPath, "Mic.data")
    ensure_file_exists(filename)
    with open(filename, "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    filename = os.path.join(DataDirPath, "Mic.data")
    ensure_file_exists(filename)
    with open(filename, "r", encoding='utf-8') as file:
        return file.read()

def SetAssistantStatus(Status):
    filename = os.path.join(DataDirPath, "Status.data")
    ensure_file_exists(filename)
    with open(filename, "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    filename = os.path.join(DataDirPath, "Status.data")
    ensure_file_exists(filename)
    with open(filename, "r", encoding='utf-8') as file:
        return file.read()

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def ShowTextToScreen(Text):
    filename = os.path.join(DataDirPath, "Responses.data")
    ensure_file_exists(filename)
    with open(filename, "w", encoding='utf-8') as file:
        file.write(Text)

class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-100)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        layout.addWidget(self.chat_text_edit)

        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie_path = os.path.join(FilesDirPath, "Jarvis.gif")
        if os.path.exists(movie_path):
            movie = QMovie(movie_path)
            max_gif_size_W, max_gif_size_H = 400, 200
            movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
            self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            self.gif_label.setMovie(movie)
            movie.start()
        else:
            print(f"Gif not found: {movie_path}")
            self.gif_label.setText("GIF missing")
        layout.addWidget(self.gif_label)

        self.label = QLabel("")
        self.label.setStyleSheet(
            "color: white; font-size:16px; margin-right: 195px; border: none; margin-top: -30px;"
        )
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        # Removed duplicate addition of gif_label here

        self.setStyleSheet("background-color: black;")
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        text_color = QColor(Qt.blue)
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)

        self.toggled = True
        self.icon_label = QLabel()
        self.load_icon(os.path.join(FilesDirPath, "Mic_off.jpg"))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

        self.chat_text_edit.viewport().installEventFilter(self)
        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def loadMessages(self):
        global old_chat_message
        filename = os.path.join(DataDirPath, "Responses.data")
        ensure_file_exists(filename)
        with open(filename, "r", encoding='utf-8') as file:
            messages = file.read()
        if messages and messages != old_chat_message and len(messages) > 1:
            self.addMessage(message=messages, color='White')
            old_chat_message = messages

    def SpeechRecogText(self):
        filename = os.path.join(DataDirPath, "Status.data")
        ensure_file_exists(filename)
        with open(filename, "r", encoding='utf-8') as file:
            messages = file.read()
        self.label.setText(messages)

    def load_icon(self, path, width=60, height=60):
        if not os.path.exists(path):
            print(f"Image not found: {path}")
            self.icon_label.clear()
            self.icon_label.setText("IMG missing")
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"Failed QPixmap: {path}")
            self.icon_label.clear()
            self.icon_label.setText("IMG null")
            return
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(os.path.join(FilesDirPath, "Mic_off.jpg"), 60, 60)
            MicButtonInitialed()
        else:
            self.load_icon(os.path.join(FilesDirPath, "Mic_on.jpg"), 60, 60)
            MicButtonClosed()
        self.toggled = not self.toggled

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        char_format = QTextCharFormat()
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)
        char_format.setForeground(QColor(color))
        cursor.setCharFormat(char_format)
        cursor.setBlockFormat(block_format)
        cursor.insertText(message + '\n')
        self.chat_text_edit.setTextCursor(cursor)

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # GIF fills the full background
        self.gif_label = QLabel(self)
        gif_path = os.path.join(FilesDirPath, "Jarvis.gif")
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.gif_label.setMovie(self.movie)
            self.gif_label.setAlignment(Qt.AlignCenter)
            self.movie.start()
        else:
            print(f"Gif not found: {gif_path}")
            self.movie = None
            self.gif_label.setText("GIF missing")

        # Status label — absolutely positioned, always horizontally centered
        self.label = QLabel("**", self)
        self.label.setStyleSheet("color: white; font-size:16px; background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)

        # Icon — absolutely positioned, always centered & in lower portion
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")

        # Start in Available mode by default — dark reactor, mic OFF
        SetMicrophoneStatus("False")
        SetAssistantStatus("Available ...")
        self.load_icon(os.path.join(FilesDirPath, "Mic_off.jpg"), 150, 150)
        self.last_mic_state = "False"
        self.icon_label.mousePressEvent = self.toggle_icon

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

    def resizeEvent(self, event):
        """Reposition everything on resize."""
        super().resizeEvent(event)
        w = self.width()
        h = self.height()

        # Scale GIF to 90% of window width, maintaining 16:9 ratio
        if hasattr(self, 'movie') and self.movie:
            gif_w = int(w * 0.90)
            gif_h = int(gif_w / 16 * 9)
            # Cap height at 70% of window
            if gif_h > int(h * 0.70):
                gif_h = int(h * 0.70)
                gif_w = int(gif_h * 16 / 9)
            self.movie.setScaledSize(QSize(gif_w, gif_h))
            # Center GIF horizontally, top of screen
            gif_x = (w - gif_w) // 2
            self.gif_label.setGeometry(gif_x, 0, gif_w, gif_h)
        else:
            self.gif_label.setGeometry(0, 0, w, int(h * 0.70))

        # Status label sits at 75% down, full width, centered
        label_y = int(h * 0.75)
        self.label.setGeometry(0, label_y, w, 30)

        # Arc reactor icon sits at 80% down, horizontally centered
        icon_size = 150
        icon_x = (w - icon_size) // 2
        icon_y = int(h * 0.80)
        self.icon_label.setGeometry(icon_x, icon_y, icon_size, icon_size)

    def SpeechRecogText(self):
        # Update status label
        filename = os.path.join(DataDirPath, "Status.data")
        ensure_file_exists(filename)
        with open(filename, 'r', encoding='utf-8') as file:
            messages = file.read()
            self.label.setText(messages)

        # Sync icon with mic state (handles wake word external activation)
        current_mic = GetMicrophoneStatus()
        if current_mic != self.last_mic_state:
            self.last_mic_state = current_mic
            if current_mic == "True":
                # Mic is ON → show glowing reactor
                self.load_icon(os.path.join(FilesDirPath, "Mic_on.jpg"), 150, 150)
            else:
                # Mic is OFF → show dark reactor
                self.load_icon(os.path.join(FilesDirPath, "Mic_off.jpg"), 150, 150)

    def load_icon(self, path, width=150, height=150):
        if not os.path.exists(path):
            print(f"Image not found: {path}")
            self.icon_label.clear()
            self.icon_label.setText("IMG missing")
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"Failed QPixmap: {path}")
            self.icon_label.clear()
            self.icon_label.setText("IMG null")
            return
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        # Always check real mic state from file — not a toggled flag
        current_mic = GetMicrophoneStatus()
        if current_mic == "True":
            # Currently listening → turn OFF
            self.load_icon(os.path.join(FilesDirPath, "Mic_off.jpg"), 150, 150)
            MicButtonInitialed()
            SetAssistantStatus("Available ...")
        else:
            # Currently available → start LISTENING
            self.load_icon(os.path.join(FilesDirPath, "Mic_on.jpg"), 150, 150)
            MicButtonClosed()
            SetAssistantStatus("Listening ...")

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        layout = QVBoxLayout()
        label = QLabel("**")
        layout.addWidget(label)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)

        home_button = QPushButton()
        home_icon = QIcon(os.path.join(FilesDirPath, "Home.jpg"))
        home_button.setIcon(home_icon)
        home_button.setText('  Home ')
        home_button.setStyleSheet(
            'height:40px; line-height:40px ; background-color:white ; color: black'
        )

        message_button = QPushButton()
        message_icon = QIcon(os.path.join(FilesDirPath, "Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText('  Chat ')
        message_button.setStyleSheet(
            'height:40px; line-height:40px ; background-color:white ; color: black'
        )

        minimize_button = QPushButton()
        minimize_icon = QIcon(os.path.join(FilesDirPath, "Minimize.png"))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet('background-color:white')
        minimize_button.clicked.connect(self.minimizeWindow)

        self.maximize_button = QPushButton()
        self.maximize_button.setFixedSize(25, 25)
        # maximize_icon is shown when window is small (to make it big)
        self.maximize_icon = QIcon(os.path.join(FilesDirPath, "Maximize.png"))
        # restore_icon is shown when window is big (to make it small)
        self.restore_icon = QIcon(os.path.join(FilesDirPath, "Minimize2.png"))
        
        # Window starts maximized, so show the restore icon initially
        self.maximize_button.setIcon(self.restore_icon)
        self.maximize_button.setFlat(False)
        self.maximize_button.setStyleSheet('background-color:white')
        self.maximize_button.clicked.connect(self.maximizeWindow)
        layout.addWidget(self.maximize_button)

        close_button = QPushButton()
        close_icon = QIcon(os.path.join(FilesDirPath, "Close.png"))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet('background-color:white')
        close_button.clicked.connect(self.closeWindow)

        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet('border-color: black;')

        title_label = QLabel(f"{Assistantname}")
        title_label.setStyleSheet('color: black; font-size: 18px; background-color:white')

        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)

        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        screen = QApplication.primaryScreen().availableGeometry()
        if self.parent().isMaximized():
            # Restore to half screen size, centered
            half_w = screen.width() // 2
            half_h = screen.height() // 2
            x = screen.x() + screen.width() // 4
            y = screen.y() + screen.height() // 4
            self.parent().showNormal()
            self.parent().setGeometry(x, y, half_w, half_h)
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def closeEvent(self, event):
        """Forcefully quit the speech recognition driver and exit when the window closes."""
        try:
            from Backend.SpeechToText import driver
            driver.quit()
        except Exception as e:
            print("Error closing driver:", e)
        
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "chromedriver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-f", "use-fake-ui-for-media-stream"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        import os
        os._exit(0)
        event.accept()

    def initUI(self):
        screen = QApplication.primaryScreen().availableGeometry()
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        self.setGeometry(screen)
        self.setStyleSheet("background-color: black;")
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()
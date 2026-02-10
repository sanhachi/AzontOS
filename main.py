import sys
import os
import glob
import subprocess
from PyQt5 import QtWidgets, QtCore, QtGui

class AzontOS(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AzontOS")
        
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        self.taskbar_width = 60
        self.panel_color = "rgba(30, 30, 30, 220)"
        self.accent_color = "#C30976"
        self.drawer_button_height = 180 
        self.drawer_button_y = 60

        self.setGeometry(self.screen_width - self.taskbar_width, 0, self.taskbar_width, self.screen_height)

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.SubWindow 
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # --- タスクバー ---
        self.taskbar = QtWidgets.QFrame(self)
        self.taskbar.setGeometry(0, 0, self.taskbar_width, self.height())
        self.taskbar.setStyleSheet(f"background-color: {self.panel_color}; border: none;")

        # --- 電源ボタン (四角) ---
        self.power_icon = QtWidgets.QPushButton("⏻", self.taskbar)
        self.power_icon.setGeometry(10, 10, 40, 40)
        self.power_icon.setStyleSheet(f"background-color: {self.accent_color}; color: white; font-size: 18px; border: none;")
        self.power_icon.clicked.connect(self.toggle_power_menu)

        # --- ドロワーボタン ---
        self.drawer_button = QtWidgets.QPushButton("≡", self.taskbar)
        self.drawer_button.setGeometry(0, self.drawer_button_y, self.taskbar_width, self.drawer_button_height)
        self.drawer_button.setStyleSheet("QPushButton { background-color: transparent; color: white; border: none; font-size: 24px; } QPushButton:hover { background-color: rgba(255,255,255,30); }")
        self.drawer_button.clicked.connect(self.toggle_drawer)

        # --- 時計 (最下部) ---
        self.clock_label = QtWidgets.QLabel(self.taskbar)
        self.clock_label.setGeometry(0, self.height() - 70, self.taskbar_width, 60)
        self.clock_label.setAlignment(QtCore.Qt.AlignCenter)
        self.clock_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        # --- パワーメニュー (シャットダウン/再起動/ログアウト) ---
        self.power_menu = QtWidgets.QFrame(self)
        self.power_menu.setGeometry(0, 10, 0, 40) # 初期は幅0
        self.power_menu.setStyleSheet("background-color: rgba(40, 40, 40, 250); border: 1px solid #C30976;")
        
        self.p_layout = QtWidgets.QHBoxLayout(self.power_menu)
        self.p_layout.setContentsMargins(5, 0, 5, 0)
        
        for name, cmd in [("Shutdown", "systemctl poweroff"), ("Reboot", "systemctl reboot"), ("Logout", "openbox --exit")]:
            btn = QtWidgets.QPushButton(name)
            btn.setStyleSheet("color: white; border: none; font-size: 10px; padding: 5px; background: rgba(255,255,255,10);")
            btn.clicked.connect(lambda _, c=cmd: os.system(c))
            self.p_layout.addWidget(btn)

        # --- ドロワーパネル ---
        self.drawer_panel = QtWidgets.QFrame(self)
        self.drawer_panel.setGeometry(0, self.drawer_button_y, 0, self.drawer_button_height)
        self.drawer_panel.setStyleSheet("background-color: rgba(20, 20, 20, 240); border-left: 1px solid #C30976;")
        
        self.scroll = QtWidgets.QScrollArea(self.drawer_panel)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.scroll_content = QtWidgets.QWidget()
        self.drawer_layout = QtWidgets.QHBoxLayout(self.scroll_content)
        self.drawer_layout.setContentsMargins(20, 10, 20, 10)
        self.drawer_layout.setSpacing(25) 
        self.scroll.setWidget(self.scroll_content)
        self.scroll.installEventFilter(self)

        self.apps = self.get_apps()
        self.favorites = [
            {"name": "Set", "exec": "xfce4-settings-manager", "icon": "preferences-system"},
            {"name": "Term", "exec": "x-terminal-emulator", "icon": "utilities-terminal"},
            {"name": "File", "exec": "thunar", "icon": "system-file-manager"}
        ]
        self.populate_drawer()
        self.populate_taskbar()

        layout = QtWidgets.QVBoxLayout(self.drawer_panel)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.scroll)

    def update_clock(self):
        self.clock_label.setText(QtCore.QTime.currentTime().toString("HH\nmm"))

    def toggle_power_menu(self):
        is_open = self.power_menu.width() > 0
        target_w = 220 if not is_open else 0
        total_w = self.taskbar_width + target_w
        
        if not is_open:
            self.setGeometry(self.screen_width - total_w, 0, total_w, self.screen_height)
            self.taskbar.move(target_w, 0)
        
        self.p_anim = QtCore.QPropertyAnimation(self.power_menu, b"geometry")
        self.p_anim.setDuration(200)
        self.p_anim.setEndValue(QtCore.QRect(0, 10, target_w, 40))
        if is_open:
            self.p_anim.finished.connect(lambda: (self.setGeometry(self.screen_width - self.taskbar_width, 0, self.taskbar_width, self.screen_height), self.taskbar.move(0,0)))
        self.p_anim.start()

    def toggle_drawer(self):
        is_open = self.width() > self.taskbar_width
        target_w = self.screen_width - self.taskbar_width - 100 if not is_open else 0
        if not is_open:
            self.setGeometry(self.screen_width - (self.taskbar_width + target_w), 0, self.taskbar_width + target_w, self.screen_height)
            self.taskbar.move(target_w, 0)
        self.anim = QtCore.QPropertyAnimation(self.drawer_panel, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEndValue(QtCore.QRect(0, self.drawer_button_y, target_w, self.drawer_button_height))
        if is_open:
            self.anim.finished.connect(lambda: (self.setGeometry(self.screen_width - self.taskbar_width, 0, self.taskbar_width, self.screen_height), self.taskbar.move(0,0)))
        self.anim.start()

    def reserve_taskbar_area(self):
        try:
            from Xlib import display, Xatom
            d = display.Display()
            window_id = int(self.winId())
            window = d.create_resource_object('window', window_id)
            type_atom = d.intern_atom('_NET_WM_WINDOW_TYPE')
            dock_atom = d.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
            window.change_property(type_atom, Xatom.ATOM, 32, [dock_atom])
            strut_atom = d.intern_atom('_NET_WM_STRUT_PARTIAL')
            struts = [0, self.taskbar_width, 0, 0, 0, 0, 0, self.screen_height, 0, 0, 0, 0]
            window.change_property(strut_atom, Xatom.CARDINAL, 32, struts)
            d.sync()
        except: pass

    def showEvent(self, event):
        super().showEvent(event)
        self.reserve_taskbar_area()

    def eventFilter(self, source, event):
        if source == self.scroll and event.type() == QtCore.QEvent.Wheel:
            hbar = self.scroll.horizontalScrollBar()
            hbar.setValue(hbar.value() - event.angleDelta().y())
            return True
        return super().eventFilter(source, event)

    def get_apps(self):
        apps = []
        for path in ["/usr/share/applications/*.desktop", os.path.expanduser("~/.local/share/applications/*.desktop")]:
            for df in glob.glob(path):
                try:
                    with open(df, "r", encoding="utf-8", errors="ignore") as f:
                        n, e, i = None, None, None
                        for l in f:
                            if l.startswith("Name="): n = l.strip().split("=",1)[1]
                            elif l.startswith("Exec="): e = l.strip().split("=",1)[1].split()[0]
                            elif l.startswith("Icon="): i = l.strip().split("=",1)[1]
                        if n and e: apps.append({"name": n, "exec": e, "icon": i})
                except: pass
        return sorted(apps, key=lambda x: x['name'].lower())

    def populate_drawer(self):
        for app in self.apps:
            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout(container)
            btn = QtWidgets.QToolButton()
            btn.setFixedSize(120, 120)
            icon = QtGui.QIcon.fromTheme(app["icon"])
            if icon.isNull(): btn.setText(app["name"][0])
            else: btn.setIcon(icon); btn.setIconSize(QtCore.QSize(64, 64))
            btn.setStyleSheet(f"background-color: {self.accent_color}; border: none; color: white;")
            btn.clicked.connect(lambda _, a=app["exec"]: self.launch_app(a))
            v_layout.addWidget(btn)
            v_layout.addWidget(QtWidgets.QLabel(app["name"], alignment=QtCore.Qt.AlignCenter, styleSheet="color: white; font-size: 11px;"))
            self.drawer_layout.addWidget(container)
        self.scroll_content.setMinimumWidth(len(self.apps) * 150)

    def populate_taskbar(self):
        y = 260
        for app in self.favorites:
            btn = QtWidgets.QPushButton(self.taskbar)
            btn.setGeometry(10, y, 40, 40)
            icon = QtGui.QIcon.fromTheme(app["icon"])
            if not icon.isNull(): btn.setIcon(icon); btn.setIconSize(QtCore.QSize(24, 24))
            else: btn.setText(app["name"][:1])
            btn.setStyleSheet("background-color: rgba(255,255,255,15); color: white; border: none;")
            btn.clicked.connect(lambda _, a=app["exec"]: self.launch_app(a))
            y += 50

    def launch_app(self, cmd):
        try: subprocess.Popen(cmd.split()); (self.toggle_drawer() if self.width() > self.taskbar_width else None)
        except: pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dm = AzontOS()
    dm.show()
    QtCore.QTimer.singleShot(1000, dm.reserve_taskbar_area)
    sys.exit(app.exec_())

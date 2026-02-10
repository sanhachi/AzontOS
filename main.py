import sys
import os
import glob
import subprocess
from PyQt5 import QtWidgets, QtCore, QtGui

class AzontOS(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AzontOS")
        
        # 画面サイズを取得
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # 設定値
        self.taskbar_width = 60
        self.panel_color = "rgba(30, 30, 30, 220)"
        self.accent_color = "#C30976"
        self.drawer_button_height = 180 
        self.drawer_button_y = 60

        # 初期配置：右端
        self.setGeometry(self.screen_width - self.taskbar_width, 0, self.taskbar_width, self.screen_height)

        # Bypassフラグを削除し、Dockとして登録する
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.SubWindow # これを入れることで他のウィンドウに干渉しにくくなる
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # --- UIパーツ ---
        self.taskbar = QtWidgets.QFrame(self)
        self.taskbar.setGeometry(0, 0, self.taskbar_width, self.height())
        self.taskbar.setStyleSheet(f"background-color: {self.panel_color}; border: none;")

        self.power_icon = QtWidgets.QPushButton(self.taskbar)
        self.power_icon.setGeometry(10, 10, 40, 40)
        self.power_icon.setStyleSheet(f"background-color: {self.accent_color}; border: none;")
        self.power_icon.clicked.connect(self.shutdown)

        self.drawer_button = QtWidgets.QPushButton("≡", self.taskbar)
        self.drawer_button.setGeometry(0, self.drawer_button_y, self.taskbar_width, self.drawer_button_height)
        self.drawer_button.setStyleSheet("""
            QPushButton { background-color: transparent; color: white; border: none; font-size: 24px; } 
            QPushButton:hover { background-color: rgba(255,255,255,30); }
        """)
        self.drawer_button.clicked.connect(self.toggle_drawer)

        self.drawer_panel = QtWidgets.QFrame(self)
        self.drawer_panel.setGeometry(0, self.drawer_button_y, 0, self.drawer_button_height)
        self.drawer_panel.setStyleSheet("background-color: rgba(20, 20, 20, 230); border: none;")
        
        self.scroll = QtWidgets.QScrollArea(self.drawer_panel)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent;")

        self.scroll_content = QtWidgets.QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.drawer_layout = QtWidgets.QHBoxLayout(self.scroll_content)
        self.drawer_layout.setContentsMargins(20, 10, 20, 10)
        self.drawer_layout.setSpacing(25) 
        self.scroll.setWidget(self.scroll_content)
        self.scroll.installEventFilter(self)

        self.apps = self.get_apps()
        self.favorites = self.apps[:3] if self.apps else []
        self.populate_drawer()
        self.populate_taskbar()

        layout = QtWidgets.QVBoxLayout(self.drawer_panel)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.scroll)

    def showEvent(self, event):
        super().showEvent(event)
        # ウィンドウが表示された後に領域予約を適用
        self.reserve_taskbar_area()

    def reserve_taskbar_area(self):
        """Openboxに対して強力に領域予約を通知する"""
        try:
            from Xlib import display, Xatom
            d = display.Display()
            window_id = int(self.winId())
            window = d.create_resource_object('window', window_id)

            # 1. Dock属性をセット
            type_atom = d.intern_atom('_NET_WM_WINDOW_TYPE')
            dock_atom = d.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')
            window.change_property(type_atom, Xatom.ATOM, 32, [dock_atom])

            # 2. Strut (領域予約) をセット
            # [left, right, top, bottom, L_start, L_end, R_start, R_end, ...]
            strut_partial_atom = d.intern_atom('_NET_WM_STRUT_PARTIAL')
            struts = [0, self.taskbar_width, 0, 0, 0, 0, 0, self.screen_height, 0, 0, 0, 0]
            window.change_property(strut_partial_atom, Xatom.CARDINAL, 32, struts)

            # 3. 古いマネージャ用のStrutもセット
            strut_atom = d.intern_atom('_NET_WM_STRUT')
            window.change_property(strut_atom, Xatom.CARDINAL, 32, struts[:4])

            d.sync()
        except Exception as e:
            print(f"Reserve Error: {e}")

    def eventFilter(self, source, event):
        if source == self.scroll and event.type() == QtCore.QEvent.Wheel:
            delta = event.angleDelta().y()
            hbar = self.scroll.horizontalScrollBar()
            hbar.setValue(hbar.value() - delta)
            return True
        return super().eventFilter(source, event)

    def get_apps(self):
        apps = []
        search_paths = ["/usr/share/applications/*.desktop", os.path.expanduser("~/.local/share/applications/*.desktop")]
        for path in search_paths:
            for desktop_file in glob.glob(path):
                try:
                    with open(desktop_file, "r", encoding="utf-8", errors="ignore") as f:
                        name, exec_cmd, icon = None, None, None
                        for line in f:
                            if line.startswith("Name="): name = line.strip().split("=", 1)[1]
                            elif line.startswith("Exec="): exec_cmd = line.strip().split("=", 1)[1].split()[0]
                            elif line.startswith("Icon="): icon = line.strip().split("=", 1)[1]
                        if name and exec_cmd:
                            apps.append({"name": name, "exec": exec_cmd, "icon": icon})
                except: pass
        return sorted(apps, key=lambda x: x['name'].lower())

    def populate_drawer(self):
        for app in self.apps:
            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(8)
            btn = QtWidgets.QToolButton()
            btn.setFixedSize(120, 120)
            icon = QtGui.QIcon.fromTheme(app["icon"])
            if icon.isNull(): btn.setText(app["name"][0])
            else:
                btn.setIcon(icon)
                btn.setIconSize(QtCore.QSize(64, 64))
            btn.setStyleSheet(f"background-color: {self.accent_color}; border: none; color: white; font-size: 40px;")
            # アプリ起動時にドロワーを閉じるように変更
            btn.clicked.connect(lambda _, a=app["exec"]: self.launch_app(a))
            
            label = QtWidgets.QLabel(app["name"])
            label.setFixedWidth(120)
            label.setWordWrap(True)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("color: white; font-size: 11px; font-weight: bold; border: none;")
            v_layout.addWidget(btn)
            v_layout.addWidget(label)
            self.drawer_layout.addWidget(container)
        self.scroll_content.setMinimumWidth(len(self.apps) * 150)

    def populate_taskbar(self):
        y = 260
        for app in self.favorites:
            btn = QtWidgets.QPushButton(self.taskbar)
            btn.setGeometry(10, y, 40, 40)
            btn.setStyleSheet("background-color: rgba(255,255,255,15); border: none;")
            btn.clicked.connect(lambda _, a=app["exec"]: self.launch_app(a))
            y += 50

    def toggle_drawer(self):
        is_open = self.width() > self.taskbar_width
        target_drawer_width = self.screen_width - self.taskbar_width - 100 if not is_open else 0
        total_width = self.taskbar_width + target_drawer_width

        if not is_open:
            self.setGeometry(self.screen_width - total_width, 0, total_width, self.screen_height)
            self.taskbar.move(total_width - self.taskbar_width, 0)

        self.animation = QtCore.QPropertyAnimation(self.drawer_panel, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEndValue(QtCore.QRect(0, self.drawer_button_y, target_drawer_width, self.drawer_button_height))
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        
        if is_open:
            self.animation.finished.connect(lambda: self.setGeometry(self.screen_width - self.taskbar_width, 0, self.taskbar_width, self.screen_height))
            self.animation.finished.connect(lambda: self.taskbar.move(0, 0))
            
        self.animation.start()

    def launch_app(self, cmd):
        try:
            subprocess.Popen(cmd.split())
            # ドロワーが開いていたら閉じる
            if self.width() > self.taskbar_width:
                self.toggle_drawer()
        except: pass

    def shutdown(self):
        QtWidgets.QApplication.quit()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dm = AzontOS()
    dm.show()
    # 起動後にタイミングをずらして再予約
    QtCore.QTimer.singleShot(1000, dm.reserve_taskbar_area)
    sys.exit(app.exec_())

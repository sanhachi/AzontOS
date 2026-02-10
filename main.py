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
        self.setFixedSize(screen.width(), screen.height())
        
        # フレームレス・最前面・デスクトップ層に固定
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.SubWindow # LinuxのWMで壁紙のように振る舞わせるため
        )

        # 設定値
        self.taskbar_width = 60
        self.panel_color = "rgba(30, 30, 30, 220)"
        self.accent_color = "#C30976"
        self.drawer_button_height = 180 
        self.drawer_button_y = 60

        # --- 0. 背景 ---
        self.wallpaper_label = QtWidgets.QLabel(self)
        self.wallpaper_label.setGeometry(0, 0, self.width(), self.height())
        self.setup_wallpaper()

        # --- 1. タスクバー本体 ---
        self.taskbar = QtWidgets.QFrame(self)
        self.taskbar.setGeometry(self.width() - self.taskbar_width, 0, self.taskbar_width, self.height())
        self.taskbar.setStyleSheet(f"background-color: {self.panel_color}; border: none;")

        # --- 2. 電源ボタン ---
        self.power_icon = QtWidgets.QPushButton(self)
        self.power_icon.setGeometry(self.width() - self.taskbar_width + 10, 10, 40, 40)
        self.power_icon.setStyleSheet(f"background-color: {self.accent_color}; border: none;")
        self.power_icon.clicked.connect(self.shutdown)

        # --- 3. ドロワー展開ボタン ---
        self.drawer_button = QtWidgets.QPushButton("≡", self)
        self.drawer_button.setGeometry(self.width() - self.taskbar_width, self.drawer_button_y, self.taskbar_width, self.drawer_button_height)
        self.drawer_button.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: white; 
                border: none; 
                font-size: 24px; 
            } 
            QPushButton:hover { background-color: rgba(255,255,255,30); }
        """)
        self.drawer_button.clicked.connect(self.toggle_drawer)

        # --- 4. ドロワーパネル ---
        self.drawer_panel = QtWidgets.QFrame(self)
        self.drawer_panel.setGeometry(self.width() - self.taskbar_width, self.drawer_button_y, 0, self.drawer_button_height)
        self.drawer_panel.setStyleSheet("background-color: rgba(20, 20, 20, 230); border: none;")
        
        self.scroll = QtWidgets.QScrollArea(self.drawer_panel)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent;")

        self.scroll_content = QtWidgets.QWidget()
        self.drawer_layout = QtWidgets.QHBoxLayout(self.scroll_content)
        self.drawer_layout.setContentsMargins(20, 10, 20, 10)
        self.drawer_layout.setSpacing(10)
        self.scroll.setWidget(self.scroll_content)

        # アプリ読み込み
        self.apps = self.get_apps()
        self.favorites = self.apps[:3] if self.apps else []
        self.populate_drawer()
        self.populate_taskbar()

        layout = QtWidgets.QVBoxLayout(self.drawer_panel)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.scroll)

    def setup_wallpaper(self):
        """Linux用の壁紙設定 (後で好きな画像パスに変更してください)"""
        # とりあえずModern UIに合う深い色
        self.wallpaper_label.setStyleSheet("background-color: #000000;")
        # 画像を使う場合はこちらをアンコメント
        # pixmap = QtGui.QPixmap("/usr/share/backgrounds/azont_bg.jpg")
        # self.wallpaper_label.setPixmap(pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation))

    def get_apps(self):
        """Linuxの.desktopファイルをスキャンしてアプリを取得"""
        apps = []
        # システムとユーザー両方のアプリディレクトリを確認
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
                except:
                    pass
        return sorted(apps, key=lambda x: x['name'].lower())

def populate_drawer(self):
        # 既存のボタン作成処理をリニューアル
        for app in self.apps:
            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout(container)
            
            # アイコン部分 (正方形タイル)
            btn = QtWidgets.QToolButton()
            btn.setFixedSize(120, 120)
            # アイコン画像の設定 (Papirusテーマなどから取得)
            icon = QtGui.QIcon.fromTheme(app["icon"])
            btn.setIcon(icon)
            btn.setIconSize(QtCore.QSize(64, 64))
            btn.setStyleSheet(f"background-color: {self.accent_color}; border: none;")
            btn.clicked.connect(lambda _, a=app["exec"]: self.launch_app(a))
            
            # ラベル部分 (タイルの下)
            label = QtWidgets.QLabel(app["name"][:12]) # 長すぎると崩れるので制限
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("color: white; font-size: 10px; border: none;")
            
            v_layout.addWidget(btn)
            v_layout.addWidget(label)
            self.drawer_layout.addWidget(container)
            # populate_drawerの最後にこれを追加
            self.scroll_content.adjustSize()


    def populate_taskbar(self):
        y = 260
        for app in self.favorites:
            btn = QtWidgets.QPushButton(self)
            btn.setGeometry(self.width() - self.taskbar_width + 10, y, 40, 40)
            btn.setStyleSheet("background-color: rgba(255,255,255,15); border: none;")
            btn.clicked.connect(lambda _, a=app["exec"]: self.launch_app(a))
            y += 50

    def toggle_drawer(self):
        is_open = self.drawer_panel.width() > 0
        target_width = self.width() - self.taskbar_width - 100 if not is_open else 0
        
        self.animation = QtCore.QPropertyAnimation(self.drawer_panel, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.drawer_panel.geometry())
        self.animation.setEndValue(QtCore.QRect(
            self.width() - self.taskbar_width - target_width,
            self.drawer_button_y,
            target_width,
            self.drawer_button_height
        ))
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.animation.start()

    def launch_app(self, cmd):
        # Linux用にコマンドをパースして実行
        try:
            subprocess.Popen(cmd.split())
        except:
            pass

    def shutdown(self):
        QtWidgets.QApplication.quit()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dm = AzontOS()
    dm.show()

    sys.exit(app.exec_())



import sys, os, glob, subprocess
from PyQt5 import QtWidgets, QtCore, QtGui

class AzontOS(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # 画面サイズ取得
        scr = QtWidgets.QApplication.primaryScreen().geometry()
        self.sw, self.sh = scr.width(), scr.height()
        
        # 設定値（AzontOS Alpha 仕様）
        self.tw, self.accent = 60, "#C30976"
        self.dh, self.dy = 180, 60  # ドロワーの高さと出現位置
        
        # OS名の設定
        self.setWindowTitle("AzontOS Alpha")
        
        # ウィンドウ属性：最前面固定（Dock属性）かつWMの干渉を回避
        self.setGeometry(self.sw - self.tw, 0, self.tw, self.sh)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | 
            QtCore.Qt.WindowStaysOnTopHint | 
            QtCore.Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_X11NetWmWindowTypeDock) # システムドックとして認識させる

        # --- タスクバー本体 ---
        self.tb = QtWidgets.QFrame(self)
        self.tb.setGeometry(0, 0, self.tw, self.sh)
        self.tb.setStyleSheet("background: rgba(30,30,30,220); border: none;")

        # 電源ボタン
        self.p_btn = QtWidgets.QPushButton("⏻", self.tb)
        self.p_btn.setGeometry(10, 10, 40, 40)
        self.p_btn.setStyleSheet(f"background:{self.accent}; color:white; border:none; font-size:18px;")
        self.p_btn.clicked.connect(self.toggle_power)

        # ドロワーボタン (1:3 ドロワー)
        self.d_btn = QtWidgets.QPushButton("≡", self.tb)
        self.d_btn.setGeometry(0, self.dy, self.tw, self.dh)
        self.d_btn.setStyleSheet("background:transparent; color:white; border:none; font-size:24px;")
        self.d_btn.clicked.connect(self.toggle_drawer)

        # 時計
        self.clock = QtWidgets.QLabel(self.tb)
        self.clock.setGeometry(0, self.sh-70, self.tw, 60)
        self.clock.setAlignment(QtCore.Qt.AlignCenter)
        self.clock.setStyleSheet("color:white; font-weight:bold; font-size:12px;")
        self.tm = QtCore.QTimer(self)
        self.tm.timeout.connect(lambda: self.clock.setText(QtCore.QTime.currentTime().toString("HH\nmm")))
        self.tm.start(1000)

        # パワーメニュー (隠しパネル)
        self.pm = QtWidgets.QFrame(self)
        self.pm.setGeometry(0, 10, 0, 40)
        self.pm.setStyleSheet(f"background:rgba(40,40,40,250); border:1px solid {self.accent};")
        p_lay = QtWidgets.QHBoxLayout(self.pm)
        p_lay.setContentsMargins(5,0,5,0)
        for n, c in [("Shut", "poweroff"), ("Reboot", "reboot"), ("Out", "pkill X")]:
            b = QtWidgets.QPushButton(n)
            b.setStyleSheet("color:white; font-size:10px; border:none; background:rgba(255,255,255,10);")
            b.clicked.connect(lambda _, cmd=c: subprocess.Popen(cmd.split()))
            p_lay.addWidget(b)

        # --- ドロワーパネル (水平展開) ---
        self.dp = QtWidgets.QFrame(self)
        self.dp.setGeometry(0, self.dy, 0, self.dh)
        self.dp.setStyleSheet(f"background:rgba(20,20,20,245); border-left:1px solid {self.accent};")
        
        self.scroll = QtWidgets.QScrollArea(self.dp)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.sc = QtWidgets.QWidget()
        self.sc.setFixedHeight(self.dh) # 縦幅固定で縦スクロールを物理的に排除
        self.dl = QtWidgets.QHBoxLayout(self.sc)
        self.dl.setContentsMargins(20,0,20,0)
        self.dl.setSpacing(30)
        self.scroll.setWidget(self.sc)
        self.scroll.installEventFilter(self) # マウスホイール用
        
        QtWidgets.QVBoxLayout(self.dp).addWidget(self.scroll)

        # アプリ読み込みとピン留め
        self.apps = self.get_apps()
        self.favs = [
            {"name":"Set","ex":"xfce4-settings-manager","ic":"preferences-system"},
            {"name":"Term","ex":"x-terminal-emulator","ic":"utilities-terminal"},
            {"name":"File","ex":"thunar","ic":"system-file-manager"}
        ]
        self.populate()

    def populate(self):
        # ドロワー内：文字切れ対策版
        for a in self.apps:
            w = QtWidgets.QWidget()
            l = QtWidgets.QVBoxLayout(w)
            b = QtWidgets.QToolButton()
            b.setFixedSize(80, 80)
            ic = QtGui.QIcon.fromTheme(a["ic"])
            if ic.isNull(): b.setText(a["name"][0])
            else: b.setIcon(ic); b.setIconSize(QtCore.QSize(40, 40))
            b.setStyleSheet(f"background:{self.accent}; border-radius:10px; color:white;")
            b.clicked.connect(lambda _, ex=a["ex"]: subprocess.Popen(ex.split()))
            
            # ラベル：幅を広げ、2行表示を許可して文字切れを完全に防ぐ
            txt = QtWidgets.QLabel(a["name"])
            txt.setFixedWidth(140) 
            txt.setWordWrap(True)
            txt.setAlignment(QtCore.Qt.AlignCenter)
            txt.setStyleSheet("color:white; font-size:10px;")
            
            l.addWidget(b, alignment=QtCore.Qt.AlignCenter)
            l.addWidget(txt, alignment=QtCore.Qt.AlignCenter)
            self.dl.addWidget(w)
        self.sc.setMinimumWidth(len(self.apps) * 160)
        
        # ピン留めアプリ
        y = 260
        for f in self.favs:
            b = QtWidgets.QPushButton(self.tb)
            b.setGeometry(10, y, 40, 40)
            ic = QtGui.QIcon.fromTheme(f["ic"])
            if not ic.isNull(): b.setIcon(ic); b.setIconSize(QtCore.QSize(24,24))
            else: b.setText(f["name"][0])
            b.setStyleSheet("background:rgba(255,255,255,15); border-radius:5px; color:white; border:none;")
            b.clicked.connect(lambda _, ex=f["ex"]: subprocess.Popen(ex.split()))
            y += 55

    def eventFilter(self, o, e):
        if o == self.scroll and e.type() == QtCore.QEvent.Wheel:
            # ホイール回転を横スクロールに変換
            self.scroll.horizontalScrollBar().setValue(self.scroll.horizontalScrollBar().value() - e.angleDelta().y())
            return True
        return False

    def get_apps(self):
        res = []
        paths = ["/usr/share/applications/*.desktop", os.path.expanduser("~/.local/share/applications/*.desktop")]
        for p in paths:
            for f in glob.glob(p):
                try:
                    with open(f, "r") as d:
                        n, ex, ic = "", "", ""
                        for line in d:
                            if line.startswith("Name="): n = line.strip().split("=")[1]
                            elif line.startswith("Exec="): ex = line.strip().split("=")[1].split()[0]
                            elif line.startswith("Icon="): ic = line.strip().split("=")[1]
                        if n and ex: res.append({"name":n, "ex":ex, "ic":ic})
                except: pass
        return sorted(res, key=lambda x: x["name"].lower())

    def toggle_power(self):
        is_open = self.pm.width() > 0
        target_w = 180 if not is_open else 0
        if not is_open:
            self.setGeometry(self.sw-(self.tw+target_w), 0, self.tw+target_w, self.sh)
            self.tb.move(target_w, 0)
        self.pa = QtCore.QPropertyAnimation(self.pm, b"geometry")
        self.pa.setDuration(200)
        self.pa.setEndValue(QtCore.QRect(0,10,target_w,40))
        if is_open:
            self.pa.finished.connect(lambda: (self.setGeometry(self.sw-self.tw, 0, self.tw, self.sh), self.tb.move(0,0)))
        self.pa.start()

    def toggle_drawer(self):
        is_open = self.width() > self.tw
        # 展開幅：画面全体からタスクバー分を引いたサイズ
        target_w = self.sw - self.tw if not is_open else 0
        
        if not is_open:
            # 展開時はウィンドウ全体を広げるが、タスクバーの位置を右端に維持
            self.setGeometry(0, 0, self.sw, self.sh)
            self.tb.move(self.sw - self.tw, 0)
        
        self.da = QtCore.QPropertyAnimation(self.dp, b"geometry")
        self.da.setDuration(300)
        self.da.setEndValue(QtCore.QRect(0, self.dy, target_w, self.dh))
        
        if is_open:
            self.da.finished.connect(lambda: (
                self.setGeometry(self.sw - self.tw, 0, self.tw, self.sh),
                self.tb.move(0, 0)
            ))
        self.da.start()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = AzontOS()
    ex.show()
    sys.exit(app.exec_())

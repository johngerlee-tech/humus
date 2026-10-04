#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《黑金魔法術─永續食物循環系統》- 區網多人互動教學工具箱與圖形介面啟動器
整合 PyQt5 桌面圖形介面、Threaded HTTP Server、區網 IP 自動偵測、學生連線 QR Code 與本地 Game-data 資料儲存
"""

import os
import re
import sys
import time
import json
import socket
import urllib.parse
import mimetypes
import webbrowser
import threading
import traceback
import importlib.util
import subprocess
import io
import base64
import zipfile
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# ------------------------------------------------------
# 記錄啟動日誌與安全輸出物件 (防 PyInstaller --windowed 崩潰)
# ------------------------------------------------------
def _early_log(msg):
    try:
        p = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)), "startup_debug.log")
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

class _NullWriter:
    def write(self, *args, **kwargs):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()

# ------------------------------------------------------
# 自動檢查必要相依套件
# ------------------------------------------------------
REQUIRED_PACKAGES = {
    "PyQt5": "PyQt5",
    "PyQt5.QtWebEngineWidgets": "PyQtWebEngine",
    "qrcode": "qrcode",
    "PIL": "Pillow",
}

def ensure_dependencies():
    if getattr(sys, "frozen", False):
        return

    missing_specs = []
    seen_pip = set()
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(module_name) is None and pip_name not in seen_pip:
            missing_specs.append(pip_name)
            seen_pip.add(pip_name)

    if not missing_specs:
        return

    for pkg in missing_specs:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
        except Exception as e:
            print(f"安裝套件失敗: {e}")

ensure_dependencies()

# ------------------------------------------------------
# 匯入 GUI 與繪圖相關模組
# ------------------------------------------------------
import qrcode
from PIL import Image

from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt, QRect, QRectF
from PyQt5.QtGui import (QIcon, QPixmap, QImage, QPainter, QColor,
                         QLinearGradient, QPen, QBrush, QCursor)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QLineEdit, QComboBox, QPushButton, QHBoxLayout,
                             QFrame, QToolTip, QMessageBox, QDialog, QFileDialog)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 安全顯示 ToolTip 輔助函式
def show_app_tooltip(text, widget=None, msec=1500):
    try:
        QToolTip.showText(QCursor.pos(), text, widget, QRect(), msec)
    except Exception:
        try:
            QToolTip.showText(QCursor.pos(), text, widget)
        except Exception:
            pass

# 設定 Windows 工作列識別碼
try:
    import ctypes
    myappid = 'teacher.blackgold.magic.rpg.launcher.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.environ.get("WEBCLASS_ORIGINAL_BASE") or os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()
DATA_DIR = os.path.join(BASE_DIR, "Game-data")
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
CUSTOM_IMG_DIR = os.path.join(IMAGES_DIR, "custom")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CUSTOM_IMG_DIR, exist_ok=True)

# 補充常見 MIME 類型
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/webp", ".webp")

def ensure_app_icon():
    ico_path = os.path.join(BASE_DIR, "app_icon.ico")
    if os.path.exists(ico_path):
        return ico_path
    png_path = os.path.join(BASE_DIR, "app_icon.png")
    if os.path.exists(png_path):
        return png_path
    return ""

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# 從 server.py 匯入請求處理器
try:
    from server import RPGGameRequestHandler
except ImportError:
    from http.server import SimpleHTTPRequestHandler
    RPGGameRequestHandler = SimpleHTTPRequestHandler

# ------------------------------------------------------
# 多執行緒 HTTP 伺服器 (支援端口重用與平滑關閉)
# ------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        super().server_bind()

class HTTPServerThread(QThread):
    server_started = pyqtSignal(str, str) # lan_url, local_url
    server_error = pyqtSignal(str)

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.port = port
        self.httpd = None

    def run(self):
        try:
            self.httpd = ThreadedHTTPServer(("", self.port), RPGGameRequestHandler)
        except OSError as e:
            self.server_error.emit(str(e))
            return

        ip = get_local_ip()
        lan_url = f"http://{ip}:{self.port}"
        local_url = f"http://127.0.0.1:{self.port}"
        self.server_started.emit(lan_url, local_url)
        try:
            self.httpd.serve_forever()
        except Exception:
            pass

    def stop(self):
        if self.httpd:
            try:
                if hasattr(self.httpd, "socket") and self.httpd.socket:
                    self.httpd.socket.close()
            except Exception:
                pass

            try:
                t = threading.Thread(target=self.httpd.shutdown, daemon=True)
                t.start()
            except Exception:
                pass

            try:
                self.httpd.server_close()
            except Exception:
                pass

# ------------------------------------------------------
# 學生連線 QR Code 彈出對話框
# ------------------------------------------------------
class QRCodeDialog(QDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.pixmap = None
        self.setWindowTitle("📱 學生掃描 QR Code 連線")
        self.setFixedSize(460, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QDialog {
                background: #0F172A;
                font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
            }
            QLabel#qrTitle {
                color: #F8FAFC;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#qrSubtitle {
                color: #94A3B8;
                font-size: 13px;
            }
            QLabel#qrImageLabel {
                background: #FFFFFF;
                border: 3px solid #10B981;
                border-radius: 16px;
                padding: 12px;
            }
            QLabel#urlDisplay {
                color: #34D399;
                font-size: 15px;
                font-weight: bold;
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 8px;
                padding: 6px 12px;
            }
            QPushButton#btnCopy {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton#btnCopy:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
            QPushButton#btnSave {
                background: rgba(255, 255, 255, 0.12);
                color: #F1F5F9;
                font-weight: 500;
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton#btnSave:hover {
                background: rgba(255, 255, 255, 0.22);
            }
            QPushButton#btnClose {
                background: rgba(255, 255, 255, 0.08);
                color: #94A3B8;
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton#btnClose:hover {
                background: rgba(255, 255, 255, 0.15);
                color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        titleLabel = QLabel("📱 學生掃描 QR Code 連線開戰")
        titleLabel.setObjectName("qrTitle")
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)

        subLabel = QLabel("請學生在同一教室區網（Wi-Fi 或有線網路）下，拿起平板或手機掃描 QR Code：")
        subLabel.setObjectName("qrSubtitle")
        subLabel.setAlignment(Qt.AlignCenter)
        subLabel.setWordWrap(True)
        layout.addWidget(subLabel)

        self.qrLabel = QLabel()
        self.qrLabel.setObjectName("qrImageLabel")
        self.qrLabel.setAlignment(Qt.AlignCenter)
        self.qrLabel.setFixedSize(290, 290)
        self.generateQRCode()
        layout.addWidget(self.qrLabel, 0, Qt.AlignCenter)

        self.urlLabel = QLabel(self.url)
        self.urlLabel.setObjectName("urlDisplay")
        self.urlLabel.setAlignment(Qt.AlignCenter)
        self.urlLabel.setCursor(QCursor(Qt.PointingHandCursor))
        self.urlLabel.setToolTip("點擊複製網址")
        self.urlLabel.mousePressEvent = self.copyUrl
        layout.addWidget(self.urlLabel)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(10)

        copyBtn = QPushButton("📋 複製網址")
        copyBtn.setObjectName("btnCopy")
        copyBtn.setCursor(QCursor(Qt.PointingHandCursor))
        copyBtn.clicked.connect(self.copyUrl)
        btnLayout.addWidget(copyBtn)

        saveBtn = QPushButton("💾 儲存圖片")
        saveBtn.setObjectName("btnSave")
        saveBtn.setCursor(QCursor(Qt.PointingHandCursor))
        saveBtn.clicked.connect(self.saveQRImage)
        btnLayout.addWidget(saveBtn)

        closeBtn = QPushButton("✕ 關閉")
        closeBtn.setObjectName("btnClose")
        closeBtn.setCursor(QCursor(Qt.PointingHandCursor))
        closeBtn.clicked.connect(self.accept)
        btnLayout.addWidget(closeBtn)

        layout.addLayout(btnLayout)

    def generateQRCode(self):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(self.url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")

            qimg = QImage()
            qimg.loadFromData(buffer.getvalue())
            self.pixmap = QPixmap.fromImage(qimg).scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qrLabel.setPixmap(self.pixmap)
        except Exception as e:
            self.qrLabel.setText(f"QR Code 生成失敗\n{e}")

    def copyUrl(self, event=None):
        QApplication.clipboard().setText(self.url)
        show_app_tooltip("✅ 網址已複製到剪貼簿！", self, 1500)

    def saveQRImage(self):
        if not self.pixmap:
            return
        filePath, _ = QFileDialog.getSaveFileName(
            self, "儲存 QR Code 圖片", "blackgold_game_qrcode.png", "PNG 圖片 (*.png);;所有檔案 (*.*)"
        )
        if filePath:
            try:
                self.pixmap.save(filePath, "PNG")
                QMessageBox.information(self, "儲存成功", f"🎉 QR Code 已成功儲存至：\n{filePath}")
            except Exception as e:
                QMessageBox.critical(self, "儲存失敗", f"儲存時發生錯誤：\n{e}")

# ------------------------------------------------------
# 主視窗 (MainWindow)
# ------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, server_thread, port):
        super().__init__()
        self.server_thread = None
        self.port = port
        self.current_lan_url = f"http://127.0.0.1:{port}"
        self.current_local_url = f"http://127.0.0.1:{port}"

        self.setWindowTitle("黑金魔法術：永續食物循環系統 - 區網互動教學工具箱")
        self.resize(1240, 820)

        icon_path = ensure_app_icon()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.initUI()
        self._wireServerThread(server_thread)

    def _wireServerThread(self, server_thread):
        self.server_thread = server_thread
        self.server_thread.server_started.connect(self.onServerStarted)
        self.server_thread.server_error.connect(self.onServerError)

    def onServerStarted(self, lan_url, local_url):
        self.current_lan_url = lan_url
        self.current_local_url = local_url
        self.urlTextLabel.setText(lan_url)
        self.statusBadge.setText("🟢 區網伺服器運行中")
        self.statusBadge.setStyleSheet("")
        self.restartBtn.setEnabled(True)
        self.restartBtn.setText("⚡ 重啟伺服器")
        self.webview.load(QUrl(local_url))
        show_app_tooltip(f"✅ 伺服器已成功運行於 Port {self.port}！", self, 2000)

    def onServerError(self, message):
        self.statusBadge.setText("🔴 伺服器啟動失敗")
        self.statusBadge.setStyleSheet("color: #F87171; background: rgba(248, 113, 113, 0.15); border: 1px solid rgba(248, 113, 113, 0.3);")
        self.restartBtn.setEnabled(True)
        self.restartBtn.setText("⚡ 重試重啟")
        QMessageBox.critical(
            self, "伺服器啟動失敗",
            f"無法在 Port {self.port} 啟動伺服器：\n{message}\n\n"
            "這通常表示該連接埠已被其他程式佔用。\n"
            "請從「Port 下拉選單」選擇其他常用的連接埠（例如 8080、8000、8888、5000、3000）後，\n"
            "再點擊「⚡ 重啟伺服器」即可！"
        )

    def initUI(self):
        centralWidget = QWidget()
        centralWidget.setObjectName("centralWidget")
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 頂部控制列 (48px)
        topBar = QFrame()
        topBar.setObjectName("topBar")
        topBar.setFixedHeight(48)
        topBarLayout = QHBoxLayout(topBar)
        topBarLayout.setContentsMargins(14, 6, 14, 6)
        topBarLayout.setSpacing(10)

        self.statusBadge = QLabel("🟢 區網伺服器運行中")
        self.statusBadge.setObjectName("statusBadge")
        self.statusBadge.setFixedHeight(28)
        topBarLayout.addWidget(self.statusBadge)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setObjectName("separator")
        sep1.setFixedHeight(20)
        topBarLayout.addWidget(sep1)

        self.urlTitleLabel = QLabel("學生連線網址：")
        self.urlTitleLabel.setObjectName("urlTitleLabel")
        self.urlTitleLabel.setFixedHeight(28)
        topBarLayout.addWidget(self.urlTitleLabel)

        self.urlTextLabel = QLabel(self.current_lan_url)
        self.urlTextLabel.setObjectName("urlTextLabel")
        self.urlTextLabel.setFixedHeight(28)
        self.urlTextLabel.setCursor(QCursor(Qt.PointingHandCursor))
        self.urlTextLabel.setToolTip("點擊複製網址")
        self.urlTextLabel.mousePressEvent = self.copyUrlToClipboard
        topBarLayout.addWidget(self.urlTextLabel)

        self.copyBtn = QPushButton("📋 複製")
        self.copyBtn.setObjectName("actionBtn")
        self.copyBtn.setFixedHeight(28)
        self.copyBtn.setToolTip("複製連線網址給學生")
        self.copyBtn.clicked.connect(self.copyUrlToClipboard)
        topBarLayout.addWidget(self.copyBtn)

        self.qrCodeBtn = QPushButton("📱 QR Code")
        self.qrCodeBtn.setObjectName("actionBtn")
        self.qrCodeBtn.setFixedHeight(28)
        self.qrCodeBtn.setToolTip("開啟大尺寸 QR Code 供學生平板/手機掃描連線")
        self.qrCodeBtn.clicked.connect(self.showQRCodeDialog)
        topBarLayout.addWidget(self.qrCodeBtn)

        self.openBrowserBtn = QPushButton("🌐 瀏覽器開啟")
        self.openBrowserBtn.setObjectName("actionBtn")
        self.openBrowserBtn.setFixedHeight(28)
        self.openBrowserBtn.setToolTip("在預設瀏覽器中開啟遊戲")
        self.openBrowserBtn.clicked.connect(self.openInExternalBrowser)
        topBarLayout.addWidget(self.openBrowserBtn)

        self.refreshBtn = QPushButton("🔄 重新整理")
        self.refreshBtn.setObjectName("actionBtn")
        self.refreshBtn.setFixedHeight(28)
        self.refreshBtn.setToolTip("重新載入內嵌遊戲畫面")
        self.refreshBtn.clicked.connect(self.refreshWebView)
        topBarLayout.addWidget(self.refreshBtn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setObjectName("separator")
        sep2.setFixedHeight(20)
        topBarLayout.addWidget(sep2)

        portLabel = QLabel("Port：")
        portLabel.setObjectName("portLabel")
        portLabel.setFixedHeight(28)
        topBarLayout.addWidget(portLabel)

        # 預選 Port 下拉選單
        self.portComboBox = QComboBox()
        self.portComboBox.setObjectName("portComboBox")
        self.portComboBox.setFixedHeight(28)
        self.portComboBox.setFixedWidth(135)
        self.portComboBox.setEditable(False)
        self.portComboBox.setToolTip("請由預選清單中選擇要運行的連接埠 (Port)")

        self.preset_ports = [
            ("8080 (預設)", 8080),
            ("8000", 8000),
            ("8888", 8888),
            ("5000", 5000),
            ("3000", 3000),
            ("8088", 8088),
        ]

        existing_ports = [p for _, p in self.preset_ports]
        if self.port not in existing_ports:
            self.preset_ports.insert(0, (f"{self.port}", self.port))

        selected_idx = 0
        for idx, (label, p) in enumerate(self.preset_ports):
            self.portComboBox.addItem(label, p)
            if p == self.port:
                selected_idx = idx

        self.portComboBox.setCurrentIndex(selected_idx)
        topBarLayout.addWidget(self.portComboBox)

        self.restartBtn = QPushButton("⚡ 重啟伺服器")
        self.restartBtn.setObjectName("restartBtn")
        self.restartBtn.setFixedHeight(28)
        self.restartBtn.setToolTip("切換 Port 後點擊重新啟動伺服器")
        self.restartBtn.clicked.connect(self.restartServer)
        topBarLayout.addWidget(self.restartBtn)

        topBarLayout.addStretch()

        # 右側作者與 CC 授權
        self.authorLabel = QLabel(
            '<span style="color:#CBD5E1; font-size:12px;">Made by </span>'
            '<a href="https://kentxchang.blogspot.tw" style="color:#34D399; text-decoration:none; font-weight:bold; font-size:12px;">阿剛老師</a>'
            '<span style="color:#94A3B8; font-size:11px;"> ｜ CC BY-NC-SA 4.0 授權</span>'
        )
        self.authorLabel.setObjectName("authorLabel")
        self.authorLabel.setTextFormat(Qt.RichText)
        self.authorLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.authorLabel.setOpenExternalLinks(True)
        self.authorLabel.setFixedHeight(28)
        topBarLayout.addWidget(self.authorLabel)

        mainLayout.addWidget(topBar, 0)

        # 內嵌 QWebEngineView
        self.webview = QWebEngineView()
        self.webview.setObjectName("webview")
        self.webview.setHtml(
            "<html><body style='display:flex;align-items:center;justify-content:center;"
            "height:100vh;margin:0;font-family:Segoe UI,Microsoft JhengHei,sans-serif;"
            "background:#0B0F19;color:#94A3B8;'>"
            "<div>🧙‍♂️ 黑金魔法術 RPG 伺服器啟動中，請稍候...</div></body></html>"
        )
        mainLayout.addWidget(self.webview, 1)

        self.setCentralWidget(centralWidget)
        self.applyModernStyle()

    def applyModernStyle(self):
        qss = """
        QWidget#centralWidget {
            background-color: #0B0F19;
            font-family: "Segoe UI", "Microsoft JhengHei", "PingFang TC", sans-serif;
        }

        QFrame#topBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #064E3B, stop:1 #0F172A);
            border-bottom: 2px solid #059669;
        }

        QLabel#statusBadge {
            color: #34D399;
            font-weight: bold;
            font-size: 13px;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 6px;
            padding: 2px 8px;
        }

        QFrame#separator {
            color: #1E293B;
            background: #1E293B;
            width: 1px;
        }

        QLabel#urlTitleLabel {
            color: #94A3B8;
            font-size: 13px;
            font-weight: 500;
        }

        QLabel#urlTextLabel {
            color: #34D399;
            font-size: 14px;
            font-weight: bold;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 6px;
            padding: 2px 8px;
        }
        QLabel#urlTextLabel:hover {
            color: #6EE7B7;
            background: rgba(16, 185, 129, 0.25);
        }

        QPushButton#actionBtn {
            background: rgba(255, 255, 255, 0.1);
            color: #F1F5F9;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton#actionBtn:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.4);
        }
        QPushButton#actionBtn:pressed {
            background: rgba(255, 255, 255, 0.05);
        }

        QLabel#portLabel {
            color: #CBD5E1;
            font-size: 13px;
            font-weight: bold;
        }

        QComboBox#portComboBox {
            background: #0F172A;
            color: #34D399;
            border: 1.5px solid #059669;
            border-radius: 6px;
            padding: 2px 22px 2px 8px;
            font-size: 12px;
            font-weight: bold;
        }
        QComboBox#portComboBox:hover {
            border-color: #34D399;
            background: #1E293B;
        }
        QComboBox#portComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #334155;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }
        QComboBox#portComboBox::down-arrow {
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #34D399;
            margin: 0 auto;
        }
        QComboBox#portComboBox QAbstractItemView {
            background: #0F172A;
            color: #F1F5F9;
            selection-background-color: #059669;
            selection-color: #FFFFFF;
            border: 1.5px solid #34D399;
            border-radius: 6px;
            padding: 4px;
            outline: none;
            font-size: 12px;
            font-weight: bold;
        }

        QPushButton#restartBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 4px 12px;
            font-size: 13px;
            font-weight: bold;
        }
        QPushButton#restartBtn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
        }
        QPushButton#restartBtn:pressed {
            background: #064E3B;
        }

        QLabel#authorLabel {
            background: rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            padding: 2px 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        QToolTip {
            background-color: #0F172A;
            color: #FFFFFF;
            border: 1px solid #10B981;
            border-radius: 6px;
            padding: 5px;
            font-size: 12px;
        }
        """
        self.setStyleSheet(qss)

    def copyUrlToClipboard(self, event=None):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_lan_url)
        show_app_tooltip("✅ 區網連線網址已複製到剪貼簿！", self, 1500)

    def openInExternalBrowser(self):
        webbrowser.open(self.current_lan_url)

    def showQRCodeDialog(self):
        dialog = QRCodeDialog(self.current_lan_url, self)
        dialog.exec_()

    def refreshWebView(self):
        self.webview.reload()
        show_app_tooltip("🔄 已重新整理畫面", self, 1000)

    def restartServer(self):
        new_port = self.portComboBox.currentData()
        if not new_port:
            raw_text = self.portComboBox.currentText().strip()
            match = re.search(r'\b\d+\b', raw_text)
            new_port = int(match.group(0)) if match else 8080

        if new_port < 1 or new_port > 65535:
            QMessageBox.warning(self, "連接埠錯誤", "請選擇有效的預選 Port！")
            return

        self.restartBtn.setEnabled(False)
        self.restartBtn.setText("⏳ 正在重啟...")
        self.statusBadge.setText("🟡 重啟中...")
        self.statusBadge.setStyleSheet("color: #FBBF24; background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.3);")
        QApplication.processEvents()

        if self.server_thread:
            try:
                self.server_thread.server_started.disconnect()
                self.server_thread.server_error.disconnect()
            except Exception:
                pass

            self.server_thread.stop()
            if not self.server_thread.wait(1500):
                try:
                    self.server_thread.terminate()
                    self.server_thread.wait(500)
                except Exception:
                    pass

        time.sleep(0.3)

        self.port = new_port
        new_thread = HTTPServerThread(new_port)
        self._wireServerThread(new_thread)
        new_thread.start()

        show_app_tooltip(f"🚀 正在連接埠 {new_port} 重啟伺服器...", self, 2000)

def main():
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    app = QApplication(sys.argv)
    icon_path = ensure_app_icon()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    server_thread = HTTPServerThread(port)
    window = MainWindow(server_thread, port)
    server_thread.start()
    window.show()

    exit_code = app.exec_()
    server_thread.stop()
    server_thread.wait()
    sys.exit(exit_code)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        _early_log(f"CRASH: {traceback.format_exc()}")
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "程式啟動失敗", f"發生嚴重錯誤：\n\n{traceback.format_exc()}")
        except Exception:
            pass

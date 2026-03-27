import sys
import subprocess
import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QScrollArea, QMessageBox, QInputDialog)

class ChromeNewsApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. إعداد المسارات (تأكد من وجود المجلدات بجانب الملف)
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.chrome_path = os.path.join(self.base_path, "ChromePortable", "GoogleChromePortable.exe")
        self.logo_dir = os.path.join(self.base_path, "Logo")
        self.db_path = os.path.join(self.base_path, "channels.json")

        # 2. تحميل القنوات من ملف JSON
        self.load_channels()

        # 3. إعداد النافذة الرئيسية
        self.setWindowTitle("بث مباشر") 
        self.setFixedWidth(420)
        self.setFixedHeight(700)
        
        # تعيين أيقونة البرنامج
        icon_path = os.path.join(self.logo_dir, "Icons.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("background-color: #050505; color: white; font-family: 'Segoe UI', Arial;")
        self.setup_ui()

    def load_channels(self):
        """تحميل القنوات المحفوظة أو الافتراضية"""
        default_channels = [
            {"name": "قناة الحــدث", "file": "قناة الحــدث.png", "vid": "xWXpl7azI8k"},
            {"name": "قناة العربـية", "file": "قناة العربـية.png", "vid": "n7eQejkXbnM"},
            {"name": "قناة الجزيرة", "file": "قناة الجزيرة.png", "vid": "bNyUyrR0PHo"},
            {"name": "قناة الــغد", "file": "قناة الــغد.png", "vid": "kOYNCXiG4IM"},
            {"name": "قناة العربى", "file": "قناة العربى.png", "vid": "e2RgSa1Wt5o"},
            {"name": "اسكاى نيوز", "file": "اسكاى نيوز.png", "vid": "U--OjmpjF5o"},
            {"name": "القاهرة الإخبارية", "file": "القاهرة الإخبارية.png", "vid": "-wS4BW7JCrk"},
            {"name": "BBC عربي", "file": "BBC عربي.png", "vid": "O1pGmVtj2Y8"},
        ]
        
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.channels = json.load(f)
            except:
                self.channels = default_channels
        else:
            self.channels = default_channels
            self.save_channels()

    def save_channels(self):
        """حفظ قائمة القنوات في ملف JSON"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.channels, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # الشريط العلوي (أضف + عن البرنامج)
        top_bar = QHBoxLayout()
        add_btn = QPushButton("أضف")
        add_btn.setFixedSize(85, 25)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton { background-color: #005500; color: white; border-radius: 5px; border: 1px solid #008800; font-size: 11px; }
            QPushButton:hover { background-color: #007700; }
        """)
        add_btn.clicked.connect(self.add_new_channel)
        top_bar.addWidget(add_btn)

        top_bar.addStretch()

        about_btn = QPushButton("عن البرنامج")
        about_btn.setFixedSize(85, 25)
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.setStyleSheet("""
            QPushButton { background-color: #222; color: #ddd; border-radius: 5px; border: 1px solid #444; font-size: 11px; }
            QPushButton:hover { background-color: #333; color: white; }
        """)
        about_btn.clicked.connect(self.show_about)
        top_bar.addWidget(about_btn)
        self.main_layout.addLayout(top_bar)

        # شعار بث.png والعنوان باللون اللبني
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_logo = QLabel()
        path_bath = os.path.join(self.logo_dir, "بث.png")
        if os.path.exists(path_bath):
            main_logo.setPixmap(QPixmap(path_bath).scaled(55, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        title_label = QLabel("دليل القنوات المباشرة")
        title_label.setStyleSheet("color: #00BFFF; font-size: 24px; font-weight: bold;") 
        title_layout.addWidget(main_logo)
        title_layout.addWidget(title_label)
        self.main_layout.addLayout(title_layout)

        # منطقة القنوات (سكرول بار يسار)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight) 
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setLayoutDirection(Qt.LayoutDirection.RightToLeft) 
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setSpacing(15)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.refresh_channel_list()
        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll)

    def refresh_channel_list(self):
        """تحديث قائمة الأزرار المعروضة"""
        for i in reversed(range(self.list_layout.count())): 
            if self.list_layout.itemAt(i).widget():
                self.list_layout.itemAt(i).widget().setParent(None)

        for ch in self.channels:
            btn = self.create_channel_button(ch)
            self.list_layout.addWidget(btn)

    def create_channel_button(self, ch):
        btn = QPushButton()
        btn.setFixedHeight(85)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #111; border-radius: 12px; border: 2px solid #00BFFF; }
            QPushButton:hover { background-color: #1a1a1a; border: 2px solid #FF8C00; }
        """)

        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(15, 0, 15, 0)
        btn_layout.setSpacing(15)

        icon_label = QLabel()
        logo_path = os.path.join(self.logo_dir, ch['file'])
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(55, 55, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        name_label = QLabel(ch['name'])
        name_label.setStyleSheet("color: white; font-size: 17px; font-weight: bold; border: none;")
        
        btn_layout.addWidget(icon_label)
        btn_layout.addWidget(name_label)
        btn_layout.addStretch()

        btn.clicked.connect(lambda checked, v=ch['vid']: self.open_in_chrome(v))
        return btn

    def add_new_channel(self):
        url, ok1 = QInputDialog.getText(self, "إضافة قناة", "أضف رابط القناة:")
        if not ok1 or not url: return
        name, ok2 = QInputDialog.getText(self, "إضافة قناة", "ادخل اسم القناة:")
        if not ok2 or not name: return

        video_id = url.split("v=")[1].split("&")[0] if "v=" in url else (url.split("youtu.be/")[1].split("?")[0] if "youtu.be/" in url else url)

        new_ch = {"name": name, "file": f"{name}.png", "vid": video_id}
        self.channels.append(new_ch)
        self.save_channels()
        self.refresh_channel_list()
        QMessageBox.information(self, "تمت الإضافة", f"تمت الإضافة بنجاح!\nيرجى وضع الشعار في Logo باسم: {name}.png")

    def show_about(self):
        QMessageBox.information(self, "حول البرنامج", "هذا البرنامج برمجة Ahmed Gamal Ali\nالنسخة 3.2.0")

    def open_in_chrome(self, video_id):
        if not os.path.exists(self.chrome_path):
            QMessageBox.critical(self, "خطأ", "لم يتم العثور على الكروم المحمول.")
            return
        
        # تم استخدام الرابط العادي (watch) لتجنب خطأ 153 مع الحفاظ على التشغيل التلقائي
        url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1&mute=1"
        try:
            # تشغيل بوضع التطبيق وملء الشاشة
            subprocess.Popen([
                self.chrome_path, 
                f"--app={url}", 
                "--start-fullscreen",
                "--no-first-run"
            ])
        except Exception as e:
            QMessageBox.warning(self, "فشل", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChromeNewsApp()
    window.show()
    sys.exit(app.exec())
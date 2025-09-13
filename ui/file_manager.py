import os
import logging
import soundfile as sf
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QFileDialog, QMessageBox, QMenu
from PyQt6.QtCore import QThread, pyqtSignal,Qt
from PyQt6.QtGui import QAction

logger = logging.getLogger(__name__)

# -----------------------------
# 音频加载线程
class AudioLoaderThread(QThread):
    finished = pyqtSignal(object, int, float)  # data, sr, duration
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            data, sr = sf.read(self.file_path, dtype='float32')
            if data.ndim > 1:
                data = data[:, 0]  # 取第一声道
            duration = len(data) / sr
            self.finished.emit(data, sr, duration)
        except Exception as e:
            self.error.emit(str(e))


# -----------------------------
# FileManager UI
class FileManager(QWidget):
    def __init__(self):
        super().__init__()
        self.audio_list = QListWidget()
        self.audio_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.audio_list.customContextMenuRequested.connect(self.show_context_menu)
        self.info_label = QLabel("未加载音频")
        self.import_button = QPushButton("导入音频文件")

        layout = QVBoxLayout()
        layout.addWidget(self.import_button)
        layout.addWidget(QLabel("音频文件列表"))
        layout.addWidget(self.audio_list)
        layout.addWidget(QLabel("文件信息"))
        layout.addWidget(self.info_label)
        self.setLayout(layout)

        self.import_button.clicked.connect(self.import_audio)

        # 状态
        self.audio_path = None
        self.y = None
        self.sr = None
        self.loader_thread = None

    # -----------------------------
    # 异步导入音频
    def import_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "音频文件 (*.wav *.mp3 *.flac)")
        if not file_path:
            return

        filename = os.path.basename(file_path)
        self.audio_list.addItem(filename)
        self.info_label.setText("加载中...")

        # 创建线程加载音频
        self.loader_thread = AudioLoaderThread(file_path)
        self.loader_thread.finished.connect(self.on_audio_loaded)
        self.loader_thread.error.connect(self.on_audio_load_error)
        self.loader_thread.start()
        self.audio_path = file_path

    # -----------------------------
    # 加载完成
    def on_audio_loaded(self, data, sr, duration):
        self.y = data
        self.sr = sr
        self.info_label.setText(f"采样率：{sr} Hz\n时长：{duration:.2f} 秒\n通道：单声道")
        logger.info(f"成功加载音频：{self.audio_path}, 采样率={sr}, 时长={duration:.2f}s")
        self.loader_thread = None

    # -----------------------------
    # 加载失败
    def on_audio_load_error(self, error_msg):
        self.info_label.setText(f"加载失败：{error_msg}")
        logger.error(f"音频加载失败：{error_msg}")
        QMessageBox.warning(self, "加载失败", error_msg)
        self.loader_thread = None

    def show_context_menu(self, pos):
        item = self.audio_list.itemAt(pos)
        if item is None:
            return  # 点击空白区域不弹出菜单

        menu = QMenu()
        remove_action = QAction("移除音频")
        menu.addAction(remove_action)
        remove_action.triggered.connect(lambda: self.remove_audio(item))
        menu.exec(self.audio_list.mapToGlobal(pos))

    def remove_audio(self, item):
        row = self.audio_list.row(item)
        self.audio_list.takeItem(row)
        logger.info(f"音频已移除: {item.text()}")

        # 如果当前移除的音频是正在播放的
        if getattr(self, 'y', None) is not None and self.audio_list.count() == 0:
            self.y = None
            self.sr = None
            logger.info("已清空当前音频数据")
import sys
import os
import time
import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
import logging

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QComboBox, QLineEdit, QFileDialog, QSplitter,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from fft_processor import compute_fft
from filter import butter_filter

# ✅ 日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# ✅ matplotlib 中文字体设置
import matplotlib
matplotlib.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

class FileManager(QWidget):
    def __init__(self):
        super().__init__()
        self.audio_list = QListWidget()
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
        self.audio_path = None
        self.y = None
        self.sr = None

    def import_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "音频文件 (*.wav *.mp3)")
        if file_path:
            filename = os.path.basename(file_path)
            self.audio_list.addItem(filename)
            try:
                y, sr = librosa.load(file_path, sr=None, mono=True)
                duration = len(y) / sr
                self.info_label.setText(f"采样率：{sr} Hz\n时长：{duration:.2f} 秒\n通道：单声道")
                self.audio_path = file_path
                self.y = y
                self.sr = sr
                logger.info(f"成功加载音频：{filename}, 采样率={sr}, 时长={duration:.2f}s")
            except Exception as e:
                self.info_label.setText(f"加载失败：{e}")
                logger.error(f"音频加载失败：{e}")

class AnalysisPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.canvas = FigureCanvas(Figure(figsize=(8, 4)))
        self.ax = self.canvas.figure.subplots()

        self.filter_type = QComboBox()
        self.filter_type.addItems(["低通", "高通", "带通"])
        self.cutoff_input = QLineEdit()
        self.cutoff_input.setPlaceholderText("截止频率（Hz），如 3000 或 300,3000")
        self.apply_button = QPushButton("应用滤波")

        self.play_original_button = QPushButton("播放原始音频")
        self.play_filtered_button = QPushButton("播放滤波后音频")
        self.test_button = QPushButton("测试播放（440Hz）")
        self.export_button = QPushButton("导出滤波音频")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("播放进度：%p%")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("滤波类型"))
        layout.addWidget(self.filter_type)
        layout.addWidget(QLabel("截止频率（单位：Hz）"))
        layout.addWidget(self.cutoff_input)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.play_original_button)
        layout.addWidget(self.play_filtered_button)
        layout.addWidget(self.test_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.apply_button.clicked.connect(self.apply_filter)
        self.play_original_button.clicked.connect(self.play_original)
        self.play_filtered_button.clicked.connect(self.play_filtered)
        self.test_button.clicked.connect(self.play_test_tone)
        self.export_button.clicked.connect(self.export_filtered)

        self.y = None
        self.sr = None
        self.y_filtered = None

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_progress)

        self.playing_data = None
        self.playing_sr = None
        self.play_start_time = None

    def load_audio(self, y, sr):
        self.y = y
        self.sr = sr
        self.y_filtered = None
        logger.info("加载音频到分析模块")
        freqs, fft_result = compute_fft(y, sr)
        self.plot(freqs, fft_result, title="原始频谱")

    def apply_filter(self):
        if self.y is None:
            return
        btype_map = {"低通": "low", "高通": "high", "带通": "bandpass"}
        btype = btype_map[self.filter_type.currentText()]
        cutoff_text = self.cutoff_input.text()
        try:
            if btype == "bandpass":
                cutoff = [float(x) for x in cutoff_text.split(",")]
            else:
                cutoff = float(cutoff_text)
            logger.info(f"应用滤波器：类型={btype}, 截止频率={cutoff}")
            y_filtered = butter_filter(self.y, self.sr, cutoff=cutoff, btype=btype, order=6)
            self.y_filtered = y_filtered
            freqs, fft_result = compute_fft(y_filtered, self.sr)
            self.plot(freqs, fft_result, title="滤波后频谱")
        except Exception as e:
            logger.error(f"滤波失败：{e}")
            QMessageBox.warning(self, "滤波失败", str(e))

    def play_audio(self, data, sr):
        try:
            logger.info("开始播放音频")
            logger.debug(f"数据长度：{len(data)}, 采样率：{sr}")
            self.playing_data = data
            self.playing_sr = sr
            self.play_start_time = time.time()
            self.progress_bar.setValue(0)
            self.timer.start()
            sd.play(data, sr)
            sd.wait()
            self.timer.stop()
            self.progress_bar.setValue(100)
            logger.info("播放完成")
        except Exception as e:
            logger.error(f"播放失败：{e}")
            QMessageBox.warning(self, "播放失败", str(e))
            self.timer.stop()
            self.progress_bar.setValue(0)

    def play_original(self):
        if self.y is not None and self.sr is not None:
            logger.info("播放原始音频")
            self.play_audio(self.y, self.sr)
        else:
            QMessageBox.information(self, "无音频", "请先导入音频文件")

    def play_filtered(self):
        if self.y_filtered is not None and self.sr is not None:
            logger.info("播放滤波后音频")
            self.play_audio(self.y_filtered, self.sr)
        else:
            QMessageBox.information(self, "无音频", "请先应用滤波")

    def play_test_tone(self):
        try:
            sr = 44100
            duration = 1.0
            t = np.linspace(0, duration, int(sr * duration), endpoint=False)
            tone = 0.5 * np.sin(2 * np.pi * 440 * t)
            logger.info("播放测试音频：440Hz 正弦波")
            self.play_audio(tone, sr)
        except Exception as e:
            logger.error(f"测试播放失败：{e}")
            QMessageBox.warning(self, "测试播放失败", str(e))

    def update_progress(self):
        if self.playing_data is None or self.play_start_time is None:
            return
        elapsed = time.time() - self.play_start_time
        total_duration = len(self.playing_data) / self.playing_sr
        progress = min(int((elapsed / total_duration) * 100), 100)
        self.progress_bar.setValue(progress)
        if progress >= 100:
            self.timer.stop()

    def export_filtered(self):
        if self.y_filtered is not None and self.sr is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存音频",
                "",
                "WAV 文件 (*.wav)"
            )
            if file_path:
                try:
                    sf.write(file_path, self.y_filtered, self.sr)
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"音频已保存到：\n{file_path}"
                    )
                    logger.info(f"音频导出成功：{file_path}")
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "导出失败",
                        f"保存失败：{e}"
                    )
                    logger.error(f"音频导出失败：{e}")
            else:
                QMessageBox.information(
                    self,
                    "导出取消",
                    "未选择保存路径"
                )
                logger.warning("导出取消：用户未选择路径")
        else:
            QMessageBox.information(
                self,
                "无音频",
                "没有可导出的滤波音频"
            )
            logger.warning("导出失败：无滤波音频可导出")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("噪音处理工作台")
        self.resize(1200, 700)

        self.file_manager = FileManager()
        self.analysis_panel = AnalysisPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.file_manager)
        splitter.addWidget(self.analysis_panel)
        splitter.setSizes([300, 900])

        layout = QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.file_manager.audio_list.itemClicked.connect(self.sync_audio)

    def sync_audio(self):
        y = self.file_manager.y
        sr = self.file_manager.sr
        if y is not None and sr is not None:
            logger.info("同步音频到分析模块")
            self.analysis_panel.load_audio(y, sr)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logger.info("应用启动成功")
    sys.exit(app.exec())

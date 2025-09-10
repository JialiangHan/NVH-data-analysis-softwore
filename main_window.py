import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QLineEdit, QFileDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # matplotlib 仍使用 Qt5 接口
from matplotlib.figure import Figure

from audio_loader import load_audio
from fft_processor import compute_fft
from filter import butter_filter
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置支持中文的字体
rcParams['font.family'] = ['Microsoft YaHei', 'SimHei']
rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块的问题

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("噪音处理工具")
        self.resize(800, 600)

        self.y = None
        self.sr = None

        # UI 元素
        self.load_button = QPushButton("导入音频")
        self.filter_type = QComboBox()
        self.filter_type.addItems(["低通", "高通", "带通"])
        self.cutoff_input = QLineEdit()
        self.cutoff_input.setPlaceholderText("截止频率（如 3000 或 300,3000）")
        self.apply_button = QPushButton("应用滤波")

        self.canvas = FigureCanvas(Figure(figsize=(8, 4)))
        self.ax = self.canvas.figure.subplots()

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(QLabel("滤波类型"))
        layout.addWidget(self.filter_type)
        layout.addWidget(QLabel("截止频率"))
        layout.addWidget(self.cutoff_input)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # 信号连接
        self.load_button.clicked.connect(self.load_audio_file)
        self.apply_button.clicked.connect(self.apply_filter)

    def load_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "音频文件 (*.wav *.mp3)")
        if file_path:
            self.y, self.sr = load_audio(file_path)
            freqs, fft_result = compute_fft(self.y, self.sr)
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
            y_filtered = butter_filter(self.y, self.sr, cutoff=cutoff, btype=btype, order=6)
            freqs, fft_result = compute_fft(y_filtered, self.sr)
            self.plot(freqs, fft_result, title="滤波后频谱")
        except Exception as e:
            print(f"滤波失败：{e}")

    def plot(self, freqs, fft_result, title="频谱图"):
        self.ax.clear()
        fft_db = 20 * np.log10(fft_result + 1e-6)
        self.ax.plot(freqs, fft_db, color='royalblue')
        self.ax.set_title(title)
        self.ax.set_xlabel("频率 (Hz)")
        self.ax.set_ylabel("幅度 (dB)")
        self.ax.grid(True)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

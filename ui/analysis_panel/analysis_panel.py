from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QProgressBar, QMessageBox
from PyQt6.QtCore import QTimer
import logging
import numpy as np
# 引入同一包内的模块，用相对导入
from .audio_player import AudioPlayer
from .filter_widget import FilterWidget
from .plot_widget import PlotWidget

# 引入算法模块
from analysis.fft_processor import compute_fft
from analysis.filter import butter_filter
from analysis.level_vs_time import compute_level_vs_time


logger = logging.getLogger(__name__)

class AnalysisPanel(QWidget):
    def __init__(self):
        super().__init__()

        # 控件
        self.filter_type = QComboBox()
        self.filter_type.addItems(["低通", "高通", "带通"])
        self.cutoff_input = QLineEdit()
        self.cutoff_input.setPlaceholderText("截止频率（Hz），如 3000 或 300,3000")
        self.apply_button = QPushButton("应用滤波")
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            "FFT(single)","FFT(average)","FFT(peak hold)",
            "波形分析 (Waveform)",
            "colormap",
            "Level vs Time"
        ])
        self.analysis_button = QPushButton("开始分析")
        # 播放控件
        self.play_pause_button = QPushButton("播放")
        self.stop_button = QPushButton("停止")
        self.export_button = QPushButton("导出滤波音频")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("0.00 / 0.00 s")

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(QLabel("滤波类型"))
        layout.addWidget(self.filter_type)
        layout.addWidget(QLabel("截止频率（Hz）"))
        layout.addWidget(self.cutoff_input)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("分析方式"))
        layout.addWidget(self.analysis_type_combo)
        layout.addWidget(self.analysis_button)
        # 绘图模块
        self.plot_widget = PlotWidget()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        # 状态
        self.y = None
        self.sr = None
        self.y_filtered = None

        # AudioPlayer
        self.audio_player = AudioPlayer(self.progress_bar)

        # 信号连接
        self.apply_button.clicked.connect(self.apply_filter)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.stop_button.clicked.connect(self.stop_audio)
        self.analysis_button.clicked.connect(self.perform_analysis)
    # -----------------------------
    # 加载音频
    def load_audio(self, y, sr, draw=False):
        logger.debug("load_audio start")
        self.y = y
        self.sr = sr
        self.y_filtered = None
        logger.info(f"音频加载完成: 长度={len(y)}, 采样率={sr}")

        if draw:
            self.perform_analysis()

    # -----------------------------
    # 应用滤波
    def apply_filter(self):
        if self.y is None:
            return
        btype_map = {"低通": "low", "高通": "high", "带通": "bandpass"}
        btype = btype_map[self.filter_type.currentText()]
        try:
            cutoff = [float(x) for x in self.cutoff_input.text().split(",")] if btype=="bandpass" else float(self.cutoff_input.text())
            self.y_filtered = butter_filter(self.y, self.sr, cutoff=cutoff, btype=btype, order=6)
            freqs, fft_result = compute_fft(self.y_filtered, self.sr)
            self.plot_widget.plot(freqs, fft_result, title="滤波后频谱")
            logger.info(f"应用滤波器：{btype}, cutoff={cutoff}")
        except Exception as e:
            logger.error(f"滤波失败: {e}")
            QMessageBox.warning(self, "滤波失败", str(e))

    # -----------------------------
    # 播放/暂停切换
    def toggle_play_pause(self):
        if self.audio_player.playing_data is None:
            # 当前没有播放 → 播放音频
            if self.y_filtered is not None:
                self.audio_player.play(self.y_filtered, self.sr)
            elif self.y is not None:
                self.audio_player.play(self.y, self.sr)
            self.play_pause_button.setText("暂停")
        else:
            # 已经在播放 → 切换暂停/恢复
            self.audio_player.pause()
            if self.audio_player.is_paused:
                self.play_pause_button.setText("播放")
            else:
                self.play_pause_button.setText("暂停")

    # -----------------------------
    # 停止播放
    def stop_audio(self):
        self.audio_player.stop()
        self.play_pause_button.setText("播放")

    def perform_analysis(self):
        if self.y is None:
            logger.warning("没有音频可分析")
            return

        choice = self.analysis_type_combo.currentText()
        data = self.y_filtered if self.y_filtered is not None else self.y  # 统一放在最前面

        mode_map = {
            "FFT(single)": "single",
            "FFT(average)": "average",
            "FFT(peak hold)": "peak"
        }

        if choice in mode_map:
            freqs, fft_result = compute_fft(data, self.sr, mode=mode_map[choice])
            self.plot_widget.plot(freqs, np.abs(fft_result), title=f"{choice} 频谱分析")
            logger.info(f"完成 {choice} 绘图")

        elif choice == "波形分析 (Waveform)":
            t = np.arange(len(data)) / self.sr
            self.plot_widget.plot(t, data, title="波形分析")
            logger.info("完成波形分析绘图")

        elif choice == "colormap":
            self.plot_widget.plot_spectrogram(data, self.sr)  # ✅ 用滤波后的
            logger.info("绘制声谱图完成")

        elif choice == "Level vs Time":
            data = self.y_filtered if self.y_filtered is not None else self.y
            times, levels = compute_level_vs_time(data, self.sr, frame_length=0.125, p0=1.0)
            self.plot_widget.plot(times, levels, title="Level vs Time")
            self.plot_widget.ax.set_xlabel("时间 (s)")
            self.plot_widget.ax.set_ylabel("声级 (dBFS)")
            logger.info("完成 Level vs Time 绘图")

        else:
            logger.warning(f"未知分析类型: {choice}")

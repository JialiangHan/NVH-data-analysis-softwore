import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QProgressBar
import logging
import time

logger = logging.getLogger(__name__)

class AudioPlayer:
    def __init__(self, progress_bar: QProgressBar):
        self.progress_bar = progress_bar
        self.timer = QTimer()
        self.timer.setInterval(100)  # 每 100ms 更新一次
        self.timer.timeout.connect(self.update_progress)

        self.playing_data = None
        self.playing_sr = None
        self.play_pos = 0
        self.is_paused = False
        self.start_time = None
        self.finished_flag = False

    # -----------------------------
    # 播放音频
    def play(self, data, sr):
        # 如果已经在播放，先停止
        self.stop()

        if data is None or len(data) == 0:
            logger.warning("播放失败：音频为空")
            return

        # 确保数据类型和单声道
        data = np.asarray(data, dtype=np.float32).copy()
        if data.ndim > 1:
            data = data[:, 0]

        self.playing_data = data
        self.playing_sr = sr
        self.play_pos = 0
        self.is_paused = False
        self.total_duration = len(data) / sr
        self.finished_flag = False

        # 初始化进度条
        self.progress_bar.setRange(0, int(self.total_duration * 1000))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"0.00 / {self.total_duration:.2f} s")

        # 开始播放
        try:
            sd.play(self.playing_data, self.playing_sr, blocking=False)
            self.start_time = time.time()
            self.timer.start()
            logger.info(f"开始播放音频，总时长 {self.total_duration:.2f}s")
        except Exception as e:
            logger.error(f"播放失败: {e}")

    # -----------------------------
    # 暂停 / 恢复
    def pause(self):
        if self.playing_data is None:
            return

        if not self.is_paused:
            # 暂停
            self.is_paused = True
            self.play_pos += int((time.time() - self.start_time) * self.playing_sr)
            sd.stop()
            self.timer.stop()
            logger.info(f"暂停播放 at sample {self.play_pos}")
        else:
            # 恢复
            self.is_paused = False
            remaining_data = self.playing_data[self.play_pos:]
            self.start_time = time.time()
            sd.play(remaining_data, self.playing_sr, blocking=False)
            self.timer.start()
            logger.info(f"恢复播放 from sample {self.play_pos}")

    # -----------------------------
    # 停止播放
    def stop(self):
        self.timer.stop()
        if self.playing_data is not None:
            try:
                sd.stop()
            except Exception as e:
                logger.warning(f"停止播放异常: {e}")
        self.playing_data = None
        self.play_pos = 0
        self.is_paused = False
        self.finished_flag = False
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0.00 / 0.00 s")
        logger.info("停止播放")

    # -----------------------------
    # 更新时间进度条
    def update_progress(self):
        if self.playing_data is None or self.playing_sr is None:
            return

        elapsed = self.play_pos / self.playing_sr + (time.time() - self.start_time if not self.is_paused else 0)

        # 更新进度条
        elapsed = min(elapsed, self.total_duration)
        self.progress_bar.setValue(int(elapsed * 1000))
        self.progress_bar.setFormat(f"{elapsed:.2f} / {self.total_duration:.2f} s")
        logger.debug(f"播放进度: {elapsed:.2f}s / {self.total_duration:.2f}s")

        # 播放完成
        if elapsed >= self.total_duration:
            self.stop()
            self.finished_flag = True
            logger.info("播放完成")

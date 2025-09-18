import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_fft(y, sr, mode="single", frame_size=4096, overlap=0.5):
    """
    通用 FFT 分析函数

    Parameters
    ----------
    y : np.ndarray
        音频信号
    sr : int
        采样率
    mode : str
        分析模式: "single"（单次 FFT）, "average"（平均 FFT）, "peak"（峰值保持 FFT）
    frame_size : int
        每帧大小（仅 average/peak 有效）
    overlap : float
        帧重叠比例 (0~1)

    Returns
    -------
    freqs : np.ndarray
        频率轴
    spectrum : np.ndarray
        频谱幅度
    """
    n = len(y)

    # 单次 FFT
    if mode == "single":
        freqs = np.fft.rfftfreq(n, 1 / sr)
        fft_result = np.fft.rfft(y) / n
        logger.info("执行单次 FFT")
        return freqs, np.abs(fft_result)

    # 帧分割设置
    hop_size = int(frame_size * (1 - overlap))
    n_frames = (len(y) - frame_size) // hop_size + 1
    if n_frames <= 0:
        raise ValueError("音频过短，无法分帧计算")

    logger.info(f"执行 {mode} FFT: frame_size={frame_size}, overlap={overlap}, frames={n_frames}")

    avg_spectrum = None
    peak_spectrum = None
    freqs = None

    for i in range(n_frames):
        start = i * hop_size
        frame = y[start:start + frame_size]
        if len(frame) < frame_size:
            break

        freqs = np.fft.rfftfreq(frame_size, 1 / sr)
        fft_result = np.fft.rfft(frame) / frame_size
        spectrum = np.abs(fft_result)

        if mode == "average":
            if avg_spectrum is None:
                avg_spectrum = spectrum
            else:
                avg_spectrum += spectrum

        elif mode == "peak":
            if peak_spectrum is None:
                peak_spectrum = spectrum
            else:
                peak_spectrum = np.maximum(peak_spectrum, spectrum)

    if mode == "average":
        return freqs, avg_spectrum / n_frames
    elif mode == "peak":
        return freqs, peak_spectrum
    else:
        raise ValueError(f"未知 FFT 模式: {mode}")

import numpy as np

def compute_level_vs_time(y, sr, frame_length=0.125, p0=1.0):
    """
    计算 Level vs Time 曲线
    :param y: 音频信号 (numpy array)
    :param sr: 采样率
    :param frame_length: 每帧时长 (秒)
    :param p0: 参考值 (默认=1.0, 表示 dBFS；设为 20e-6 表示 dB SPL)
    :return: times, levels (numpy arrays)
    """
    frame_size = int(frame_length * sr)
    num_frames = len(y) // frame_size

    levels = []
    times = []

    for i in range(num_frames):
        frame = y[i*frame_size:(i+1)*frame_size]
        if len(frame) == 0:
            continue
        rms = np.sqrt(np.mean(frame**2))
        level = 20 * np.log10(rms / p0 + 1e-12)  # 避免 log(0)
        levels.append(level)
        times.append(i * frame_length)

    return np.array(times), np.array(levels)

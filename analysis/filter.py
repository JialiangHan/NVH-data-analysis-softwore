import numpy as np
from scipy.signal import butter, filtfilt

def butter_filter(y, sr, cutoff, btype='low', order=6):
    """
    通用 Butterworth 滤波器
    -------------------------
    y      : numpy.array, 输入信号
    sr     : int, 采样率 (Hz)
    cutoff : float or list, 截止频率
             - 单值 float 用于低通或高通
             - [f1, f2] list 用于带通
    btype  : 'low', 'high', 'bandpass'
    order  : int, 滤波器阶数
    -------------------------
    返回滤波后的信号 (numpy.array)
    """
    nyq = 0.5 * sr  # 奈奎斯特频率

    if btype in ['low', 'high']:
        normal_cutoff = cutoff / nyq
    elif btype == 'bandpass':
        if not isinstance(cutoff, (list, tuple)) or len(cutoff) != 2:
            raise ValueError("bandpass 需要 cutoff=[低频, 高频]")
        normal_cutoff = [cutoff[0]/nyq, cutoff[1]/nyq]
    else:
        raise ValueError("btype 必须是 'low', 'high', 'bandpass'")

    # 设计滤波器
    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    # 零相位滤波，避免相位失真
    y_filtered = filtfilt(b, a, y)
    return y_filtered

# ===============================
# 测试代码（直接运行 filter.py）
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    fs = 44100
    t = np.linspace(0, 1, fs)
    # 合成信号：50Hz + 1000Hz
    sig = np.sin(2*np.pi*50*t) + np.sin(2*np.pi*1000*t)

    y_low = butter_filter(sig, fs, cutoff=200, btype='low')
    y_high = butter_filter(sig, fs, cutoff=200, btype='high')
    y_band = butter_filter(sig, fs, cutoff=[40, 60], btype='bandpass')

    plt.figure(figsize=(10,6))
    plt.plot(t, sig, label='原始信号', alpha=0.5)
    plt.plot(t, y_low, label='低通 200Hz')
    plt.plot(t, y_high, label='高通 200Hz')
    plt.plot(t, y_band, label='带通 40-60Hz')
    plt.legend()
    plt.xlabel("时间 (s)")
    plt.ylabel("幅值")
    plt.show()

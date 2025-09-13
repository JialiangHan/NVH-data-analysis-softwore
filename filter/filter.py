from scipy.signal import butter, lfilter

def butter_filter(y, sr, cutoff, btype='low', order=5):
    """
    应用 Butterworth 滤波器
    参数：
        y      : 音频数据（numpy 数组）
        sr     : 采样率（Hz）
        cutoff : 截止频率（Hz）
        btype  : 滤波类型（'low'、'high'、'bandpass'）
        order  : 滤波器阶数（越高越陡峭）
    返回：
        y_filtered : 滤波后的音频数据
    """
    nyq = 0.5 * sr  # Nyquist 频率
    if btype == 'bandpass':
        if isinstance(cutoff, (list, tuple)) and len(cutoff) == 2:
            normal_cutoff = [f / nyq for f in cutoff]
        else:
            raise ValueError("bandpass 模式需要两个截止频率")
    else:
        normal_cutoff = cutoff / nyq

    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    y_filtered = lfilter(b, a, y)
    return y_filtered

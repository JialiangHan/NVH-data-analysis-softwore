import numpy as np

def compute_fft(y, sr):
    """
    对音频信号进行快速傅里叶变换（FFT）
    参数：
        y  : 音频数据（numpy 数组）
        sr : 采样率（int）
    返回：
        freqs       : 频率轴（Hz）
        fft_result  : 幅度谱（振幅）
    """
    N = len(y)
    fft_result = np.abs(np.fft.fft(y))
    freqs = np.fft.fftfreq(N, d=1/sr)

    # 只保留前半部分（正频率）
    half_N = N // 2
    return freqs[:half_N], fft_result[:half_N]

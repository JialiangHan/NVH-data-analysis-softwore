import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np

# ✅ 设置中文字体（自动选择系统常见字体）
rcParams['font.family'] = ['Microsoft YaHei', 'SimHei']
rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块的问题


def plot_fft(freqs, fft_result, title="频谱图", use_db=False, freq_limit=None):
    """
    绘制频谱图（支持中文）

    参数：
        freqs       : 频率轴（Hz）
        fft_result  : 幅度谱（线性或 dB）
        title       : 图表标题（支持中文）
        use_db      : 是否使用对数坐标（dB）
        freq_limit  : 最大频率显示范围（Hz），如 8000
    """
    plt.figure(figsize=(10, 4))

    if use_db:
        fft_result = 20 * np.log10(fft_result + 1e-6)
        plt.ylabel("幅度 (dB)")
    else:
        plt.ylabel("幅度")

    plt.plot(freqs, fft_result, color='royalblue')
    plt.xlabel("频率 (Hz)")
    plt.title(title)
    plt.grid(True)

    if freq_limit:
        plt.xlim(0, freq_limit)
    else:
        plt.xlim(0, freqs[-1])

    plt.tight_layout()
    plt.show()

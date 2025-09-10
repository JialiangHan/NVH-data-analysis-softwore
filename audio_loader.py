import librosa
import soundfile as sf
from PyQt6.QtWidgets import QApplication, QFileDialog
import sys

def select_audio_file():
    """
    弹出文件选择对话框，返回用户选择的音频文件路径
    """
    app = QApplication(sys.argv)
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "选择音频文件",
        "",
        "音频文件 (*.wav *.mp3 *.flac *.ogg)"
    )
    app.quit()
    return file_path

def load_audio(file_path):
    """
    读取音频文件，返回音频数据和采样率
    """
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True)
        print(f"成功导入音频：{file_path}")
        print(f"采样率：{sr}，样本数：{len(y)}")
        return y, sr
    except Exception as e:
        print(f"导入音频失败：{e}")
        return None, None

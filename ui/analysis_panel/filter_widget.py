from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox
from analysis.filter import butter_filter
from analysis.fft_processor import compute_fft

class FilterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.filter_type = QComboBox()
        self.filter_type.addItems(["低通", "高通", "带通"])
        self.cutoff_input = QLineEdit()
        self.cutoff_input.setPlaceholderText("截止频率（Hz），如 3000 或 300,3000")
        self.apply_button = QPushButton("应用滤波")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("滤波类型"))
        layout.addWidget(self.filter_type)
        layout.addWidget(QLabel("截止频率（Hz）"))
        layout.addWidget(self.cutoff_input)
        layout.addWidget(self.apply_button)
        self.setLayout(layout)

    def apply_filter(self, y, sr):
        if y is None:
            QMessageBox.information(self, "无音频", "请先加载音频")
            return None
        btype_map = {"低通": "low", "高通": "high", "带通": "bandpass"}
        btype = btype_map[self.filter_type.currentText()]
        cutoff_text = self.cutoff_input.text()
        try:
            if btype == "bandpass":
                cutoff = [float(x) for x in cutoff_text.split(",")]
            else:
                cutoff = float(cutoff_text)
            y_filtered = butter_filter(y, sr, cutoff=cutoff, btype=btype)
            return y_filtered
        except Exception as e:
            QMessageBox.warning(self, "滤波失败", str(e))
            return None

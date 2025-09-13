from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from .file_manager import FileManager
from ui.analysis_panel.analysis_panel import AnalysisPanel
import logging

logger = logging.getLogger(__name__)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("噪音处理工作台")
        self.resize(1200, 700)

        # 子模块
        self.file_manager = FileManager()
        self.analysis_panel = AnalysisPanel()

        # splitter 布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.file_manager)
        splitter.addWidget(self.analysis_panel)
        splitter.setSizes([300, 900])

        layout = QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # 信号连接
        self.file_manager.audio_list.itemClicked.connect(self.sync_audio)

    def sync_audio(self):
        """文件导入后，同步音频到分析面板"""
        y = self.file_manager.y
        sr = self.file_manager.sr
        if y is not None and sr is not None:
            logger.info("同步音频到分析模块")
            self.analysis_panel.load_audio(y, sr,draw=False)

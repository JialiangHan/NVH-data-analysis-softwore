from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        rcParams['font.family'] = ['Microsoft YaHei', 'SimHei']
        rcParams['axes.unicode_minus'] = False
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.subplots()

        # 用户自定义的坐标轴范围
        self.user_xlim = None
        self.user_ylim = None
        # 坐标轴输入控件
        self.x_min_input = QLineEdit()
        self.x_min_input.setPlaceholderText("X最小")
        self.x_max_input = QLineEdit()
        self.x_max_input.setPlaceholderText("X最大")
        self.y_min_input = QLineEdit()
        self.y_min_input.setPlaceholderText("Y最小")
        self.y_max_input = QLineEdit()
        self.y_max_input.setPlaceholderText("Y最大")
        self.apply_button = QPushButton("应用坐标范围")

        # 布局
        axis_layout = QHBoxLayout()
        axis_layout.addWidget(QLabel("X范围:"))
        axis_layout.addWidget(self.x_min_input)
        axis_layout.addWidget(self.x_max_input)
        axis_layout.addWidget(QLabel("Y范围:"))
        axis_layout.addWidget(self.y_min_input)
        axis_layout.addWidget(self.y_max_input)
        axis_layout.addWidget(self.apply_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(axis_layout)
        main_layout.addWidget(self.canvas)
        self.setLayout(main_layout)

        # 信号连接
        self.apply_button.clicked.connect(self.apply_limits)

    # -----------------------------
    # 绘图方法
    def plot(self, x, y, title=""):
        self.ax.clear()
        self.ax.plot(x, y)
        self.ax.set_title(title)
        self.ax.set_xlabel("频率 (Hz)")
        self.ax.set_ylabel("幅值")
        # ✅ 如果用户设置了坐标轴范围，应用它
        if self.user_xlim is not None:
            self.ax.set_xlim(*self.user_xlim)
        if self.user_ylim is not None:
            self.ax.set_ylim(*self.user_ylim)
        self.canvas.draw()
        logger.info(f"绘制图像: {title}")

    # -----------------------------
    # 应用坐标轴范围
    def apply_limits(self):
        try:
            xmin = float(self.x_min_input.text()) if self.x_min_input.text() else None
            xmax = float(self.x_max_input.text()) if self.x_max_input.text() else None
            ymin = float(self.y_min_input.text()) if self.y_min_input.text() else None
            ymax = float(self.y_max_input.text()) if self.y_max_input.text() else None
            # 保存用户设置
            self.user_xlim = (xmin, xmax) if xmin is not None or xmax is not None else None
            self.user_ylim = (ymin, ymax) if ymin is not None or ymax is not None else None

            if xmin is not None or xmax is not None:
                self.ax.set_xlim(left=xmin, right=xmax)
            if ymin is not None or ymax is not None:
                self.ax.set_ylim(bottom=ymin, top=ymax)

            self.canvas.draw()
            logger.info(f"应用坐标轴范围: X{self.user_xlim} Y{self.user_ylim}")
        except Exception as e:
            logger.error(f"应用坐标轴范围失败: {e}")

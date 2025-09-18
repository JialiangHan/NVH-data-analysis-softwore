from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,QInputDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
import numpy as np
import logging
from scipy.signal import spectrogram
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

logger = logging.getLogger(__name__)

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        rcParams['font.family'] = ['Microsoft YaHei', 'SimHei']
        rcParams['axes.unicode_minus'] = False

        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.subplots()
        # 添加 Matplotlib 工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        # 初始化交互
        self.connect_interaction()
        # 连接双击事件
        self.canvas.mpl_connect("button_press_event", self.on_double_click)
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
        main_layout.addWidget(self.toolbar)  # 工具栏
        main_layout.addWidget(self.canvas)  # 画布
        self.setLayout(main_layout)

        # 信号连接
        self.apply_button.clicked.connect(self.apply_limits)

    # -----------------------------
    def clear(self):
        """清除图像"""
        self.figure.clear()
        self.canvas.draw()
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

    def plot_spectrogram(self, y, sr):
        """绘制声谱图"""
        self.ax.clear()
        f, t, Sxx = spectrogram(y, fs=sr, nperseg=1024)

        pcm = self.ax.pcolormesh(
            t, f, 10 * np.log10(Sxx + 1e-10),
            shading="gouraud", cmap="magma"
        )
        self.ax.set_ylabel("频率 [Hz]")
        self.ax.set_xlabel("时间 [s]")
        self.ax.set_title("声谱图")
        self.canvas.figure.colorbar(pcm, ax=self.ax, label="功率 [dB]")
        self.canvas.draw()

    def connect_interaction(self):
        """添加鼠标滚轮缩放功能"""

        def on_scroll(event):
            ax = event.inaxes
            if ax is None:
                return

            # 滚轮方向
            scale_factor = 1.2 if event.button == "up" else 1 / 1.2

            # 当前坐标范围
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # 以鼠标为中心缩放
            x_center, y_center = event.xdata, event.ydata
            ax.set_xlim([
                x_center - (x_center - xlim[0]) * scale_factor,
                x_center + (xlim[1] - x_center) * scale_factor
            ])
            ax.set_ylim([
                y_center - (y_center - ylim[0]) * scale_factor,
                y_center + (ylim[1] - y_center) * scale_factor
            ])

            self.canvas.draw_idle()

        # 绑定事件
        self.canvas.mpl_connect("scroll_event", on_scroll)

    def on_double_click(self, event):
        """双击坐标轴时调整范围"""
        if not event.dblclick:
            return
        if event.inaxes is None:
            logger.debug("双击在空白区域，忽略")
            return

        # 获取画布大小
        fig_w, fig_h = self.canvas.figure.get_size_inches() * self.canvas.figure.dpi
        ax_pos = event.inaxes.get_position()

        # 坐标轴在像素中的位置
        x0 = ax_pos.x0 * fig_w
        x1 = ax_pos.x1 * fig_w
        y0 = ax_pos.y0 * fig_h
        y1 = ax_pos.y1 * fig_h

        # 判断是否在 X 轴附近（底部）
        if abs(event.y - y0) < 30 and x0 <= event.x <= x1:
            axis = "x"
            current_range = event.inaxes.get_xlim()
        # 判断是否在 Y 轴附近（左侧）
        elif abs(event.x - x0) < 50 and y0 <= event.y <= y1:
            axis = "y"
            current_range = event.inaxes.get_ylim()
        else:
            logger.debug("双击不在坐标轴附近，忽略")
            return

        logger.info(f"双击 {axis.upper()} 轴, 当前范围={current_range}")

        # 弹窗输入范围
        text, ok = QInputDialog.getText(
            self, f"设置 {axis.upper()} 轴范围", f"输入范围 (min,max)，当前={current_range}:"
        )
        if ok and "," in text:
            try:
                vmin, vmax = map(float, text.split(","))
                if axis == "x":
                    event.inaxes.set_xlim(vmin, vmax)
                    logger.info(f"设置X轴范围: {vmin} ~ {vmax}")
                else:
                    event.inaxes.set_ylim(vmin, vmax)
                    logger.info(f"设置Y轴范围: {vmin} ~ {vmax}")
                self.canvas.draw()
            except Exception as e:
                logger.error(f"输入错误: {e}")
        else:
            logger.debug("用户取消输入或输入格式不正确")

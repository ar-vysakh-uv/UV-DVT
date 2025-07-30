## Sample File for Upload for GUI 
import sys
import pandas as pd
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QCheckBox, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
import itertools

# Event map
event_map = {
    "0x01": "Charging Started",
    "0x02": "Connector 1 Active",
    "0x03": "Connector 2 Active",
    "0x04": "Door Open",
    "0x05": "Emergency Stop"
}

colors = itertools.cycle(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0'])

class ChargingUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Charging Status Visualizer")
        self.setGeometry(100, 100, 1300, 750)

        self.file_path = None
        self.checkboxes = {}
        self.df_cached = None
        self.selected_events = []

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ==== LEFT PANEL ====
        control_panel = QVBoxLayout()

        title = QLabel("🔧 Select Events to Plot:")
        title.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        control_panel.addWidget(title)

        # Select All / None buttons
        btn_row = QHBoxLayout()
        sel_all_btn = QPushButton("Select All")
        sel_all_btn.clicked.connect(self.select_all)
        btn_row.addWidget(sel_all_btn)

        sel_none_btn = QPushButton("Select None")
        sel_none_btn.clicked.connect(self.select_none)
        btn_row.addWidget(sel_none_btn)
        control_panel.addLayout(btn_row)

        # Scroll Area with checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout()

        for _, event_name in event_map.items():
            cb = QCheckBox(event_name)
            cb.setStyleSheet("margin: 5px;")
            self.checkboxes[event_name] = cb
            checkbox_layout.addWidget(cb)

        checkbox_container.setLayout(checkbox_layout)
        scroll.setWidget(checkbox_container)
        scroll.setFixedHeight(300)
        control_panel.addWidget(scroll)

        # File & Plot buttons
        control_panel.addSpacing(10)
        load_btn = QPushButton("📂 Load Log File")
        load_btn.clicked.connect(self.load_file)
        control_panel.addWidget(load_btn)
        self.path_label = QLabel("No file selected.")
        self.path_label.setStyleSheet("font-size: 11px; color: #555;")
        control_panel.addWidget(self.path_label)

        plot_btn = QPushButton("📊 Plot Graph")
        plot_btn.clicked.connect(self.plot_graph)
        control_panel.addWidget(plot_btn)

        # Info panel
        spacer = QFrame()
        spacer.setFrameShape(QFrame.HLine)
        control_panel.addWidget(spacer)

        info = QLabel("Use toolbar below the graph to zoom/pan.\nClick the magnifying glass, then drag to zoom.")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 12px; color: gray;")
        control_panel.addWidget(info)

        main_layout.addLayout(control_panel, 2)

        # ==== RIGHT PANEL WITH PLOT + TOOLBAR ====
        right_panel = QVBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)
        right_panel.addWidget(self.toolbar)
        right_panel.addWidget(self.canvas)

        main_layout.addLayout(right_panel, 8)

        self.setLayout(main_layout)

    def select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def select_none(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Charging Log File", "", "Text Files (*.txt)")
        if fname:
            self.file_path = fname
            self.path_label.setText(f"Loaded file: {fname}")
            self.df_cached = None  # Reset cache on new file

    def plot_graph(self):
        if not self.file_path:
            return

        self.selected_events = [e for e, cb in self.checkboxes.items() if cb.isChecked()]
        if not self.selected_events:
            return

        # Read and cache data if not already done
        if self.df_cached is None:
            df_rows = []
            start_time = datetime.now()

            with open(self.file_path, 'r') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                hex_val = line.strip()
                timestamp = start_time + timedelta(seconds=i)
                row = {event: 0 for event in event_map.values()}
                if hex_val in event_map:
                    row[event_map[hex_val]] = 1
                row["Time"] = timestamp
                df_rows.append(row)

            df = pd.DataFrame(df_rows)
            df.set_index("Time", inplace=True)
            df = df.replace(0, pd.NA).ffill().fillna(0)
            self.df_cached = df

        df = self.df_cached[self.selected_events]

        self.figure.clear()
        axes = self.figure.subplots(len(self.selected_events), 1, sharex=True)

        if len(self.selected_events) == 1:
            axes = [axes]

        for i, event in enumerate(self.selected_events):
            c = next(colors)
            axes[i].plot(df.index, df[event], drawstyle='steps-post', color=c, linewidth=2.5, label=event)
            axes[i].set_ylabel(event, fontsize=10)
            axes[i].set_ylim(-0.1, 1.1)
            axes[i].grid(True, linestyle='--', alpha=0.6)
            axes[i].legend(loc="upper right", fontsize=9)

        axes[-1].set_xlabel("Time", fontsize=11)
        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QPushButton { padding: 6px 12px; font-weight: bold; }")
    window = ChargingUI()
    window.show()
    sys.exit(app.exec_())

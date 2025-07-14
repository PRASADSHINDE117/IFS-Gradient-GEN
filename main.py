import sys
import platform
import ctypes
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QColorDialog,
    QComboBox, QFileDialog, QMessageBox, QFrame, QSizeGrip, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QMouseEvent, QFont, QPalette, QBrush, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize, QTimer, pyqtSignal
import json
import math

# --- Windows Acrylic Helper ---
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int)
    ]
class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t)
    ]

def enable_windows_acrylic(hwnd):
    accent = ACCENTPOLICY()
    accent.AccentFlags = 2
    accent.AnimationId = 0
    accent_states = [4, 3, 2]
    for state in accent_states:
        accent.AccentState = state
        # Format: 0xAABBGGRR (Alpha, Blue, Green, Red)
        accent.GradientColor = 0xbb200000  # 60% opacity white
        data = WINCOMPATTRDATA()
        data.Attribute = 19
        data.Data = ctypes.addressof(accent)
        data.SizeOfData = ctypes.sizeof(accent)
        try:
            ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        except Exception:
            continue

class ColorStop:
    def __init__(self, position, color):
        self.position = position  # 0.0 - 1.0
        self.color = QColor(color)

class GradientRamp(QWidget):
    def __init__(self, stops, on_change, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)
        self.stops = stops
        self.selected = None
        self.dragging = False
        self.on_change = on_change
        self.setMouseTracking(True)
        self.setStyleSheet("background: rgba(255, 255, 255, 0.60);")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Main gradient rect
        rect = self.rect().adjusted(20, 20, -20, -40)
        
        # Draw gradient background
        grad = QLinearGradient(rect.left(), 0, rect.right(), 0)
        for stop in self.stops:
            grad.setColorAt(stop.position, stop.color)
        
        # Draw gradient with enhanced glass border
        painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(rect, 15, 15)
        
        # Draw multiple inner glows for glass effect
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)
        
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 13, 13)
        
        # Draw stops with glass effect
        for i, stop in enumerate(self.stops):
            x = rect.left() + stop.position * rect.width()
            y = rect.bottom() + 20
            r = 14 if i == self.selected else 12
            
            # Multiple shadow layers for depth
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.drawEllipse(QPointF(x + 3, y + 3), r + 3, r + 3)
            painter.setBrush(QColor(0, 0, 0, 60))
            painter.drawEllipse(QPointF(x + 2, y + 2), r + 2, r + 2)
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.drawEllipse(QPointF(x + 1, y + 1), r + 1, r + 1)
            
            # Stop circle with glass effect
            painter.setBrush(QBrush(stop.color))
            painter.setPen(QPen(QColor(255, 255, 255, 220), 3 if i == self.selected else 2))
            painter.drawEllipse(QPointF(x, y), r, r)
            
            # Inner highlight
            painter.setBrush(QColor(255, 255, 255, 60))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x - r/3, y - r/3), r/2, r/2)
            
            # Selection indicator with glow
            if i == self.selected:
                painter.setPen(QPen(QColor(100, 200, 255, 200), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(x, y), r + 6, r + 6)
                painter.setPen(QPen(QColor(100, 200, 255, 100), 1))
                painter.drawEllipse(QPointF(x, y), r + 8, r + 8)

    def mousePressEvent(self, event: QMouseEvent):
        rect = self.rect().adjusted(20, 20, -20, -40)
        
        # Check if clicking on existing stop
        for i, stop in enumerate(self.stops):
            x = rect.left() + stop.position * rect.width()
            y = rect.bottom() + 20
            if (QPointF(x, y) - event.pos()).manhattanLength() < 18:
                self.selected = i
                self.dragging = True
                self.on_change()
                self.update()
                return
        
        # Add new stop if clicking on gradient area
        if rect.contains(event.pos()):
            pos = max(0.0, min(1.0, (event.x() - rect.left()) / rect.width()))
            
            # Interpolate color at this position
            color = self.interpolate_color_at_position(pos)
            
            new_stop = ColorStop(pos, color)
            self.stops.append(new_stop)
            self.stops.sort(key=lambda s: s.position)
            self.selected = next(i for i, s in enumerate(self.stops) if s.position == pos)
            self.on_change()
            self.update()

    def interpolate_color_at_position(self, pos):
        if not self.stops:
            return QColor(255, 255, 255)
        
        # Find surrounding stops
        left_stop = None
        right_stop = None
        
        for stop in self.stops:
            if stop.position <= pos:
                left_stop = stop
            if stop.position >= pos and right_stop is None:
                right_stop = stop
        
        if left_stop is None:
            return right_stop.color
        if right_stop is None:
            return left_stop.color
        if left_stop == right_stop:
            return left_stop.color
        
        # Linear interpolation
        factor = (pos - left_stop.position) / (right_stop.position - left_stop.position)
        r = int(left_stop.color.red() + factor * (right_stop.color.red() - left_stop.color.red()))
        g = int(left_stop.color.green() + factor * (right_stop.color.green() - left_stop.color.green()))
        b = int(left_stop.color.blue() + factor * (right_stop.color.blue() - left_stop.color.blue()))
        
        return QColor(r, g, b)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.selected is not None:
            rect = self.rect().adjusted(20, 20, -20, -40)
            pos = (event.x() - rect.left()) / rect.width()
            pos = max(0.0, min(1.0, pos))
            self.stops[self.selected].position = pos
            self.stops.sort(key=lambda s: s.position)
            # Update selected index after sorting
            self.selected = next(i for i, s in enumerate(self.stops) if s.position == pos)
            self.on_change()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.selected is not None and len(self.stops) > 2:
            del self.stops[self.selected]
            self.selected = None
            self.on_change()
            self.update()

class ColorPreviewButton(QPushButton):
    def __init__(self, color, on_color, parent=None):
        super().__init__(parent)
        self.color = color
        self.on_color = on_color
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
        self.clicked.connect(self.pick_color)

    def update_style(self):
        border_color = self.color.name()
        self.setStyleSheet(f'''
            QPushButton {{
                border-radius: 22px;
                border: 3px solid {border_color};
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5,
                    stop:0 #fff,
                    stop:0.5 {self.color.name()},
                    stop:1 #222a36);
                box-shadow: 0 2px 10px rgba(0,0,0,0.25);
            }}
            QPushButton:hover {{
                border: 3px solid #fff;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5,
                    stop:0 #fff,
                    stop:0.5 {self.color.name()},
                    stop:1 #2a2a2a);
            }}
            QPushButton:pressed {{
                border: 3px solid {border_color};
                background: {self.color.name()};
            }}
        '''.replace('{', '{{').replace('}', '}}').replace('{{self.color.name()}}', '{self.color.name()}').replace('{{border_color}}', '{border_color}'))

    def setColor(self, color):
        self.color = color
        self.update_style()

    def pick_color(self):
        dlg = QColorDialog(self.color, self)
        dlg.setOption(QColorDialog.DontUseNativeDialog)
        palette = dlg.palette()
        palette.setColor(dlg.backgroundRole(), Qt.white)
        palette.setColor(dlg.foregroundRole(), Qt.black)
        dlg.setPalette(palette)
        if dlg.exec_():
            color = dlg.selectedColor()
            if color.isValid():
                self.color = color
                self.update_style()
                self.on_color(color)

# --- Improved FineSlider ---
def create_fine_slider_style():
    return """
        QSlider::groove:horizontal {
            border: 1px solid rgba(255, 255, 255, 0.6);
            height: 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(40, 50, 70, 0.8),
                stop:1 rgba(60, 80, 120, 0.8));
            border-radius: 6px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.95),
                stop:1 rgba(240, 240, 240, 0.9));
            border: 2px solid rgba(100, 150, 255, 0.9);
            width: 24px;
            height: 24px;
            border-radius: 12px;
            margin: -6px 0;
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 1.0),
                stop:1 rgba(255, 255, 255, 0.95));
            border: 2px solid rgb(120, 170, 255);
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 150, 255, 0.9),
                stop:1 rgba(120, 170, 255, 0.8));
            border-radius: 6px;
        }
    """
class ImprovedFineSlider(QWidget):
    def __init__(self, label, value, minv, maxv, on_change, parent=None):
        super().__init__(parent)
        self.on_change = on_change
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        self.label = QLabel(label)
        self.label.setFixedWidth(24)
        self.label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-weight: bold;
                font-size: 14px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 6px;
                padding: 6px;
                text-align: center;
            }
        """)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(minv)
        self.slider.setMaximum(maxv)
        self.slider.setValue(value)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(10)
        self.slider.setStyleSheet(create_fine_slider_style())
        self.value_label = QLabel(str(value))
        self.value_label.setFixedWidth(50)
        self.value_label.setStyleSheet("""
            QLabel {
                color: rgba(40, 50, 70, 0.95);
                font-size: 13px;
                font-weight: bold;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 8px;
                padding: 6px 10px;
                text-align: center;
            }
        """)
        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        self.slider.valueChanged.connect(self.value_changed)
    def value_changed(self, value):
        self.value_label.setText(str(value))
        self.on_change(value)
# --- UI improvement utilities ---
def update_color_preview_styling(self):
    if hasattr(self, 'color_preview'):
        self.color_preview.setStyleSheet(f'''
            QPushButton {{
                border-radius: 22px;
                border: 3px solid rgba(255, 255, 255, 0.8);
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.3, fy:0.3,
                    stop:0 rgba(255, 255, 255, 0.9),
                    stop:0.3 {self.color_preview.color.name()},
                    stop:1 rgba(40, 50, 70, 0.8));
                min-width: 44px;
                min-height: 44px;
            }}
            QPushButton:hover {{
                border: 3px solid rgba(255, 255, 255, 1.0);
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.3, fy:0.3,
                    stop:0 rgba(255, 255, 255, 1.0),
                    stop:0.3 {self.color_preview.color.name()},
                    stop:1 rgba(60, 70, 90, 0.9));
            }}
            QPushButton:pressed {{
                border: 3px solid rgba(100, 150, 255, 1.0);
                background: {self.color_preview.color.name()};
            }}
            QPushButton:disabled {{
                border: 3px solid rgba(255, 255, 255, 0.3);
                background: rgba(100, 100, 100, 0.5);
            }}
        ''')
def improve_gradient_ramp_styling(self):
    if hasattr(self, 'ramp'):
        self.ramp.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.7),
                    stop:1 rgba(255, 255, 255, 0.6));
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
            }
        """)
def improve_label_contrast():
    return """
        QLabel {
            color: rgba(255, 255, 255, 0.95);
            font-weight: 600;
            font-size: 14px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            padding: 6px 12px;
            margin: 2px;
        }
    """
def improve_combo_box_styling():
    return """
        QComboBox {
            background: rgba(255, 255, 255, 0.25);
            color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            padding: 10px 15px;
            font-size: 13px;
            font-weight: 500;
            min-width: 120px;
        }
        QComboBox:hover {
            background: rgba(255, 255, 255, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.7);
        }
        QComboBox::drop-down {
            border: none;
            width: 30px;
            background: transparent;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 7px solid transparent;
            border-right: 7px solid transparent;
            border-top: 7px solid rgba(255, 255, 255, 0.8);
            margin-right: 10px;
        }
        QComboBox::down-arrow:hover {
            border-top: 7px solid rgba(255, 255, 255, 1.0);
        }
        QComboBox QAbstractItemView {
            background: rgba(40, 50, 70, 0.95);
            color: rgba(255, 255, 255, 0.95);
            selection-background-color: rgba(100, 150, 255, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 8px;
            padding: 5px;
            outline: none;
        }
        QComboBox QAbstractItemView::item {
            padding: 8px 12px;
            border-radius: 4px;
            margin: 2px;
        }
        QComboBox QAbstractItemView::item:selected {
            background: rgba(100, 150, 255, 0.6);
        }
    """
def apply_ui_improvements(self):
    self.interp_combo.setStyleSheet(improve_combo_box_styling())
    update_color_preview_styling(self)
    improve_gradient_ramp_styling(self)
    for label in [self.selected_label]:
        if hasattr(label, 'setStyleSheet'):
            label.setStyleSheet(improve_label_contrast())

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25),
                    stop:1 rgba(255, 255, 255, 0.15));
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel(" Glass Gradient Editor")
        title.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 15px;
                font-weight: bold;
                background: transparent;
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
            }
        """)
        
        layout.addWidget(title)
        layout.addStretch()
        
        # Minimize button
        min_btn = QPushButton("−")
        min_btn.setFixedSize(32, 32)
        min_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 16px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
        """)
        min_btn.clicked.connect(parent.showMinimized)
        layout.addWidget(min_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 100, 100, 0.4);
                border: 1px solid rgba(255, 100, 100, 0.6);
                border-radius: 16px;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.7);
                border: 1px solid rgba(255, 100, 100, 0.9);
            }
        """)
        close_btn.clicked.connect(parent.close)
        layout.addWidget(close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self.parent, 'drag_pos'):
            self.parent.move(self.parent.pos() + event.globalPos() - self.parent.drag_pos)
            self.parent.drag_pos = event.globalPos()

class GradientEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gradient Editor")
        self.setGeometry(200, 200, 1200, 700)
        self.setMinimumSize(1200, 700)
        
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(GlassStyles.main_window())
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_widget.setStyleSheet(GlassStyles.main_widget())
        controls_frame = QFrame()
        controls_frame.setStyleSheet(GlassStyles.controls_frame())
        # Add subtle drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        # Apply blur after show
        if platform.system() == "Windows":
            QTimer.singleShot(100, lambda: enable_windows_acrylic(int(self.winId())))
        
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        # Content area
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.setSpacing(24)
        
        # Color stops
        self.stops = [ColorStop(0.0, '#FF6B6B'), ColorStop(0.5, '#4ECDC4'), ColorStop(1.0, '#45B7D1')]
        self.ramp = GradientRamp(self.stops, self.update_ui)
        content_layout.addWidget(self.ramp)
        
        # Controls container with enhanced glass effect
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.18),
                    stop:1 rgba(255, 255, 255, 0.12));
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(24, 20, 24, 20)
        controls_layout.setSpacing(18)
        
        # Interpolation
        interp_layout = QHBoxLayout()
        interp_label = QLabel("Interpolation:")
        interp_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-weight: bold;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
            }
        """)
        
        self.interp_combo = QComboBox()
        self.interp_combo.addItems(["Linear", "Ease In", "Ease Out", "Ease In-Out"])
        self.interp_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 12px;
                font-weight: 500;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.8);
            }
            QComboBox QAbstractItemView {
                background: rgba(30, 30, 50, 0.95);
                color: rgba(255, 255, 255, 0.95);
                selection-background-color: rgba(100, 150, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        interp_layout.addWidget(interp_label)
        interp_layout.addWidget(self.interp_combo)
        interp_layout.addStretch()
        controls_layout.addLayout(interp_layout)
        
        # Selected stop editor
        self.selected_label = QLabel("Click on a gradient stop to edit")
        self.selected_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
                font-style: italic;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
            }
        """)
        controls_layout.addWidget(self.selected_label)
        
        # Color wheel
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        color_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-weight: bold;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
            }
        """)
        color_layout.addWidget(color_label)
        self.color_preview = ColorPreviewButton(QColor('#FF6B6B'), self.change_selected_color)
        self.color_preview.setEnabled(False)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        controls_layout.addLayout(color_layout)
        
        # Fine sliders
        self.fine_slider_layout = QVBoxLayout()
        self.fine_slider_layout.setSpacing(10)
        controls_layout.addLayout(self.fine_slider_layout)
        
        content_layout.addWidget(controls_frame)
        
        # Buttons with enhanced glass styling
        btn_layout = QHBoxLayout()
        btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25),
                    stop:1 rgba(255, 255, 255, 0.15));
                color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.35),
                    stop:1 rgba(255, 255, 255, 0.25));
                border: 1px solid rgba(255, 255, 255, 0.6);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15),
                    stop:1 rgba(255, 255, 255, 0.1));
                box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
            }
        """
        
        save_btn = QPushButton("Save Gradient")
        load_btn = QPushButton("Load Gradient")
        export_btn = QPushButton("Export CSS")
        export_jw_btn = QPushButton("Export JWF Gradient")
        export_full_btn = QPushButton("Export Full .gradient")
        export_png_btn = QPushButton("Export PNG")
        # Now set their styles
        for btn in [save_btn, load_btn, export_btn, export_jw_btn, export_full_btn, export_png_btn]:
            btn.setStyleSheet(GlassStyles.glass_button() + btn_style)
        
        save_btn.clicked.connect(self.save_gradient)
        
        load_btn.clicked.connect(self.load_gradient)
        
        export_btn.clicked.connect(self.export_css)
        
        # Add JWildfire export button
        export_jw_btn.clicked.connect(self.export_jwildfire_gradient)

        # Add Full .gradient export button
        export_full_btn.clicked.connect(self.export_full_gradient)

        export_png_btn.clicked.connect(self.export_png)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(export_jw_btn)
        btn_layout.addWidget(export_full_btn)
        btn_layout.addWidget(export_png_btn)
        btn_layout.addStretch()
        
        content_layout.addLayout(btn_layout)
        main_layout.addWidget(content)
        
        self.fine_sliders = []
        
        # Size grip for resizing
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("""
            QSizeGrip {
                background: rgba(255, 255, 255, 0.3);
                width: 18px;
                height: 18px;
                border-radius: 9px;
            }
        """)
        
        self.update_ui()

        # --- GLASSMORPHIC UI IMPROVEMENTS (Reference-Inspired) ---
        # Remove unsupported QSS properties and improve button spacing
        # Title bar styling (no text-shadow/box-shadow)
        self.title_bar.setFixedHeight(44)
        self.title_bar.setStyleSheet("""
            QFrame#titleBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.18), stop:1 rgba(255,255,255,0.10));
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                border-bottom: 1px solid rgba(255,255,255,0.60);
            }
        """)
        # Main widget background
        self.main_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(40, 45, 60, 0.82), stop:1 rgba(30, 32, 40, 0.92));
                border-radius: 20px;
                border: 1.5px solid rgba(255,255,255,0.60);
            }
        """)
        # Control panel glass effect
        controls_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.09);
                border-radius: 14px;
                border: 1.2px solid rgba(255,255,255,0.60);
            }
        """)
        # Button bar
        btn_layout.setSpacing(28)
        btn_layout.setContentsMargins(20, 18, 20, 18)
        for btn in [save_btn, load_btn, export_btn, export_jw_btn, export_full_btn, export_png_btn]:
            btn.setMinimumWidth(150)
            btn.setMaximumWidth(220)
            btn.setMinimumHeight(44)
            btn.setStyleSheet(
                """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #444a5a, stop:1 #353945);
                    color: #e0e0e0;
                    border: 1.5px solid rgba(255,255,255,0.13);
                    border-radius: 10px;
                    font-size: 13px;
                    margin: 0 12px;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background: #5a5f73;
                    border: 1.5px solid #7faaff;
                }
                QPushButton:pressed {
                    background: #23242a;
                }
                """
            )
        btn_layout.setSpacing(24)
        btn_layout.setContentsMargins(24, 12, 24, 12)
        btn_layout.insertStretch(0, 1)
        btn_layout.addStretch(1)
        self.setMinimumHeight(700)
        # Interpolation and color controls
        interp_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #e0e0e0; padding-right: 8px;")
        self.interp_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0,0,0,0.18); border-radius: 8px; padding: 7px 16px;
                border: 1.2px solid rgba(255,255,255,0.13); color: #e0e0e0; font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 22px; }
            QComboBox QAbstractItemView {
                background: #23242a; border: 1px solid rgba(255,255,255,0.13);
                selection-background-color: rgba(100, 150, 255, 0.13);
            }
        """)
        color_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #e0e0e0; padding-right: 8px;")
        # Interpolation label: high contrast
        interp_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f0f0; padding-right: 10px;")
        # Selected label: high contrast
        self.selected_label.setStyleSheet('''
            QLabel {
                color: #f0f0f0;
                font-size: 13px;
                font-style: italic;
                background: rgba(60,60,80,0.18);
                border-radius: 10px;
                padding: 18px 12px;
                margin-bottom: 10px;
            }
        ''')
        # Fine slider layout
        self.fine_slider_layout.setSpacing(14)
        controls_layout.setSpacing(22)
        controls_layout.setContentsMargins(32, 28, 32, 28)
        content_layout.setSpacing(32)
        # Window background polish
        self.setStyleSheet(self.styleSheet() + "QMainWindow {background: #23242a;}")
        # --- END GLASSMORPHIC UI IMPROVEMENTS ---

        # --- UI COLOR & FONT IMPROVEMENTS (APPLY AFTER UI CREATION) ---
        # Set a modern, readable font for the whole app
        try:
            app_font = QFont("Segoe UI", 11)
            self.setFont(app_font)
        except Exception:
            pass
        # Apply font and color to all labels and buttons
        def set_font_recursive(widget, font):
            widget.setFont(font)
            for child in widget.findChildren(QWidget):
                child.setFont(font)
        set_font_recursive(self, QFont("Segoe UI", 11))
        # Ensure all labels use high-contrast color
        for label in self.findChildren(QLabel):
            label.setStyleSheet(label.styleSheet() + "color: #f0f0f0; font-family: 'Segoe UI', Arial, sans-serif;")
        for btn in self.findChildren(QPushButton):
            btn.setStyleSheet(btn.styleSheet() + "color: #f0f0f0; font-family: 'Segoe UI', Arial, sans-serif;")
        for combo in self.findChildren(QComboBox):
            combo.setStyleSheet(combo.styleSheet() + "color: #f0f0f0; font-family: 'Segoe UI', Arial, sans-serif;")
        # Color wheel button: make border and background stand out
        self.color_preview.setStyleSheet(f'''
            QPushButton {{
                border-radius: 22px;
                border: 3px solid #7faaff;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5,
                    stop:0 #fff,
                    stop:0.7 {self.color_preview.color.name()},
                    stop:1 #222a36);
            }}
            QPushButton:hover {{
                border: 3px solid #fff;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5,
                    stop:0 #fff,
                    stop:0.7 {self.color_preview.color.name()},
                    stop:1 #2a2a2a);
            }}
            QPushButton:pressed {{
                border: 3px solid #7faaff;
                background: {self.color_preview.color.name()};
            }}
        ''')
        # Color label: high contrast
        color_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f0f0; padding-right: 10px;")
        # Interpolation label: high contrast
        interp_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f0f0; padding-right: 10px;")
        # Selected label: high contrast
        self.selected_label.setStyleSheet('''
            QLabel {
                color: #f0f0f0;
                font-size: 13px;
                font-style: italic;
                background: rgba(60,60,80,0.18);
                border-radius: 10px;
                padding: 18px 12px;
                margin-bottom: 10px;
            }
        ''')
        # --- END UI COLOR & FONT IMPROVEMENTS ---

        apply_ui_improvements(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position size grip in bottom right
        if hasattr(self, 'size_grip'):
            self.size_grip.move(self.width() - 18, self.height() - 18)

    def update_ui(self):
        sel = self.ramp.selected
        # Clear existing sliders
        for slider in self.fine_sliders:
            slider.setParent(None)
        self.fine_sliders.clear()
        # Remove old color wheel if present
        if hasattr(self, 'hsv_color_wheel') and self.hsv_color_wheel:
            self.hsv_color_wheel.setParent(None)
            self.hsv_color_wheel = None
        if hasattr(self, 'quick_color_label') and self.quick_color_label:
            self.quick_color_label.setParent(None)
            self.quick_color_label = None
        if sel is not None and sel < len(self.stops):
            stop = self.stops[sel]
            self.selected_label.setText(f"Editing stop at position {stop.position:.3f}")
            self.color_preview.setEnabled(True)
            self.color_preview.setColor(stop.color)
            # Add 'QUICK COLOR' label
            from PyQt5.QtWidgets import QLabel
            self.quick_color_label = QLabel("QUICK COLOR")
            self.quick_color_label.setStyleSheet("color: #f0f0f0; font-size: 13px; font-weight: bold; letter-spacing: 2px; margin-bottom: 4px; font-family: 'Segoe UI', Arial, sans-serif;")
            self.fine_slider_layout.addWidget(self.quick_color_label)
            # Add HSV color wheel
            self.hsv_color_wheel = HSVColorWheel(stop.color, self)
            self.hsv_color_wheel.colorChanged.connect(self.change_selected_color)
            self.fine_slider_layout.addWidget(self.hsv_color_wheel)
            # Link: when color is changed by QColorDialog, update HSV wheel and stop
            def open_linked_color_dialog():
                dlg = QColorDialog(stop.color, self)
                dlg.setOption(QColorDialog.DontUseNativeDialog)
                dark_palette = dlg.palette()
                from PyQt5.QtGui import QPalette
                dark_palette.setColor(QPalette.Window, QColor(34, 34, 40))
                dark_palette.setColor(QPalette.Base, QColor(34, 34, 40))
                dark_palette.setColor(QPalette.Text, QColor(240, 240, 240))
                dark_palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
                dark_palette.setColor(QPalette.WindowText, QColor(240, 240, 240))
                dark_palette.setColor(QPalette.Highlight, QColor(100, 150, 255))
                dark_palette.setColor(QPalette.HighlightedText, QColor(34, 34, 40))
                dlg.setPalette(dark_palette)
                dlg.setStyleSheet("QWidget { color: #f0f0f0; background: #222228; font-family: 'Segoe UI', Arial, sans-serif; }")
                if dlg.exec_():
                    color = dlg.selectedColor()
                    if color.isValid():
                        self.hsv_color_wheel.setColor(color)
                        self.change_selected_color(color)
            # Patch the color options button to open the linked dialog
            self.hsv_color_wheel._picker_btn.clicked.disconnect()
            self.hsv_color_wheel._picker_btn.clicked.connect(open_linked_color_dialog)
        else:
            self.selected_label.setText("Click on a gradient stop to edit")
            self.color_preview.setEnabled(False)

    def change_selected_rgb(self, channel, value):
        sel = self.ramp.selected
        if sel is not None and sel < len(self.stops):
            color = self.stops[sel].color
            rgb = [color.red(), color.green(), color.blue()]
            rgb[channel] = value
            self.stops[sel].color = QColor(*rgb)
            self.ramp.update()
            self.update_ui()

    def change_selected_position(self, value):
        sel = self.ramp.selected
        if sel is not None and sel < len(self.stops):
            pos = value / 1000.0
            self.stops[sel].position = pos
            self.stops.sort(key=lambda s: s.position)
            self.ramp.selected = self.stops.index(self.stops[sel])
            self.ramp.update()
            self.update_ui()

    def change_selected_color(self, color):
        sel = self.ramp.selected
        if sel is not None and sel < len(self.stops):
            self.stops[sel].color = color
            self.ramp.update()
            self.color_preview.setColor(color)
            self.update_ui()

    def save_gradient(self):
        data = [
            {'position': stop.position, 'color': stop.color.name()} for stop in self.stops
        ]
        try:
            with open('gradient.json', 'w') as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Saved", "Gradient saved to gradient.json")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save: {e}")

    def load_gradient(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Gradient", "", "Gradient Files (*.json *.gradient)")
        if not fname:
            return
        if fname.endswith('.json'):
            try:
                with open(fname, 'r') as f:
                    data = json.load(f)
                self.stops.clear()
                for stop in data:
                    self.stops.append(ColorStop(stop['position'], stop['color']))
                self.ramp.selected = None
                self.ramp.update()
                self.update_ui()
                QMessageBox.information(self, "Loaded", f"Gradient loaded from {fname}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load: {e}")
        elif fname.endswith('.gradient'):
            try:
                with open(fname, 'r') as f:
                    lines = f.readlines()
                # First, try to parse editor metadata stops
                stops = []
                for line in lines:
                    if line.strip().startswith('# pos='):
                        parts = line.strip().split()
                        pos = float(parts[1].split('=')[1])
                        color = parts[2].split('=')[1]
                        stops.append(ColorStop(pos, color))
                if stops:
                    self.stops.clear()
                    self.stops.extend(sorted(stops, key=lambda s: s.position))
                    self.ramp.selected = None
                    self.ramp.update()
                    self.update_ui()
                    QMessageBox.information(self, "Loaded", f"Gradient loaded from {fname}")
                    return
                # Fallback: parse index/color lines as before
                stops = []
                for line in lines:
                    if line.strip().startswith('index=') and 'color=' in line:
                        parts = line.strip().split()
                        idx = int(parts[0].split('=')[1])
                        packed = int(parts[1].split('=')[1])
                        r = (packed >> 16) & 0xFF
                        g = (packed >> 8) & 0xFF
                        b = packed & 0xFF
                        color = QColor(r, g, b)
                        pos = idx / 511.0
                        stops.append(ColorStop(pos, color))
                    elif len(line.strip().split()) == 4 and line.strip().split()[0].isdigit():
                        # JWildfire simple format: pos r g b
                        parts = line.strip().split()
                        pos = int(parts[0]) / 255.0
                        r, g, b = map(int, parts[1:4])
                        color = QColor(r, g, b)
                        stops.append(ColorStop(pos, color))
                if stops:
                    self.stops.clear()
                    self.stops.extend(sorted(stops, key=lambda s: s.position))
                    self.ramp.selected = None
                    self.ramp.update()
                    self.update_ui()
                    QMessageBox.information(self, "Loaded", f"Gradient loaded from {fname}")
                else:
                    QMessageBox.warning(self, "Error", "No stops found in .gradient file.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load: {e}")

    def export_css(self):
        stops_css = ', '.join(f"{stop.color.name()} {int(stop.position * 100)}%" for stop in self.stops)
        css = f"background: linear-gradient(90deg, {stops_css});"
        try:
            fname, _ = QFileDialog.getSaveFileName(self, "Export CSS", "gradient.css", "CSS Files (*.css)")
            if fname:
                with open(fname, 'w') as f:
                    f.write(css)
                QMessageBox.information(self, "Exported", f"CSS exported to {fname}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export: {e}")

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.strip().lstrip("#")
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif len(hex_color) == 8:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  # ignore alpha
        else:
            return (255, 255, 255)

    def export_jwildfire_gradient(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export JWildfire Gradient", "gradient.gradient", "JWildfire Gradient (*.gradient)")
        if fname:
            try:
                with open(fname, "w") as f:
                    f.write("JWFGradient\n")
                    sorted_stops = sorted(self.stops, key=lambda s: s.position)
                    for stop in sorted_stops:
                        pos = int(stop.position * 255)
                        # Use hex_to_rgb for robust color extraction
                        r, g, b = self.hex_to_rgb(stop.color.name())
                        line = f"{pos} {r} {g} {b}\n"
                        print(line.strip())  # Debug print
                        f.write(line)
                QMessageBox.information(self, "Exported", f"JWildfire gradient exported to {fname}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export: {e}")

    def get_color_at(self, t):
        # Interpolate color at position t in [0, 1] using current stops and interpolation
        stops = sorted(self.stops, key=lambda s: s.position)
        if t <= stops[0].position:
            return stops[0].color.name()
        if t >= stops[-1].position:
            return stops[-1].color.name()
        for i in range(1, len(stops)):
            left = stops[i-1]
            right = stops[i]
            if left.position <= t <= right.position:
                # Linear interpolation (can be replaced with other methods)
                f = (t - left.position) / (right.position - left.position)
                r = int(left.color.red() + f * (right.color.red() - left.color.red()))
                g = int(left.color.green() + f * (right.color.green() - left.color.green()))
                b = int(left.color.blue() + f * (right.color.blue() - left.color.blue()))
                return '#{:02X}{:02X}{:02X}'.format(r, g, b)
        return stops[-1].color.name()

    def export_full_gradient(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export Full .gradient", "full.gradient", "Full Gradient (*.gradient)")
        if fname:
            try:
                with open(fname, "w") as f:
                    # Write editor metadata as comments
                    f.write("# editor_version=1.0\n")
                    f.write("# editable_stops:\n")
                    for stop in self.stops:
                        f.write(f"# pos={stop.position:.6f} color={stop.color.name()}\n")
                    f.write("\ngradient:\n")
                    f.write(' title="CustomGradient" smooth=no\n')
                    for i in range(512):
                        t = i / 511.0
                        hex_color = self.get_color_at(t)
                        r, g, b = self.hex_to_rgb(hex_color)
                        packed = (r << 16) | (g << 8) | b
                        f.write(f" index={i} color={packed}\n")
                QMessageBox.information(self, "Exported", f"Full .gradient exported to {fname}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export: {e}")

    def export_png(self):
        from PyQt5.QtWidgets import QInputDialog
        width, ok1 = QInputDialog.getInt(self, "PNG Width", "Enter PNG width:", 1200, 100, 8000)
        if not ok1:
            return
        height, ok2 = QInputDialog.getInt(self, "PNG Height", "Enter PNG height:", 200, 50, 4000)
        if not ok2:
            return
        fname, _ = QFileDialog.getSaveFileName(self, "Export PNG", "gradient.png", "PNG Files (*.png)")
        if not fname:
            return
        # Render the gradient ramp to a QImage
        from PyQt5.QtGui import QImage
        img = QImage(width, height, QImage.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, width, 0)
        for stop in self.stops:
            grad.setColorAt(stop.position, stop.color)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, width, height)
        painter.end()
        img.save(fname)
        QMessageBox.information(self, "Exported", f"Gradient PNG exported to {fname}")

class GlassStyles:
    @staticmethod
    def main_window():
        return """
            QMainWindow {
                background: transparent;
            }
        """
    @staticmethod
    def main_widget():
        return """
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.18),
                stop:0.3 rgba(255, 255, 255, 0.12),
                stop:0.7 rgba(255, 255, 255, 0.10),
                stop:1 rgba(255, 255, 255, 0.08));
            border-radius: 20px;
            border: 1.5px solid rgba(255,255,255,0.10);
        """
    @staticmethod
    def controls_frame():
        return """
            QFrame {
                background: rgba(255, 255, 255, 0.12);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.13);
            }
        """
    @staticmethod
    def glass_button():
        return """
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.13),
                stop:1 rgba(255, 255, 255, 0.08));
        """

# --- Replace HSVColorWheel with improved version ---
class HSVColorWheel(QWidget):
    """A modern HSV color wheel with SV triangle and screen color picker."""
    colorChanged = pyqtSignal(QColor)
    def __init__(self, color=QColor(255, 0, 0), parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self._color = color
        self._hue = color.hueF() if color.isValid() else 0
        self._sat = color.saturationF() if color.isValid() else 1
        self._val = color.valueF() if color.isValid() else 1
        self._drag_mode = None  # 'hue' or 'sv'
        self._triangle_points = None
        self._picker_btn = QPushButton('color options', self)
        self._picker_btn.setGeometry(10, self.height()-40, 160, 30)
        self._picker_btn.clicked.connect(self.pick_screen_color)
        self._picker_btn.raise_()
        self._picker_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._picker_btn.setStyleSheet("color: #f0f0f0; background: #222; border-radius: 8px; font-family: 'Segoe UI', Arial, sans-serif;")
    def resizeEvent(self, event):
        self._picker_btn.setGeometry(10, self.height()-40, 160, 30)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = min(self.width(), self.height()-50) // 2 - 8
        center = QPointF(self.width()/2, (self.height()-50)/2+10)
        # Draw hue ring
        for angle in range(0, 360, 1):
            color = QColor.fromHsv(angle, 255, 255)
            painter.setPen(QPen(color, 10))
            painter.drawArc(int(center.x()-r), int(center.y()-r), 2*r, 2*r, angle*16, 16)
        # SV triangle points (top: white, bottom left: black, bottom right: pure hue)
        tri_r = r-18
        p_white = QPointF(center.x(), center.y() - tri_r)
        p_black = QPointF(center.x() - tri_r * math.sin(math.radians(60)), center.y() + tri_r * math.cos(math.radians(60)))
        p_hue = QPointF(center.x() + tri_r * math.sin(math.radians(60)), center.y() + tri_r * math.cos(math.radians(60)))
        self._triangle_points = [p_white, p_black, p_hue]
        # Draw triangle with correct color interpolation
        steps = 80
        for i in range(steps):
            for j in range(steps-i):
                u = i / steps
                v = j / steps
                w = 1 - u - v
                if w < 0: continue
                x = u*p_white.x() + v*p_black.x() + w*p_hue.x()
                y = u*p_white.y() + v*p_black.y() + w*p_hue.y()
                # Color at this barycentric
                # S = w (hue), V = u + w
                s = w
                vval = u + w
                color = QColor.fromHsvF(self._hue, s, vval)
                painter.setPen(color)
                painter.drawPoint(int(x), int(y))
        # Draw triangle border
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(p_white, p_black, p_hue)
        # Draw selector for hue
        hue_angle = int(self._hue * 360)
        sel_r = r - 5
        angle_rad = math.radians(hue_angle)
        sel_x = center.x() + sel_r * math.cos(angle_rad)
        sel_y = center.y() - sel_r * math.sin(angle_rad)
        painter.setPen(QPen(Qt.white, 3))
        painter.setBrush(self._color)
        painter.drawEllipse(QPointF(sel_x, sel_y), 9, 9)
        # Draw selector for SV
        sv_x, sv_y = self._sv_to_pos()
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(Qt.white)
        painter.drawEllipse(QPointF(sv_x, sv_y), 7, 7)
    def mousePressEvent(self, event):
        if self._on_hue_ring(event.pos()):
            self._drag_mode = 'hue'
            self._set_hue_from_pos(event.pos())
        elif self._on_sv_triangle(event.pos()):
            self._drag_mode = 'sv'
            self._set_sv_from_pos(event.pos())
    def mouseMoveEvent(self, event):
        if self._drag_mode == 'hue':
            self._set_hue_from_pos(event.pos())
        elif self._drag_mode == 'sv':
            self._set_sv_from_pos(event.pos())
    def mouseReleaseEvent(self, event):
        self._drag_mode = None
    def _on_hue_ring(self, pos):
        center = QPointF(self.width()/2, (self.height()-50)/2+10)
        r = min(self.width(), self.height()-50) // 2 - 8
        dist = math.hypot(pos.x()-center.x(), pos.y()-center.y())
        return r-12 < dist < r+12
    def _on_sv_triangle(self, pos):
        if not self._triangle_points:
            return False
        p_white, p_black, p_hue = self._triangle_points
        # Barycentric coordinates
        def sign(p1, p2, p3):
            return (p1.x() - p3.x()) * (p2.y() - p3.y()) - (p2.x() - p3.x()) * (p1.y() - p3.y())
        b1 = sign(pos, p_white, p_black) < 0.0
        b2 = sign(pos, p_black, p_hue) < 0.0
        b3 = sign(pos, p_hue, p_white) < 0.0
        return ((b1 == b2) and (b2 == b3))
    def _set_hue_from_pos(self, pos):
        center = QPointF(self.width()/2, (self.height()-50)/2+10)
        dx = pos.x() - center.x()
        dy = center.y() - pos.y()
        angle = math.atan2(dy, dx)
        hue = (math.degrees(angle) % 360) / 360.0
        self._hue = hue
        self._color = QColor.fromHsvF(self._hue, self._sat, self._val)
        self.colorChanged.emit(self._color)
        self.update()
    def _set_sv_from_pos(self, pos):
        p_white, p_black, p_hue = self._triangle_points
        # Barycentric coordinates
        def barycentric(p, a, b, c):
            v0 = b - a
            v1 = c - a
            v2 = p - a
            d00 = QPointF.dotProduct(v0, v0)
            d01 = QPointF.dotProduct(v0, v1)
            d11 = QPointF.dotProduct(v1, v1)
            d20 = QPointF.dotProduct(v2, v0)
            d21 = QPointF.dotProduct(v2, v1)
            denom = d00 * d11 - d01 * d01
            v = (d11 * d20 - d01 * d21) / denom
            w = (d00 * d21 - d01 * d20) / denom
            u = 1.0 - v - w
            return u, v, w
        u, v, w = barycentric(pos, p_white, p_black, p_hue)
        # Clamp barycentric
        u = max(0, min(1, u))
        v = max(0, min(1, v))
        w = max(0, min(1, w))
        s = w
        vval = u + w
        self._sat = s
        self._val = vval
        self._color = QColor.fromHsvF(self._hue, self._sat, self._val)
        self.colorChanged.emit(self._color)
        self.update()
    def _sv_to_pos(self):
        p_white, p_black, p_hue = self._triangle_points
        s = self._sat
        vval = self._val
        # Inverse mapping: for given s,v, find barycentric (u,v,w)
        # S = w, V = u + w, so u = V - S, v = 1 - u - w
        w = s
        u = max(0, min(1, vval - s))
        v = 1 - u - w
        x = u*p_white.x() + v*p_black.x() + w*p_hue.x()
        y = u*p_white.y() + v*p_black.y() + w*p_hue.y()
        return x, y
    def setColor(self, color):
        self._color = color
        self._hue = color.hueF() if color.isValid() else 0
        self._sat = color.saturationF() if color.isValid() else 1
        self._val = color.valueF() if color.isValid() else 1
        self.update()
    def color(self):
        return self._color
    def pick_screen_color(self):
        dlg = QColorDialog(self._color, self)
        dlg.setOption(QColorDialog.DontUseNativeDialog)
        dark_palette = dlg.palette()
        dark_palette.setColor(QPalette.Window, QColor(34, 34, 40))
        dark_palette.setColor(QPalette.Base, QColor(34, 34, 40))
        dark_palette.setColor(QPalette.Text, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.WindowText, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.Highlight, QColor(100, 150, 255))
        dark_palette.setColor(QPalette.HighlightedText, QColor(34, 34, 40))
        dlg.setPalette(dark_palette)
        dlg.setStyleSheet("QWidget { color: #f0f0f0; background: #222228; font-family: 'Segoe UI', Arial, sans-serif; }")
        if dlg.exec_():
            color = dlg.selectedColor()
            if color.isValid():
                self.setColor(color)
                self.colorChanged.emit(color)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GradientEditorWindow()
    window.show()
    sys.exit(app.exec_())
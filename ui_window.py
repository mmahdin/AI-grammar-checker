"""
UI module for displaying grammar correction results using PySide6.
"""
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QTextEdit, QLabel, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor
import sys
from typing import Optional



class ResultSignal(QObject):
    """Signal emitter for thread-safe UI updates."""
    show_result = Signal(dict)


class GrammarResultWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grammar Check Results")
        self.setMinimumSize(700, 500)
        self.setup_ui()

    def closeEvent(self, event):
        """Keep the app running when the window is closed; just hide it."""
        event.ignore()
        self.hide()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Grammar Correction Results")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Corrected text section
        corrected_label = QLabel("✓ Corrected Text:")
        corrected_font = QFont()
        corrected_font.setPointSize(11)
        corrected_font.setBold(True)
        corrected_label.setFont(corrected_font)
        layout.addWidget(corrected_label)
        
        self.corrected_text = QTextEdit()
        self.corrected_text.setReadOnly(True)
        self.corrected_text.setMaximumHeight(100)
        self.corrected_text.setStyleSheet("""
            QTextEdit {
                background-color: #808080;
                border: 2px solid #4caf50;
                border-radius: 5px;
                padding: 10px;
                font-size: 12pt;
            }
        """)
        layout.addWidget(self.corrected_text)
        
        # Errors section
        errors_label = QLabel("📝 Error Analysis:")
        errors_label.setFont(corrected_font)
        layout.addWidget(errors_label)
        
        # Scroll area for errors
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        self.errors_widget = QWidget()
        self.errors_layout = QVBoxLayout(self.errors_widget)
        self.errors_layout.setSpacing(10)
        scroll.setWidget(self.errors_widget)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMaximumWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def display_result(self, result: dict):
        """Display grammar check result."""
        # Show corrected text
        corrected = result.get('corrected_text', 'No correction available')
        self.corrected_text.setText(corrected)

        # Clear previous errors (widgets + spacers)
        while self.errors_layout.count():
            item = self.errors_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Display errors
        errors = result.get('error_analysis', [])

        if not errors:
            no_errors = QLabel("✓ No errors found! Your English is perfect.")
            no_errors.setStyleSheet("""
                QLabel {
                    color: #4caf50;
                    font-size: 11pt;
                    padding: 20px;
                }
            """)
            self.errors_layout.addWidget(no_errors)
        else:
            for idx, error in enumerate(errors, 1):
                error_widget = self._create_error_widget(idx, error)
                self.errors_layout.addWidget(error_widget)

        # Add a stretch only once at the end
        self.errors_layout.addStretch()

        self.show()
        self.activateWindow()
        self.raise_()

    
    def _create_error_widget(self, idx: int, error: dict) -> QWidget:
        """Create a widget for displaying a single error."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #1b1b1b;
                border-left: 4px solid #ff9800;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # Error number
        num_label = QLabel(f"Error #{idx}")
        num_font = QFont()
        num_font.setBold(True)
        num_font.setPointSize(12)
        num_label.setFont(num_font)
        layout.addWidget(num_label)
        
        # Original text
        original = QLabel(f"❌ Original: {error.get('original', 'N/A')}")
        original.setWordWrap(True)
        original.setStyleSheet("color: #d32f2f; font-size: 12pt;")
        layout.addWidget(original)
        
        # Corrected text
        corrected = QLabel(f"✓ Corrected: {error.get('corrected', 'N/A')}")
        corrected.setWordWrap(True)
        corrected.setStyleSheet("color: #388e3c; font-size: 12pt;")
        layout.addWidget(corrected)
        
        # Explanation
        explanation = QLabel(f"💡 {error.get('explanation', 'N/A')}")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #ffffff; font-size: 11pt; margin-top: 5px;")
        layout.addWidget(explanation)
        
        return widget


class UIManager:
    def __init__(self):
        """Initialize UI manager."""
        self.app: Optional[QApplication] = None
        self.window: Optional[GrammarResultWindow] = None
        self.signal = ResultSignal()
        
    def initialize(self):
        """Initialize QApplication."""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        # Keep background services alive even if the window closes.
        self.app.setQuitOnLastWindowClosed(False)
        
        self.window = GrammarResultWindow()
        self.signal.show_result.connect(self._show_result)
    
    def show_result(self, result: dict):
        """Thread-safe method to show result."""
        self.signal.show_result.emit(result)
    
    def _show_result(self, result: dict):
        """Internal method to display result (runs in UI thread)."""
        if self.window:
            self.window.display_result(result)

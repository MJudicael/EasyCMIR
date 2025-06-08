from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class PIDDialog(QDialog):
    """Dialog pour les outil PID."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PID")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fonction PID à implémenter"))
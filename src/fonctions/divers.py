from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class DiversDialog(QDialog):
    """Dialog pour les outils divers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Outils Divers")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fonction outils divers à implémenter"))
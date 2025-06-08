from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class IdentificationDialog(QDialog):
    """Dialog pour l'identification des substances."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identification")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fonction d'identification à implémenter"))
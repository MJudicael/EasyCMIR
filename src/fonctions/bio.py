from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class BioDialog(QDialog):
    """Dialog pour les risques biologiques."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Risques Biologiques")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fonction risques biologiques à implémenter"))
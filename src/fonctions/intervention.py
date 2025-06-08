from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class InterventionDialog(QDialog):
    """Dialog pour les procédures d'intervention."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Intervention")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fonction intervention à implémenter"))
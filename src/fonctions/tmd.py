from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel

class TMDDialog(QDialog):
    """Dialog pour le Transport de Matières Dangereuses."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transport MD")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fonction TMD à implémenter"))
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Informations sur l'application
        info_text = """
        <h2>EasyCMIR 1.3</h2>
        <p>Application de calculs radiologiques</p>
        <p>Développé par Judicaël Mougin - SDIS 71</p>
        <p>Version 1.3</p>
        <p>© 2024 - Tous droits réservés</p>
        """
        
        info_label = QLabel(info_text)
        info_label.setOpenExternalLinks(True)
        layout.addWidget(info_label)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
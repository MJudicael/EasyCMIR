from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
import os

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos")
        self.setFixedSize(300, 250)
        
        layout = QVBoxLayout(self)
        
        # Informations sur l'application
        info_text = """
        <h2>EasyCMIR</h2>
        <p>Version 1.5</p>
        <p>Développé par Judicaël Mougin - SDIS 71</p>
        <p>© 2024 - Logiciel sous licence.</p>
        <p>Gratuit à usage des SDIS</p>
        <p>Usage commercial & modification interdit</p>
        
        """
        
        info_label = QLabel(info_text)
        info_label.setOpenExternalLinks(True)
        layout.addWidget(info_label)
        
        # Bouton pour afficher la licence
        license_button = QPushButton("Voir la licence")
        license_button.clicked.connect(self.show_license)
        layout.addWidget(license_button)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def show_license(self):
        """Affiche le contenu du fichier licence.txt"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(current_dir))
            license_path = os.path.join(root_dir, "data", "license.txt")
            
            with open(license_path, 'r', encoding='utf-8') as f:
                license_text = f.read()
            
            # Création d'une boîte de dialogue pour afficher la licence
            QMessageBox.information(self, "Licence EasyCMIR", license_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", 
                f"Impossible de charger le fichier de licence: {e}")
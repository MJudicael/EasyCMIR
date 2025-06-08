from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox, 
    QScrollArea, QWidget
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from ..utils.icon_manager import IconManager

class CodeDangerDialog(QDialog):
    """Dialog pour l'identification des codes danger."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Code Danger")
        self.setFixedSize(400, 500)
        
        # Initialisation du gestionnaire d'icônes
        self.icon_manager = IconManager()
        
        # Chargement des données
        self.danger_data = self.load_danger_data()
        
        self.main_layout = QVBoxLayout(self)
        
        # Création des widgets
        self.create_input_widgets()
        self.create_result_widgets()
        
        # Ajout d'un QScrollArea pour les pictogrammes
        self.picto_scroll = QScrollArea()
        self.picto_widget = QWidget()
        self.picto_layout = QGridLayout(self.picto_widget)
        self.picto_scroll.setWidget(self.picto_widget)
        self.picto_scroll.setWidgetResizable(True)
        self.main_layout.addWidget(self.picto_scroll)

    def load_danger_data(self):
        """Charge les données depuis le fichier codes_danger.txt"""
        data = {
            'CODES_DANGER': {},
            'PROTECTION_RECOMMENDATIONS': {}
        }
        
        # Chemin vers le fichier de données
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_path, "data", "codes_danger.txt")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                current_section = None
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        if line.startswith('#'):
                            current_section = line[1:]
                        continue
                    
                    key, value = line.split(':', 1)
                    if current_section == 'CODES_DANGER':
                        data['CODES_DANGER'][key] = value.strip()
                    elif current_section == 'PROTECTION_RECOMMENDATIONS':
                        data['PROTECTION_RECOMMENDATIONS'][key] = value.strip().split(':')
        
        except FileNotFoundError:
            print(f"Erreur: Fichier non trouvé: {file_path}")
            raise
        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
            raise
            
        return data

    def create_input_widgets(self):
        """Crée les widgets de saisie."""
        input_group = QGroupBox("Recherche de code danger")
        input_layout = QGridLayout()
        
        # Zone de saisie
        self.code_label = QLabel("Code :")
        self.code_input = QComboBox()
        self.code_input.setEditable(True)
        self.code_input.addItems(sorted(self.danger_data['CODES_DANGER'].keys()))
        
        input_layout.addWidget(self.code_label, 0, 0)
        input_layout.addWidget(self.code_input, 0, 1)
        
        # Bouton de recherche
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self.identify_code)
        input_layout.addWidget(search_button, 1, 0, 1, 2)
        
        input_group.setLayout(input_layout)
        self.main_layout.addWidget(input_group)

    def create_result_widgets(self):
        """Crée les widgets d'affichage des résultats."""
        result_group = QGroupBox("Résultats")
        result_layout = QVBoxLayout()
        
        self.result_description = QLabel()
        self.result_danger = QLabel()
        self.result_danger.setWordWrap(True)
        self.result_action = QLabel()
        self.result_action.setWordWrap(True)
        
        result_layout.addWidget(self.result_description)
        result_layout.addWidget(self.result_danger)
        result_layout.addWidget(self.result_action)
        
        result_group.setLayout(result_layout)
        self.main_layout.addWidget(result_group)

    def identify_code(self):
        """Identifie le code danger saisi."""
        try:
            code = self.code_input.currentText().upper()
            
            if code in self.danger_data['CODES_DANGER']:
                description = "Code danger identifié:"
                danger = self.danger_data['CODES_DANGER'][code]
                action = self.get_protection_recommendations(code)
            else:
                description = "Code non trouvé"
                danger = "Code danger non répertorié"
                action = "Aucune recommandation disponible"
            
            self.result_description.setText(description)
            self.result_danger.setText(danger)
            self.result_action.setText(action)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def get_protection_recommendations(self, code):
        """Récupère les recommandations de protection pour un code."""
        if code in self.danger_data['PROTECTION_RECOMMENDATIONS']:
            return "\n".join("• " + rec for rec in self.danger_data['PROTECTION_RECOMMENDATIONS'][code])
        return "Pas de recommandations spécifiques"
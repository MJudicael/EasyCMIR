from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt

class PPublicDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul Périmètre Public")
        self.main_layout = QVBoxLayout(self)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Création du formulaire principal
        form_layout = QFormLayout()
        
        # Ajout des champs de saisie
        self.ded_input = QLineEdit()
        form_layout.addRow("DED (µSv/h):", self.ded_input)
        
        # Bouton de calcul
        calc_button = QPushButton("Calculer")
        calc_button.clicked.connect(self.calculate)
        
        # Résultat
        self.result_label = QLabel()
        
        # Ajout des widgets au layout principal
        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(calc_button)
        self.main_layout.addWidget(self.result_label)
        
        self.setLayout(self.main_layout)
    
    def calculate(self):
        """Effectue le calcul du périmètre public"""
        try:
            ded = float(self.ded_input.text())
            # Formule de calcul : Distance = √(DED/0.5)
            distance = (ded/0.5)**0.5
            self.result_label.setText(f"Distance périmètre public : {distance:.2f} m")
        except ValueError:
            self.result_label.setText("Erreur : Veuillez entrer un nombre valide")
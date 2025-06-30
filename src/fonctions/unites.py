from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QLabel, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt

class UnitesRadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversion Unités")
        self.main_layout = QVBoxLayout(self)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Groupe pour la conversion
        convert_group = QGroupBox("Conversion")
        convert_layout = QFormLayout()
        
        # Widgets pour la valeur d'entrée
        self.input_value = QLineEdit()
        self.input_unit = QComboBox()
        self.input_unit.addItems(["µSv/h", "mSv/h", "Sv/h", "mR/h", "R/h"])
        
        # Widgets pour la valeur de sortie
        self.output_unit = QComboBox()
        self.output_unit.addItems(["µSv/h", "mSv/h", "Sv/h", "mR/h", "R/h"])
        self.result_label = QLabel("Résultat: ")
        
        # Bouton de conversion
        convert_button = QPushButton("Convertir")
        convert_button.clicked.connect(self.convert)
        
        # Ajout des widgets au layout
        convert_layout.addRow("Valeur:", self.input_value)
        convert_layout.addRow("De:", self.input_unit)
        convert_layout.addRow("Vers:", self.output_unit)
        convert_layout.addRow("", convert_button)
        convert_layout.addRow(self.result_label)
        
        # Finalisation du layout
        convert_group.setLayout(convert_layout)
        self.main_layout.addWidget(convert_group)
    
    def convert(self):
        """Effectue la conversion entre les unités"""
        try:
            value = float(self.input_value.text())
            from_unit = self.input_unit.currentText()
            to_unit = self.output_unit.currentText()
            
            # Conversion en µSv/h comme unité intermédiaire
            if from_unit == "mSv/h":
                value *= 1000
            elif from_unit == "Sv/h":
                value *= 1000000
            elif from_unit == "mR/h":
                value *= 10
            elif from_unit == "R/h":
                value *= 10000
            
            # Conversion vers l'unité cible
            if to_unit == "mSv/h":
                value /= 1000
            elif to_unit == "Sv/h":
                value /= 1000000
            elif to_unit == "mR/h":
                value /= 10
            elif to_unit == "R/h":
                value /= 10000
            
            self.result_label.setText(f"Résultat: {value:.6f} {to_unit}")
        except ValueError:
            self.result_label.setText("Erreur: Veuillez entrer un nombre valide")
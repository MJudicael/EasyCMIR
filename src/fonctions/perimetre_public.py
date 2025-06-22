from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt

class PerimetrePublicDialog(QDialog):
    """Dialogue pour le calcul du périmètre public."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul Périmètre Public")
        self.setMinimumWidth(400)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Création des widgets
        self.create_input_widgets()
        self.create_result_widgets()
        self.create_buttons()
        
    def create_input_widgets(self):
        """Crée les widgets de saisie."""
        input_group = QGroupBox("Paramètres")
        layout = QVBoxLayout()
        
        # Débit de dose
        debit_layout = QHBoxLayout()
        self.debit_input = QDoubleSpinBox()
        self.debit_input.setRange(0, 1000000)
        self.debit_input.setDecimals(3)
        self.debit_input.setSuffix(" µSv/h")
        debit_layout.addWidget(QLabel("Débit de dose :"))
        debit_layout.addWidget(self.debit_input)
        layout.addLayout(debit_layout)
        
        input_group.setLayout(layout)
        self.main_layout.addWidget(input_group)
        
    def create_result_widgets(self):
        """Crée les widgets d'affichage des résultats."""
        result_group = QGroupBox("Résultats")
        layout = QVBoxLayout()
        
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
        
        result_group.setLayout(layout)
        self.main_layout.addWidget(result_group)
        
    def create_buttons(self):
        """Crée les boutons de contrôle."""
        buttons_layout = QHBoxLayout()
        
        calculate_btn = QPushButton("Calculer")
        calculate_btn.clicked.connect(self.calculate)
        buttons_layout.addWidget(calculate_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        self.main_layout.addLayout(buttons_layout)
        
    def calculate(self):
        """Effectue le calcul du périmètre public."""
        try:
            debit = self.debit_input.value()
            
            # Calcul selon la formule : périmètre = débit/2.5
            perimetre = debit / 2.5
            
            # Mise à jour du résultat
            self.result_label.setText(
                f"Pour un débit de dose de {debit:.3f} µSv/h,\n"
                f"le périmètre public est de : {perimetre:.1f} mètres"
            )
            
        except Exception as e:
            self.result_label.setText(f"Erreur de calcul : {str(e)}")
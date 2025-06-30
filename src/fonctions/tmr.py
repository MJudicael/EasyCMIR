from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from ..utils.widgets import ClearingDoubleSpinBox
from ..utils.database import save_to_history

class TMRDialog(QDialog):
    """Dialog pour le calcul du TMR."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul TMR")
        self.setFixedSize(300, 200)

        self.layout = QVBoxLayout(self)

        # Section DED contact
        contact_ded_form = QFormLayout()
        self.ded_contact_input = ClearingDoubleSpinBox()
        self.ded_contact_input.setDecimals(3)
        self.ded_contact_input.setRange(0.0, 1e6)
        self.ded_contact_input.setValue(0.0)
        self.ded_contact_input.setToolTip("Débit de dose équivalent au contact en µSv/h")
        contact_ded_form.addRow("Ded au contact (µSv/h) :", self.ded_contact_input)
        self.layout.addLayout(contact_ded_form)

        # Section DED 1m
        ded1m_tmr_form = QFormLayout()
        self.ded_1m_tmr_input = ClearingDoubleSpinBox()
        self.ded_1m_tmr_input.setDecimals(3)
        self.ded_1m_tmr_input.setRange(0.0, 1e6)
        self.ded_1m_tmr_input.setValue(0.0)
        self.ded_1m_tmr_input.setToolTip("Débit de dose équivalent à 1 mètre en µSv/h")
        ded1m_tmr_form.addRow("Ded 1 mètre (µSv/h) :", self.ded_1m_tmr_input)
        self.layout.addLayout(ded1m_tmr_form)

        # Section étiquette TMR
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Etiquette TMR :"))
        self.tmr_label_display = QLabel(" ")  # Un seul espace suffit
        self.tmr_label_display.setObjectName("tmrLabel")
        self.tmr_label_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tmr_label_display.setFixedSize(40, 40)  # Taille carrée en pixels
        label_layout.addWidget(self.tmr_label_display)
        label_layout.addStretch()  # Ajoute un espace élastique à droite
        self.layout.addLayout(label_layout)

        # Section bouton et IT
        calculate_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Calculer")
        self.calculate_button.clicked.connect(self.calculate_tmr)
        calculate_layout.addWidget(self.calculate_button)

        it_layout = QHBoxLayout()
        it_layout.addWidget(QLabel("IT :"))
        self.it_value_label = QLabel("")
        self.it_value_label.setObjectName("resultLabel")
        it_layout.addWidget(self.it_value_label)
        calculate_layout.addLayout(it_layout)
        self.layout.addLayout(calculate_layout)

        self.layout.addStretch(1)

    def calculate_tmr(self):
        """Calcule la catégorie TMR et l'IT."""
        try:
            ded_contact = self.ded_contact_input.value()
            ded_1m = self.ded_1m_tmr_input.value()

            # Réinitialisation du label
            self.tmr_label_display.setText("       ")
            self.tmr_label_display.setStyleSheet(
                "font: bold 10pt 'Arial'; background-color: white; color: red; border: 1px solid gray;"
            )

            # Calcul de l'IT
            it = round(ded_1m / 10, 2)
            self.it_value_label.setText(str(it))

            # Détermination de la catégorie
            if ded_contact < 5 and ded_1m == 0:
                self._set_tmr_category("I", "#EAF5E4", "#00824B")
            elif 5 <= ded_contact <= 500 and 0 < ded_1m <= 10:
                self._set_tmr_category("II", "#FFF8E1", "#D37000")
            elif 500 < ded_contact <= 2000 and 10 < ded_1m <= 100:
                self._set_tmr_category("III", "#FFECB3", "#FC0909")
            elif 2000 < ded_contact <= 10000 :
                self._set_tmr_category("EX", "#FFEBEE", "#020202")
            else:
                self._set_tmr_category("N/A", "#e2e3e5", "#383d41")

            # Sauvegarde dans l'historique
            save_to_history([
                "TMR",
                f"Ded contact: {ded_contact} µSv/h",
                f"Ded 1m: {ded_1m} µSv/h",
                f"IT: {it}",
                f"Etiquette: {self.tmr_label_display.text()}"
            ])

        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _set_tmr_category(self, category, bg_color, text_color):
        """Définit la catégorie TMR avec le style approprié."""
        self.tmr_label_display.setText(category)
        self.tmr_label_display.setStyleSheet(
            f"font: bold 16pt 'Arial'; "  # Police plus grande
            f"background-color: {bg_color}; "
            f"color: {text_color}; "
            f"border: 2px solid {text_color}; "  # Bordure plus épaisse
            f"border-radius: 5px; "  # Coins légèrement arrondis
            f"padding: 2px; "  # Espace intérieur
            f"margin: 2px; "  # Espace extérieur
            f"min-width: 40px; "  # Largeur minimale
            f"max-width: 40px; "  # Largeur maximale
            f"min-height: 40px; "  # Hauteur minimale
            f"max-height: 40px; "  # Hauteur maximale
        )
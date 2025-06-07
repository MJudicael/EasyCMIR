from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QPushButton, 
    QComboBox, QVBoxLayout, QHBoxLayout, QFormLayout, QMessageBox, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt
from ..utils.widgets import ClearingDoubleSpinBox
from ..utils.database import save_to_history
from math import sqrt

class DistanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distance")
        self.setFixedSize(300, 100)
        
        layout = QGridLayout(self)
        
        # Création des widgets
        self.create_widgets()
        
    def create_widgets(self):
        # ... Code de création des widgets ...
        pass

class PerimetrePublicDialog(QDialog):
    """Dialog pour le calcul du périmètre public."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Périmètre public")
        self.setFixedSize(400, 300)  # Peut être trop grande/petite selon le contenu
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)  # Espacement entre les widgets

        # Titre explicatif
        title_label = QLabel("Calcul du périmètre de zone publique")
        title_label.setObjectName("titleLabel")  # Pour le style CSS
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        # Formulaire de saisie avec groupe
        input_group = QGroupBox("Paramètres")
        input_form = QFormLayout()
        input_form.setSpacing(10)
        input_form.setContentsMargins(5, 5, 5, 5)  # Marges intérieures
        input_form.setAlignment(Qt.AlignVCenter)  # Alignement vertical

        # Ajustement du QDoubleSpinBox
        self.ded1m_ppublic_input = ClearingDoubleSpinBox()
        self.ded1m_ppublic_input.setDecimals(3)
        self.ded1m_ppublic_input.setRange(0.0, 1e6)
        self.ded1m_ppublic_input.setValue(0.0)
        self.ded1m_ppublic_input.setToolTip("Débit de dose équivalent à 1 mètre en µSv/h")
        self.ded1m_ppublic_input.setSingleStep(0.1)
        # Supprimer le setStyleSheet du QDoubleSpinBox
        self.ded1m_ppublic_input.setMinimumHeight(30)
        input_form.addRow("DED 1 mètre (µSv/h) :", self.ded1m_ppublic_input)

        input_group.setLayout(input_form)
        input_group.setMinimumHeight(70)
        self.layout.addWidget(input_group)

        # Groupe de résultats
        result_group = QGroupBox("Résultat")
        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(5, 5, 5, 5)
        result_layout.setAlignment(Qt.AlignVCenter)

        # Label de résultat centré
        self.p_public_result_label = QLabel("En attente d'une valeur...")
        self.p_public_result_label.setObjectName("resultLabel")
        self.p_public_result_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.p_public_result_label)

        result_group.setLayout(result_layout)
        result_group.setMinimumHeight(70)
        self.layout.addWidget(result_group)

        # Info supplémentaire
        info_label = QLabel("Note: Calcul basé sur la limite publique de 2,5 µSv/h")
        info_label.setObjectName("infoLabel")
        info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(info_label)
        self.layout.addStretch(1)

        # Ne garder qu'une seule connexion pour éviter les doublons
        self.ded1m_ppublic_input.valueChanged.connect(self.calculate_p_public)

    def calculate_p_public(self):
        """Calcule le périmètre public basé sur le DED à 1m."""
        try:
            ded1m_value = self.ded1m_ppublic_input.value()
            if not self._validate_input(ded1m_value):
                return
                
            result = self._calculate_result(ded1m_value)
            self._update_display(result)
            self._save_to_history(ded1m_value, result)
            
        except Exception as e:
            self._handle_error(e)

    def _validate_input(self, ded1m_value):
        """Valide l'entrée de l'utilisateur."""
        if ded1m_value < 0:
            QMessageBox.warning(self, "Erreur Saisie", "Le DED 1 mètre ne peut pas être négatif.")
            self.p_public_result_label.setText("DED négatif")
            return False
        return True

    def _calculate_result(self, ded1m_value):
        """Calcule le résultat basé sur la valeur du DED."""
        if ded1m_value == 0:
            return 0.0
        else:
            return sqrt(ded1m_value / 2.5)  # 2.5 µSv/h est la limite publique

    def _update_display(self, result):
        """Met à jour l'affichage du résultat."""
        result = round(result, 2)
        self.p_public_result_label.setText(f"Périmètre public à : {result} m")

    def _save_to_history(self, ded1m_value, result):
        """Sauvegarde les données dans l'historique."""
        save_to_history([
            "Perimetre public",
            f"DED 1m: {ded1m_value} uSv/h",
            f"Perimetre: {result} m"
        ])

    def _handle_error(self, e):
        """Gère l'affichage des erreurs."""
        QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

# distance.py pour DistanceDialog
# p_public.py pour PerimetrePublicDialog
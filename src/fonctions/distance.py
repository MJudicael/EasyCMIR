from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QPushButton, 
    QComboBox, QMessageBox
)
import matplotlib.pyplot as plt
import numpy as np
from ..utils.widgets import ClearingDoubleSpinBox
from ..utils.database import save_to_history

class DistanceDialog(QDialog):
    """Dialog pour le calcul de distance."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distance")
        self.setFixedSize(500, 150)
        
        self.layout = QGridLayout(self)
        
        # Liste des unités disponibles
        unit_options = ["Sv/h", "mSv/h", "µSv/h", "nSv/h", "pSv/h", 
                       "R/h", "mR/h", "µR/h", "Rad/h", "mRad/h", 
                       "µRad/h", "Rem/h", "mRem/h"]

        # Labels des entrées
        self.layout.addWidget(QLabel("Débit de dose initial"), 0, 0)
        self.layout.addWidget(QLabel("Distance initiale (m)"), 0, 2)
        self.layout.addWidget(QLabel("Distance souhaitée (m)"), 0, 4)

        # Widget débit de dose
        self.ded1_input = ClearingDoubleSpinBox()
        self.ded1_input.setDecimals(2)
        self.ded1_input.setRange(0.0, 1e9)
        self.ded1_input.setValue(0.0)
        self.ded1_input.setToolTip("Débit de dose connu")
        self.layout.addWidget(self.ded1_input, 1, 0)

        # ComboBox des unités
        self.unit_choice_combo = QComboBox()
        self.unit_choice_combo.addItems(unit_options)
        self.unit_choice_combo.setCurrentText("mSv/h")
        self.unit_choice_combo.setToolTip("Unité du débit de dose connu")
        self.layout.addWidget(self.unit_choice_combo, 1, 1)

        # Distance initiale
        self.d1_input = ClearingDoubleSpinBox()
        self.d1_input.setDecimals(2)
        self.d1_input.setRange(0.0, 10000.0)
        self.d1_input.setValue(0.0)
        self.d1_input.setToolTip("Distance pour le débit de dose connu (m)")
        self.layout.addWidget(self.d1_input, 1, 2)

        # Distance souhaitée
        self.d2_input = ClearingDoubleSpinBox()
        self.d2_input.setDecimals(2)
        self.d2_input.setRange(0.0, 10000.0)
        self.d2_input.setValue(0.0)
        self.d2_input.setToolTip("Distance souhaitée (m)")
        self.layout.addWidget(self.d2_input, 1, 4)

        # Bouton de calcul
        self.calculate_button = QPushButton("Calculer")
        self.calculate_button.clicked.connect(self.calculate_distance)
        self.layout.addWidget(self.calculate_button, 2, 0)

        # Labels des résultats
        self.distance_result_label = QLabel("Débit de dose calculé")
        self.distance_result_label.setObjectName("resultLabel")
        self.layout.addWidget(self.distance_result_label, 2, 1, 1, 4)

        self.actual_distance_result_label = QLabel("")
        self.actual_distance_result_label.setObjectName("subResultLabel")
        self.layout.addWidget(self.actual_distance_result_label, 3, 0, 1, 5)

        # Ajout du bouton pour le graphique après le bouton calculer
        self.plot_button = QPushButton("Afficher le graphique")
        self.plot_button.setEnabled(False)  # Désactivé par défaut
        self.layout.addWidget(self.plot_button, 2, 4)
        self.plot_button.clicked.connect(self.show_plot)
        
    def calculate_distance(self):
        """Calcule le débit de dose à une distance donnée."""
        try:
            ded1 = self.ded1_input.value()
            d1 = self.d1_input.value()
            d2 = self.d2_input.value()
            chosen_unit = self.unit_choice_combo.currentText()

            # Vérifications des entrées
            if d2 == 0:
                QMessageBox.warning(self, "Erreur Saisie", 
                                  "La distance souhaitée (D2) ne peut pas être zéro.")
                self.actual_distance_result_label.setText("Distance D2 nulle")
                return
                
            if d1 == 0:
                QMessageBox.warning(self, "Erreur Saisie", 
                                  "La distance initiale (D1) ne peut pas être zéro.")
                self.actual_distance_result_label.setText("Distance D1 nulle")
                return
                
            if ded1 < 0:
                QMessageBox.warning(self, "Erreur Saisie", 
                                  "Le débit de dose ne peut pas être négatif.")
                self.actual_distance_result_label.setText("Débit de dose négatif")
                return

            # Calcul selon la loi inverse du carré de la distance
            result = round((ded1 * d1 ** 2) / (d2 ** 2), 2)
            self.actual_distance_result_label.setText(f"{result} {chosen_unit} à {d2} m")
            
            # Activation du bouton du graphique
            self.plot_button.setEnabled(True)
            # Stockage des valeurs pour le graphique
            self._last_calculation = (d1, d2, ded1, result)
            

            # Sauvegarde dans l'historique
            save_to_history([
                "Distance",
                f"Debit de dose connu: {ded1} {chosen_unit} à {d1} mètres",
                f"Debit de dose calcule: {result} {chosen_unit} à {d2} mètres"
            ])

        except ValueError:
            QMessageBox.critical(self, "Erreur Saisie", 
                               "Veuillez entrer des valeurs numériques valides.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

    def show_plot(self):
        """Affiche la fenêtre du graphique."""
        from .plot_window import PlotDialog
        if hasattr(self, '_last_calculation'):
            d1, d2, ded1, result = self._last_calculation
            unit = self.unit_choice_combo.currentText()
            dialog = PlotDialog(d1, d2, ded1, result, unit, self)
            dialog.exec()
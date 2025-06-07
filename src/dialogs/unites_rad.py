from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QWidget,
    QComboBox, QGridLayout, QGroupBox
)
from ..utils.widgets import ClearingDoubleSpinBox
from ..utils.database import save_to_history

class UnitesRadDialog(QDialog):
    # Constantes de classe pour les unités et facteurs de conversion
    DOSE_UNITS = ["Sv/h", "mSv/h", "µSv/h", "nSv/h", "pSv/h", 
                  "R/h", "mR/h", "µR/h", "Rad/h", "mRad/h", 
                  "µRad/h", "Rem/h", "mRem/h"]
    
    ACTIVITY_UNITS = ["Bq", "kBq", "MBq", "GBq", "TBq", 
                      "Ci", "mCi", "µCi", "nCi"]
    
    DOSE_CONVERSIONS = {
        "Sv/h": (1000, 1/1000), 
        "mSv/h": (1, 1),
        "µSv/h": (0.001, 1000),
        "nSv/h": (0.000001, 1000000),
        "pSv/h": (0.000000001, 1000000000),
        "R/h": (8.77, 1/8.77),
        "mR/h": (0.00877, 1/0.00877),
        "µR/h": (0.00000877, 1/0.00000877),
        "Rad/h": (10, 1/10),
        "mRad/h": (0.01, 1/0.01),
        "µRad/h": (0.00001, 1/0.00001),
        "Rem/h": (10, 1/10),
        "mRem/h": (0.01, 1/0.01)
    }
    
    ACTIVITY_CONVERSIONS = {
        "Bq": (1, 1),
        "kBq": (1e3, 1e-3),
        "MBq": (1e6, 1e-6),
        "GBq": (1e9, 1e-9),
        "TBq": (1e12, 1e-12),
        "Ci": (3.7e10, 1/3.7e10),
        "mCi": (3.7e7, 1/3.7e7),
        "µCi": (3.7e4, 1/3.7e4),
        "nCi": (3.7e1, 1/3.7e1)
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        self._initial_calculations()

    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Unités RAD")
        self.setFixedSize(500, 250)
        
        self.layout = QVBoxLayout(self)
        
        # Configuration des groupes
        self._setup_dose_rate_group()
        
        # Ajoute un espacement vertical entre les groupes
        spacer = QWidget()
        spacer.setFixedHeight(20)  # 20 pixels d'espacement
        self.layout.addWidget(spacer)
        
        self._setup_activity_group()
        self.layout.addStretch(1)

    def _setup_spinbox(self, decimals=5, max_value=1e9):
        """Crée et configure un QDoubleSpinBox."""
        spinbox = ClearingDoubleSpinBox()
        spinbox.setDecimals(decimals)
        spinbox.setRange(0.0, max_value)
        spinbox.setValue(0.0)
        return spinbox

    def _setup_conversion_widget(self, layout, label_text, units, current_unit, max_value=1e9):
        """Configure un widget de conversion générique."""
        layout.addWidget(QLabel(label_text), 0, 0)
        
        value_input = self._setup_spinbox(max_value=max_value)
        layout.addWidget(value_input, 0, 1)
        
        unit_combo = QComboBox()
        unit_combo.addItems(units)
        unit_combo.setCurrentText(current_unit)
        layout.addWidget(unit_combo, 0, 2)
        
        return value_input, unit_combo

    def _convert_value(self, value, from_unit, to_unit, conversions):
        """Convertit une valeur entre deux unités."""
        if value < 0:
            raise ValueError("Valeur négative")
            
        to_base, from_base = conversions[from_unit][0], conversions[to_unit][1]
        return value * to_base * from_base

    def calculate_conversion(self, value_input, unit_from_combo, unit_to_combo, 
                       result_label, conversions, history_type):
        """Calcule et affiche une conversion."""
        try:
            value = value_input.value()
            from_unit = unit_from_combo.currentText()
            to_unit = unit_to_combo.currentText()

            if value < 0:
                result_label.setText("Valeur négative")
                return

            result = self._convert_value(value, from_unit, to_unit, conversions)
            
            # Formatage du résultat sans notation scientifique
            if result >= 1000000:
                formatted_result = f"{result:,.2f}".replace(",", " ")  # Utilise espace comme séparateur
            else:
                formatted_result = f"{result:.3f}".rstrip('0').rstrip('.')  # Supprime les zéros inutiles
            
            result_label.setText(f"Résultat : {formatted_result} {to_unit}")

            save_to_history([
                history_type,
                f"De: {value} {from_unit}",
                f"Vers: {formatted_result} {to_unit}"
            ])

        except Exception as e:
            result_label.setText(f"Erreur: {e}")

    def calculate_ded_conversion(self):
        """Calcule la conversion de débit de dose."""
        self.calculate_conversion(
            self.ded_value_origin_input,
            self.ded_unit_origin_combo,
            self.ded_unit_target_combo,
            self.ded_conversion_result_label,
            self.DOSE_CONVERSIONS,
            "Conversion Debit de Dose"
        )

    def calculate_activity_conversion(self):
        """Calcule la conversion d'activité."""
        self.calculate_conversion(
            self.activity_value_origin_input,
            self.activity_unit_origin_combo,
            self.activity_unit_target_combo,
            self.activity_conversion_result_label,
            self.ACTIVITY_CONVERSIONS,
            "Conversion Activite"
        )

    def _setup_dose_rate_group(self):
        """Configure le groupe de widgets pour le débit de dose."""
        group = QGroupBox("Conversion Débit de Dose")
        layout = QGridLayout()
        
        # Widget de valeur d'entrée et unité source
        self.ded_value_origin_input, self.ded_unit_origin_combo = self._setup_conversion_widget(
            layout, "De :", self.DOSE_UNITS, "mSv/h"
        )
        
        # Widget d'unité cible
        layout.addWidget(QLabel("Vers :"), 0, 3)
        self.ded_unit_target_combo = QComboBox()
        self.ded_unit_target_combo.addItems(self.DOSE_UNITS)
        self.ded_unit_target_combo.setCurrentText("µSv/h")
        layout.addWidget(self.ded_unit_target_combo, 0, 4)
        
        # Label de résultat
        self.ded_conversion_result_label = QLabel("Résultat :")
        self.ded_conversion_result_label.setObjectName("resultLabel")
        layout.addWidget(self.ded_conversion_result_label, 1, 0, 1, 5)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def _setup_activity_group(self):
        """Configure le groupe de widgets pour l'activité."""
        group = QGroupBox("Conversion Activité")
        layout = QGridLayout()
        
        # Widget de valeur d'entrée et unité source
        self.activity_value_origin_input, self.activity_unit_origin_combo = self._setup_conversion_widget(
            layout, "De :", self.ACTIVITY_UNITS, "GBq", max_value=1e12
        )
        
        # Widget d'unité cible
        layout.addWidget(QLabel("Vers :"), 0, 3)
        self.activity_unit_target_combo = QComboBox()
        self.activity_unit_target_combo.addItems(self.ACTIVITY_UNITS)
        self.activity_unit_target_combo.setCurrentText("Bq")
        layout.addWidget(self.activity_unit_target_combo, 0, 4)
        
        # Label de résultat
        self.activity_conversion_result_label = QLabel("Résultat :")
        self.activity_conversion_result_label.setObjectName("resultLabel")
        layout.addWidget(self.activity_conversion_result_label, 1, 0, 1, 5)
        
        group.setLayout(layout)
        self.layout.addWidget(group)

    def _connect_signals(self):
        """Connecte les signaux pour les calculs en temps réel."""
        # Signaux débit de dose
        self.ded_value_origin_input.valueChanged.connect(self.calculate_ded_conversion)
        self.ded_unit_origin_combo.currentIndexChanged.connect(self.calculate_ded_conversion)
        self.ded_unit_target_combo.currentIndexChanged.connect(self.calculate_ded_conversion)
        
        # Signaux activité
        self.activity_value_origin_input.valueChanged.connect(self.calculate_activity_conversion)
        self.activity_unit_origin_combo.currentIndexChanged.connect(self.calculate_activity_conversion)
        self.activity_unit_target_combo.currentIndexChanged.connect(self.calculate_activity_conversion)

    def _initial_calculations(self):
        """Effectue les calculs initiaux."""
        self.calculate_ded_conversion()
        self.calculate_activity_conversion()
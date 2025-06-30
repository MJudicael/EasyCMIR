from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
import os
from src.utils.widgets import ClearingDoubleSpinBox
from src.utils.database import save_to_history

def load_isotopes():
    """Charge les isotopes depuis le fichier texte."""
    isotopes = {}
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        isotopes_path = os.path.join(root_dir, "data", "isotopes.txt")
        
        with open(isotopes_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith("//") or not line.strip():
                    continue
                data = line.strip().split(';')
                if len(data) >= 9:
                    name = data[0]
                    # Sépare le type d'usage des valeurs numériques
                    numeric_values = data[1:9]
                    usage_type = data[8].split(',')[1] if ',' in data[8] else "N/A"
                    
                    # Conversion des valeurs numériques uniquement
                    try:
                        values = [float(x.split(',')[0] if ',' in x else x) 
                                for x in numeric_values]
                        values.append(usage_type)  # Ajoute le type d'usage comme chaîne
                        isotopes[name] = values
                    except ValueError as e:
                        print(f"Erreur de conversion pour {name}: {e}")
                        continue
                    
    except FileNotFoundError:
        QMessageBox.critical(None, "Fichier Non Trouvé", 
            f"Fichier isotopes.txt non trouvé à {isotopes_path}")
    except Exception as e:
        QMessageBox.critical(None, "Erreur", 
            f"Erreur lors du chargement des isotopes: {e}")
    
    return isotopes

# Chargement des isotopes 
try:
    ISOTOPES = load_isotopes()
    ISOTOPE_NAMES = list(ISOTOPES.keys())
except Exception as e:
    QMessageBox.critical(None, "Erreur de chargement", 
                        f"Impossible de charger les isotopes: {e}\n"
                        "Vérifiez que le fichier isotopes.txt existe dans le dossier data/")
    ISOTOPES = {}
    ISOTOPE_NAMES = []

class Ded1mDialog(QDialog):  # Renommé de Ded1mDialog à DED1MDialog
    """Dialog pour le calcul du débit de dose à 1m."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul DED à 1m")
        self.setFixedSize(300, 220)

        self.layout = QVBoxLayout(self)

        # Formulaire de saisie
        input_form = QFormLayout()
        self.isotope_selection_combo = QComboBox()
        self.isotope_selection_combo.addItems(ISOTOPE_NAMES)
        self.isotope_selection_combo.setToolTip("Sélectionnez un isotope")
        input_form.addRow("Choix de l'isotope :", self.isotope_selection_combo)

        # Layout horizontal pour l'activité et son unité
        activity_layout = QHBoxLayout()
        
        self.activity_ded1m_input = ClearingDoubleSpinBox()
        self.activity_ded1m_input.setDecimals(3)
        self.activity_ded1m_input.setRange(0.0, 1e12)
        self.activity_ded1m_input.setSingleStep(0.1)
        self.activity_ded1m_input.setValue(0.0)
        self.activity_ded1m_input.setToolTip("Activité")
        
        # Ajout du menu déroulant pour les unités
        self.activity_unit = QComboBox()
        self.activity_unit.addItems(["Bq", "kBq", "MBq", "GBq", "TBq"])
        self.activity_unit.setCurrentText("GBq")  # Unité par défaut
        
        activity_layout.addWidget(self.activity_ded1m_input)
        activity_layout.addWidget(self.activity_unit)
        
        input_form.addRow("Activité :", activity_layout)
        self.layout.addLayout(input_form)

        calculate_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Calculer")
        self.calculate_button.clicked.connect(self.calculate_ded1m)
        calculate_layout.addWidget(self.calculate_button)

        self.isotope_count_label = QLabel(f"{len(ISOTOPE_NAMES)} isotopes en mémoire")
        self.isotope_count_label.setObjectName("infoLabel")
        calculate_layout.addWidget(self.isotope_count_label)
        self.layout.addLayout(calculate_layout)

        self.layout.addWidget(QLabel("<b>Débit de dose à 1m</b>"))
        self.ded1m_result_msv_label = QLabel("           ")
        self.ded1m_result_msv_label.setObjectName("resultLabel")
        self.ded1m_result_msv_label.setToolTip("Débit de dose en mSv/h")
        self.layout.addWidget(self.ded1m_result_msv_label)

        self.ded1m_result_usv_label = QLabel("           ")
        self.ded1m_result_usv_label.setObjectName("subResultLabel")
        self.ded1m_result_usv_label.setToolTip("Débit de dose en µSv/h")
        self.layout.addWidget(self.ded1m_result_usv_label)

        self.manual_mode_button = QPushButton("Mode manuel")
        self.manual_mode_button.clicked.connect(self.open_manual_mode)
        self.layout.addWidget(self.manual_mode_button)

        self.layout.addStretch(1)

        # Ajout du label pour le type d'usage après la combobox
        self.usage_type_label = QLabel("")
        self.usage_type_label.setObjectName("infoLabel")
        input_form.addRow("Type d'usage :", self.usage_type_label)
        
        # Connexion du changement de sélection à la mise à jour du type
        self.isotope_selection_combo.currentTextChanged.connect(self.update_usage_type)

    def update_usage_type(self, isotope_name):
        """Met à jour l'affichage du type d'usage quand un isotope est sélectionné."""
        if isotope_name in ISOTOPES:
            usage = ISOTOPES[isotope_name][-1]  # Le type est la dernière valeur
            usage_text = {
                "Med": "Médical",
                "Ind": "Industriel",
                "Mil": "Militaire"
            }.get(usage, "Non spécifié")
            self.usage_type_label.setText(usage_text)
        else:
            self.usage_type_label.setText("")

    def calculate_ded1m(self):
        """Calcule le débit de dose à 1m pour l'isotope sélectionné."""
        try:
            selected_isotope_name = self.isotope_selection_combo.currentText()
            activity_value = self.activity_ded1m_input.value()
            unit = self.activity_unit.currentText()

            # Conversion en Bq selon l'unité sélectionnée
            conversion = {
                "Bq": 1,
                "kBq": 1e3,
                "MBq": 1e6,
                "GBq": 1e9,
                "TBq": 1e12
            }
            
            activity_bq = activity_value * conversion[unit]
            
            if not selected_isotope_name or selected_isotope_name not in ISOTOPES:
                QMessageBox.warning(self, "Erreur Saisie", "Veuillez sélectionner un isotope valide.")
                return

            isotope_data = ISOTOPES[selected_isotope_name]
            e1, e2, e3 = isotope_data[2:5]
            # Conversion des pourcentages en décimales (division par 100)
            q1, q2, q3 = [x/100 for x in isotope_data[5:8]]

            ded1m_msvh = 1.3e-10 * activity_bq * (e1 * q1 + e2 * q2 + e3 * q3)
            ded1m_msvh = round(ded1m_msvh, 4)  # Augmentation de la précision
            ded1m_usvh = round(ded1m_msvh * 1e3, 2)

            self.ded1m_result_msv_label.setText(f"{ded1m_msvh} mSv/h")
            self.ded1m_result_usv_label.setText(f"{ded1m_usvh} µSv/h")

            save_to_history([
                "Debit de dose 1 m",
                f"Isotope: {selected_isotope_name}",
                f"Activite: {activity_value} {unit}",
                f"Debit de dose: {ded1m_msvh} mSv/h",
                f"{ded1m_usvh} uSv/h"
            ])

        except ValueError:
            QMessageBox.critical(self, "Erreur Saisie", "Veuillez entrer une activité numérique valide.")
        except IndexError:
            QMessageBox.critical(self, "Erreur Données", "Données d'isotope incomplètes ou malformées.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

    def open_manual_mode(self):
        """Ouvre la fenêtre du mode manuel."""
        manual_dialog = Ded1mManualDialog(self)
        manual_dialog.exec()

class Ded1mManualDialog(QDialog):
    """Dialog pour le calcul manuel du débit de dose à 1m."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DED en Manuel")
        self.setFixedSize(400, 300)

        self.layout = QGridLayout(self)

        # Configuration des entrées d'énergie et rendement 1
        self.layout.addWidget(QLabel("E1 (MeV)"), 0, 0)
        self.e1_input = ClearingDoubleSpinBox()
        self.e1_input.setDecimals(3)
        self.e1_input.setRange(0.0, 10.0)
        self.e1_input.setValue(0.0)
        self.e1_input.setToolTip("Énergie 1 en MeV")
        self.layout.addWidget(self.e1_input, 0, 1)

        self.layout.addWidget(QLabel("Q1 (decimal, ex: 0.83)"), 0, 2)
        self.q1_input = ClearingDoubleSpinBox()
        self.q1_input.setDecimals(3)
        self.q1_input.setRange(0.0, 10.0)
        self.q1_input.setValue(0.0)
        self.q1_input.setToolTip("Rendement 1 (fraction, ex: 0.83 pour 83%)")
        self.layout.addWidget(self.q1_input, 0, 3)

        # Entrée d'activité
        self.layout.addWidget(QLabel("Activité (GBq)"), 0, 4)
        self.activity_manual_input = ClearingDoubleSpinBox()
        self.activity_manual_input.setDecimals(3)
        self.activity_manual_input.setRange(0.0, 1e12)
        self.activity_manual_input.setValue(0.0)
        self.activity_manual_input.setToolTip("Activité en GBq")
        self.layout.addWidget(self.activity_manual_input, 0, 5)

        # Configuration des entrées d'énergie et rendement 2
        self.layout.addWidget(QLabel("E2 (MeV)"), 1, 0)
        self.e2_input = ClearingDoubleSpinBox()
        self.e2_input.setDecimals(3)
        self.e2_input.setRange(0.0, 10.0)
        self.e2_input.setValue(0.0)
        self.e2_input.setToolTip("Énergie 2 en MeV")
        self.layout.addWidget(self.e2_input, 1, 1)

        self.layout.addWidget(QLabel("Q2 (decimal, ex: 0.48)"), 1, 2)
        self.q2_input = ClearingDoubleSpinBox()
        self.q2_input.setDecimals(3)
        self.q2_input.setRange(0.0, 10.0)
        self.q2_input.setValue(0.0)
        self.q2_input.setToolTip("Rendement 2 (fraction, ex: 0.48 pour 48%)")
        self.layout.addWidget(self.q2_input, 1, 3)

        # Configuration des entrées d'énergie et rendement 3
        self.layout.addWidget(QLabel("E3 (MeV)"), 2, 0)
        self.e3_input = ClearingDoubleSpinBox()
        self.e3_input.setDecimals(3)
        self.e3_input.setRange(0.0, 10.0)
        self.e3_input.setValue(0.0)
        self.e3_input.setToolTip("Énergie 3 en MeV")
        self.layout.addWidget(self.e3_input, 2, 1)

        self.layout.addWidget(QLabel("Q3 (decimal, ex: 0.08)"), 2, 2)
        self.q3_input = ClearingDoubleSpinBox()
        self.q3_input.setDecimals(3)
        self.q3_input.setRange(0.0, 10.0)
        self.q3_input.setValue(0.0)
        self.q3_input.setToolTip("Rendement 3 (fraction, ex: 0.08 pour 8%)")
        self.layout.addWidget(self.q3_input, 2, 3)

        # Bouton de calcul et affichage du résultat
        self.calculate_button = QPushButton("Calculer")
        self.calculate_button.clicked.connect(self.calculate_manual_ded1m)
        self.layout.addWidget(self.calculate_button, 3, 0)

        self.manual_ded1m_result_label = QLabel("")
        self.manual_ded1m_result_label.setObjectName("resultLabel")
        self.manual_ded1m_result_label.setToolTip("Débit de dose en mSv/h")
        self.layout.addWidget(self.manual_ded1m_result_label, 3, 1, 1, 5)

    def calculate_manual_ded1m(self):
        """Calcule le débit de dose à 1m avec les paramètres manuels."""
        try:
            activity_gbq = self.activity_manual_input.value()
            e1, e2, e3 = self.e1_input.value(), self.e2_input.value(), self.e3_input.value()
            q1, q2, q3 = self.q1_input.value(), self.q2_input.value(), self.q3_input.value()

            activity_bq = activity_gbq * 1e9
            ded1m_msvh = 1.3e-10 * activity_bq * (e1 * q1 + e2 * q2 + e3 * q3)
            ded1m_msvh = round(ded1m_msvh, 2)

            self.manual_ded1m_result_label.setText(f"{ded1m_msvh} mSv/h")

            save_to_history([
                "Debit de dose 1 m (Manuel)", 
                f"E1:{e1}, Q1:{q1}",
                f"E2:{e2}, Q2:{q2}",
                f"E3:{e3}, Q3:{q3}",
                f"Activite: {activity_gbq} GBq",
                f"Debit de dose: {ded1m_msvh} mSv/h"
            ])

        except ValueError:
            QMessageBox.critical(self, "Erreur Saisie",
                               "Veuillez entrer des valeurs numériques valides pour tous les champs.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

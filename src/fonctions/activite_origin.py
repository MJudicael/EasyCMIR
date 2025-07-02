import os
import math
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFormLayout, QGroupBox, QMessageBox,
    QDoubleSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ..constants import ICONS_DIR
from ..utils.config_manager import config_manager


class ActiviteOriginDialog(QDialog):
    """Dialog pour calculer l'activité d'origine à partir du débit de dose."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul Activité d'Origine")
        self.setMinimumSize(500, 400)
        self.resize(500, 450)
        
        # Chargement des isotopes depuis la base de données
        self.load_isotopes()
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Configuration de l'icône
        self.setup_icon()
    
    def setup_icon(self):
        """Configure l'icône de la fenêtre."""
        icon_path = os.path.join(ICONS_DIR, "activite_origin.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def load_isotopes(self):
        """Charge la liste des isotopes depuis le fichier isotopes.txt."""
        self.isotopes_data = {}
        
        try:
            isotopes_file = config_manager.get_isotopes_path()
            
            with open(isotopes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(';')
                        if len(parts) >= 9:
                            nom = parts[0]
                            activite_specifique = float(parts[1]) if parts[1] != '0' else 0
                            demi_vie = float(parts[2]) if parts[2] != '0' else 0
                            
                            # Stocker les données de l'isotope
                            self.isotopes_data[nom] = {
                                'activite_specifique': activite_specifique,
                                'demi_vie': demi_vie,
                                'energie1': float(parts[3]) if parts[3] != '0.000' else 0,
                                'energie2': float(parts[4]) if parts[4] != '0.000' else 0,
                                'energie3': float(parts[5]) if parts[5] != '0.000' else 0,
                                'intensite1': float(parts[6]) if parts[6] != '0.0' else 0,
                                'intensite2': float(parts[7]) if parts[7] != '0.0' else 0,
                                'intensite3': float(parts[8].split(',')[0]) if parts[8].split(',')[0] != '0.0' else 0
                            }
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement des isotopes: {str(e)}")
            self.isotopes_data = {}
    
    def get_atomic_number(self, isotope_name):
        """Extrait le numéro atomique d'un isotope à partir de son nom."""
        # Dictionnaire des éléments avec leurs numéros atomiques
        atomic_numbers = {
            'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
            'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20,
            'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30,
            'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40,
            'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50,
            'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60,
            'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70,
            'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80,
            'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90,
            'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100
        }
        
        # Dictionnaire des correspondances spéciales pour les noms français
        french_elements = {
            'Deutérium': 'H', 'Tritium': 'H', 'Carbone': 'C', 'Fluor': 'F', 'Sodium': 'Na',
            'Phosphore': 'P', 'Potassium': 'K', 'Scandium': 'Sc', 'Fer': 'Fe', 'Cobalt': 'Co',
            'Nickel': 'Ni', 'Cuivre': 'Cu', 'Zinc': 'Zn', 'Gallium': 'Ga', 'Germanium': 'Ge',
            'Sélénium': 'Se', 'Krypton': 'Kr', 'Rubidium': 'Rb', 'Strontium': 'Sr', 'Yttrium': 'Y',
            'Zirconium': 'Zr', 'Molybdène': 'Mo', 'Technétium': 'Tc', 'Palladium': 'Pd',
            'Cadmium': 'Cd', 'Indium': 'In', 'Étain': 'Sn', 'Iode': 'I', 'Xénon': 'Xe',
            'Césium': 'Cs', 'Baryum': 'Ba', 'Prométhium': 'Pm', 'Samarium': 'Sm', 'Europium': 'Eu',
            'Gadolinium': 'Gd', 'Terbium': 'Tb', 'Holmium': 'Ho', 'Thulium': 'Tm', 'Lutétium': 'Lu',
            'Rhenium': 'Re', 'Iridium': 'Ir', 'Or': 'Au', 'Thallium': 'Tl', 'Plomb': 'Pb',
            'Bismuth': 'Bi', 'Polonium': 'Po', 'Astate': 'At', 'Radon': 'Rn', 'Radium': 'Ra',
            'Actinium': 'Ac', 'Thorium': 'Th', 'Protactinium': 'Pa', 'Uranium': 'U',
            'Neptunium': 'Np', 'Plutonium': 'Pu', 'Américium': 'Am', 'Curium': 'Cm',
            'Californium': 'Cf'
        }
        
        # Extraire le nom de l'élément (avant le tiret ou la parenthèse)
        element_name = isotope_name.split('-')[0].split('(')[0].strip()
        
        # Rechercher d'abord dans les correspondances françaises
        if element_name in french_elements:
            symbol = french_elements[element_name]
            return atomic_numbers.get(symbol, 999)
        
        # Puis dans les symboles directs
        if element_name in atomic_numbers:
            return atomic_numbers[element_name]
        
        # Si pas trouvé, retourner un numéro élevé pour le placer à la fin
        return 999
    
    def sort_isotopes_by_atomic_number(self):
        """Trie les isotopes par numéro atomique croissant."""
        isotope_list = list(self.isotopes_data.keys())
        
        # Tri par numéro atomique, puis par nom pour les isotopes du même élément
        sorted_isotopes = sorted(isotope_list, key=lambda x: (self.get_atomic_number(x), x))
        
        return sorted_isotopes
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur."""
        layout = QVBoxLayout(self)
               
        # Groupe de saisie
        input_group = QGroupBox("Paramètres de calcul")
        input_layout = QFormLayout(input_group)
        
        # Sélection de l'isotope
        self.isotope_combo = QComboBox()
        self.isotope_combo.addItem("Sélectionner un isotope")
        
        # Chargement des isotopes triés par numéro atomique croissant
        isotope_names = self.sort_isotopes_by_atomic_number()
        self.isotope_combo.addItems(isotope_names)
        
        self.isotope_combo.setToolTip("Sélectionner l'isotope à analyser")
        input_layout.addRow("Isotope:", self.isotope_combo)
        
        # Débit de dose
        dose_layout = QHBoxLayout()
        self.dose_input = QDoubleSpinBox()
        self.dose_input.setDecimals(3)
        self.dose_input.setMinimum(0.001)
        self.dose_input.setMaximum(999999.999)
        self.dose_input.setValue(1.0)
        self.dose_input.setToolTip("Saisir le débit de dose mesuré")
        
        # Unité du débit de dose
        self.dose_unit_combo = QComboBox()
        self.dose_unit_combo.addItems([
            "µSv/h", "mSv/h", "Sv/h"
        ])
        self.dose_unit_combo.setCurrentText("µSv/h")
        self.dose_unit_combo.setToolTip("Unité du débit de dose")
        
        dose_layout.addWidget(self.dose_input)
        dose_layout.addWidget(self.dose_unit_combo)
        input_layout.addRow("Débit de dose:", dose_layout)
        
        # Distance
        self.distance_input = QDoubleSpinBox()
        self.distance_input.setDecimals(2)
        self.distance_input.setMinimum(0.01)
        self.distance_input.setMaximum(1000.0)
        self.distance_input.setValue(1.0)
        self.distance_input.setSuffix(" m")
        self.distance_input.setToolTip("Distance de mesure en mètres")
        input_layout.addRow("Distance:", self.distance_input)
        
        layout.addWidget(input_group)
        
        # Bouton de calcul
        self.calc_button = QPushButton("Calculer l'Activité")
        self.calc_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.calc_button.clicked.connect(self.calculate_activity)
        layout.addWidget(self.calc_button)
        
        # Groupe de résultats
        result_group = QGroupBox("Résultats")
        result_layout = QFormLayout(result_group)
        
        self.result_label = QLabel("-")
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        self.result_label.setWordWrap(True)
        self.result_label.setMinimumHeight(20)
        self.result_label.adjustSize()
        result_layout.addRow("Activité calculée:", self.result_label)
        
        self.info_label = QLabel("-")
        self.info_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(60)
        self.info_label.adjustSize()
        result_layout.addRow("Informations:", self.info_label)
        
        layout.addWidget(result_group)
        
        # Bouton fermer
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
    
    def calculate_activity(self):
        """Calcule l'activité d'origine en fonction des paramètres saisis."""
        try:
            # Récupération des valeurs
            isotope_name = self.isotope_combo.currentText()
            dose_rate = self.dose_input.value()
            dose_unit = self.dose_unit_combo.currentText()
            distance = self.distance_input.value()
            
            if isotope_name == "Sélectionner un isotope" or not isotope_name or isotope_name not in self.isotopes_data:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un isotope valide.")
                return
            
            isotope_data = self.isotopes_data[isotope_name]
            
            # Conversion du débit de dose en µSv/h
            if dose_unit == "mSv/h":
                dose_rate_usv = dose_rate * 1000
            elif dose_unit == "Sv/h":
                dose_rate_usv = dose_rate * 1000000
            else:  # µSv/h
                dose_rate_usv = dose_rate
            
            # Correction du débit de dose à 1m selon la loi de l'inverse du carré de la distance
            dose_rate_1m = dose_rate_usv * (distance * distance)
            
            # Calcul de la constante gamma à partir des données de l'isotope
            gamma_constant = self.calculate_gamma_constant(isotope_data)
            
            if gamma_constant <= 0:
                QMessageBox.warning(self, "Erreur", f"Impossible de calculer pour {isotope_name}: données gamma insuffisantes pour le calcul de la constante.")
                return
            
            # Calcul de l'activité selon la formule : A (MBq) = D (µSv/h) / Γ ((µSv·h⁻¹)/(MBq·m⁻²))
            activity_mbq = dose_rate_1m / gamma_constant
            activity_bq = activity_mbq * 1e6  # Conversion MBq vers Bq
            
            # Formatage du résultat avec l'unité appropriée
            formatted_result = self.format_activity(activity_bq)
            
            # Affichage des résultats
            self.result_label.setText(formatted_result)
            self.result_label.adjustSize()
            
            info_text = f"Isotope: {isotope_name}\n"
            info_text += f"Débit de dose: {dose_rate} {dose_unit} à {distance} m\n"
            info_text += f"Débit de dose à 1m: {dose_rate_1m:.2f} µSv/h\n"
            info_text += f"Constante γ calculée: {gamma_constant:.3f} (µSv·h⁻¹)/(MBq·m⁻²)\n"
            info_text += f"Activité: {activity_mbq:.2f} MBq"
            
            self.info_label.setText(info_text)
            self.info_label.adjustSize()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du calcul: {str(e)}")
    
    def calculate_gamma_constant(self, isotope_data):
        """Calcule la constante gamma à partir des données de l'isotope.
        
        Utilise la formule empirique basée sur les énergies et intensités gamma :
        Γ = K × Σ(E × I) où :
        - E = énergie gamma en MeV
        - I = intensité gamma en %
        - K = facteur de conversion empirique
        
        Résultat en (µSv·h⁻¹)/(MBq·m⁻²)
        """
        
        total_gamma_contribution = 0
        
        # Somme pondérée des énergies par leurs intensités
        if isotope_data['energie1'] > 0 and isotope_data['intensite1'] > 0:
            total_gamma_contribution += isotope_data['energie1'] * isotope_data['intensite1']
        
        if isotope_data['energie2'] > 0 and isotope_data['intensite2'] > 0:
            total_gamma_contribution += isotope_data['energie2'] * isotope_data['intensite2']
        
        if isotope_data['energie3'] > 0 and isotope_data['intensite3'] > 0:
            total_gamma_contribution += isotope_data['energie3'] * isotope_data['intensite3']
        
        # Facteur de conversion empirique pour obtenir (µSv·h⁻¹)/(MBq·m⁻²)
        # Facteur calibré pour correspondre aux valeurs expérimentales connues
        # (basé sur Cobalt-60: constante gamma = 0.35)
        conversion_factor = 1.4e-3
        
        gamma_constant = total_gamma_contribution * conversion_factor
        
        return gamma_constant
    
    def format_activity(self, activity_bq):
        """Formate l'activité avec l'unité appropriée pour avoir au maximum 2 décimales."""
        
        if activity_bq < 1:
            return f"{activity_bq:.3f} Bq"
        elif activity_bq < 1000:
            return f"{activity_bq:.2f} Bq"
        elif activity_bq < 1000000:
            return f"{activity_bq/1000:.2f} kBq"
        elif activity_bq < 1000000000:
            return f"{activity_bq/1000000:.2f} MBq"
        elif activity_bq < 1000000000000:
            return f"{activity_bq/1000000000:.2f} GBq"
        else:
            return f"{activity_bq/1000000000000:.2f} TBq"

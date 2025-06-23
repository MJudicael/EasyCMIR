from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QLineEdit, QComboBox, 
    QMessageBox, QSlider
)
from PySide6.QtCore import Qt
import os
import math

class IdentificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul d'écran de protection")
        self.setMinimumWidth(400)
        
        # Définition des coefficients d'atténuation (en cm^-1)
        self.mu_data = {
            "plomb": [(0.5, 1.7), (1.0, 0.8), (2.0, 0.5), (3.0, 0.4)],
            "plexiglas": [(0.5, 0.1), (1.0, 0.07), (2.0, 0.05), (3.0, 0.04)]
        }
        
        # Chargement des isotopes
        self.isotopes_data = {}
        self.load_isotopes()
        
        # Création de l'interface
        self.setup_ui()

    def load_isotopes(self):
        """Charge les données des isotopes depuis le fichier."""
        isotopes_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "isotopes.txt"
        )
        
        try:
            with open(isotopes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        parts = line.strip().split(';')
                        if len(parts) >= 9:
                            name = parts[0]
                            energies = [float(parts[i]) for i in range(3, 6)]
                            abundances = [float(parts[i].split(',')[0] if i == 8 else parts[i]) 
                                        for i in range(6, 9)]
                            
                            self.isotopes_data[name] = {
                                'energies': energies,
                                'abundances': abundances
                            }
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les isotopes: {str(e)}")

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout()

        # Section activité
        activity_group = QGroupBox("Activité")
        activity_layout = QHBoxLayout()
        
        self.activity_input = QLineEdit()
        self.activity_input.setPlaceholderText("Entrez l'activité")
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Bq", "kBq", "MBq", "GBq", "TBq"])
        
        activity_layout.addWidget(self.activity_input)
        activity_layout.addWidget(self.unit_combo)
        activity_group.setLayout(activity_layout)
        
        # Section isotope
        isotope_group = QGroupBox("Isotope")
        isotope_layout = QHBoxLayout()
        
        self.isotope_combo = QComboBox()
        self.isotope_combo.addItems(sorted(self.isotopes_data.keys()))
        
        isotope_layout.addWidget(self.isotope_combo)
        isotope_group.setLayout(isotope_layout)
        
        # Section matériau
        material_group = QGroupBox("Matériau")
        material_layout = QHBoxLayout()
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Plomb", "Plexiglas"])  # Suppression du béton
        
        material_layout.addWidget(self.material_combo)
        material_group.setLayout(material_layout)
        
        # Section épaisseur
        thickness_group = QGroupBox("Épaisseur de l'écran")
        thickness_layout = QVBoxLayout()  # Changé en VBoxLayout pour un meilleur arrangement
        
        # Création du curseur
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setMinimum(0)
        self.thickness_slider.setMaximum(50)
        self.thickness_slider.setTickPosition(QSlider.TicksBelow)
        self.thickness_slider.setTickInterval(2)
        
        # Label pour afficher la valeur
        self.thickness_value_label = QLabel("0 cm")
        self.thickness_value_label.setAlignment(Qt.AlignCenter)
        
        # Connexion du signal valueChanged du slider
        self.thickness_slider.valueChanged.connect(self.update_thickness_label)
        
        thickness_layout.addWidget(self.thickness_slider)
        thickness_layout.addWidget(self.thickness_value_label)
        
        thickness_group.setLayout(thickness_layout)
        
        # Bouton de calcul
        calculate_btn = QPushButton("Calculer")
        calculate_btn.clicked.connect(self.calculate_shield)
        
        # Résultat
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        
        # Assemblage
        layout.addWidget(activity_group)
        layout.addWidget(isotope_group)
        layout.addWidget(material_group)
        layout.addWidget(thickness_group)
        layout.addWidget(calculate_btn)
        layout.addWidget(self.result_label)
        
        self.setLayout(layout)

    def format_dose_rate(self, dose_rate):
        """Formate le débit de dose avec l'unité appropriée."""
        if dose_rate >= 1000:  # Plus de 1000 mSv/h -> Sv/h
            return f"{dose_rate/1000:.1f} Sv/h"
        elif dose_rate >= 1:  # Entre 1 et 1000 mSv/h
            return f"{dose_rate:.1f} mSv/h"
        elif dose_rate >= 0.001:  # Entre 0.001 et 1 mSv/h -> µSv/h
            return f"{dose_rate * 1000:.1f} µSv/h"
        else:  # Moins de 1 µSv/h -> nSv/h
            return f"{dose_rate * 1000000:.1f} nSv/h"

    def calculate_shield(self):
        """Calcule le facteur d'atténuation pour l'épaisseur donnée."""
        try:
            # Récupération des valeurs
            activity = float(self.activity_input.text())
            unit = self.unit_combo.currentText()
            isotope = self.isotope_combo.currentText()
            material = self.material_combo.currentText().lower()
            thickness = float(self.thickness_slider.value())  # Utilisation du slider
            
            # Conversion en Bq
            unit_factors = {
                "Bq": 1,
                "kBq": 1e3,
                "MBq": 1e6,
                "GBq": 1e9,
                "TBq": 1e12
            }
            
            activity_bq = activity * unit_factors[unit]
            
            # Initialisation du facteur à 1
            total_factor = 1
            
            # Calcul du facteur d'atténuation pour chaque énergie
            isotope_data = self.isotopes_data[isotope]
            energies = isotope_data['energies']
            abundances = isotope_data['abundances']
            
            for energy, abundance in zip(energies, abundances):
                if energy > 0 and abundance > 0:
                    mu = self.get_mu(material, energy)
                    if mu is not None:  # Vérifie que mu existe
                        # Calcul du facteur d'atténuation: e^(μx)
                        attenuation = math.exp(mu * thickness)
                        total_factor = max(total_factor, attenuation)
            
            # Calcul des débits de dose
            initial_dose_rate = self.calculate_dose_rate(activity_bq, energies, abundances)
            final_dose_rate = initial_dose_rate / total_factor
            
            # Formatage des résultats
            initial_dose_str = self.format_dose_rate(initial_dose_rate)
            final_dose_str = self.format_dose_rate(final_dose_rate)
            
            # Calcul de l'épaisseur recommandée pour 2.5 µSv/h
            target_dose_rate = 2.5e-3  # 2.5 µSv/h = 0.0025 mSv/h
            recommended_thickness = self.calculate_required_thickness(
                target_dose_rate, 
                activity_bq, 
                energies, 
                abundances, 
                material
            )
            
            # Affichage du résultat
            result = (f"Facteur d'atténuation: {total_factor:.1f}\n"
                     f"Débit de dose initial: {initial_dose_str}\n"
                     f"Débit de dose après écran: {final_dose_str}")
            
            # Ajout de la recommandation
            if recommended_thickness is not None:
                result += f"\nPour atteindre 2.5 µSv/h il est recommandée un écran de: {recommended_thickness:.1f} cm"
            else:
                result += "\nImpossible d'atteindre 2.5 µSv/h avec une épaisseur raisonnable"

            self.result_label.setText(result)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de calcul: {str(e)}")

    def get_mu(self, material, energy):
        """Obtient le coefficient d'atténuation pour un matériau et une énergie."""
        if material not in self.mu_data:
            return None
            
        data_points = self.mu_data[material]
        
        # Si l'énergie est inférieure au minimum ou supérieure au maximum
        min_energy = data_points[0][0]
        max_energy = data_points[-1][0]
        
        if energy <= min_energy:
            return data_points[0][1]
        if energy >= max_energy:
            return data_points[-1][1]
        
        # Trouve les points d'encadrement
        for i in range(len(data_points)-1):
            e1, mu1 = data_points[i]
            e2, mu2 = data_points[i+1]
            
            if e1 <= energy <= e2:
                # Interpolation linéaire
                return mu1 + (mu2 - mu1) * (energy - e1) / (e2 - e1)
        
        return None

    def calculate_dose_rate(self, activity, energies, abundances):
        """Calcule le débit de dose à 1m."""
        dose_rate = 0
        for energy, abundance in zip(energies, abundances):
            if energy > 0 and abundance > 0:
                dose_rate += activity * energy * abundance * 1.3e-10
        return dose_rate

    def update_thickness_label(self, value):
        """Met à jour le label avec la valeur actuelle du curseur."""
        self.thickness_value_label.setText(f"{value} cm")

    def calculate_required_thickness(self, target_dose_rate, activity_bq, energies, abundances, material):
        """Calcule l'épaisseur nécessaire pour atteindre un débit de dose cible."""
        initial_dose_rate = self.calculate_dose_rate(activity_bq, energies, abundances)
        required_factor = initial_dose_rate / target_dose_rate
        
        # Si le débit initial est déjà inférieur à la cible
        if required_factor <= 1:
            return 0
            
        # Recherche par itération de l'épaisseur nécessaire
        thickness = 0
        step = 1.0  # Pas de 1 cm
        max_thickness = 300  # Épaisseur maximale de 300 cm
        
        while thickness <= max_thickness:
            total_factor = 1
            for energy, abundance in zip(energies, abundances):
                if energy > 0 and abundance > 0:
                    mu = self.get_mu(material, energy)
                    if mu is not None:
                        attenuation = math.exp(mu * thickness)
                        total_factor = max(total_factor, attenuation)
            
            if total_factor >= required_factor:
                return thickness
                
            thickness += step
            
        return None  # Si aucune épaisseur trouvée
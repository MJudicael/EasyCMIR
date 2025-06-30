from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QDoubleSpinBox, QComboBox,
    QDateEdit, QMessageBox, QGridLayout, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os
from math import log, exp
import numpy as np
from ..utils.database import save_to_history
from ..utils.widgets import ClearingSpinBox

class DecroissanceCalculator:
    """Classe pour calculer la décroissance radioactive."""
    
    def __init__(self):
        self.initial_activity = 0
        self.half_life = 0
        self.start_datetime = None
        self.isotope_name = None  # Ajout du nom de l'isotope
        
    def plot_decay(self):
        """Génère le graphique de décroissance avec indication des 10 périodes et DED."""
        if not all([self.initial_activity, self.half_life, self.start_datetime]):
            raise ValueError("Les paramètres initiaux doivent être définis")
            
        # Calcul de lambda
        lambda_const = log(2) / (self.half_life * 3600)  # conversion half_life en secondes
        
        # Calcul pour 10 périodes
        end_datetime = self.start_datetime + timedelta(hours=self.half_life * 10)
        final_activity = self.initial_activity * exp(-lambda_const * (self.half_life * 10 * 3600))
        
        # Conversion en MBq pour le calcul du DED
        final_activity_mbq = final_activity * 1e-6  # Conversion de Bq en MBq
        final_ded = 0  # Initialisation par défaut

        # Récupération des données de l'isotope depuis le fichier
        try:
            isotopes_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "isotopes.txt"
            )
            with open(isotopes_file, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        values = line.strip().split(';')
                        name = values[0]
                        if name == self.isotope_name:
                            e1, e2, e3 = float(values[3]), float(values[4]), float(values[5])
                            q1, q2, q3 = float(values[6]), float(values[7]), float(values[8].split(',')[0])
                            # Calcul du DED avec la formule générique
                            final_ded = 1.3e-10 * final_activity_mbq * 1e6 * (e1 * q1/100 + e2 * q2/100 + e3 * q3/100)
                            break
        except Exception:
            final_ded = 0

        # Points pour le graphique
        total_hours = self.half_life * 10
        time_points = np.linspace(0, total_hours * 3600, 1000)  # en secondes
        dates = [self.start_datetime + timedelta(seconds=t) for t in time_points]
        
        # Calcul des activités selon la loi de décroissance A(t) = A0 * e^(-λt)
        activities = [self.initial_activity * exp(-lambda_const * t) for t in time_points]
        
        # Création du graphique
        plt.figure(figsize=(12, 8))
        plt.plot(dates, activities, 'b-', label='Décroissance')
        
        # Formatage de l'activité finale avec l'unité adaptée
        if final_activity >= 1e12:  # TBq
            activity_str = f"{final_activity * 1e-12:.1f} TBq"
        elif final_activity >= 1e9:  # GBq
            activity_str = f"{final_activity * 1e-9:.1f} GBq"
        elif final_activity >= 1e6:  # MBq
            activity_str = f"{final_activity * 1e-6:.1f} MBq"
        elif final_activity >= 1e3:  # kBq
            activity_str = f"{final_activity * 1e-3:.1f} kBq"
        else:  # Bq
            activity_str = f"{final_activity:.1f} Bq"

        # Formatage du débit de dose avec l'unité adaptée
        if final_ded >= 1:  # > 1 mSv/h
            ded_str = f"{final_ded:.1f} mSv/h"
        elif final_ded >= 0.001:  # > 1 µSv/h
            ded_str = f"{final_ded * 1000:.1f} µSv/h"
        else:  # < 1 µSv/h
            ded_str = f"{final_ded * 1000000:.1f} nSv/h"

        # Ajout du point à 10 périodes avec bulle d'information
        plt.plot(end_datetime, final_activity, 'yo', label='10 périodes',
                markerfacecolor='yellow', markeredgecolor='black')
        plt.annotate(
            f'Après 10 périodes:\n'
            f'Date: {end_datetime.strftime("%d/%m/%Y %H:%M")}\n'
            f'Activité: {activity_str}\n'
            f'DED à 1m: {ded_str}',
            xy=(end_datetime, final_activity),
            xytext=(0, 30),
            textcoords='offset points',
            ha='center',
            va='bottom',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
        
        # Calcul de l'activité actuelle
        current_datetime = datetime.now()
        delta_seconds = (current_datetime - self.start_datetime).total_seconds()
        current_activity = self.initial_activity * exp(-lambda_const * delta_seconds)
        
        # Calcul du DED actuel
        current_activity_mbq = current_activity * 1e-6
        current_ded = final_ded * (current_activity / final_activity)  # Utilise le même rapport que final_ded

        # Formatage de l'activité actuelle
        if current_activity >= 1e12:
            current_activity_str = f"{current_activity * 1e-12:.1f} TBq"
        elif current_activity >= 1e9:
            current_activity_str = f"{current_activity * 1e-9:.1f} GBq"
        elif current_activity >= 1e6:
            current_activity_str = f"{current_activity * 1e-6:.1f} MBq"
        elif current_activity >= 1e3:
            current_activity_str = f"{current_activity * 1e-3:.1f} kBq"
        else:
            current_activity_str = f"{current_activity:.1f} Bq"

        # Formatage du DED actuel
        if current_ded >= 1:
            current_ded_str = f"{current_ded:.1f} mSv/h"
        elif current_ded >= 0.001:
            current_ded_str = f"{current_ded * 1000:.1f} µSv/h"
        else:
            current_ded_str = f"{current_ded * 1000000:.1f} nSv/h"

        # Ajout du point actuel avec bulle d'information
        plt.plot(current_datetime, current_activity, 'mo', label='Actuel',
                markerfacecolor='magenta', markeredgecolor='black')
        plt.annotate(
            f'Actuellement:\n'
            f'Date: {current_datetime.strftime("%d/%m/%Y %H:%M")}\n'
            f'Activité: {current_activity_str}\n'
            f'DED à 1m: {current_ded_str}',
            xy=(current_datetime, current_activity),
            xytext=(30, 30),
            textcoords='offset points',
            ha='left',
            va='bottom',
            bbox=dict(boxstyle='round,pad=0.5', fc='magenta', alpha=0.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
        
        # Ajout d'une bulle pour DED = 2.5 µSv/h si le DED final > 2.5 µSv/h
        if final_ded >= 0.0025:  # 2.5 µSv/h en mSv/h
            # Calcul du temps nécessaire pour atteindre 2.5 µSv/h
            target_ded = 0.0025  # 2.5 µSv/h en mSv/h
            ratio = target_ded / final_ded
            target_activity = final_activity * ratio
            
            # Calcul de la date correspondante
            time_to_target = -log(target_activity / self.initial_activity) / lambda_const
            target_datetime = self.start_datetime + timedelta(seconds=time_to_target)
            
            # Formatage de l'activité cible
            if target_activity >= 1e12:
                target_activity_str = f"{target_activity * 1e-12:.1f} TBq"
            elif target_activity >= 1e9:
                target_activity_str = f"{target_activity * 1e-9:.1f} GBq"
            elif target_activity >= 1e6:
                target_activity_str = f"{target_activity * 1e-6:.1f} MBq"
            elif target_activity >= 1e3:
                target_activity_str = f"{target_activity * 1e-3:.1f} kBq"
            else:
                target_activity_str = f"{target_activity:.1f} Bq"

            # Ajout du point et de la bulle d'information
            plt.plot(target_datetime, target_activity, 'go', label='Périmètre public',
                    markerfacecolor='lightgreen', markeredgecolor='black')
            plt.annotate(
                f'Périmètre public\n'
                f'Date: {target_datetime.strftime("%d/%m/%Y %H:%M")}\n'
                f'Activité: {target_activity_str}\n'
                f'DED à 1m: 2.5 µSv/h',
                xy=(target_datetime, target_activity),
                xytext=(60, 150),
                textcoords='offset points',
                ha='right',
                va='top',
                bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
            )

        # Formatage du graphique
        plt.gcf().autofmt_xdate()
        plt.xlabel('Date et Heure')
        plt.ylabel('Activité (Bq)')
        plt.title('Décroissance Radioactive')
        plt.grid(True)
        plt.legend()
        
        return plt.gcf()

class DecroissanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcul de décroissance")
        self.main_layout = QVBoxLayout(self)  # Définir main_layout avant setup_ui
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Créer les widgets
        self.create_input_widgets()
        
    def create_input_widgets(self):
        """Crée les widgets de saisie"""
        input_group = QGroupBox("Paramètres")
        input_layout = QFormLayout()
        
        # Activité initiale
        self.activity_input = QDoubleSpinBox()
        self.activity_input.setRange(0, 1e20)
        self.activity_input.setDecimals(3)
        
        # Menu déroulant des unités
        self.activity_unit = QComboBox()
        self.activity_unit.addItems(["Bq", "kBq", "MBq", "GBq", "TBq"])
        self.activity_unit.setCurrentText("Bq")
        
        input_layout.addRow(QLabel("Activité:"), self.activity_input)
        input_layout.addRow(QLabel("Unité:"), self.activity_unit)
        
        # Période
        period_group = QGroupBox("Période")
        period_layout = QVBoxLayout()
        
        # ComboBox pour les isotopes
        self.isotope_combo = QComboBox()
        self.isotope_combo.addItem("Sélectionner un isotope")
        
        # Chargement des isotopes depuis le fichier
        isotopes_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "isotopes.txt"
        )
        
        try:
            with open(isotopes_file, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        isotope, _, period, *_ = line.strip().split(';')
                        self.isotope_combo.addItem(isotope)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de charger la liste des isotopes: {str(e)}")
    
        period_layout.addWidget(self.isotope_combo)
        
        # Bouton période personnalisée
        self.custom_period_btn = QPushButton("Personnalisé")
        self.custom_period_btn.clicked.connect(self.show_custom_period)
        period_layout.addWidget(self.custom_period_btn)
        
        period_group.setLayout(period_layout)
        input_layout.addRow(period_group)
        
        # Date initiale
        date_group = QGroupBox("Date initiale")
        date_layout = QHBoxLayout()
        
        # Création du sélecteur de date
        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.date_input.setCalendarPopup(True)  # Active le popup calendrier
        
        # Date par défaut : 22/05/2012
        default_date = QDate(2012, 5, 22)
        self.date_input.setDate(default_date)
        
        date_layout.addWidget(QLabel("Date:"))
        date_layout.addWidget(self.date_input)
        
        date_group.setLayout(date_layout)
        input_layout.addRow(date_group)
        
        input_group.setLayout(input_layout)
        self.main_layout.addWidget(input_group)

        # Bouton de calcul
        calc_button = QPushButton("Calculer")
        calc_button.clicked.connect(self.calculate_decay)
        self.main_layout.addWidget(calc_button)
        
        # Groupe résultats
        result_group = QGroupBox("Résultats")
        result_layout = QVBoxLayout()
        self.result_gbq_label = QLabel()
        self.result_bq_label = QLabel()
        result_layout.addWidget(self.result_gbq_label)
        result_layout.addWidget(self.result_bq_label)
        result_group.setLayout(result_layout)
        self.main_layout.addWidget(result_group)
        
        # Bouton graphique
        self.plot_button = QPushButton("Afficher le graphique")
        self.plot_button.clicked.connect(self.show_decay_plot)
        self.plot_button.setEnabled(False)
        self.main_layout.addWidget(self.plot_button)

    def show_custom_period(self):
        """Affiche le dialog de période personnalisée."""
        dialog = CustomPeriodDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.period_seconds = dialog.get_period_seconds()
            self.isotope_combo.setCurrentIndex(0)
            
    def update_period(self, index):
        """Met à jour la période selon l'isotope sélectionné."""
        if index == 0:  # "Sélectionner un isotope"
            return
        
        isotope = self.isotope_combo.currentText()
        isotopes_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "isotopes.txt"
        )
        
        try:
            with open(isotopes_file, "r", encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        values = line.strip().split(';')
                        name = values[0]
                        if name == isotope:
                            self.period_seconds = float(values[2])  # La période est en 3ème position
                            break
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de lire la période de l'isotope: {str(e)}")

    def calculate_decay(self):
        """Calcule la décroissance radioactive selon N(t) = N0 e^(-λt)"""
        try:
            if not self.period_seconds:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un isotope ou définir une période personnalisée")
                return
            
            # Récupération de l'activité initiale
            initial_activity = self.activity_input.value()
            
            # Conversion de l'activité selon l'unité choisie en Bq
            unit_factors = {"Bq": 1, "kBq": 1e3, "MBq": 1e6, "GBq": 1e9, "TBq": 1e12}
            initial_activity_bq = initial_activity * unit_factors[self.activity_unit.currentText()]
            
            # Calcul de λ (lambda) = ln(2)/T
            lambda_const = log(2) / self.period_seconds
            
            # Récupération de la date
            selected_date = self.date_input.date()
            initial_date = datetime(
                year=selected_date.year(),
                month=selected_date.month(),
                day=selected_date.day(),
                hour=0,  # On fixe l'heure à minuit
                minute=0,
                second=0
            )
            
            # Calcul du temps écoulé
            current_datetime = datetime.now()
            delta_seconds = (current_datetime - initial_date).total_seconds()
            
            # Calcul du nombre de périodes écoulées
            n_periodes = delta_seconds / self.period_seconds  # Nombre de périodes écoulées
            current_activity_bq = initial_activity_bq * (0.5 ** n_periodes)  # Division par 2 pour chaque période
            current_activity_gbq = current_activity_bq * 1e-9
            
            # Mise à jour des résultats
            # Formatage de l'activité avec l'unité adaptée
            if current_activity_bq >= 1e12:  # TBq
                formatted_activity = f"{current_activity_bq * 1e-12:.1f} TBq"
            elif current_activity_bq >= 1e9:  # GBq
                formatted_activity = f"{current_activity_bq * 1e-9:.1f} GBq"
            elif current_activity_bq >= 1e6:  # MBq
                formatted_activity = f"{current_activity_bq * 1e-6:.1f} MBq"
            elif current_activity_bq >= 1e3:  # kBq
                formatted_activity = f"{current_activity_bq * 1e-3:.1f} kBq"
            else:  # Bq
                formatted_activity = f"{current_activity_bq:.1f} Bq"
            
            self.result_gbq_label.setText(formatted_activity)
            self.result_bq_label.setText(f"{current_activity_bq:.1e} Bq")
            
            # Conversion vers l'unité sélectionnée pour le graphique
            unit_text = self.activity_unit.currentText()
            unit_factors = {"Bq": 1, "kBq": 1e-3, "MBq": 1e-6, "GBq": 1e-9, "TBq": 1e-12}
            conversion_factor = unit_factors[unit_text]
            
            # Préparation des données pour le graphique
            max_plot_time = max(self.period_seconds * 3, delta_seconds * 1.5)
            time_points = np.linspace(0, max_plot_time, 200)
            activity_points = initial_activity_bq * np.exp(-lambda_const * time_points) * conversion_factor
            
            self._time_data_for_plot = time_points / 3600  # Conversion en heures
            self._activity_data_for_plot = activity_points
            self._activity_unit = unit_text  # Stocke l'unité pour le graphique
            self.plot_button.setEnabled(True)
            
            # Sauvegarde dans l'historique
            save_to_history([
                "Décroissance",
                f"Activité initiale: {initial_activity} {self.activity_unit.currentText()}",
                f"Date initiale: {initial_date}",
                f"Période: {self.period_seconds/3600:.1f} heures",
                f"Activité actuelle: {current_activity_gbq:.2f} GBq"
            ])
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            
    def show_decay_plot(self):
        """Affiche le graphique de décroissance avec les 10 périodes."""
        try:
            # Récupération des données initiales
            initial_activity = self.activity_input.value()
            unit_factors = {"Bq": 1, "kBq": 1e3, "MBq": 1e6, "GBq": 1e9, "TBq": 1e12}
            initial_activity_bq = initial_activity * unit_factors[self.activity_unit.currentText()]
            
            # Utilisation directe de period_seconds au lieu des widgets
            period_hours = self.period_seconds / 3600  # Conversion secondes en heures
            
            # Date initiale avec le nouveau widget QDateEdit
            selected_date = self.date_input.date()
            start_datetime = datetime(
                year=selected_date.year(),
                month=selected_date.month(),
                day=selected_date.day(),
                hour=0,  # On fixe l'heure à minuit
                minute=0,
                second=0
            )
            
            # Création du calculateur
            calculator = DecroissanceCalculator()
            calculator.initial_activity = initial_activity_bq
            calculator.half_life = period_hours
            calculator.start_datetime = start_datetime
            calculator.isotope_name = self.isotope_combo.currentText()  # Ajout du nom de l'isotope
            
            # Génération du graphique
            figure = calculator.plot_decay()
            
            # Affichage dans une nouvelle fenêtre
            plot_dialog = PlotDisplayDialog(
                figure=figure,
                parent=self
            )
            plot_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du graphique : {str(e)}")

class PlotDisplayDialog(QDialog):
    def __init__(self, figure=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graphique de décroissance")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        from matplotlib.backends.backend_qt5agg import FigureCanvas
        canvas = FigureCanvas(figure)
        layout.addWidget(canvas)
        
        # Bouton Fermer
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

class CustomPeriodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Période personnalisée")
        layout = QVBoxLayout(self)
        
        period_group = QGroupBox("Période")
        period_layout = QGridLayout()
        
        # Widgets pour la période
        self.p_year_input = ClearingSpinBox()
        self.p_month_input = ClearingSpinBox()
        self.p_day_input = ClearingSpinBox()
        self.p_hour_input = ClearingSpinBox()
        self.p_minute_input = ClearingSpinBox()
        self.p_second_input = ClearingSpinBox()
        
        # Layout
        period_layout.addWidget(QLabel("Années:"), 0, 0)
        period_layout.addWidget(self.p_year_input, 0, 1)
        period_layout.addWidget(QLabel("Mois:"), 0, 2)
        period_layout.addWidget(self.p_month_input, 0, 3)
        period_layout.addWidget(QLabel("Jours:"), 1, 0)
        period_layout.addWidget(self.p_day_input, 1, 1)
        period_layout.addWidget(QLabel("Heures:"), 1, 2)
        period_layout.addWidget(self.p_hour_input, 1, 3)
        period_layout.addWidget(QLabel("Minutes:"), 2, 0)
        period_layout.addWidget(self.p_minute_input, 2, 1)
        period_layout.addWidget(QLabel("Secondes:"), 2, 2)
        period_layout.addWidget(self.p_second_input, 2, 3)
        
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)
        
        # Boutons
        btn_layout = QHBoxLayout()
        validate_btn = QPushButton("Valider")
        validate_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(validate_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_period_seconds(self):
        return (
            self.p_year_input.value() * 365 * 24 * 3600 +
            self.p_month_input.value() * 30 * 24 * 3600 +
            self.p_day_input.value() * 24 * 3600 +
            self.p_hour_input.value() * 3600 +
            self.p_minute_input.value() * 60 +
            self.p_second_input.value()
        )
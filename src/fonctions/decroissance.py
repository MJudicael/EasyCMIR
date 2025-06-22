from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QDoubleSpinBox, QComboBox,
    QDateEdit, QMessageBox, QGridLayout
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
        
        # Calcul du DED 1m pour l'activité finale (en GBq)
        final_activity_gbq = final_activity * 1e-9
        selected_isotope = self.isotope_name  # Nouveau paramètre à ajouter
        
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
                        if name == selected_isotope:
                            e1, e2, e3 = float(values[3]), float(values[4]), float(values[5])
                            q1, q2, q3 = float(values[6]), float(values[7]), float(values[8].split(',')[0])
                            final_ded = 1.3e-10 * final_activity * (e1 * q1 + e2 * q2 + e3 * q3)
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
        
        # Formatage du débit de dose avec l'unité adaptée
        if final_ded > 1:
            ded_str = f"{final_ded:.1f} mSv/h"
        elif final_ded > 0.001:
            ded_str = f"{final_ded * 1000:.1f} µSv/h"
        else:
            ded_str = f"{final_ded * 1000000:.1f} nSv/h"

        # Ajout du point à 10 périodes avec bulle d'information
        plt.plot(end_datetime, final_activity, 'ro', label='10 périodes')
        plt.annotate(
            f'Après 10 périodes:\n'
            f'Date: {end_datetime.strftime("%d/%m/%Y %H:%M")}\n'
            f'Activité: {final_activity:.2e} Bq\n'
            f'DED à 1m: {ded_str}',
            xy=(end_datetime, final_activity),
            xytext=(0, 30),
            textcoords='offset points',
            ha='center',
            va='bottom',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
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
        self.setMinimumWidth(400)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        
        # Initialisation des variables
        self.period_seconds = 0
        self._time_data_for_plot = []
        self._activity_data_for_plot = []
        
        # Création des widgets
        self.create_input_widgets()
        self.create_period_widgets()
        self.create_date_widgets()
        
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

    def create_input_widgets(self):
        input_group = QGroupBox("Activité initiale")
        layout = QHBoxLayout()
        
        self.activity_input = QDoubleSpinBox()
        self.activity_input.setRange(0, 1e20)
        self.activity_input.setDecimals(3)
        
        # Menu déroulant des unités
        self.activity_unit = QComboBox()
        self.activity_unit.addItems(["Bq", "kBq", "MBq", "GBq", "TBq"])
        self.activity_unit.setCurrentText("Bq")
        
        layout.addWidget(QLabel("Activité:"))
        layout.addWidget(self.activity_input)
        layout.addWidget(self.activity_unit)
        
        input_group.setLayout(layout)
        self.main_layout.addWidget(input_group)

    def create_period_widgets(self):
        """Crée les widgets pour la sélection de la période."""
        period_group = QGroupBox("Période")
        layout = QVBoxLayout()
        
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
    
        layout.addWidget(self.isotope_combo)
        
        # Bouton période personnalisée
        self.custom_period_btn = QPushButton("Personnalisé")
        self.custom_period_btn.clicked.connect(self.show_custom_period)
        layout.addWidget(self.custom_period_btn)
        
        period_group.setLayout(layout)
        self.main_layout.addWidget(period_group)
        
        # Connexion du signal
        self.isotope_combo.currentIndexChanged.connect(self.update_period)

    def create_date_widgets(self):
        """Crée les widgets pour la sélection de la date."""
        date_group = QGroupBox("Date initiale")
        layout = QHBoxLayout()
        
        # Création du sélecteur de date
        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.date_input.setCalendarPopup(True)  # Active le popup calendrier
        
        # Date par défaut : 22/05/2012
        default_date = QDate(2012, 5, 22)
        self.date_input.setDate(default_date)
        
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.date_input)
        
        date_group.setLayout(layout)
        self.main_layout.addWidget(date_group)

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
            
            # Calcul de l'activité finale selon N(t) = N0 e^(-λt)
            current_activity_bq = initial_activity_bq * exp(-lambda_const * delta_seconds)
            current_activity_gbq = current_activity_bq * 1e-9
            
            # Mise à jour des résultats
            self.result_gbq_label.setText(f"{current_activity_gbq:.2f} GBq")
            self.result_bq_label.setText(f"{current_activity_bq:.2e} Bq")
            
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
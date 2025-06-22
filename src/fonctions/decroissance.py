from datetime import datetime, timedelta
from math import log, exp  # Ajout des fonctions mathématiques nécessaires
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox
)
from ..utils.widgets import ClearingDoubleSpinBox, ClearingSpinBox
from ..utils.database import save_to_history
from .plot import PlotDisplayDialog

class DecroissanceCalculator:
    def __init__(self):
        self.initial_activity = 0
        self.half_life = 0
        self.start_datetime = None
        
    def calculate_ten_periods(self, initial_activity, half_life, start_datetime=None):
        """Calcule l'activité après 10 périodes."""
        if start_datetime is None:
            start_datetime = datetime.now()
            
        self.initial_activity = initial_activity
        self.half_life = half_life
        self.start_datetime = start_datetime
        
        # Calcul de la date après 10 périodes
        ten_periods_hours = 10 * self.half_life
        end_datetime = self.start_datetime + timedelta(hours=ten_periods_hours)
        
        # Calcul de l'activité restante après 10 périodes
        remaining_activity = self.initial_activity * (0.5 ** 10)
        
        return end_datetime, remaining_activity
        
    def plot_decay(self):
        """Génère le graphique de décroissance avec indication des 10 périodes."""
        if not all([self.initial_activity, self.half_life, self.start_datetime]):
            raise ValueError("Les paramètres initiaux doivent être définis")
            
        # Calcul pour 10 périodes
        end_datetime, final_activity = self.calculate_ten_periods(
            self.initial_activity, 
            self.half_life, 
            self.start_datetime
        )
        
        # Création des points pour le graphique
        time_points = np.linspace(0, 10 * self.half_life, 1000)
        dates = [self.start_datetime + timedelta(hours=t) for t in time_points]
        activities = [self.initial_activity * (0.5 ** (t/self.half_life)) for t in time_points]
        
        # Création du graphique
        plt.figure(figsize=(12, 8))
        plt.plot(dates, activities, 'b-', label='Décroissance')
        
        # Ajout du point à 10 périodes
        plt.plot(end_datetime, final_activity, 'ro', label='10 périodes')
        
        # Annotation centrée au-dessus du point avec police plus petite
        plt.annotate(
            f'Après 10 périodes:\nDate: {end_datetime.strftime("%d/%m/%Y %H:%M")}\nActivité: {final_activity:.2e} Bq',
            xy=(end_datetime, final_activity),
            xytext=(0, 30),  # Décalage vertical uniquement
            textcoords='offset points',
            ha='center',  # Centrage horizontal
            va='bottom',  # Alignement vertical en bas
            fontsize=9,   # Taille de police à 9px
            bbox=dict(
                boxstyle='round,pad=0.5',
                fc='yellow',
                alpha=0.5,
                ec='gray'
            ),
            arrowprops=dict(
                arrowstyle='->', 
                connectionstyle='arc3,rad=0',
                color='gray'
            )
        )
        
        # Formatage du graphique
        plt.gcf().autofmt_xdate()
        plt.gca().xaxis.set_major_formatter(DateFormatter('%d/%m/%Y\n%H:%M'))
        plt.xlabel('Date et Heure')
        plt.ylabel('Activité (Bq)')
        plt.title('Décroissance Radioactive')
        plt.grid(True)
        plt.legend()
        
        return plt.gcf()

class DecroissanceDialog(QDialog):
    """Dialog pour le calcul de décroissance."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Décroissance")
        self.setFixedSize(300, 500)
        
        self.main_layout = QVBoxLayout(self)
        
        # Création des widgets
        self.create_input_widgets()
        self.create_period_widgets()
        self.create_date_widgets()
        
        # Bouton de calcul
        calc_button = QPushButton("Calculer")
        calc_button.clicked.connect(self.calculate_decay)
        self.main_layout.addWidget(calc_button)
        
        # Bouton pour le graphique
        self.plot_button = QPushButton("Afficher le graphique")
        self.plot_button.clicked.connect(self.show_decay_plot)
        self.plot_button.setEnabled(False)
        self.main_layout.addWidget(self.plot_button)
        
        # Labels pour les résultats
        result_group = QGroupBox("Résultats")
        result_layout = QVBoxLayout()
        self.result_gbq_label = QLabel()
        self.result_bq_label = QLabel()
        result_layout.addWidget(self.result_gbq_label)
        result_layout.addWidget(self.result_bq_label)
        result_group.setLayout(result_layout)
        self.main_layout.addWidget(result_group)

        # Variables pour le graphique
        self._time_data_for_plot = []
        self._activity_data_for_plot = []

    def create_input_widgets(self):
        """Crée les widgets de saisie pour le calcul de décroissance."""
        input_layout = QGridLayout()
        
        # Activité initiale
        self.activity_label = QLabel("Activité initiale :")
        self.activity_input = ClearingDoubleSpinBox()
        self.activity_input.setRange(0, 1000000)
        input_layout.addWidget(self.activity_label, 0, 0)
        input_layout.addWidget(self.activity_input, 0, 1)
        
        # Unité d'activité
        self.activity_unit = QComboBox()
        self.activity_unit.addItems(["Bq", "kBq", "MBq", "GBq", "TBq"])
        input_layout.addWidget(self.activity_unit, 0, 2)
        
        # Utilisez l'attribut main_layout au lieu de layout()
        self.main_layout.addLayout(input_layout)
        
    def create_period_widgets(self):
        period_group = QGroupBox("Période")
        period_layout = QGridLayout()
        
        # Ajout d'espacement
        period_layout.setSpacing(10)  # Espacement entre les widgets
        period_layout.setContentsMargins(10, 15, 10, 15)  # Marges intérieures
        
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
        self.main_layout.addWidget(period_group)

    def create_date_widgets(self):
        date_group = QGroupBox("Date initiale")
        date_layout = QGridLayout()
        
        # Ajout d'espacement
        date_layout.setSpacing(10)  # Espacement entre les widgets
        date_layout.setContentsMargins(10, 15, 10, 15)  # Marges intérieures
        
        # Widgets pour la date
        self.year_input = ClearingSpinBox()
        self.month_input = ClearingSpinBox()
        self.day_input = ClearingSpinBox()
        self.hour_input = ClearingSpinBox()
        self.minute_input = ClearingSpinBox()
        self.second_input = ClearingSpinBox()
        
        # Configuration des ranges
        now = datetime.now()
        self.year_input.setRange(1900, 2100)
        self.month_input.setRange(1, 12)
        self.day_input.setRange(1, 31)
        self.hour_input.setRange(0, 23)
        self.minute_input.setRange(0, 59)
        self.second_input.setRange(0, 59)
        
        # Valeurs par défaut
        self.year_input.setValue(2012)
        self.month_input.setValue(5)
        self.day_input.setValue(22)
        self.hour_input.setValue(6)
        self.minute_input.setValue(0)
        self.second_input.setValue(0)
        
        # Layout
        date_layout.addWidget(QLabel("Année:"), 0, 0)
        date_layout.addWidget(self.year_input, 0, 1)
        date_layout.addWidget(QLabel("Mois:"), 0, 2)
        date_layout.addWidget(self.month_input, 0, 3)
        date_layout.addWidget(QLabel("Jour:"), 1, 0)
        date_layout.addWidget(self.day_input, 1, 1)
        date_layout.addWidget(QLabel("Heure:"), 1, 2)
        date_layout.addWidget(self.hour_input, 1, 3)
        date_layout.addWidget(QLabel("Minute:"), 2, 0)
        date_layout.addWidget(self.minute_input, 2, 1)
        date_layout.addWidget(QLabel("Seconde:"), 2, 2)
        date_layout.addWidget(self.second_input, 2, 3)
        
        date_group.setLayout(date_layout)
        self.main_layout.addWidget(date_group)

    def calculate_decay(self):
        """Calcule la décroissance radioactive selon N(t) = N0 e^(-λt)"""
        try:
            # Récupération de l'activité initiale
            initial_activity = self.activity_input.value()
            
            # Conversion de l'activité selon l'unité choisie en Bq
            unit_factors = {"Bq": 1, "kBq": 1e3, "MBq": 1e6, "GBq": 1e9, "TBq": 1e12}
            initial_activity_bq = initial_activity * unit_factors[self.activity_unit.currentText()]
            
            # Calcul de la période en secondes
            period_seconds = (
                self.p_year_input.value() * 365 * 24 * 3600 +
                self.p_month_input.value() * 30 * 24 * 3600 +
                self.p_day_input.value() * 24 * 3600 +
                self.p_hour_input.value() * 3600 +
                self.p_minute_input.value() * 60 +
                self.p_second_input.value()
            )
            
            if period_seconds <= 0:
                QMessageBox.warning(self, "Erreur", "La période doit être supérieure à zéro")
                return
            
            # Calcul de λ (lambda) = ln(2)/T
            lambda_const = log(2) / period_seconds
            
            # Calcul du temps écoulé
            initial_date = datetime(
                year=self.year_input.value(),
                month=self.month_input.value(),
                day=self.day_input.value(),
                hour=self.hour_input.value(),
                minute=self.minute_input.value(),
                second=self.second_input.value()
            )
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
            max_plot_time = max(period_seconds * 3, delta_seconds * 1.5)
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
                f"Période: {period_seconds/3600:.1f} heures",
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
            
            # Calcul de la période en heures
            period_hours = (
                self.p_year_input.value() * 365 * 24 +
                self.p_month_input.value() * 30 * 24 +
                self.p_day_input.value() * 24 +
                self.p_hour_input.value() +
                self.p_minute_input.value() / 60 +
                self.p_second_input.value() / 3600
            )
            
            # Date initiale
            start_datetime = datetime(
                year=self.year_input.value(),
                month=self.month_input.value(),
                day=self.day_input.value(),
                hour=self.hour_input.value(),
                minute=self.minute_input.value(),
                second=self.second_input.value()
            )
            
            # Création du calculateur
            calculator = DecroissanceCalculator()
            calculator.initial_activity = initial_activity_bq
            calculator.half_life = period_hours
            calculator.start_datetime = start_datetime
            
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
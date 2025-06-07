from PySide6.QtWidgets import QDialog, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class PlotDialog(QDialog):
    def __init__(self, d1, d2, ded1, ded2, unit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualisation des distances et débits")
        self.setMinimumSize(600, 400)
        
        # Conversion des valeurs en µSv/h pour la comparaison
        conversion_factors = {
            "Sv/h": 1e6,
            "mSv/h": 1e3,
            "µSv/h": 1,
            "nSv/h": 1e-3,
            "pSv/h": 1e-6,
            "R/h": 1e4,
            "mR/h": 10,
            "µR/h": 0.01,
            "Rad/h": 1e4,
            "mRad/h": 10,
            "µRad/h": 0.01,
            "Rem/h": 1e4,
            "mRem/h": 10
        }
        
        # Conversion en µSv/h pour le calcul
        factor = conversion_factors.get(unit, 1)
        ded1_converted = ded1 * factor
        ded2_converted = ded2 * factor
        
        layout = QVBoxLayout(self)
        
        # Création de la figure en mode polaire
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        # Calcul du point seuil
        d_threshold = d1 * np.sqrt(ded1_converted / 2.5)
        
        # Création des cercles pour chaque distance
        theta = np.linspace(0, 2*np.pi, 100)
        
        # Cercles de distance
        distances = [d1, d2, d_threshold]
        debits = [ded1_converted, ded2_converted, 2.5]
        colors = ['blue', 'blue', 'red']
        styles = ['-', '-', '--']
        
        # Tracer les cercles
        for d, debit, color, style in zip(distances, debits, colors, styles):
            ax.plot(theta, [d]*len(theta), color=color, linestyle=style, alpha=0.5)
        
        # Zones colorées
        if max(debits) > 2.5:
            # Zone orange pour débit > 2.5 µSv/h
            ax.fill_between(theta, 0, d_threshold, color='orange', alpha=0.2)
            # Zone verte pour débit ≤ 2.5 µSv/h
            ax.fill_between(theta, d_threshold, max(distances)*1.1, color='green', alpha=0.2)
        
        # Points de mesure
        ax.scatter([0, 0], [d1, d2], color='blue', s=100, label='Points de mesure')
        ax.scatter(0, d_threshold, color='red', marker='s', s=100, label='Périmètre public')
        
        # Annotations avec les valeurs séparées
        # Point initial
        ax.annotate(f"{ded1} {unit}", (0, d1), 
                   xytext=(0.2, d1), textcoords='data', fontsize=9,
                   va='bottom')  # Débit au-dessus
        ax.annotate(f"{d1} m", (0, d1), 
                   xytext=(0.2, d1), textcoords='data', fontsize=9,
                   va='top')    # Distance en-dessous
        
        # Point calculé
        ax.annotate(f"{ded2} {unit}", (0, d2), 
                   xytext=(0.2, d2), textcoords='data', fontsize=9,
                   va='bottom')  # Débit au-dessus
        ax.annotate(f"{d2} m", (0, d2), 
                   xytext=(0.2, d2), textcoords='data', fontsize=9,
                   va='top')    # Distance en-dessous
        
        # Point seuil
        ax.annotate("2.5 µSv/h", (0, d_threshold), 
                   xytext=(0.2, d_threshold), textcoords='data', fontsize=9,
                   va='bottom')  # Débit au-dessus
        ax.annotate(f"{d_threshold:.2f} m", (0, d_threshold), 
                   xytext=(0.2, d_threshold), textcoords='data', fontsize=9,
                   va='top')    # Distance en-dessous
        
        # Configuration du graphique
        ax.set_theta_zero_location('N')  # 0° au Nord
        ax.set_theta_direction(-1)       # Sens horaire
        ax.set_rticks([])  # Supprime les marques de distance automatiques
        ax.grid(True)
        
        # Supprime les graduations angulaires
        ax.set_xticks([])
        
        # Ajustement de la taille des labels des axes
        ax.tick_params(axis='both', which='major', labelsize=9)
        
        # Légende avec taille de police réduite
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
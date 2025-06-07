from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotDisplayDialog(QDialog):
    def __init__(self, time_data_hours, activity_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graphique de Décroissance")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Configuration du graphique
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Récupération de l'unité depuis le parent
        activity_unit = parent._activity_unit if hasattr(parent, '_activity_unit') else 'Bq'
        
        # Tracé de la courbe avec la bonne unité
        self.plot_decay_curve(time_data_hours, activity_data, activity_unit)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def plot_decay_curve(self, time_data_hours, activity_data, activity_unit):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.plot(time_data_hours, activity_data)
        ax.set_title("Décroissance Radioactive")
        ax.set_xlabel("Temps (heures)")
        ax.set_ylabel(f"Activité ({activity_unit})")
        ax.grid(True)
        
        # Échelle logarithmique pour l'activité
        ax.set_yscale('log')
        
        self.canvas.draw()
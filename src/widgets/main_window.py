from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QMenu, QMenuBar
)
from PySide6.QtCore import Qt

from ..dialogs.decroissance import DecroissanceDialog
from ..dialogs.ded1m import Ded1mDialog
from ..dialogs.distance import DistanceDialog
from ..dialogs.news import NewsDialog
from ..dialogs.p_public import PerimetrePublicDialog  # Correction ici
from ..dialogs.tmr import TMRDialog
from ..dialogs.unites_rad import UnitesRadDialog
from ..dialogs.about import AboutDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyCMIR 1.4")
        self.setFixedSize(350, 100)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Layout pour les boutons
        button_grid = QGridLayout()
        
        # Création des boutons
        self.create_buttons(button_grid)
        
        layout.addLayout(button_grid)
        
        # Création du menu
        self.create_menu()

    def create_buttons(self, layout):
        buttons = [
            ("Décroissance", self.run_decroissance, 0, 0),
            ("DED 1m", self.run_ded1m, 0, 1),
            ("P Public", self.run_p_public, 0, 2),
            ("TMR", self.run_tmr, 1, 0),
            ("Distance", self.run_distance, 1, 1),
            ("Unités RAD", self.run_unites_rad, 1, 2)
        ]
        
        for text, slot, row, col in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn, row, col)

    def create_menu(self):
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        actions = [
            ("Décroissance", self.run_decroissance),
            ("Débit de dose 1m", self.run_ded1m),
            ("Périmètre public", self.run_p_public),
            ("TMR", self.run_tmr),
            ("Distance", self.run_distance),
            ("Unités RAD", self.run_unites_rad)
        ]
        
        for text, slot in actions:
            action = file_menu.addAction(text)
            action.triggered.connect(slot)
            
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        about_action = help_menu.addAction("A propos...")
        about_action.triggered.connect(self.run_about)
        news_action = help_menu.addAction("News ASNR")
        news_action.triggered.connect(self.run_news)

    def run_decroissance(self):
        dialog = DecroissanceDialog(self)
        dialog.exec()

    def run_ded1m(self):
        dialog = Ded1mDialog(self)
        dialog.exec()

    def run_distance(self):
        dialog = DistanceDialog(self)
        dialog.exec()

    def run_p_public(self):
        dialog = PerimetrePublicDialog(self)
        dialog.exec()

    def run_tmr(self):
        dialog = TMRDialog(self)
        dialog.exec()

    def run_unites_rad(self):
        dialog = UnitesRadDialog(self)
        dialog.exec()

    def run_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def run_news(self):
        dialog = NewsDialog(self)
        dialog.exec()
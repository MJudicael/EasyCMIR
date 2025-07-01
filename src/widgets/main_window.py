from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QMenu, QMenuBar, QToolButton
)
from PySide6.QtCore import Qt, QSize
from src.utils.icon_manager import IconManager

# Import des dialogues RAD
from ..fonctions.decroissance import DecroissanceDialog
from ..fonctions.ded1m import Ded1mDialog
from ..fonctions.distance import DistanceDialog
from ..fonctions.p_public import PerimetrePublicDialog
from ..fonctions.tmr import TMRDialog
from ..fonctions.unites_rad import UnitesRadDialog

# Import des dialogues RCH
from ..fonctions.codedanger import CodeDangerDialog
from ..fonctions.ecran import EcranDialog
from ..fonctions.bio import BioDialog
from ..fonctions.gestion_matériel import BD_gestDialog
from ..fonctions.gestion_matériel import BD_gestDialog
from ..fonctions.tmd import TMDDialog
from ..fonctions.intervention import InterventionDialog

# Import des dialogues du menu Aide
from ..fonctions.about import AboutDialog
from ..fonctions.news import NewsDialog
from ..fonctions.configuration import ConfigurationDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyCMIR")
        
        # Initialisation du gestionnaire d'icônes
        self.icon_manager = IconManager()
        
        # Création du widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        
        # Création de la grille unique pour tous les boutons
        buttons_grid = self.create_buttons_grid()
        
        # Ajout de la grille au layout principal
        main_layout.addLayout(buttons_grid)
        
        self.create_menu()

    def create_buttons_grid(self):
        """Crée une grille unifiée avec tous les boutons"""
        grid = QGridLayout()
        
        # Tous les boutons dans une seule liste
        all_buttons = [
            # 1ère ligne : Décroissance, DED 1m, P Public
            ("Décroissance", self.run_decroissance, 0, 0),
            ("DED 1m", self.run_ded1m, 0, 1),
            ("P Public", self.run_p_public, 0, 2),
            # 2ème ligne : Distance, Ecran, Unités RAD
            ("Distance", self.run_distance, 1, 0),
            ("Ecran", self.run_ecran, 1, 1),
            ("Unités RAD", self.run_unites_rad, 1, 2),
            # 3ème ligne : TMR, TMD, Intervention
            ("TMR", self.run_tmr, 2, 0),
            ("TMD", self.run_tmd, 2, 1),
            ("Intervention", self.run_intervention, 2, 2),
            # 4ème ligne : Code DANGER, Bio, Matériel
            ("Code DANGER", self.run_code_danger, 3, 0),
            ("Bio", self.run_bio, 3, 1),
            ("Matériel", self.run_BD_gest, 3, 2)
        ]
        
        for text, slot, row, col in all_buttons:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            
            icon = self.icon_manager.get_icon(text)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(32, 32))
            
            btn.setMinimumSize(QSize(100, 80))
            btn.clicked.connect(slot)
            grid.addWidget(btn, row, col)
        
        return grid

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
        help_menu.addSeparator()
        config_action = help_menu.addAction("Configuration")
        config_action.triggered.connect(self.run_configuration)

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

    def run_configuration(self):
        dialog = ConfigurationDialog(self)
        dialog.exec()

    def run_code_danger(self):
        """Lance la fenêtre Code Danger."""
        dialog = CodeDangerDialog(self)
        dialog.exec()

    def run_ecran(self):
        dialog = EcranDialog(self)
        dialog.exec()

    def run_bio(self):
        dialog = BioDialog(self)
        dialog.exec()

    def run_BD_gest(self):
        dialog = BD_gestDialog(self)
    def run_BD_gest(self):
        dialog = BD_gestDialog(self)
        dialog.exec()

    def run_tmd(self):
        dialog = TMDDialog(self)
        dialog.exec()

    def run_intervention(self):
        dialog = InterventionDialog(self)
        dialog.exec()

    def show_intervention_dialog(self):
        """Ouvre la fenêtre d'intervention"""
        dialog = InterventionDialog(self)
        dialog.setWindowModality(Qt.NonModal)  # Permet l'interaction avec la fenêtre principale
        dialog.show()  # Utiliser show() au lieu de exec() pour un dialogue non-modal
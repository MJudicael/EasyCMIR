from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QGridLayout, QToolButton, QGroupBox
)
<<<<<<< HEAD
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize  # Ajout de QSize
from ..utils.icon_manager import IconManager
from ..fonctions.codeonu import CodeONUDialog
=======
from PySide6.QtCore import Qt, QSize
from ..utils.icon_manager import IconManager
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8

# Import des dialogues RAD
from ..fonctions.decroissance import DecroissanceDialog
from ..fonctions.ded1m import Ded1mDialog
from ..fonctions.distance import DistanceDialog
from ..fonctions.p_public import PerimetrePublicDialog
from ..fonctions.tmr import TMRDialog
from ..fonctions.unites_rad import UnitesRadDialog

# Import des dialogues RCH
<<<<<<< HEAD
from ..fonctions.codeonu import CodeONUDialog
from ..fonctions.identification import IdentificationDialog
from ..fonctions.bio import BioDialog
from ..fonctions.PID import PIDDialog
=======
from ..fonctions.codedanger import CodeDangerDialog
from ..fonctions.identification import IdentificationDialog
from ..fonctions.bio import BioDialog
from ..fonctions.divers import DiversDialog
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8
from ..fonctions.tmd import TMDDialog
from ..fonctions.intervention import InterventionDialog

# Import des dialogues du menu Aide
from ..fonctions.about import AboutDialog
from ..fonctions.news import NewsDialog

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
        
        # Création des sections RAD et RCH
        rad_section = self.create_rad_section()
        rch_section = self.create_rch_section()
        
<<<<<<< HEAD
        # Utiliser addWidget au lieu de addLayout pour les QGroupBox
        main_layout.addWidget(rad_section)
        main_layout.addWidget(rch_section)
=======
        # Ajout des sections au layout principal
        main_layout.addLayout(rad_section)
        main_layout.addLayout(rch_section)
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8
        
        self.create_menu()

    def create_rad_section(self):
<<<<<<< HEAD
        """Crée la section RAD."""
        group = QGroupBox("RAD")
        layout = QGridLayout()

        # Configuration des boutons RAD
        rad_buttons = [
            ("Décroissance", self.run_decroissance),
            ("Distance", self.run_distance),
            ("DED 1m", self.run_ded1m),
            ("P Public", self.run_p_public),
            ("TMR", self.run_tmr),
            ("Unités RAD", self.run_unites_rad)
=======
        # Création du conteneur pour la section RAD
        rad_layout = QVBoxLayout()
        
        # Titre RAD
        rad_title = QLabel("RAD")
        rad_title.setAlignment(Qt.AlignCenter)
        rad_title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        rad_layout.addWidget(rad_title)
        
        # Grid pour les boutons RAD
        rad_grid = QGridLayout()
        
        # Boutons RAD existants
        buttons = [
            ("Décroissance", self.run_decroissance, 0, 0),
            ("DED 1m", self.run_ded1m, 0, 1),
            ("P Public", self.run_p_public, 0, 2),
            ("TMR", self.run_tmr, 1, 0),
            ("Distance", self.run_distance, 1, 1),
            ("Unités RAD", self.run_unites_rad, 1, 2)
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8
        ]

        # Création des boutons dans une grille 2x3
        for i, (text, callback) in enumerate(rad_buttons):
            btn = QToolButton()
            icon = self.icon_manager.get_icon(text)
            btn.setIcon(icon)
            btn.setIconSize(QSize(32, 32))
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
<<<<<<< HEAD
            btn.setMinimumSize(QSize(100, 80))
            btn.clicked.connect(callback)
            
            # Modification ici : changement du calcul de row et col
            row = i // 3  # Division entière par 3 pour obtenir la ligne
            col = i % 3   # Modulo 3 pour obtenir la colonne
            layout.addWidget(btn, row, col)
=======
            
            icon = self.icon_manager.get_icon(text)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(32, 32))
            
            btn.setMinimumSize(QSize(100, 80))
            btn.clicked.connect(slot)
            rad_grid.addWidget(btn, row, col)
        
        rad_layout.addLayout(rad_grid)
        return rad_layout

    def create_rch_section(self):
        # Création du conteneur pour la section RCH
        rch_layout = QVBoxLayout()
        
        # Titre RCH
        rch_title = QLabel("RCH")
        rch_title.setAlignment(Qt.AlignCenter)
        rch_title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        rch_layout.addWidget(rch_title)
        
        # Grid pour les boutons RCH
        rch_grid = QGridLayout()
        
        # Configuration des boutons RCH
        rch_buttons = [
            ("Identification", self.run_identification),
            ("Code DANGER", self.run_code_danger),
            ("Bio", self.run_bio),
            ("Divers", self.run_divers),
            ("TMD", self.run_tmd),
            ("Intervention", self.run_intervention)
        ]
        
        # Création des boutons
        row = col = 0
        
        for text, slot in rch_buttons:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            
            # Obtenir l'icône
            icon = self.icon_manager.get_icon(text)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(32, 32))
            
            # Important : Connecter le signal clicked au slot
            if slot is not None:
                btn.clicked.connect(slot)
            
            btn.setMinimumSize(QSize(100, 80))
            rch_grid.addWidget(btn, row, col)
            
            col += 1
            if col > 2:  # 3 boutons par ligne
                col = 0
                row += 1
                
        rch_layout.addLayout(rch_grid)
        return rch_layout
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8

        group.setLayout(layout)
        return group

    def create_rch_section(self):
        """Crée la section RCH"""
        group = QGroupBox("RCH")
        layout = QGridLayout()

        # Configuration des boutons RCH
        rch_buttons = [
            ("Identification", self.run_identification),
            ("Code DANGER", self.run_code_danger),
            ("Bio", self.run_bio),
            ("PID", self.run_PID),
            ("TMD", self.run_tmd),
            ("Intervention", self.run_intervention)
        ]

        # Création des boutons dans une grille 3x2
        for i, (text, callback) in enumerate(rch_buttons):
            btn = QToolButton()
            icon = self.icon_manager.get_icon(text)
            btn.setIcon(icon)
            btn.setIconSize(QSize(32, 32))
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setMinimumSize(QSize(100, 80))
            btn.clicked.connect(callback)
            
            row = i // 3
            col = i % 3
            layout.addWidget(btn, row, col)

        group.setLayout(layout)
        return group  # Retourne le QGroupBox au lieu du layout

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
        
        # Menu Recherche
        menu_rech = self.menuBar().addMenu("Recherche")
        
        action_codes = QAction("Recherche Codes", self)
        action_codes.triggered.connect(self.run_code_search)
        menu_rech.addAction(action_codes)

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

    def run_code_danger(self):
        """Lance la fenêtre Code Danger."""
<<<<<<< HEAD
        dialog = CodeONUDialog(self)  # Changement de CodeDangerDialog à CodeONUDialog
=======
        dialog = CodeDangerDialog(self)
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8
        dialog.exec()

    def run_identification(self):
        dialog = IdentificationDialog(self)
        dialog.exec()

    def run_bio(self):
        dialog = BioDialog(self)
        dialog.exec()

<<<<<<< HEAD
    def run_PID(self):
        dialog = PIDDialog(self)
=======
    def run_divers(self):
        dialog = DiversDialog(self)
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8
        dialog.exec()

    def run_tmd(self):
        dialog = TMDDialog(self)
        dialog.exec()

    def run_intervention(self):
        dialog = InterventionDialog(self)
<<<<<<< HEAD
        dialog.exec()

    def run_code_search(self):
        """Ouvre la fenêtre de recherche de codes"""
        dialog = CodeONUDialog(self)
        dialog.exec()

    def run_rad_identification(self):
        """Lance la fenêtre d'Identification RAD."""
        dialog = IdentificationDialog(self)
        dialog.exec()

    def run_rad_irradiation(self):
        """Lance la fenêtre d'Irradiation RAD."""
        dialog = BioDialog(self)
        dialog.exec()

    def run_rad_contamination(self):
        """Lance la fenêtre de Contamination RAD."""
        dialog = PIDDialog(self)
        dialog.exec()

    def run_rad_intervention(self):
        """Lance la fenêtre d'Intervention RAD."""
        dialog = InterventionDialog(self)
=======
>>>>>>> 1910f35c16d38685cbb0fcdaf23be3b01fd424c8
        dialog.exec()
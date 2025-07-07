from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QMenu, QMenuBar, QToolButton, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from src.utils.icon_manager import IconManager
from ..utils.auth_manager import auth_manager

# Import des dialogues RAD
from ..fonctions.decroissance import DecroissanceDialog
from ..fonctions.ded1m import Ded1mDialog
from ..fonctions.distance import DistanceDialog
from ..fonctions.p_public import PerimetrePublicDialog
from ..fonctions.tmr import TMRDialog
from ..fonctions.unites_rad import UnitesRadDialog

# Import des dialogues RCH
from ..fonctions.ecran import EcranDialog
from ..fonctions.RH import RHDialog
from ..fonctions.gestion_matériel import open_gestion_materiel
from ..fonctions.activite_origin import ActiviteOriginDialog
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
            # 1ère ligne 
            ("Décroissance", self.run_decroissance, 0, 0),
            ("DED 1m", self.run_ded1m, 0, 1),
            ("P Public", self.run_p_public, 0, 2),
            # 2ème ligne 
            ("Distance", self.run_distance, 1, 0),
            ("Ecran", self.run_ecran, 1, 1),
            ("Unités RAD", self.run_unites_rad, 1, 2),
            # 3ème ligne 
            ("TMR", self.run_tmr, 2, 0),
            ("Activité", self.run_activite_origin, 2, 1),
            ("Intervention", self.run_intervention, 2, 2)
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
        
        # Menu Gestion
        gestion_menu = menubar.addMenu("Gestion")
        
        # Action Gestion RH avec raccourci clavier et icône
        rh_action = gestion_menu.addAction("Gestion RH")
        rh_action.setShortcut("Ctrl+R")
        rh_icon = self.icon_manager.get_icon("Gestion RH")
        if rh_icon:
            rh_action.setIcon(rh_icon)
        rh_action.triggered.connect(self.run_rh)
        
        # Action Matériel avec raccourci clavier et icône
        materiel_action = gestion_menu.addAction("Matériel")
        materiel_action.setShortcut("Ctrl+M")
        materiel_icon = self.icon_manager.get_icon("Matériel")
        if materiel_icon:
            materiel_action.setIcon(materiel_icon)
        materiel_action.triggered.connect(self.run_BD_gest)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        about_action = help_menu.addAction("A propos...")
        about_action.triggered.connect(self.run_about)
        news_action = help_menu.addAction("News ASNR")
        news_action.triggered.connect(self.run_news)
        help_menu.addSeparator()
        config_action = help_menu.addAction("Configuration")
        config_action.triggered.connect(self.run_configuration)
        
        # Menu Utilisateur (si connecté)
        if auth_manager.is_authenticated():
            user_menu = menubar.addMenu(f"👤 {auth_manager.get_current_user()['username']}")
            logout_action = user_menu.addAction("🚪 Se déconnecter")
            logout_action.triggered.connect(self.logout)

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

    def run_ecran(self):
        dialog = EcranDialog(self)
        dialog.exec()

    def run_rh(self):
        dialog = RHDialog(self)
        dialog.exec()

    def run_BD_gest(self):
        open_gestion_materiel(self)

    def run_activite_origin(self):
        dialog = ActiviteOriginDialog(self)
        dialog.exec()

    def run_intervention(self):
        dialog = InterventionDialog(self)
        dialog.exec()

    def show_intervention_dialog(self):
        """Ouvre la fenêtre d'intervention"""
        dialog = InterventionDialog(self)
        dialog.setWindowModality(Qt.NonModal)  # Permet l'interaction avec la fenêtre principale
        dialog.show()  # Utiliser show() au lieu de exec() pour un dialogue non-modal
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application principale"""
        # Vérifier s'il y a une intervention en cours
        from ..fonctions.intervention import load_intervention_state, clear_intervention_state
        
        intervention_state = load_intervention_state()
        
        if intervention_state and intervention_state.get("current_file"):
            # Il y a une intervention en cours
            reply = QMessageBox.question(
                self,
                "Fermeture de l'application",
                "Une intervention est en cours.\n\n"
                "Que voulez-vous faire ?\n\n"
                "• Fermer sans terminer : L'intervention reprendra au prochain démarrage\n"
                "• Terminer l'intervention : L'intervention sera définitivement terminée\n"
                "• Annuler : Continuer à utiliser l'application",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                # Annuler la fermeture
                event.ignore()
                return
            elif reply == QMessageBox.Discard:
                # Terminer l'intervention avant de fermer
                from datetime import datetime
                import os
                
                try:
                    # Ajouter une entrée de fin dans le fichier d'intervention
                    current_file = intervention_state.get("current_file")
                    start_datetime = intervention_state.get("start_datetime")
                    
                    if isinstance(start_datetime, str):
                        from datetime import datetime
                        start_datetime = datetime.fromisoformat(start_datetime)
                    
                    end_entry = {
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "name": "SYSTEM",
                        "team": "-",
                        "entry": "-",
                        "exit": datetime.now().strftime("%H:%M"),
                        "dose": "0",
                        "comment": f"Intervention du {start_datetime.strftime('%d/%m/%Y %H:%M')} terminée à la fermeture de l'application"
                    }
                    
                    if current_file and os.path.exists(current_file):
                        with open(current_file, 'a', encoding='utf-8') as f:
                            f.write(f"{';'.join(end_entry.values())}\n")
                except Exception:
                    pass  # Ignorer les erreurs lors de la fermeture
                
                # Supprimer l'état sauvegardé
                clear_intervention_state()
                
                # Continuer la fermeture
                event.accept()
            else:  # Save
                # Fermer sans terminer l'intervention (elle reprendra au prochain démarrage)
                event.accept()
        else:
            # Pas d'intervention en cours, demander confirmation simple
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Fermeture de l'application")
            msg_box.setText("Voulez-vous vraiment fermer EasyCMIR ?")
            msg_box.setIcon(QMessageBox.Icon.Question)
            
            # Boutons en français
            btn_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
            btn_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(btn_non)  # Non par défaut
            
            msg_box.exec()
            
            if msg_box.clickedButton() == btn_oui:
                event.accept()
            else:
                event.ignore()
    
    def logout(self):
        """Déconnecte l'utilisateur actuel"""
        reply = QMessageBox.question(
            self,
            "Déconnexion",
            "Voulez-vous vraiment vous déconnecter ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            auth_manager.logout()
            QMessageBox.information(self, "Déconnexion", "Vous avez été déconnecté avec succès.")
            # Recréer le menu pour retirer le menu utilisateur
            self.menuBar().clear()
            self.create_menu()
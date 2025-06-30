from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTabWidget, QWidget,
    QLineEdit, QMessageBox, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import os
from ..utils.config_manager import config_manager

class ConfigurationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setMinimumSize(500, 400)
        self.setup_ui()
        # Charger la configuration existante
        self.load_current_config()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Création des onglets
        tab_widget = QTabWidget()
        
        # Onglet Général (vide pour usage futur)
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "Général")
        
        # Onglet Chemins
        paths_tab = self.create_paths_tab()
        tab_widget.addTab(paths_tab, "Chemins")
        
        layout.addWidget(tab_widget)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        # Obtenir le chemin des icônes
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        icons_path = os.path.join(project_root, "resources", "icons")
        
        ok_button = QPushButton("OK")
        ok_button.setIcon(QIcon(os.path.join(icons_path, "angle-cercle-vers-le-bas.png")))
        ok_button.setIconSize(ok_button.iconSize())
        ok_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.setIcon(QIcon(os.path.join(icons_path, "croix-cercle.png")))
        cancel_button.setIconSize(cancel_button.iconSize())
        cancel_button.clicked.connect(self.reject)
        
        apply_button = QPushButton("Appliquer")
        apply_button.setIcon(QIcon(os.path.join(icons_path, "angle-cercle-vers-le-bas.png")))
        apply_button.setIconSize(apply_button.iconSize())
        apply_button.clicked.connect(self.apply_settings)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(apply_button)
        
        layout.addLayout(buttons_layout)
    
    def create_general_tab(self):
        """Crée l'onglet des paramètres généraux (vide pour usage futur)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Onglet vide avec un message d'information
        info_label = QLabel("Cet onglet est réservé pour de futurs paramètres généraux.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray; font-style: italic; padding: 50px;")
        
        layout.addWidget(info_label)
        layout.addStretch()
        
        return widget
    
    def create_paths_tab(self):
        """Crée l'onglet des chemins des fichiers"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Groupe Base de données matériel
        db_group = QGroupBox("Base de données matériel")
        db_layout = QFormLayout()
        
        # Chemin de la base de données
        db_path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        # Chemin depuis la configuration
        self.db_path_edit.setText(config_manager.get_database_path())
        
        db_browse_btn = QPushButton("Parcourir...")
        db_browse_btn.clicked.connect(self.browse_database_path)
        
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(db_browse_btn)
        
        db_layout.addRow("Chemin de la base de données:", db_path_layout)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Groupe Fichiers isotopes
        isotopes_group = QGroupBox("Fichier des isotopes")
        isotopes_layout = QFormLayout()
        
        # Chemin du fichier isotopes
        isotopes_path_layout = QHBoxLayout()
        self.isotopes_path_edit = QLineEdit()
        # Chemin depuis la configuration
        self.isotopes_path_edit.setText(config_manager.get_isotopes_path())
        
        isotopes_browse_btn = QPushButton("Parcourir...")
        isotopes_browse_btn.clicked.connect(self.browse_isotopes_path)
        
        isotopes_path_layout.addWidget(self.isotopes_path_edit)
        isotopes_path_layout.addWidget(isotopes_browse_btn)
        
        isotopes_layout.addRow("Chemin du fichier isotopes.txt:", isotopes_path_layout)
        isotopes_group.setLayout(isotopes_layout)
        layout.addWidget(isotopes_group)
        
        # Groupe Interventions
        interventions_group = QGroupBox("Dossier des interventions")
        interventions_layout = QFormLayout()
        
        # Chemin du dossier interventions
        interventions_path_layout = QHBoxLayout()
        self.interventions_path_edit = QLineEdit()
        # Chemin depuis la configuration
        self.interventions_path_edit.setText(config_manager.get_interventions_path())
        
        interventions_browse_btn = QPushButton("Parcourir...")
        interventions_browse_btn.clicked.connect(self.browse_interventions_path)
        
        interventions_path_layout.addWidget(self.interventions_path_edit)
        interventions_path_layout.addWidget(interventions_browse_btn)
        
        interventions_layout.addRow("Dossier de sauvegarde des interventions:", interventions_path_layout)
        interventions_group.setLayout(interventions_layout)
        layout.addWidget(interventions_group)
        
        # Bouton pour réinitialiser aux valeurs par défaut
        reset_btn = QPushButton("Réinitialiser aux chemins par défaut")
        reset_btn.clicked.connect(self.reset_default_paths)
        layout.addWidget(reset_btn)
        
        # Espaceur pour pousser le contenu vers le haut
        layout.addStretch()
        
        return widget
    
    def browse_database_path(self):
        """Ouvre un dialogue pour choisir le fichier de base de données"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner la base de données matériel",
            self.db_path_edit.text(),
            "Fichiers de base de données (*.db *.sqlite *.sqlite3);;Tous les fichiers (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def browse_isotopes_path(self):
        """Ouvre un dialogue pour choisir le fichier des isotopes"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le fichier des isotopes",
            self.isotopes_path_edit.text(),
            "Fichiers texte (*.txt);;Tous les fichiers (*)"
        )
        if file_path:
            self.isotopes_path_edit.setText(file_path)
    
    def browse_interventions_path(self):
        """Ouvre un dialogue pour choisir le dossier des interventions"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier des interventions",
            self.interventions_path_edit.text()
        )
        if dir_path:
            self.interventions_path_edit.setText(dir_path)
    
    def reset_default_paths(self):
        """Remet les chemins par défaut"""
        # Chemins par défaut
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        default_db_path = os.path.join(project_root, "data", "materiel.db")
        default_isotopes_path = os.path.join(project_root, "data", "isotopes.txt")
        default_interventions_path = os.path.join(project_root, "interventions")
        
        self.db_path_edit.setText(default_db_path)
        self.isotopes_path_edit.setText(default_isotopes_path)
        self.interventions_path_edit.setText(default_interventions_path)
        
        QMessageBox.information(self, "Configuration", "Chemins réinitialisés aux valeurs par défaut!")
    
    def apply_settings(self):
        """Applique les paramètres sans fermer la fenêtre"""
        # Validation des chemins
        if not self.validate_paths():
            return
        
        # Sauvegarder les paramètres dans la configuration
        self.save_current_config()
        
        QMessageBox.information(self, "Configuration", "Paramètres appliqués et sauvegardés avec succès!")
    
    def load_current_config(self):
        """Charge la configuration actuelle dans l'interface"""
        # L'onglet Général est vide, pas de configuration à charger
        # Les chemins sont déjà chargés dans create_paths_tab()
        pass
    
    def save_current_config(self):
        """Sauvegarde la configuration actuelle depuis l'interface"""
        # L'onglet Général est vide, pas de configuration à sauvegarder
        
        # Onglet Chemins
        config_manager.set_database_path(self.db_path_edit.text().strip())
        config_manager.set_isotopes_path(self.isotopes_path_edit.text().strip())
        config_manager.set_interventions_path(self.interventions_path_edit.text().strip())
        
        # Sauvegarder dans le fichier
        config_manager.save_config()
    
    def validate_paths(self):
        """Valide que les chemins spécifiés sont corrects"""
        # Vérification de la base de données
        db_path = self.db_path_edit.text().strip()
        if db_path and not os.path.exists(os.path.dirname(db_path)):
            QMessageBox.warning(self, "Erreur", f"Le dossier parent de la base de données n'existe pas:\n{os.path.dirname(db_path)}")
            return False
        
        # Vérification du fichier isotopes
        isotopes_path = self.isotopes_path_edit.text().strip()
        if isotopes_path and not os.path.exists(isotopes_path):
            QMessageBox.warning(self, "Erreur", f"Le fichier des isotopes n'existe pas:\n{isotopes_path}")
            return False
        
        # Vérification du dossier interventions
        interventions_path = self.interventions_path_edit.text().strip()
        if interventions_path and not os.path.exists(interventions_path):
            reply = QMessageBox.question(
                self, 
                "Dossier inexistant", 
                f"Le dossier des interventions n'existe pas:\n{interventions_path}\n\nVoulez-vous le créer?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(interventions_path, exist_ok=True)
                    QMessageBox.information(self, "Succès", f"Dossier créé avec succès:\n{interventions_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Impossible de créer le dossier:\n{str(e)}")
                    return False
            else:
                return False
        
        return True
    
    def accept(self):
        """Applique les paramètres et ferme la fenêtre"""
        self.apply_settings()
        super().accept()

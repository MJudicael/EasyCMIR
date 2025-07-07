from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QWidget,
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
        
        # Contenu des chemins directement dans la fenêtre
        paths_content = self.create_paths_content()
        layout.addWidget(paths_content)
        
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
    
    def create_paths_content(self):
        """Crée le contenu des chemins des fichiers"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Groupe Base de données matériel SQLite
        db_group = QGroupBox("Base de données matériel (SQLite)")
        db_layout = QFormLayout()
        
        # Chemin du fichier SQLite
        db_path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        # Chemin depuis la configuration
        self.db_path_edit.setText(config_manager.get_database_path())
        
        db_browse_btn = QPushButton("Parcourir...")
        db_browse_btn.clicked.connect(self.browse_materiel_db_path)
        
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(db_browse_btn)
        
        db_layout.addRow("Chemin du fichier materiel.db:", db_path_layout)
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
        
        # Groupe Base RH
        rh_group = QGroupBox("Base de données RH")
        rh_layout = QFormLayout()
        
        # Chemin de la base RH
        rh_path_layout = QHBoxLayout()
        self.rh_path_edit = QLineEdit()
        # Chemin depuis la configuration
        self.rh_path_edit.setText(config_manager.get_rh_database_path())
        
        rh_browse_btn = QPushButton("Parcourir...")
        rh_browse_btn.clicked.connect(self.browse_rh_path)
        
        rh_path_layout.addWidget(self.rh_path_edit)
        rh_path_layout.addWidget(rh_browse_btn)
        
        rh_layout.addRow("Chemin de la base de données RH:", rh_path_layout)
        rh_group.setLayout(rh_layout)
        layout.addWidget(rh_group)
        
        # Bouton pour réinitialiser aux valeurs par défaut
        reset_btn = QPushButton("Réinitialiser aux chemins par défaut")
        reset_btn.clicked.connect(self.reset_default_paths)
        layout.addWidget(reset_btn)
        
        # Espaceur pour pousser le contenu vers le haut
        layout.addStretch()
        
        return widget
    
    def browse_materiel_db_path(self):
        """Ouvre un dialogue pour choisir le fichier materiel.db"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le fichier materiel.db",
            self.db_path_edit.text(),
            "Fichiers SQLite (*.db *.sqlite *.sqlite3);;Tous les fichiers (*)"
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
    
    def browse_rh_path(self):
        """Ouvre un dialogue pour choisir la base de données RH"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner la base de données RH",
            self.rh_path_edit.text(),
            "Fichiers de base de données (*.db *.sqlite *.sqlite3);;Tous les fichiers (*)"
        )
        if file_path:
            self.rh_path_edit.setText(file_path)
    
    def reset_default_paths(self):
        """Remet les chemins par défaut"""
        # Chemins par défaut
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        default_db_path = os.path.join(project_root, "data", "materiel.db")
        default_isotopes_path = os.path.join(project_root, "data", "isotopes.txt")
        default_interventions_path = os.path.join(project_root, "interventions")
        default_rh_path = os.path.join(project_root, "data", "RH.db")
        
        self.db_path_edit.setText(default_db_path)
        self.isotopes_path_edit.setText(default_isotopes_path)
        self.interventions_path_edit.setText(default_interventions_path)
        self.rh_path_edit.setText(default_rh_path)
        
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
        # Les chemins sont déjà chargés dans create_paths_content()
        pass
    
    def save_current_config(self):
        """Sauvegarde la configuration actuelle depuis l'interface"""
        # Sauvegarde des chemins
        config_manager.set_database_path(self.db_path_edit.text().strip())
        config_manager.set_isotopes_path(self.isotopes_path_edit.text().strip())
        config_manager.set_interventions_path(self.interventions_path_edit.text().strip())
        config_manager.set_rh_database_path(self.rh_path_edit.text().strip())
        
        # Sauvegarder dans le fichier
        config_manager.save_config()
    
    def validate_paths(self):
        """Valide que les chemins spécifiés sont corrects"""
        # Vérification du fichier de base de données SQLite
        db_path = self.db_path_edit.text().strip()
        if db_path and not os.path.exists(os.path.dirname(db_path)):
            QMessageBox.warning(self, "Erreur", f"Le dossier parent du fichier materiel.db n'existe pas:\n{os.path.dirname(db_path)}")
            return False
        
        # Si le fichier de base n'existe pas, proposer de le créer
        if db_path and not os.path.exists(db_path):
            reply = QMessageBox.question(
                self, 
                "Fichier inexistant", 
                f"Le fichier materiel.db n'existe pas:\n{db_path}\n\nVoulez-vous créer une base de données vide?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    # Créer une base de données SQLite vide avec la structure de base
                    import sqlite3
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Créer la table materiel
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS materiel (
                            id TEXT PRIMARY KEY,
                            nom TEXT NOT NULL,
                            quantite INTEGER DEFAULT 0,
                            unite TEXT,
                            emplacement TEXT,
                            statut TEXT DEFAULT 'Disponible'
                        )
                    ''')
                    
                    # Créer la table caracteristiques
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS caracteristiques (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            materiel_id TEXT,
                            nom TEXT,
                            valeur TEXT,
                            FOREIGN KEY (materiel_id) REFERENCES materiel (id)
                        )
                    ''')
                    
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(self, "Succès", f"Base de données materiel.db créée avec succès:\n{db_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Impossible de créer la base de données:\n{str(e)}")
                    return False
            else:
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
        
        # Vérification de la base de données RH
        rh_path = self.rh_path_edit.text().strip()
        if rh_path and not os.path.exists(os.path.dirname(rh_path)):
            QMessageBox.warning(self, "Erreur", f"Le dossier parent de la base RH n'existe pas:\n{os.path.dirname(rh_path)}")
            return False
        
        return True
    
    def accept(self):
        """Applique les paramètres et ferme la fenêtre"""
        self.apply_settings()
        super().accept()

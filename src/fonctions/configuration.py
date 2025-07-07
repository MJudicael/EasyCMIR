from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QWidget, QTabWidget,
    QLineEdit, QMessageBox, QFileDialog, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QAbstractItemView, QInputDialog, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import os
from ..utils.config_manager import config_manager
from ..utils.auth_manager import auth_manager
from ..widgets.login_dialog import require_authentication

class ConfigurationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setMinimumSize(700, 600)
        self.setup_ui()
        # Charger la configuration existante
        self.load_current_config()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Créer le widget d'onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
                color: #2c3e50;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                color: #3498db;
            }
            QTabBar::tab:hover {
                background-color: #e3f2fd;
                color: #2980b9;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
        
        # Onglet Chemins
        paths_tab = self.create_paths_tab()
        self.tab_widget.addTab(paths_tab, "Chemins des fichiers")
        
        # Onglet Administration (seulement pour les administrateurs)
        if auth_manager.is_authenticated() and auth_manager.is_admin():
            admin_tab = self.create_admin_tab()
            self.tab_widget.addTab(admin_tab, "Administration")
        
        layout.addWidget(self.tab_widget)
        
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
    
    def create_paths_tab(self):
        """Crée l'onglet des chemins des fichiers"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Contenu des chemins
        paths_content = self.create_paths_content()
        layout.addWidget(paths_content)
        
        return widget
    
    def create_admin_tab(self):
        """Crée l'onglet administration (réservé aux administrateurs)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Vérification des permissions
        if not auth_manager.is_authenticated() or not auth_manager.is_admin():
            access_denied = QLabel("⚠️ Accès réservé aux administrateurs")
            access_denied.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            access_denied.setAlignment(Qt.AlignCenter)
            layout.addWidget(access_denied)
            return widget
        
        # Titre
        title = QLabel("🔧 Administration des utilisateurs")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Section Gestion des utilisateurs
        users_group = QGroupBox("Gestion des utilisateurs")
        users_layout = QVBoxLayout()
        
        # Table des utilisateurs
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "Nom d'utilisateur", "Administrateur", "Accès RH", "Accès Matériel", "Créé le", "Dernière connexion"
        ])
        
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        
        users_layout.addWidget(self.users_table)
        
        # Boutons de gestion des utilisateurs
        users_buttons_layout = QHBoxLayout()
        
        add_user_btn = QPushButton("➕ Ajouter utilisateur")
        add_user_btn.clicked.connect(self.add_user)
        users_buttons_layout.addWidget(add_user_btn)
        
        edit_user_btn = QPushButton("✏️ Modifier utilisateur")
        edit_user_btn.clicked.connect(self.edit_user)
        users_buttons_layout.addWidget(edit_user_btn)
        
        delete_user_btn = QPushButton("🗑️ Supprimer utilisateur")
        delete_user_btn.clicked.connect(self.delete_user)
        users_buttons_layout.addWidget(delete_user_btn)
        
        users_buttons_layout.addStretch()
        
        refresh_users_btn = QPushButton("🔄 Actualiser")
        refresh_users_btn.clicked.connect(self.load_users)
        users_buttons_layout.addWidget(refresh_users_btn)
        
        users_layout.addLayout(users_buttons_layout)
        users_group.setLayout(users_layout)
        layout.addWidget(users_group)
        
        # Section Configuration de la base d'authentification
        auth_db_group = QGroupBox("Base de données d'authentification")
        auth_db_layout = QFormLayout()
        
        # Chemin de la base d'authentification
        auth_db_path_layout = QHBoxLayout()
        self.auth_db_path_edit = QLineEdit()
        self.auth_db_path_edit.setText(auth_manager.db_path)
        
        auth_db_browse_btn = QPushButton("Parcourir...")
        auth_db_browse_btn.clicked.connect(self.browse_auth_db_path)
        
        auth_db_path_layout.addWidget(self.auth_db_path_edit)
        auth_db_path_layout.addWidget(auth_db_browse_btn)
        
        auth_db_layout.addRow("Chemin du fichier users.db:", auth_db_path_layout)
        auth_db_group.setLayout(auth_db_layout)
        layout.addWidget(auth_db_group)
        
        # Section Changement de mot de passe administrateur
        admin_pwd_group = QGroupBox("Mot de passe administrateur")
        admin_pwd_layout = QHBoxLayout()
        
        change_pwd_btn = QPushButton("🔑 Changer le mot de passe")
        change_pwd_btn.clicked.connect(self.change_admin_password)
        admin_pwd_layout.addWidget(change_pwd_btn)
        admin_pwd_layout.addStretch()
        
        admin_pwd_group.setLayout(admin_pwd_layout)
        layout.addWidget(admin_pwd_group)
        
        # Charger la liste des utilisateurs
        self.load_users()
        
        return widget
    
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
        
        # Groupe Dossier interventions
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
        
        interventions_layout.addRow("Chemin du dossier:", interventions_path_layout)
        interventions_group.setLayout(interventions_layout)
        layout.addWidget(interventions_group)
        
        # Groupe Base de données RH
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
        
        rh_layout.addRow("Chemin du fichier RH.db:", rh_path_layout)
        rh_group.setLayout(rh_layout)
        layout.addWidget(rh_group)
        
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
        
        # Sauvegarde du chemin de la base d'authentification si l'onglet admin est présent
        if hasattr(self, 'auth_db_path_edit'):
            new_auth_path = self.auth_db_path_edit.text().strip()
            if new_auth_path != auth_manager.db_path:
                if auth_manager.change_database_path(new_auth_path):
                    QMessageBox.information(self, "Info", "Chemin de la base d'authentification mis à jour.")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de changer le chemin de la base d'authentification.")
        
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
    
    def load_users(self):
        """Charge la liste des utilisateurs dans la table"""
        if not hasattr(self, 'users_table'):
            return
            
        users = auth_manager.get_all_users()
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user['username']))
            self.users_table.setItem(row, 1, QTableWidgetItem("Oui" if user['is_admin'] else "Non"))
            self.users_table.setItem(row, 2, QTableWidgetItem("Oui" if user['can_access_rh'] else "Non"))
            self.users_table.setItem(row, 3, QTableWidgetItem("Oui" if user['can_access_materiel'] else "Non"))
            self.users_table.setItem(row, 4, QTableWidgetItem(user['created_at'] or ""))
            self.users_table.setItem(row, 5, QTableWidgetItem(user['last_login'] or "Jamais"))
            
            # Stocker l'ID utilisateur
            self.users_table.item(row, 0).setData(Qt.UserRole, user['id'])
    
    def add_user(self):
        """Ajoute un nouvel utilisateur"""
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            user_data = dialog.get_user_data()
            if auth_manager.create_user(
                user_data['username'], 
                user_data['password'],
                user_data['is_admin'],
                user_data['can_access_rh'],
                user_data['can_access_materiel']
            ):
                QMessageBox.information(self, "Succès", "Utilisateur créé avec succès.")
                self.load_users()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de créer l'utilisateur. Le nom d'utilisateur existe peut-être déjà.")
    
    def edit_user(self):
        """Modifie un utilisateur existant"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un utilisateur à modifier.")
            return
        
        user_id = self.users_table.item(current_row, 0).data(Qt.UserRole)
        username = self.users_table.item(current_row, 0).text()
        is_admin = self.users_table.item(current_row, 1).text() == "Oui"
        can_access_rh = self.users_table.item(current_row, 2).text() == "Oui"
        can_access_materiel = self.users_table.item(current_row, 3).text() == "Oui"
        
        user_data = {
            'username': username,
            'password': '',  # Ne pas pré-remplir le mot de passe
            'is_admin': is_admin,
            'can_access_rh': can_access_rh,
            'can_access_materiel': can_access_materiel
        }
        
        dialog = UserDialog(self, user_data, edit_mode=True)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_user_data()
            
            # Préparer les paramètres de mise à jour
            update_params = {
                'username': new_data['username'],
                'is_admin': new_data['is_admin'],
                'can_access_rh': new_data['can_access_rh'],
                'can_access_materiel': new_data['can_access_materiel']
            }
            
            # Ajouter le mot de passe seulement s'il a été modifié
            if new_data['password']:
                update_params['password'] = new_data['password']
            
            if auth_manager.update_user(user_id, **update_params):
                QMessageBox.information(self, "Succès", "Utilisateur modifié avec succès.")
                self.load_users()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de modifier l'utilisateur.")
    
    def delete_user(self):
        """Supprime un utilisateur"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un utilisateur à supprimer.")
            return
        
        username = self.users_table.item(current_row, 0).text()
        user_id = self.users_table.item(current_row, 0).data(Qt.UserRole)
        
        if username == "administrateur":
            QMessageBox.warning(self, "Attention", "Impossible de supprimer l'utilisateur administrateur principal.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{username}' ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if auth_manager.delete_user(user_id):
                QMessageBox.information(self, "Succès", "Utilisateur supprimé avec succès.")
                self.load_users()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer l'utilisateur.")
    
    def browse_auth_db_path(self):
        """Parcourir pour choisir le chemin de la base d'authentification"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Choisir l'emplacement de la base de données d'authentification",
            self.auth_db_path_edit.text(),
            "Base de données SQLite (*.db)"
        )
        
        if file_path:
            self.auth_db_path_edit.setText(file_path)
    
    def change_admin_password(self):
        """Change le mot de passe de l'administrateur actuel"""
        current_user = auth_manager.get_current_user()
        if not current_user or not current_user['is_admin']:
            QMessageBox.warning(self, "Erreur", "Seuls les administrateurs peuvent changer leur mot de passe.")
            return
        
        # Demander le nouveau mot de passe
        new_password, ok = QInputDialog.getText(
            self, 
            "Nouveau mot de passe", 
            "Saisissez le nouveau mot de passe:",
            QLineEdit.Password
        )
        
        if ok and new_password:
            if len(new_password) < 4:
                QMessageBox.warning(self, "Attention", "Le mot de passe doit contenir au moins 4 caractères.")
                return
            
            # Confirmer le mot de passe
            confirm_password, ok = QInputDialog.getText(
                self, 
                "Confirmation", 
                "Confirmez le nouveau mot de passe:",
                QLineEdit.Password
            )
            
            if ok and confirm_password == new_password:
                if auth_manager.update_user(current_user['id'], password=new_password):
                    QMessageBox.information(self, "Succès", "Mot de passe administrateur modifié avec succès.")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de modifier le mot de passe.")
            elif ok:
                QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")


class UserDialog(QDialog):
    """Dialogue pour créer/modifier un utilisateur"""
    
    def __init__(self, parent=None, user_data=None, edit_mode=False):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.setWindowTitle("Modifier l'utilisateur" if edit_mode else "Nouvel utilisateur")
        self.setFixedSize(450, 400)
        
        # Style général du dialogue
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit {
                padding: 6px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                padding: 8px 16px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        self.setup_ui()
        
        if user_data:
            self.load_user_data(user_data)
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Nom d'utilisateur
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Nom d'utilisateur unique")
        form_layout.addRow("Nom d'utilisateur:", self.username_edit)
        
        # Mot de passe
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Laissez vide pour ne pas changer" if self.edit_mode else "Mot de passe")
        form_layout.addRow("Mot de passe:", self.password_edit)
        
        # Confirmation mot de passe
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("Confirmez le mot de passe")
        form_layout.addRow("Confirmer mot de passe:", self.confirm_password_edit)
        
        layout.addLayout(form_layout)
        
        # Permissions
        permissions_group = QGroupBox("Permissions d'accès")
        permissions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
                background-color: #f8f9fa;
            }
        """)
        permissions_layout = QVBoxLayout()
        
        self.admin_checkbox = QCheckBox("Administrateur (accès à tous les modules et à l'administration)")
        self.admin_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-weight: bold;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #2980b9;
            }
        """)
        
        self.rh_checkbox = QCheckBox("Accès au module Ressources Humaines")
        self.rh_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #27ae60;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border: 2px solid #229954;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #229954;
            }
        """)
        
        self.materiel_checkbox = QCheckBox("Accès au module Gestion Matériel")
        self.materiel_checkbox.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #e67e22;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #e67e22;
                border: 2px solid #d68910;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #d68910;
            }
        """)
        
        permissions_layout.addWidget(self.admin_checkbox)
        permissions_layout.addWidget(self.rh_checkbox)
        permissions_layout.addWidget(self.materiel_checkbox)
        
        permissions_group.setLayout(permissions_layout)
        layout.addWidget(permissions_group)
        
        # Note
        note = QLabel("ℹ️ Les administrateurs ont automatiquement accès à tous les modules")
        note.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(note)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(ok_button)
        
        layout.addLayout(buttons_layout)
    
    def load_user_data(self, user_data):
        """Charge les données d'un utilisateur existant"""
        self.username_edit.setText(user_data['username'])
        self.admin_checkbox.setChecked(user_data['is_admin'])
        self.rh_checkbox.setChecked(user_data['can_access_rh'])
        self.materiel_checkbox.setChecked(user_data['can_access_materiel'])
    
    def accept(self):
        """Valide les données avant fermeture"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        # Validation nom d'utilisateur
        if not username:
            QMessageBox.warning(self, "Erreur", "Le nom d'utilisateur est requis.")
            return
        
        # Validation mot de passe
        if not self.edit_mode or password:  # Mot de passe requis pour nouveau, optionnel pour modification
            if len(password) < 4:
                QMessageBox.warning(self, "Erreur", "Le mot de passe doit contenir au moins 4 caractères.")
                return
            
            if password != confirm_password:
                QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
                return
        
        # Validation permissions
        is_admin = self.admin_checkbox.isChecked()
        can_access_rh = self.rh_checkbox.isChecked()
        can_access_materiel = self.materiel_checkbox.isChecked()
        
        if not is_admin and not can_access_rh and not can_access_materiel:
            QMessageBox.warning(self, "Erreur", "L'utilisateur doit avoir au moins une permission d'accès.")
            return
        
        super().accept()
    
    def get_user_data(self):
        """Retourne les données saisies"""
        return {
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text(),
            'is_admin': self.admin_checkbox.isChecked(),
            'can_access_rh': self.rh_checkbox.isChecked(),
            'can_access_materiel': self.materiel_checkbox.isChecked()
        }

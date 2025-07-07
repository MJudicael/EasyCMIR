"""
Dialogue de connexion pour l'authentification des utilisateurs
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFormLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QFont
import os
from ..constants import ICONS_DIR
from ..utils.auth_manager import auth_manager


class LoginDialog(QDialog):
    """Dialogue de connexion utilisateur"""
    
    def __init__(self, module_name="", parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self.setWindowTitle(f"Connexion - {module_name}")
        self.setFixedSize(450, 280)  # Augmenté légèrement la largeur et réduit la hauteur
        self.setModal(True)
        
        # Centrer la fenêtre
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        
        # Variables de résultat
        self.authenticated = False
    
    def setup_ui(self):
        """Création de l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)  # Ajout de marges appropriées
        
        # En-tête avec icône
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Icône de sécurité
        icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, "reglages.png")  # Utiliser l'icône réglages comme fallback
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Réduit légèrement
            icon_label.setPixmap(icon_pixmap)
        else:
            icon_label.setText("🔒")
            icon_label.setStyleSheet("font-size: 40px;")  # Réduit légèrement
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(50, 50)  # Taille fixe pour éviter les débordements
        
        # Titre
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        title_label = QLabel("Authentification requise")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")  # Réduit légèrement
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setWordWrap(True)  # Permet le retour à la ligne si nécessaire
        
        subtitle_label = QLabel(f"Accès au module : {self.module_name}")
        subtitle_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")  # Réduit légèrement
        subtitle_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subtitle_label.setWordWrap(True)  # Permet le retour à la ligne si nécessaire
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()  # Ajoute de l'espace flexible
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()  # Ajoute de l'espace flexible à droite
        layout.addLayout(header_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator)
        
        # Formulaire de connexion
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        form_layout = QFormLayout(form_frame)
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(10)
        
        # Champ nom d'utilisateur
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 2px solid #e9ecef;
                border-radius: 4px;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        
        # Champ mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 2px solid #e9ecef;
                border-radius: 4px;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        
        form_layout.addRow("Utilisateur:", self.username_input)
        form_layout.addRow("Mot de passe:", self.password_input)
        
        layout.addWidget(form_frame)
        
        
        # Boutons (taille réduite de 30%)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.login_button = QPushButton("Se connecter")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 7px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.login_button.clicked.connect(self.authenticate)
        self.login_button.setDefault(True)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 7px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(self.login_button)
        
        layout.addLayout(buttons_layout)
        
        # Connecter Enter pour valider
        self.username_input.returnPressed.connect(self.authenticate)
        self.password_input.returnPressed.connect(self.authenticate)
        
        # Focus sur le premier champ
        self.username_input.setFocus()
    
    def authenticate(self):
        """Tente l'authentification"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Attention", "Veuillez saisir un nom d'utilisateur et un mot de passe.")
            return
        
        # Tentative d'authentification
        if auth_manager.authenticate(username, password):
            # Vérifier les permissions selon le module
            user = auth_manager.get_current_user()
            has_permission = False
            
            if self.module_name == "Gestion RH" and user['can_access_rh']:
                has_permission = True
            elif self.module_name == "Gestion Matériel" and user['can_access_materiel']:
                has_permission = True
            elif user['is_admin']:  # Les admins ont accès à tout
                has_permission = True
            
            if has_permission:
                self.authenticated = True
                self.accept()
            else:
                QMessageBox.warning(
                    self, 
                    "Accès refusé", 
                    f"Votre compte n'a pas les permissions pour accéder au module '{self.module_name}'."
                )
                auth_manager.logout()
        else:
            QMessageBox.warning(
                self, 
                "Échec de connexion", 
                "Nom d'utilisateur ou mot de passe incorrect."
            )
        
        # Effacer le mot de passe en cas d'échec
        if not self.authenticated:
            self.password_input.clear()
            self.password_input.setFocus()
    
    def is_authenticated(self):
        """Retourne True si l'authentification a réussi"""
        return self.authenticated


def require_authentication(module_name: str, parent=None) -> bool:
    """
    Fonction utilitaire pour demander l'authentification avant l'accès à un module
    
    Args:
        module_name: Nom du module à protéger
        parent: Widget parent pour le dialogue
    
    Returns:
        True si l'authentification a réussi, False sinon
    """
    # Vérifier d'abord si l'utilisateur est déjà connecté avec les bonnes permissions
    if auth_manager.is_authenticated():
        user = auth_manager.get_current_user()
        
        if module_name == "Gestion RH" and user['can_access_rh']:
            return True
        elif module_name == "Gestion Matériel" and user['can_access_materiel']:
            return True
        elif user['is_admin']:
            return True
    
    # Sinon, demander l'authentification
    login_dialog = LoginDialog(module_name, parent)
    return login_dialog.exec() == QDialog.Accepted and login_dialog.is_authenticated()

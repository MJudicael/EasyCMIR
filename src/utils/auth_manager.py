"""
Gestionnaire d'authentification pour EasyCMIR
Gère les utilisateurs, mots de passe et permissions d'accès aux modules
"""

import sqlite3
import hashlib
import os
from typing import Optional, List, Dict, Tuple
from ..utils.config_manager import config_manager


class AuthManager:
    """Gestionnaire d'authentification et des permissions utilisateurs"""
    
    def __init__(self):
        self.db_path = self.get_auth_database_path()
        self.current_user = None
        self.init_database()
    
    def get_auth_database_path(self) -> str:
        """Récupère le chemin de la base de données d'authentification"""
        try:
            # Récupérer le chemin depuis la configuration
            auth_db_path = config_manager.get_auth_database_path()
            if auth_db_path and os.path.exists(auth_db_path):
                return auth_db_path
        except:
            pass
        
        # Chemin par défaut dans le dossier data
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'users.db'
        )
        return default_path
    
    def init_database(self):
        """Initialise la base de données des utilisateurs"""
        try:
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table des utilisateurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    can_access_rh BOOLEAN DEFAULT 0,
                    can_access_materiel BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Vérifier si l'utilisateur administrateur par défaut existe
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("administrateur",))
            if cursor.fetchone()[0] == 0:
                # Créer l'utilisateur administrateur par défaut
                admin_password_hash = self.hash_password("encarta")
                cursor.execute('''
                    INSERT INTO users (username, password_hash, is_admin, can_access_rh, can_access_materiel)
                    VALUES (?, ?, 1, 1, 1)
                ''', ("administrateur", admin_password_hash))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la base d'authentification: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authentifie un utilisateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                SELECT id, username, is_admin, can_access_rh, can_access_materiel
                FROM users 
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                self.current_user = {
                    'id': user[0],
                    'username': user[1],
                    'is_admin': bool(user[2]),
                    'can_access_rh': bool(user[3]),
                    'can_access_materiel': bool(user[4])
                }
                
                # Mettre à jour la date de dernière connexion
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                conn.close()
                return True
            
            conn.close()
            return False
            
        except Exception as e:
            print(f"Erreur lors de l'authentification: {e}")
            return False
    
    def logout(self):
        """Déconnecte l'utilisateur actuel"""
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """Vérifie si un utilisateur est connecté"""
        return self.current_user is not None
    
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur actuel est administrateur"""
        return self.current_user and self.current_user['is_admin']
    
    def can_access_rh(self) -> bool:
        """Vérifie si l'utilisateur peut accéder au module RH"""
        return self.current_user and self.current_user['can_access_rh']
    
    def can_access_materiel(self) -> bool:
        """Vérifie si l'utilisateur peut accéder au module matériel"""
        return self.current_user and self.current_user['can_access_materiel']
    
    def get_current_user(self) -> Optional[Dict]:
        """Retourne les informations de l'utilisateur actuel"""
        return self.current_user
    
    def create_user(self, username: str, password: str, is_admin: bool = False, 
                   can_access_rh: bool = False, can_access_materiel: bool = False) -> bool:
        """Crée un nouvel utilisateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, is_admin, can_access_rh, can_access_materiel)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, is_admin, can_access_rh, can_access_materiel))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            # Nom d'utilisateur déjà existant
            return False
        except Exception as e:
            print(f"Erreur lors de la création de l'utilisateur: {e}")
            return False
    
    def update_user(self, user_id: int, username: str = None, password: str = None,
                   is_admin: bool = None, can_access_rh: bool = None, 
                   can_access_materiel: bool = None) -> bool:
        """Met à jour un utilisateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if username is not None:
                updates.append("username = ?")
                params.append(username)
            
            if password is not None:
                updates.append("password_hash = ?")
                params.append(self.hash_password(password))
            
            if is_admin is not None:
                updates.append("is_admin = ?")
                params.append(is_admin)
            
            if can_access_rh is not None:
                updates.append("can_access_rh = ?")
                params.append(can_access_rh)
            
            if can_access_materiel is not None:
                updates.append("can_access_materiel = ?")
                params.append(can_access_materiel)
            
            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur (sauf l'administrateur principal)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier que ce n'est pas l'administrateur principal
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user and user[0] == "administrateur":
                conn.close()
                return False  # Ne pas supprimer l'administrateur principal
            
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """Récupère tous les utilisateurs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, is_admin, can_access_rh, can_access_materiel, 
                       created_at, last_login
                FROM users
                ORDER BY username
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'is_admin': bool(row[2]),
                    'can_access_rh': bool(row[3]),
                    'can_access_materiel': bool(row[4]),
                    'created_at': row[5],
                    'last_login': row[6]
                })
            
            conn.close()
            return users
            
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []
    
    def change_database_path(self, new_path: str) -> bool:
        """Change le chemin de la base de données d'authentification"""
        try:
            # Sauvegarder le nouveau chemin dans la configuration
            config_manager.set_auth_database_path(new_path)
            
            # Copier la base actuelle vers le nouveau chemin si elle n'existe pas
            if not os.path.exists(new_path) and os.path.exists(self.db_path):
                import shutil
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.copy2(self.db_path, new_path)
            
            # Mettre à jour le chemin
            self.db_path = new_path
            self.init_database()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors du changement de chemin de base: {e}")
            return False


# Instance globale du gestionnaire d'authentification
auth_manager = AuthManager()

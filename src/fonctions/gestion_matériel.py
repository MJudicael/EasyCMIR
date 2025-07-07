#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Matériel pour EasyCMIR
======================================

Module unifié pour la gestion du matériel de radioprotection.
- Interface moderne avec icônes
- Base de données JSON configurable
- Intégration complète avec EasyCMIR

Auteur: EasyCMIR Team
Date: Juillet 2025
"""

import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize, QDate
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLineEdit, QFormLayout, QDialog,
    QDialogButtonBox, QMessageBox, QLabel, QComboBox, QFrame, 
    QSizePolicy, QFileDialog, QDateEdit, QSpinBox
)
from PySide6.QtGui import QIcon
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from ..utils.config_manager import config_manager
from ..constants import ICONS_DIR


# ====================================================================
# GESTION DE LA BASE DE DONNÉES SQLITE
# ====================================================================

def get_db_file_path():
    """Récupère le chemin du fichier materiel.db depuis la configuration."""
    try:
        # Essayer d'abord la configuration
        db_path = config_manager.get_value('paths', 'materiel_db_path', None)
        if db_path and os.path.exists(db_path):
            return db_path
        
        # Chemin par défaut dans le répertoire data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        default_path = os.path.join(project_root, "data", "materiel.db")
        
        return default_path
        
    except Exception:
        # En cas d'erreur, utiliser le chemin par défaut
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, "data", "materiel.db")


def get_db_connection():
    """Obtient une connexion à la base de données SQLite."""
    db_path = get_db_file_path()
    return sqlite3.connect(db_path)


def load_db_data():
    """Charge les données depuis la base de données SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Requête pour récupérer tous les matériels avec leurs caractéristiques
        cursor.execute("""
            SELECT m.id, m.nom, m.type, m.usage, m.marque, m.lieu, m.affectation
            FROM materiel m
            ORDER BY m.id
        """)
        
        materiels = []
        for row in cursor.fetchall():
            materiel = {
                'id': row[0],
                'nom': row[1],
                'type': row[2],
                'usage': row[3],
                'marque': row[4],
                'lieu': row[5],
                'affectation': row[6]
            }
            
            # Récupérer les caractéristiques pour ce matériel
            cursor.execute("""
                SELECT nom_caracteristique, valeur_caracteristique FROM caracteristiques 
                WHERE materiel_id = ? 
                ORDER BY nom_caracteristique
            """, (row[0],))
            
            for carac_row in cursor.fetchall():
                materiel[carac_row[0]] = carac_row[1]
            
            materiels.append(materiel)
        
        conn.close()
        return materiels
        
    except Exception as e:
        print(f"Erreur lors du chargement de la base de données: {e}")
        return []


def save_materiel_to_db(materiel_data):
    """Sauvegarde un matériel dans la base de données."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Champs de base de la table materiel
        base_fields = ['id', 'nom', 'type', 'usage', 'marque', 'lieu', 'affectation']
        
        # Vérifier si le matériel existe déjà
        cursor.execute("SELECT id FROM materiel WHERE id = ?", (materiel_data['id'],))
        exists = cursor.fetchone()
        
        if exists:
            # Mise à jour
            cursor.execute("""
                UPDATE materiel 
                SET nom = ?, type = ?, usage = ?, marque = ?, lieu = ?, affectation = ?
                WHERE id = ?
            """, (
                materiel_data.get('nom', ''),
                materiel_data.get('type', ''),
                materiel_data.get('usage', ''),
                materiel_data.get('marque', ''),
                materiel_data.get('lieu', ''),
                materiel_data.get('affectation', ''),
                materiel_data['id']
            ))
            
            # Supprimer les anciennes caractéristiques
            cursor.execute("DELETE FROM caracteristiques WHERE materiel_id = ?", (materiel_data['id'],))
        else:
            # Insertion
            cursor.execute("""
                INSERT INTO materiel (id, nom, type, usage, marque, lieu, affectation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                materiel_data['id'],
                materiel_data.get('nom', ''),
                materiel_data.get('type', ''),
                materiel_data.get('usage', ''),
                materiel_data.get('marque', ''),
                materiel_data.get('lieu', ''),
                materiel_data.get('affectation', '')
            ))
        
        # Insérer les caractéristiques supplémentaires
        for key, value in materiel_data.items():
            if key not in base_fields and value:
                cursor.execute("""
                    INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique)
                    VALUES (?, ?, ?)
                """, (materiel_data['id'], key, str(value)))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False


def delete_materiel_from_db(materiel_id):
    """Supprime un matériel de la base de données."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Supprimer les caractéristiques
        cursor.execute("DELETE FROM caracteristiques WHERE materiel_id = ?", (materiel_id,))
        
        # Supprimer le matériel
        cursor.execute("DELETE FROM materiel WHERE id = ?", (materiel_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        return False


def get_next_id_rt():
    """Génère le prochain ID-RT disponible."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer le plus grand numéro d'ID-RT existant
        cursor.execute("""
            SELECT id FROM materiel 
            WHERE id LIKE 'ID-RT-%'
            ORDER BY CAST(SUBSTR(id, 7) AS INTEGER) DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            last_id = result[0]
            try:
                num = int(last_id.split('-')[2])
                return f"ID-RT-{num + 1}"
            except (IndexError, ValueError):
                return "ID-RT-1"
        else:
            return "ID-RT-1"
            
    except Exception as e:
        print(f"Erreur lors de la génération de l'ID: {e}")
        return "ID-RT-1"


def parse_date_from_string(date_str):
    """Parse une date depuis une chaîne de caractères avec différents formats possibles."""
    if not date_str:
        return None
    
    # Essayer différents formats de date
    formats = [
        '%Y-%m-%d',      # Format ISO : 2024-01-01
        '%d/%m/%Y',      # Format français : 01/01/2024
        '%d-%m-%Y',      # Format français avec tirets : 01-01-2024
        '%d %B %Y',      # Format français avec mois en texte : 1 janvier 2024
        '%d %b %Y'       # Format français avec mois abrégé : 1 jan 2024
    ]
    
    # Traduction des mois français vers l'anglais pour le parsing
    date_en = str(date_str).replace('janvier', 'January').replace('février', 'February')\
                            .replace('mars', 'March').replace('avril', 'April')\
                            .replace('mai', 'May').replace('juin', 'June')\
                            .replace('juillet', 'July').replace('août', 'August')\
                            .replace('septembre', 'September').replace('octobre', 'October')\
                            .replace('novembre', 'November').replace('décembre', 'December')
    
    for fmt in formats:
        try:
            return datetime.strptime(date_en, fmt)
        except ValueError:
            continue
    
    return None


def convert_materiel_to_tuple(materiel):
    """Convertit un dictionnaire materiel en tuple pour compatibilité avec le modèle de table."""
    # Ordre des colonnes: ID, Type, Usage, Modèle, Marque, Numéro de série, Quantité, Statut, Lieu, Affectation
    
    # Rechercher le modèle dans différents champs possibles
    modele = (materiel.get('modele') or 
              materiel.get('modèle') or 
              materiel.get('Modèle') or 
              '')
    
    # Rechercher le numéro de série dans différents champs possibles
    numero_serie = (materiel.get('numero_serie') or 
                    materiel.get('numéro de série') or 
                    materiel.get('Numéro de série') or 
                    materiel.get('numero serie') or
                    '')
    
    # Rechercher la quantité dans différents champs possibles
    quantite = (materiel.get('quantite') or 
                materiel.get('Quantité') or 
                materiel.get('quantité') or 
                1)
    
    # Rechercher le statut dans différents champs possibles
    statut = (materiel.get('statut') or 
              materiel.get('Statut') or 
              'En service')
    
    return (
        materiel.get('id', ''),
        materiel.get('type', ''),
        materiel.get('usage', ''),
        modele,
        materiel.get('marque', ''),
        numero_serie,
        str(quantite),
        statut,
        materiel.get('lieu', ''),
        materiel.get('affectation', '')
    )


# ====================================================================
# MODÈLE DE DONNÉES
# ====================================================================

class MaterielTableModel(QAbstractTableModel):
    """Modèle de données pour lier les données de la base SQLite au QTableView."""
    
    def __init__(self, data=None):
        super().__init__()
        if data is None:
            db_data = load_db_data()
            self._data = [convert_materiel_to_tuple(materiel) for materiel in db_data]
        else:
            self._data = data
        self._headers = ["ID", "Type", "Usage", "Modèle", "Marque", "Numéro de série", "Quantité", "Statut", "Lieu", "Affectation"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def refresh_data(self, new_data=None):
        self.beginResetModel()
        if new_data is not None:
            self._data = new_data
        else:
            # Recharger depuis la base de données
            db_data = load_db_data()
            self._data = [convert_materiel_to_tuple(materiel) for materiel in db_data]
        self.endResetModel()

    def get_materiel_by_row(self, row):
        """Récupère le matériel complet pour une ligne donnée."""
        if 0 <= row < len(self._data):
            # Récupérer l'ID du matériel affiché à cette ligne
            materiel_id = self._data[row][0]  # L'ID est dans la première colonne
            
            # Charger toutes les données de la base et chercher par ID
            db_data = load_db_data()
            for materiel in db_data:
                if materiel.get('id') == materiel_id:
                    return materiel
        return None

    def search_materiels(self, query):
        """Filtre les matériels selon plusieurs critères de recherche."""
        if not query.strip():
            self.refresh_data()
            return
        
        # Séparer les critères de recherche
        search_criteria = [q.strip().lower() for q in query.split(';')]
        
        db_data = load_db_data()
        filtered_data = []
        
        for materiel in db_data:
            # Créer une liste de tous les champs de recherche pour chaque matériel
            search_fields = []
            for key, value in materiel.items():
                if value:  # Ignorer les valeurs vides
                    search_fields.append(str(value).lower())
            
            # Un matériel est inclus si TOUS les critères correspondent à AU MOINS un champ
            if all(any(criterion in field for field in search_fields) 
                   for criterion in search_criteria):
                filtered_data.append(convert_materiel_to_tuple(materiel))
        
        self.refresh_data(filtered_data)


# ====================================================================
# DIALOGUE D'ÉDITION DU MATÉRIEL
# ====================================================================

class MaterielDialog(QDialog):
    """Boîte de dialogue pour créer ou éditer un matériel."""
    
    def __init__(self, materiel_id=None, parent=None):
        super().__init__(parent)
        self.materiel_id = materiel_id
        
        self.setWindowTitle("Ajouter du matériel" if not materiel_id else "Modifier le matériel")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.load_combo_options()
        
        if self.materiel_id:
            self.load_data()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("📦 " + ("Nouveau matériel" if not self.materiel_id else f"Modification - {self.materiel_id}"))
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                border-bottom: 2px solid #3498db;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(title)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Champs d'édition
        self.id_field = QLineEdit()
        self.id_field.setReadOnly(True)
        self.type_field = QLineEdit()
        self.usage_field = QLineEdit()
        self.modele_field = QLineEdit()
        self.marque_field = QLineEdit()
        self.numero_serie_field = QLineEdit()
        self.quantite_field = QLineEdit()
        self.quantite_field.setText("1")
        
        # Champs de date
        self.date_achat_field = QDateEdit()
        self.date_achat_field.setCalendarPopup(True)
        self.date_achat_field.setSpecialValueText("(Aucune date)")  # Texte affiché pour date minimale
        self.date_achat_field.setMinimumDate(QDate(1900, 1, 1))
        self.date_achat_field.setDate(QDate(1900, 1, 1))  # Commencer avec la date minimale (vide)
        
        self.date_peremption_field = QDateEdit()
        self.date_peremption_field.setCalendarPopup(True)
        self.date_peremption_field.setSpecialValueText("(Aucune date)")  # Texte affiché pour date minimale
        self.date_peremption_field.setMinimumDate(QDate(1900, 1, 1))
        self.date_peremption_field.setDate(QDate(1900, 1, 1))  # Commencer avec la date minimale (vide)
        
        # ComboBox éditables
        self.statut_field = QComboBox()
        self.statut_field.setEditable(True)
        self.lieu_field = QComboBox()
        self.lieu_field.setEditable(True)
        self.affectation_field = QComboBox()
        self.affectation_field.setEditable(True)
        
        # Ajouter les champs au formulaire
        if self.materiel_id:
            form_layout.addRow("ID:", self.id_field)
        form_layout.addRow("Type:", self.type_field)
        form_layout.addRow("Usage:", self.usage_field)
        form_layout.addRow("Modèle:", self.modele_field)
        form_layout.addRow("Marque:", self.marque_field)
        form_layout.addRow("Numéro de série:", self.numero_serie_field)
        form_layout.addRow("Quantité:", self.quantite_field)
        form_layout.addRow("Date d'achat:", self.date_achat_field)
        form_layout.addRow("Date de péremption:", self.date_peremption_field)
        form_layout.addRow("Statut:", self.statut_field)
        form_layout.addRow("Lieu:", self.lieu_field)
        form_layout.addRow("Affectation:", self.affectation_field)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Style des boutons
        button_box.setStyleSheet("""
            QDialogButtonBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        layout.addWidget(button_box)

    def load_combo_options(self):
        """Charge les options des ComboBox depuis les données existantes."""
        materiels = load_db_data()
        
        # Collecter les valeurs uniques
        statuts = set()
        lieux = set()
        affectations = set()
        
        for materiel in materiels:
            statuts.add(materiel.get('statut', materiel.get('Statut', '')))
            lieux.add(materiel.get('lieu', ''))
            affectations.add(materiel.get('affectation', ''))
        
        # Ajouter aux ComboBox (supprimer les valeurs vides)
        self.statut_field.addItems([""] + sorted([s for s in statuts if s]))
        self.lieu_field.addItems([""] + sorted([l for l in lieux if l]))
        self.affectation_field.addItems([""] + sorted([a for a in affectations if a]))

    def load_data(self):
        """Charge les données du matériel à modifier."""
        materiels = load_db_data()
        materiel = None
        
        # Chercher le matériel par ID
        for m in materiels:
            if m.get('id') == self.materiel_id:
                materiel = m
                break
        
        if materiel:
            self.id_field.setText(materiel.get('id', ''))
            self.type_field.setText(materiel.get('type', ''))
            self.usage_field.setText(materiel.get('usage', ''))
            
            # Rechercher le modèle dans différents champs
            modele = (materiel.get('modele') or 
                     materiel.get('modèle') or 
                     materiel.get('Modèle') or 
                     '')
            self.modele_field.setText(modele)
            
            self.marque_field.setText(materiel.get('marque', ''))
            
            # Rechercher le numéro de série dans différents champs
            numero_serie = (materiel.get('numero_serie') or 
                           materiel.get('numéro de série') or 
                           materiel.get('Numéro de série') or 
                           materiel.get('numero serie') or
                           '')
            self.numero_serie_field.setText(numero_serie)
            
            # Rechercher la quantité dans différents champs
            quantite = (materiel.get('quantite') or 
                       materiel.get('Quantité') or 
                       materiel.get('quantité') or 
                       1)
            self.quantite_field.setText(str(quantite))
            
            # Charger les dates depuis la base de données
            # Ne PAS utiliser de valeur par défaut si la donnée n'existe pas dans la base
            date_achat = (materiel.get('Date d\'achat') or 
                         materiel.get('date_achat') or 
                         materiel.get('Date d achat') or
                         None)
            
            if date_achat:
                date_parsed = parse_date_from_string(date_achat)
                if date_parsed:
                    self.date_achat_field.setDate(QDate(date_parsed.year, date_parsed.month, date_parsed.day))
                else:
                    # Si on ne peut pas parser, laisser une date minimale (indique absence de donnée)
                    self.date_achat_field.setDate(QDate(1900, 1, 1))
            else:
                # Aucune date d'achat trouvée dans la base, laisser une date minimale
                self.date_achat_field.setDate(QDate(1900, 1, 1))
            
            date_peremption = (materiel.get('Date de péremption') or 
                              materiel.get('date_peremption') or 
                              materiel.get('Date de peremption') or
                              materiel.get('Date d\'expiration') or
                              materiel.get('Date de validité') or
                              None)
            
            if date_peremption:
                date_parsed = parse_date_from_string(date_peremption)
                if date_parsed:
                    self.date_peremption_field.setDate(QDate(date_parsed.year, date_parsed.month, date_parsed.day))
                else:
                    # Si on ne peut pas parser, laisser une date minimale
                    self.date_peremption_field.setDate(QDate(1900, 1, 1))
            else:
                # Aucune date de péremption trouvée dans la base, laisser une date minimale
                self.date_peremption_field.setDate(QDate(1900, 1, 1))
            
            # Rechercher le statut dans différents champs
            statut = (materiel.get('statut') or 
                     materiel.get('Statut') or 
                     '')
            self.statut_field.setCurrentText(statut)
            
            self.lieu_field.setCurrentText(materiel.get('lieu', ''))
            self.affectation_field.setCurrentText(materiel.get('affectation', ''))

    def accept(self):
        """Sauvegarde les données."""
        # Validation basique
        if not self.type_field.text().strip():
            QMessageBox.warning(self, "Erreur", "Le type est obligatoire.")
            return
        
        try:
            quantite = int(self.quantite_field.text()) if self.quantite_field.text() else 1
        except ValueError:
            QMessageBox.warning(self, "Erreur", "La quantité doit être un nombre entier.")
            return
        
        # Préparer le nouveau matériel
        nouveau_materiel = {
            'id': self.materiel_id if self.materiel_id else get_next_id_rt(),
            'type': self.type_field.text().strip(),
            'usage': self.usage_field.text().strip(),
            'marque': self.marque_field.text().strip(),
            'lieu': self.lieu_field.currentText().strip(),
            'affectation': self.affectation_field.currentText().strip(),
            'modified': datetime.now().isoformat(),
            # Caractéristiques qui vont dans la table caracteristiques
            'modèle': self.modele_field.text().strip(),
            'numéro de série': self.numero_serie_field.text().strip(),
            'Quantité': quantite,
            'Statut': self.statut_field.currentText().strip()
        }
        
        # Ajouter les dates seulement si elles ne sont pas "minimales" (1900-01-01)
        date_achat = self.date_achat_field.date()
        if date_achat != QDate(1900, 1, 1):
            nouveau_materiel['Date d\'achat'] = date_achat.toString("yyyy-MM-dd")
        
        date_peremption = self.date_peremption_field.date()
        if date_peremption != QDate(1900, 1, 1):
            nouveau_materiel['Date de péremption'] = date_peremption.toString("yyyy-MM-dd")
        
        if self.materiel_id is None:  # Création
            nouveau_materiel['created'] = datetime.now().isoformat()
        
        # Sauvegarder dans la base de données
        if save_materiel_to_db(nouveau_materiel):
            super().accept()
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les données.")


# ====================================================================
# DIALOGUE DE PÉREMPTION
# ====================================================================

class PeremptionDialog(QDialog):
    """Boîte de dialogue pour définir les critères de vérification des dates de péremption."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vérification des dates de péremption")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        # Widget principal
        self.delai_spinbox = QSpinBox()
        self.delai_spinbox.setMinimum(1)
        self.delai_spinbox.setMaximum(10)
        self.delai_spinbox.setValue(1)
        self.delai_spinbox.setSuffix(" an(s)")

        # Layout du formulaire
        form_layout = QFormLayout()
        form_layout.addRow("Délai d'alerte (années):", self.delai_spinbox)
        
        # Instructions
        instructions = QLabel("""
<b>Instructions:</b><br>
• Sélectionnez le délai en années pour l'alerte de péremption<br>
• Le système recherchera tous les matériels ayant une date de péremption<br>
• Seuls les matériels périment dans le délai spécifié ou déjà périmés seront listés<br>
• Un PDF sera généré avec la liste des matériels concernés<br><br>
<b>Formats de date acceptés:</b><br>
• JJ/MM/AAAA (ex: 15/12/2025)<br>
• AAAA-MM-JJ (ex: 2025-12-15)<br>
• JJ-MM-AAAA (ex: 15-12-2025)
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { background-color: #f5f5f5; color: #333333; padding: 10px; border: 1px solid #cccccc; border-radius: 5px; }")

        # Boutons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.generer_rapport_peremption)
        button_box.rejected.connect(self.reject)
        
        # Bouton de diagnostic
        btn_diagnostic = QPushButton("🔍 Diagnostic des dates")
        btn_diagnostic.clicked.connect(self.diagnostiquer_dates)
        btn_diagnostic.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(instructions)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(btn_diagnostic)
        main_layout.addStretch()
        main_layout.addWidget(button_box)

    def get_date_peremption(self, materiel):
        """Extrait la date de péremption d'un matériel en cherchant dans différents champs possibles."""
        # Champs possibles pour la date de péremption (selon la structure de la BDD)
        date_fields = [
            'Date de péremption',
            'date_peremption', 
            'datePeremption', 
            'date_expiration',
            'Date d\'expiration',
            'expiration',
            'peremption',
            'validite',
            'date_validite',
            'Date de validité'
        ]
        
        # Chercher dans les champs principaux
        for field in date_fields:
            date_str = materiel.get(field, '')
            if date_str and str(date_str).strip():
                return str(date_str).strip()
        
        return None

    def parse_date(self, date_str):
        """Parse une date depuis différents formats possibles."""
        return parse_date_from_string(date_str)

    def generer_rapport_peremption(self):
        """Génère le rapport de péremption selon les critères définis."""
        delai_annees = self.delai_spinbox.value()
        
        # Calculer la date limite (dans X ans)
        date_limite = datetime.now() + timedelta(days=delai_annees * 365)
        
        # Récupérer les matériels de la vue actuelle (avec filtres appliqués)
        if hasattr(self.parent(), 'table_model'):
            # Récupérer les matériels visibles dans la table filtrée
            materiels_visibles = []
            for i in range(self.parent().table_model.rowCount()):
                materiel = self.parent().table_model.get_materiel_by_row(i)
                if materiel:
                    materiels_visibles.append(materiel)
        else:
            # Fallback : charger tous les matériels
            materiels_visibles = load_db_data()
        
        # Filtrer les matériels avec date de péremption
        materiels_perimes = []
        materiels_non_dates = []
        
        for materiel in materiels_visibles:
            # Utiliser la nouvelle méthode pour extraire la date
            date_peremption_str = self.get_date_peremption(materiel)
            
            # Vérifier si le matériel a une date de péremption
            if date_peremption_str:
                date_peremption = self.parse_date(date_peremption_str)
                if date_peremption:
                    # Inclure si la date de péremption est avant la date limite
                    if date_peremption <= date_limite:
                        materiels_perimes.append(materiel)
                else:
                    # Date invalide mais présente
                    materiels_non_dates.append(materiel)
            else:
                # Pas de date de péremption
                materiels_non_dates.append(materiel)
        
        # Vérifier s'il y a des résultats
        if not materiels_perimes and not materiels_non_dates:
            QMessageBox.information(
                self,
                "Info",
                f"Aucun matériel n'arrive à péremption dans les {delai_annees} an{'s' if delai_annees > 1 else ''} à venir."
            )
            return
        
        # Afficher un message informatif sur ce qui a été trouvé
        info_message = f"Matériels trouvés dans la sélection actuelle :\n"
        info_message += f"• {len(materiels_perimes)} matériel(s) avec date de péremption dans les {delai_annees} an{'s' if delai_annees > 1 else ''}\n"
        info_message += f"• {len(materiels_non_dates)} matériel(s) sans date de péremption\n"
        info_message += f"• Total analysé : {len(materiels_visibles)} matériel(s) (selon les filtres de recherche)"
        
        QMessageBox.information(self, "Analyse des dates", info_message)
        
        # Générer le PDF
        self.generer_pdf_peremption(materiels_perimes, delai_annees, materiels_non_dates)
        self.accept()

    def generer_pdf_peremption(self, materiels, delai_annees, materiels_non_dates):
        """Génère le PDF de péremption."""
        # Dialogue de sélection du fichier
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le rapport de péremption",
            f"peremption_{delai_annees}ans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "Fichiers PDF (*.pdf)"
        )
        
        if not filename:
            return
        
        try:
            # Configuration PDF en paysage
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            elements = []
            
            # Titre
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, Spacer
            styles = getSampleStyleSheet()
            
            # Titre avec informations de filtrage
            titre_base = f"Rapport de Péremption - Délai: {delai_annees} an{'s' if delai_annees > 1 else ''}"
            
            # Ajouter l'info sur le filtrage si applicable
            if hasattr(self.parent(), 'search_edit') and self.parent().search_edit.text().strip():
                filtre_texte = self.parent().search_edit.text().strip()
                titre_complet = f"{titre_base}<br/>Filtres appliqués: {filtre_texte}"
            else:
                titre_complet = f"{titre_base}<br/>Tous les matériels"
            
            title = Paragraph(f"<b>{titre_complet}</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Matériels avec dates de péremption
            if materiels:
                subtitle = Paragraph(f"<b>Matériels arrivant à péremption ({len(materiels)} éléments)</b>", styles['Heading2'])
                elements.append(subtitle)
                elements.append(Spacer(1, 12))
                
                # Préparer les données pour le tableau
                headers = ["ID", "Type", "Usage", "Modèle", "Marque", "Date Péremption", "Jours Restants", "Statut", "Lieu", "Affectation"]
                data_to_export = [headers]
                
                for materiel in materiels:
                    # Utiliser la nouvelle méthode pour extraire la date
                    date_peremption_str = self.get_date_peremption(materiel)
                    date_peremption = self.parse_date(date_peremption_str) if date_peremption_str else None
                    
                    if date_peremption:
                        jours_restants = (date_peremption - datetime.now()).days
                        statut_peremption = "PÉRIMÉ" if jours_restants < 0 else f"{jours_restants} jours"
                        date_affichage = date_peremption.strftime('%d/%m/%Y')
                    else:
                        statut_peremption = "Date invalide"
                        date_affichage = date_peremption_str or "Aucune"
                    
                    row = [
                        materiel.get('id', ''),
                        materiel.get('type', ''),
                        materiel.get('usage', ''),
                        materiel.get('modele', ''),
                        materiel.get('marque', ''),
                        date_affichage,
                        statut_peremption,
                        materiel.get('statut', ''),
                        materiel.get('lieu', ''),
                        materiel.get('affectation', '')
                    ]
                    data_to_export.append(row)
                
                # Créer le tableau
                table = Table(data_to_export)
                
                # Style du tableau
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ])
                
                # Colorer les lignes selon l'urgence
                for i, materiel in enumerate(materiels, 1):
                    date_peremption_str = self.get_date_peremption(materiel)
                    date_peremption = self.parse_date(date_peremption_str) if date_peremption_str else None
                    
                    if date_peremption:
                        jours_restants = (date_peremption - datetime.now()).days
                        
                        if jours_restants < 0:  # Périmé
                            style.add('BACKGROUND', (0, i), (-1, i), colors.red)
                            style.add('TEXTCOLOR', (0, i), (-1, i), colors.white)
                        elif jours_restants <= 30:  # Rouge pour moins de 30 jours
                            style.add('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                        elif jours_restants <= 90:  # Orange pour moins de 90 jours
                            style.add('BACKGROUND', (0, i), (-1, i), colors.lightyellow)
                
                table.setStyle(style)
                elements.append(table)
            
            # Matériels sans dates
            if materiels_non_dates:
                elements.append(Spacer(1, 20))
                subtitle2 = Paragraph(f"<b>Matériels sans date de péremption ({len(materiels_non_dates)} éléments)</b>", styles['Heading2'])
                elements.append(subtitle2)
                elements.append(Spacer(1, 12))
                
                # Tableau des matériels sans dates
                headers2 = ["ID", "Type", "Usage", "Modèle", "Marque", "Statut", "Lieu", "Affectation"]
                data_sans_dates = [headers2]
                
                for materiel in materiels_non_dates:
                    row = [
                        materiel.get('id', ''),
                        materiel.get('type', ''),
                        materiel.get('usage', ''),
                        materiel.get('modele', ''),
                        materiel.get('marque', ''),
                        materiel.get('statut', ''),
                        materiel.get('lieu', ''),
                        materiel.get('affectation', '')
                    ]
                    data_sans_dates.append(row)
                
                table2 = Table(data_sans_dates)
                style2 = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ])
                table2.setStyle(style2)
                elements.append(table2)
            
            # Générer le PDF
            doc.build(elements)
            
            QMessageBox.information(
                self,
                "Succès",
                f"Rapport de péremption créé: {filename}\n"
                f"• {len(materiels)} matériel(s) avec dates de péremption\n"
                f"• {len(materiels_non_dates)} matériel(s) sans dates"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de créer le PDF: {e}")

    def diagnostiquer_dates(self):
        """Diagnostique comment sont stockées les dates dans les matériels."""
        # Récupérer quelques matériels pour diagnostic
        if hasattr(self.parent(), 'table_model'):
            materiels_visibles = []
            for i in range(min(10, self.parent().table_model.rowCount())):  # Max 10 pour diagnostic
                materiel = self.parent().table_model.get_materiel_by_row(i)
                if materiel:
                    materiels_visibles.append(materiel)
        else:
            materiels_visibles = load_db_data()[:10]  # Max 10 pour diagnostic
        
        diagnostic_text = "🔍 <b>Diagnostic des dates de péremption :</b><br><br>"
        
        if not materiels_visibles:
            diagnostic_text += "Aucun matériel trouvé pour le diagnostic."
        else:
            for i, materiel in enumerate(materiels_visibles):
                diagnostic_text += f"<b>Matériel {i+1} - ID: {materiel.get('id', 'N/A')}</b><br>"
                diagnostic_text += f"&nbsp;&nbsp;• Type: {materiel.get('type', 'N/A')}<br>"
                diagnostic_text += f"&nbsp;&nbsp;• Usage: {materiel.get('usage', 'N/A')}<br>"
                
                # Afficher tous les champs du matériel contenant des mots-clés de date
                champs_dates_trouves = []
                for key, value in materiel.items():
                    if any(keyword in key.lower() for keyword in ['date', 'peremption', 'expiration', 'validit']):
                        champs_dates_trouves.append(f"{key}: {value}")
                        diagnostic_text += f"&nbsp;&nbsp;• {key}: {value}<br>"
                
                if not champs_dates_trouves:
                    diagnostic_text += f"&nbsp;&nbsp;• <i>Aucun champ de date trouvé</i><br>"
                
                # Vérifier ce que trouve notre fonction
                date_trouvee = self.get_date_peremption(materiel)
                diagnostic_text += f"&nbsp;&nbsp;• <b>Date détectée:</b> {date_trouvee or 'Aucune'}<br>"
                
                if date_trouvee:
                    date_parsee = self.parse_date(date_trouvee)
                    diagnostic_text += f"&nbsp;&nbsp;• <b>Date parsée:</b> {date_parsee or 'Échec du parsing'}<br>"
                    if date_parsee:
                        jours_restants = (date_parsee - datetime.now()).days
                        diagnostic_text += f"&nbsp;&nbsp;• <b>Jours restants:</b> {jours_restants}<br>"
                
                diagnostic_text += "<br>"
        
        # Afficher le diagnostic
        QMessageBox.information(self, "Diagnostic des dates", diagnostic_text)


# ====================================================================
# FENÊTRE PRINCIPALE DE GESTION
# ====================================================================

class GestionMaterielWindow(QMainWindow):
    """Fenêtre principale de gestion du matériel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 Gestionnaire de Matériel - EasyCMIR")
        self.setGeometry(100, 100, 1400, 800)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # En-tête avec recherche
        header_layout = QHBoxLayout()
        
        # Recherche
        search_label = QLabel("🔍 Recherche:")
        search_label.setStyleSheet("font-weight: bold; color: #34495e; font-size: 14px;")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Rechercher (séparer les critères par des point-virgules, ex: DMC;Macon)")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
                min-width: 300px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.search_edit.textChanged.connect(self.search_materials)
        
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_edit)
        
        main_layout.addLayout(header_layout)
        
        # Table
        self.table_model = MaterielTableModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        
        # Configuration des colonnes
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)
        
        # Largeurs des colonnes optimisées
        column_widths = [90, 120, 100, 180, 120, 130, 80, 100, 150]  # 9 colonnes
        for i, width in enumerate(column_widths):
            if i < len(column_widths):
                self.table_view.setColumnWidth(i, width)
        
        # Style de la table
        self.table_view.setStyleSheet("""
            QTableView {
                gridline-color: #bdc3c7;
                font-size: 12px;
                selection-background-color: #3498db;
            }
            QTableView::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        main_layout.addWidget(self.table_view)
        
        # Barre d'outils avec boutons
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(20)
        
        # Boutons d'action avec icônes
        self.btn_add = self.create_icon_button("ajouter.png", "Ajouter un nouveau matériel")
        self.btn_add.setText("  Ajouter")
        self.btn_add.clicked.connect(self.add_material)
        
        self.btn_edit = self.create_icon_button("parametres-curseurs.png", "Modifier le matériel sélectionné")
        self.btn_edit.setText("  Modifier")
        self.btn_edit.clicked.connect(self.edit_material)
        
        self.btn_delete = self.create_icon_button("poubelle.png", "Supprimer le matériel sélectionné")
        self.btn_delete.setText("  Supprimer")
        self.btn_delete.clicked.connect(self.delete_material)
        
        self.btn_export = self.create_icon_button("exportation-de-fichiers.png", "Exporter en PDF")
        self.btn_export.setText("  Export PDF")
        self.btn_export.clicked.connect(self.export_pdf)
        
        self.btn_peremption = self.create_icon_button("calendrier-horloge.png", "Vérifier les dates de péremption")
        self.btn_peremption.setText("  Péremption")
        self.btn_peremption.clicked.connect(self.verifier_peremption)
        
        toolbar_layout.addWidget(self.btn_add)
        toolbar_layout.addWidget(self.btn_edit)
        toolbar_layout.addWidget(self.btn_delete)
        
        # Espacement de 350px avant les boutons export et péremption
        spacer_350px = QWidget()
        spacer_350px.setFixedWidth(350)
        toolbar_layout.addWidget(spacer_350px)
        
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_peremption)
        toolbar_layout.addStretch()
        
        # Info sur le chemin de la base de données
        db_path = get_db_file_path()
        path_label = QLabel(f"📄 Base de données: {os.path.basename(db_path)}")
        path_label.setStyleSheet("color: #000000; font-size: 11px; font-weight: bold;")
        path_label.setToolTip(f"Chemin complet: {db_path}")
        toolbar_layout.addWidget(path_label)
        
        main_layout.addLayout(toolbar_layout)
        
        # Barre de statut
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #ecf0f1;
                color: #000000;
                font-weight: bold;
                font-size: 12px;
                border-top: 1px solid #bdc3c7;
                padding: 5px;
            }
        """)
        self.update_status()

    def create_icon_button(self, icon_name, tooltip_text):
        """Crée un bouton avec une icône et un style moderne."""
        button = QPushButton()
        
        # Charger l'icône
        icon_path = os.path.join(ICONS_DIR, icon_name)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(24, 24))
        else:
            # Icônes de fallback
            fallback_icons = {
                "ajouter.png": "➕",
                "parametres-curseurs.png": "⚙️",
                "poubelle.png": "🗑️",
                "exportation-de-fichiers.png": "📄",
                "calendrier-horloge.png": "⏰"
            }
            button.setText(fallback_icons.get(icon_name, "?"))
        
        button.setToolTip(tooltip_text)
        
        # Style moderne des boutons (taille réduite de 50%)
        button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: bold;
                color: #000000;
                min-width: 60px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: white;
                border-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2980b9;
                border-color: #21618c;
            }
        """)
        
        return button

    def create_confirmation_dialog(self, parent, title, message):
        """Crée une boîte de dialogue de confirmation avec boutons Oui/Non personnalisés."""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # Réserver une hauteur minimale de 30px pour le texte
        msg_box.setMinimumHeight(150)  # Hauteur minimale globale
        msg_box.setMinimumWidth(400)   # Largeur minimale pour éviter que le texte soit trop condensé
        
        # Bouton Oui avec icône
        btn_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        oui_icon_path = os.path.join(ICONS_DIR, "angle-cercle-vers-le-bas.png")
        if os.path.exists(oui_icon_path):
            btn_oui.setIcon(QIcon(oui_icon_path))
        else:
            btn_oui.setText("✓ Oui")  # Fallback avec emoji
        
        # Bouton Non avec icône
        btn_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        non_icon_path = os.path.join(ICONS_DIR, "croix-cercle.png")
        if os.path.exists(non_icon_path):
            btn_non.setIcon(QIcon(non_icon_path))
        else:
            btn_non.setText("✗ Non")  # Fallback avec emoji
        
        msg_box.setDefaultButton(btn_non)  # Non par défaut pour sécurité
        
        # Style des boutons
        msg_box.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 12px;
                font-weight: bold;
                color: #000000;
                min-width: 80px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: white;
            }
        """)
        
        msg_box.exec()
        return msg_box.clickedButton() == btn_oui

    def load_data(self):
        """Charge et rafraîchit les données."""
        self.table_model.refresh_data()
        self.update_status()

    def search_materials(self):
        """Effectue la recherche dans les matériels."""
        query = self.search_edit.text()
        self.table_model.search_materiels(query)
        self.update_status()

    def update_status(self):
        """Met à jour la barre de statut."""
        count = self.table_model.rowCount()
        db_path = get_db_file_path()
        self.status_bar.showMessage(f"📊 {count} matériel(s) affiché(s) • 💾 {os.path.basename(db_path)}")

    def add_material(self):
        """Ajoute un nouveau matériel."""
        dialog = MaterielDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def edit_material(self):
        """Modifie le matériel sélectionné."""
        current_row = self.table_view.currentIndex().row()
        if current_row < 0:
            QMessageBox.information(self, "Info", "Veuillez sélectionner un matériel à modifier.")
            return
        
        materiel = self.table_model.get_materiel_by_row(current_row)
        if materiel:
            dialog = MaterielDialog(materiel_id=materiel.get('id'), parent=self)
            if dialog.exec():
                self.load_data()

    def delete_material(self):
        """Supprime le matériel sélectionné."""
        current_row = self.table_view.currentIndex().row()
        if current_row < 0:
            QMessageBox.information(self, "Info", "Veuillez sélectionner un matériel à supprimer.")
            return
        
        materiel = self.table_model.get_materiel_by_row(current_row)
        if not materiel:
            return
        
        # Confirmation avec boutons personnalisés
        if self.create_confirmation_dialog(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer le matériel '{materiel.get('id', '')}'?"
        ):
            # Supprimer de la base de données
            if delete_materiel_from_db(materiel.get('id')):
                self.load_data()
                QMessageBox.information(self, "Succès", "Matériel supprimé avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer le matériel.")

    def export_pdf(self):
        """Exporte les données en PDF."""
        data_to_export = [self.table_model._headers] + self.table_model._data
        if len(data_to_export) <= 1:
            QMessageBox.information(self, "Info", "Aucune donnée à exporter.")
            return
        
        # Dialogue de sélection du fichier
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'export PDF",
            f"export_materiel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "Fichiers PDF (*.pdf)"
        )
        
        if not filename:
            return
        
        try:
            # Configuration PDF en paysage
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            
            # Créer le tableau
            table = Table(data_to_export)
            
            # Style du tableau
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            table.setStyle(style)
            doc.build([table])
            
            QMessageBox.information(self, "Succès", f"Export PDF créé: {filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de créer le PDF: {e}")

    def verifier_peremption(self):
        """Ouvre la fenêtre de vérification des dates de péremption."""
        dialog = PeremptionDialog(parent=self)
        dialog.exec()


# ====================================================================
# FONCTION D'OUVERTURE DIRECTE
# ====================================================================

def open_gestion_materiel(parent=None):
    """Ouvre directement la fenêtre de gestion du matériel."""
    window = GestionMaterielWindow(parent)
    window.show()
    return window


# ====================================================================
# DIALOGUE PRINCIPAL D'INTÉGRATION (OBSOLÈTE - GARDÉ POUR COMPATIBILITÉ)
# ====================================================================

class BD_gestDialog:
    """Classe de compatibilité - redirige vers l'ouverture directe."""
    
    def __init__(self, parent=None):
        # Ouvrir directement la fenêtre de gestion sans créer de QDialog
        self.manager_window = GestionMaterielWindow(parent)
        self.manager_window.show()
    
    def exec(self):
        """Méthode de compatibilité pour l'interface QDialog."""
        return 1  # Retourne QDialog.Accepted
    
    def exec_(self):
        """Méthode de compatibilité pour l'ancienne API Qt."""
        return 1  # Retourne QDialog.Accepted


if __name__ == "__main__":
    # Test de l'application
    import sys
    app = QApplication(sys.argv)
    
    # Tester directement la fenêtre de gestion
    window = GestionMaterielWindow()
    window.show()
    
    sys.exit(app.exec())

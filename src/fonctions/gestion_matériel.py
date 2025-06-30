import sys
import sqlite3
import csv
import re
import os
from datetime import datetime, timedelta
from PySide6.QtCore import (Qt, QAbstractTableModel, QModelIndex, QSize)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLineEdit, QFormLayout, QDialog,
    QDialogButtonBox, QMessageBox, QHeaderView, QLabel, QSpinBox,
    QFileDialog, QGroupBox, QComboBox, QSlider, QFrame, QSizePolicy
)
from PySide6.QtGui import QIcon
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from ..utils.config_manager import config_manager
from ..constants import ICONS_DIR


def get_config_db_path():
    """Récupère le chemin de la base de données depuis la configuration."""
    try:
        return config_manager.get_database_path()
    except Exception:
        # En cas d'erreur, retourne le chemin par défaut
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, "data", "materiel.db")


def get_default_db_path():
    """Retourne le chemin par défaut de la base de données."""
    # Obtenir le répertoire racine du projet
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_path = os.path.join(project_root, "data", "materiel.db")
    
    return db_path


def check_database_exists(db_path):
    """Vérifie si la base de données existe."""
    return os.path.exists(db_path)


def initialiser_db(db_name=None):
    """Crée les tables de la BDD avec un ID texte si la base existe."""
    if db_name is None:
        db_name = get_config_db_path()
    
    # Vérifier que la base de données existe
    if not check_database_exists(db_name):
        return False
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Table principale pour le matériel avec un ID TEXTE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materiel (
            id TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            type TEXT,
            usage TEXT,
            marque TEXT,
            lieu TEXT,
            affectation TEXT
        )
    """)
    
    # Table pour les caractéristiques avec une clé étrangère TEXTE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS caracteristiques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materiel_id TEXT,
            nom_caracteristique TEXT NOT NULL,
            valeur_caracteristique TEXT,
            FOREIGN KEY (materiel_id) REFERENCES materiel (id) ON DELETE CASCADE
        )
    """)
    
    # Ajouter la colonne usage si elle n'existe pas encore (pour compatibilité avec anciennes versions)
    try:
        cursor.execute("ALTER TABLE materiel ADD COLUMN usage TEXT")
    except sqlite3.OperationalError:
        # La colonne existe déjà
        pass
    
    conn.commit()
    conn.close()
    return True


def generer_prochain_id_rt(db_name=None):
    """Génère le prochain ID-RT-xxx en se basant sur le plus grand existant."""
    if db_name is None:
        db_name = get_config_db_path()
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM materiel WHERE id LIKE 'ID-RT-%'")
    ids = cursor.fetchall()
    conn.close()

    max_num = 0
    if ids:
        for (id_str,) in ids:
            # Extrait le nombre de l'ID avec une expression régulière
            match = re.search(r'(\d+)$', id_str)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    
    return f"ID-RT-{max_num + 1}"


def importer_csv_si_necessaire(db_name=None, csv_file_path=None):
    """Importe les données du CSV si la table materiel est vide."""
    if db_name is None:
        db_name = get_config_db_path()
    
    if csv_file_path is None:
        return  # Pas de fichier CSV spécifié
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Vérifier si la table est vide
    cursor.execute("SELECT COUNT(*) FROM materiel")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # La table contient déjà des données

    print("Base de données vide. Tentative d'importation du CSV...")

    try:
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Colonnes de base à mapper directement (noms du CSV -> noms de la base)
            COLUMN_MAPPING = {
                'Id': 'ID-RT',
                ' Modèle': 'Designation', 
                'Type': 'Type',
                'Usage': 'Usage',
                'Marque': 'Marque',
                'CIS d\'affectation': 'Lieu',
                'Vecteur': 'Affectation'
            }
            
            # Colonnes de base pour éviter de les dupliquer en caractéristiques
            CORE_COLUMNS = ['Id', ' Modèle', 'Type', 'Usage', 'Marque', 'CIS d\'affectation', 'Vecteur']

            for row in reader:
                # Gestion des noms de colonnes potentiellement variables (minuscules/majuscules, espaces)
                row_cleaned = {k.strip() if k.strip() != k else k: v for k, v in row.items()}

                materiel_id = row_cleaned.get('Id')
                if not materiel_id:
                    continue  # Ignorer les lignes sans ID

                # Insertion dans la table materiel
                materiel_data = (
                    materiel_id,
                    row_cleaned.get(' Modèle', ''),
                    row_cleaned.get('Type', ''),
                    row_cleaned.get('Usage', ''),
                    row_cleaned.get('Marque', ''),
                    row_cleaned.get('CIS d\'affectation', ''),
                    row_cleaned.get('Vecteur', '')
                )
                cursor.execute("INSERT INTO materiel (id, nom, type, usage, marque, lieu, affectation) VALUES (?, ?, ?, ?, ?, ?, ?)", materiel_data)

                # Insertion des autres colonnes comme caractéristiques
                for col_name, value in row_cleaned.items():
                    if col_name not in CORE_COLUMNS and value:  # Si ce n'est pas une colonne de base et qu'il y a une valeur
                        carac_data = (materiel_id, col_name, value)
                        cursor.execute("INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique) VALUES (?, ?, ?)", carac_data)

            print(f"Importation depuis '{csv_file_path}' terminée avec succès.")

    except FileNotFoundError:
        print(f"AVERTISSEMENT : Fichier CSV '{csv_file_path}' non trouvé. La base de données restera vide.")
    except Exception as e:
        print(f"ERREUR lors de l'importation du CSV : {e}")
    
    conn.commit()
    conn.close()


class MaterielTableModel(QAbstractTableModel):
    """Modèle de données pour lier la BDD au QTableView."""
    
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ["ID-RT", "Type", "Usage", "Modèle", "Marque", "Numéro de série", "Quantité", "Statut", "CIS affectation", "Vecteur"]

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

    def refresh_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class MaterielDialog(QDialog):
    """Boîte de dialogue pour créer ou éditer un matériel et ses caractéristiques."""
    
    def __init__(self, materiel_id=None, db_name=None, parent=None):
        super().__init__(parent)
        self.db_name = db_name or get_config_db_path()
        self.materiel_id = materiel_id
        
        self.setWindowTitle("Ajouter/Modifier du Matériel")
        self.setMinimumWidth(400)

        # Champs principaux
        self.id_label = QLabel()  # Pour afficher l'ID en mode modification
        self.nom = QLineEdit()
        self.type = QLineEdit()
        self.usage = QLineEdit()
        self.marque = QLineEdit()
        self.numero_serie = QLineEdit()
        self.quantite = QLineEdit()
        self.statut = QComboBox()
        self.lieu = QComboBox()
        self.affectation = QComboBox()
        
        # Configurer les ComboBox comme éditables
        self.statut.setEditable(True)
        self.lieu.setEditable(True)
        self.affectation.setEditable(True)
        
        # Charger les options des menus déroulants
        self.charger_options_combobox()
        
        form_layout = QFormLayout()
        if self.materiel_id:
            form_layout.addRow("ID-RT:", self.id_label)
        form_layout.addRow("Nom:", self.nom)
        form_layout.addRow("Type:", self.type)
        form_layout.addRow("Usage:", self.usage)
        form_layout.addRow("Marque:", self.marque)
        form_layout.addRow("Numéro de série:", self.numero_serie)
        form_layout.addRow("Quantité:", self.quantite)
        form_layout.addRow("Statut:", self.statut)
        form_layout.addRow("CIS d'affectation:", self.lieu)
        form_layout.addRow("Vecteur:", self.affectation)

        self.caracteristiques_layout = QVBoxLayout()
        self.btn_add_caracteristique = QPushButton("Ajouter une caractéristique")
        self.btn_add_caracteristique.clicked.connect(self.ajouter_champ_caracteristique)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(QLabel("Caractéristiques personnalisées:"))
        main_layout.addLayout(self.caracteristiques_layout)
        main_layout.addWidget(self.btn_add_caracteristique)
        main_layout.addWidget(button_box)

        self.caracteristiques_widgets = []
        if self.materiel_id:
            self.charger_donnees()

    def ajouter_champ_caracteristique(self, nom="", valeur=""):
        layout = QHBoxLayout()
        # S'assurer que nom et valeur sont des chaînes de caractères
        nom_str = str(nom) if nom is not None else ""
        valeur_str = str(valeur) if valeur is not None else ""
        
        nom_widget = QLineEdit(nom_str)
        nom_widget.setPlaceholderText("Nom de la caractéristique")
        valeur_widget = QLineEdit(valeur_str)
        valeur_widget.setPlaceholderText("Valeur")
        btn_supprimer = QPushButton("X")
        layout.addWidget(nom_widget)
        layout.addWidget(valeur_widget)
        layout.addWidget(btn_supprimer)
        self.caracteristiques_layout.addLayout(layout)
        self.caracteristiques_widgets.append((layout, nom_widget, valeur_widget, btn_supprimer))
        btn_supprimer.clicked.connect(lambda: self.supprimer_champ_caracteristique(layout))

    def supprimer_champ_caracteristique(self, layout):
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.caracteristiques_widgets = [w for w in self.caracteristiques_widgets if w[0] is not layout]
        layout.deleteLater()

    def charger_donnees(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        self.id_label.setText(self.materiel_id)
        cursor.execute("SELECT nom, type, usage, marque, lieu, affectation FROM materiel WHERE id=?", (self.materiel_id,))
        res = cursor.fetchone()
        if res:
            self.nom.setText(res[0] or "")
            self.type.setText(res[1] or "")
            self.usage.setText(res[2] or "")
            self.marque.setText(res[3] or "")
            # Définir les valeurs des ComboBox
            self.lieu.setCurrentText(res[4] or "")
            self.affectation.setCurrentText(res[5] or "")
        
        # Récupérer statut, quantité et numéro de série depuis les caractéristiques
        cursor.execute("SELECT nom_caracteristique, valeur_caracteristique FROM caracteristiques WHERE materiel_id=? AND nom_caracteristique IN ('Statut', 'Quantité', 'Numéro de série', 'N° de série', 'Numero de serie', 'Serial', 'SN')", (self.materiel_id,))
        caracteristiques_speciales = cursor.fetchall()
        
        for nom_car, val_car in caracteristiques_speciales:
            if nom_car == 'Statut':
                self.statut.setCurrentText(val_car or "")
            elif nom_car == 'Quantité':
                self.quantite.setText(val_car or "")
            elif nom_car in ['Numéro de série', 'N° de série', 'Numero de serie', 'Serial', 'SN']:
                self.numero_serie.setText(val_car or "")

        # Récupérer les autres caractéristiques (exclure Statut, Quantité, Numéro de série et Modèle)
        cursor.execute("SELECT nom_caracteristique, valeur_caracteristique FROM caracteristiques WHERE materiel_id=? AND nom_caracteristique NOT IN ('Statut', 'Quantité', 'Numéro de série', 'N° de série', 'Numero de serie', 'Serial', 'SN', 'Modèle')", (self.materiel_id,))
        for nom_car, val_car in cursor.fetchall():
            # S'assurer que les valeurs sont des chaînes
            nom_safe = str(nom_car) if nom_car is not None else ""
            val_safe = str(val_car) if val_car is not None else ""
            self.ajouter_champ_caracteristique(nom_safe, val_safe)
        
        conn.close()

    def accept(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        data_principales = (self.nom.text(), self.type.text(), self.usage.text(), self.marque.text(), self.lieu.currentText(), self.affectation.currentText())

        if self.materiel_id is None:  # Création
            new_id = generer_prochain_id_rt(self.db_name)
            self.materiel_id = new_id
            cursor.execute("INSERT INTO materiel (id, nom, type, usage, marque, lieu, affectation) VALUES (?, ?, ?, ?, ?, ?, ?)", (new_id, *data_principales))
        else:  # Mise à jour
            cursor.execute("UPDATE materiel SET nom=?, type=?, usage=?, marque=?, lieu=?, affectation=? WHERE id=?", (*data_principales, self.materiel_id))
            cursor.execute("DELETE FROM caracteristiques WHERE materiel_id=?", (self.materiel_id,))

        # Sauvegarder Statut, Quantité et Numéro de série comme caractéristiques spéciales
        if self.statut.currentText():
            cursor.execute("INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique) VALUES (?, ?, ?)", (self.materiel_id, 'Statut', self.statut.currentText()))
        
        if self.quantite.text():
            cursor.execute("INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique) VALUES (?, ?, ?)", (self.materiel_id, 'Quantité', self.quantite.text()))
        
        if self.numero_serie.text():
            cursor.execute("INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique) VALUES (?, ?, ?)", (self.materiel_id, 'Numéro de série', self.numero_serie.text()))

        # Sauvegarder les autres caractéristiques personnalisées
        for _, nom_widget, valeur_widget, _ in self.caracteristiques_widgets:
            nom_car = nom_widget.text()
            val_car = valeur_widget.text()
            if nom_car:
                cursor.execute(
                    "INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique) VALUES (?, ?, ?)",
                    (self.materiel_id, nom_car, val_car)
                )

        conn.commit()
        conn.close()
        super().accept()

    def charger_options_combobox(self):
        """Charge les options des ComboBox à partir des données existantes dans la base."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Charger les statuts distincts depuis les caractéristiques
            cursor.execute("""
                SELECT DISTINCT valeur_caracteristique 
                FROM caracteristiques 
                WHERE nom_caracteristique = 'Statut' 
                AND valeur_caracteristique IS NOT NULL 
                AND valeur_caracteristique != ''
                ORDER BY valeur_caracteristique
            """)
            statuts = [row[0] for row in cursor.fetchall()]
            self.statut.addItems([""] + statuts)  # Ajouter une option vide en premier
            
            # Charger les CIS distincts depuis la table materiel
            cursor.execute("""
                SELECT DISTINCT lieu 
                FROM materiel 
                WHERE lieu IS NOT NULL 
                AND lieu != ''
                ORDER BY lieu
            """)
            cis = [row[0] for row in cursor.fetchall()]
            self.lieu.addItems([""] + cis)  # Ajouter une option vide en premier
            
            # Charger les vecteurs distincts depuis la table materiel
            cursor.execute("""
                SELECT DISTINCT affectation 
                FROM materiel 
                WHERE affectation IS NOT NULL 
                AND affectation != ''
                ORDER BY affectation
            """)
            vecteurs = [row[0] for row in cursor.fetchall()]
            self.affectation.addItems([""] + vecteurs)  # Ajouter une option vide en premier
            
        except Exception as e:
            print(f"Erreur lors du chargement des options : {e}")
        finally:
            conn.close()

    def show_message(self, title, text, message_type="info", buttons=None):
        """
        Méthode unifiée pour afficher tous types de messages avec style cohérent.
        
        Args:
            title (str): Titre du popup
            text (str): Texte du message (supporte HTML)
            message_type (str): Type de message ("info", "warning", "error", "question")
            buttons (QMessageBox.StandardButton): Boutons à afficher (par défaut selon le type)
        
        Returns:
            QMessageBox.StandardButton: Bouton cliqué par l'utilisateur
        """
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        
        # Configuration selon le type de message
        if message_type == "info":
            msgbox.setIcon(QMessageBox.Icon.Information)
            if buttons is None:
                buttons = QMessageBox.StandardButton.Ok
        elif message_type == "warning":
            msgbox.setIcon(QMessageBox.Icon.Warning)
            # Ajouter l'icône d'attention personnalisée
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
            if buttons is None:
                buttons = QMessageBox.StandardButton.Ok
        elif message_type == "error":
            msgbox.setIcon(QMessageBox.Icon.Critical)
            # Ajouter l'icône d'attention personnalisée pour les erreurs critiques
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
            if buttons is None:
                buttons = QMessageBox.StandardButton.Ok
        elif message_type == "question":
            msgbox.setIcon(QMessageBox.Icon.Question)
            if buttons is None:
                buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        
        # Définir les boutons
        msgbox.setStandardButtons(buttons)
        
        # Calculer la taille optimale - amélioré pour textes multilignes
        text_length = len(text)
        base_width = 420
        base_height = 180
        
        # Compter les lignes réelles (balises HTML <br> et retours chariot)
        html_breaks = text.count('<br>') + text.count('<br/>') + text.count('<br />')
        real_line_count = text.count('\n') + html_breaks + (text_length // 60)
        
        # Ajuster la largeur pour les textes longs
        if text_length > 80:
            base_width = min(650, base_width + (text_length // 8))
        
        # Ajuster la hauteur pour les textes multi-lignes avec marge supplémentaire
        if real_line_count > 2:
            base_height = min(400, base_height + (real_line_count * 30))
        elif real_line_count > 1:
            base_height = min(320, base_height + (real_line_count * 25))
        
        # Taille minimale optimisée pour un bon rendu sans excès
        msgbox.setMinimumSize(base_width, base_height)
        msgbox.resize(base_width + 40, base_height + 40)
        
        # Style CSS unifié - compact mais professionnel
        msgbox.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 18px;
                min-width: 420px;
                min-height: 180px;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 8px;
                margin: 8px;
                margin-left: 25px;
                margin-top: 10px;
                margin-bottom: 10px;
                max-width: 400px;
                text-align: left;
                line-height: 1.4;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
            QMessageBox QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        # Pour les questions avec Yes/No, personnaliser les boutons
        if message_type == "question" and buttons == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
            # Récupérer les boutons après les avoir ajoutés
            yes_btn = msgbox.button(QMessageBox.StandardButton.Yes)
            no_btn = msgbox.button(QMessageBox.StandardButton.No)
            
            if yes_btn and no_btn:
                # Charger les icônes personnalisées
                yes_icon_path = os.path.join(ICONS_DIR, "angle-cercle-vers-le-bas.png")
                no_icon_path = os.path.join(ICONS_DIR, "croix-cercle.png")
                
                # Configurer le bouton Oui
                if os.path.exists(yes_icon_path):
                    yes_btn.setIcon(QIcon(yes_icon_path))
                    yes_btn.setText("  Oui")
                    yes_btn.setIconSize(QSize(20, 20))
                else:
                    yes_btn.setText("✓ Oui")
                
                # Configurer le bouton Non
                if os.path.exists(no_icon_path):
                    no_btn.setIcon(QIcon(no_icon_path))
                    no_btn.setText("  Non")
                    no_btn.setIconSize(QSize(20, 20))
                else:
                    no_btn.setText("✗ Non")
                
                # Style spécial pour les boutons de confirmation
                button_style = """
                    QPushButton {
                        padding: 8px 16px;
                        font-weight: bold;
                        border-radius: 4px;
                        border: 2px solid #ccc;
                        background-color: #f8f9fa;
                        color: #333;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border-color: #007bff;
                    }
                    QPushButton:pressed {
                        background-color: #dee2e6;
                    }
                """
                yes_btn.setStyleSheet(button_style)
                no_btn.setStyleSheet(button_style)
                
                # Définir le bouton par défaut
                msgbox.setDefaultButton(no_btn)
        
        return msgbox.exec()

    def show_info_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "info")
    
    def show_warning_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "warning")
    
    def show_error_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "error")

    def verifier_peremption(self):
        """Ouvre la fenêtre de vérification des dates de péremption."""
        dialog = PeremptionDialog(db_name=self.db_name, parent=self)
        dialog.exec()

    def exporter_pdf(self):
        """Exporter les données du tableau en PDF."""
        data_to_export = [self.table_model._headers] + self.table_model._data
        if len(data_to_export) <= 1:
            self.show_info_message("Info", "Aucune donnée à exporter.")
            return
            
        # Dialogue de sélection du fichier de sortie
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'export PDF",
            "export_materiel.pdf",
            "Fichiers PDF (*.pdf);;Tous les fichiers (*)"
        )
        
        if not filename:  # L'utilisateur a annulé
            return
            
        try:
            # Configuration de la page en format paysage
            page_width, page_height = landscape(letter)
            # Marges (gauche, droite, haut, bas)
            margins = 36  # 0.5 pouce de marge de chaque côté
            available_width = page_width - (2 * margins)
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter),
                                leftMargin=margins, rightMargin=margins,
                                topMargin=margins, bottomMargin=margins)
            
            # Calculer les largeurs de colonnes pour s'adapter à la page
            num_cols = len(self.table_model._headers)
            col_widths = None
            if num_cols > 0:
                # Largeurs relatives basées sur le contenu typique de chaque colonne
                # ID-RT, Type, Usage, Modèle, Marque, N°série, Quantité, Statut, CIS affectation, Vecteur
                col_ratios = [0.8, 1.0, 1.0, 1.2, 1.0, 1.2, 0.6, 1.0, 1.2, 1.2]
                total_ratio = sum(col_ratios[:num_cols])
                col_widths = [(ratio / total_ratio) * available_width for ratio in col_ratios[:num_cols]]
            
            # Créer le tableau avec largeurs définies
            table = Table(data_to_export, colWidths=col_widths)
            
            # Style du tableau optimisé
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            
            # Ajouter l'alternance de couleurs pour les lignes de données
            for i in range(1, len(data_to_export)):
                if i % 2 == 0:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
            
            style = TableStyle(table_style)
            table.setStyle(style)
            
            doc.build([table])
            self.show_info_message("Succès", f"Le fichier '{filename}' a été créé en format paysage adapté à la page.")
        except Exception as e:
            self.show_error_message("Erreur", f"Impossible de générer le PDF : {e}")

    def create_icon_button(self, icon_name, tooltip_text):
        """Crée un bouton avec une icône et un tooltip."""
        button = QPushButton()
        
        # Construire le chemin vers l'icône
        icon_path = os.path.join(ICONS_DIR, icon_name)
        
        if os.path.exists(icon_path):
            # Charger l'icône
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(16, 16))  # Taille de l'icône réduite de moitié
        else:
            # Si l'icône n'existe pas, utiliser du texte de fallback
            fallback_text = {
                "ajouter.png": "➕",
                "parametres-curseurs.png": "⚙️",
                "poubelle.png": "🗑️",
                "calendrier-horloge.png": "📅",
                "exportation-de-fichiers.png": "📄"
            }
            button.setText(fallback_text.get(icon_name, "?"))
        
        # Définir le tooltip
        button.setToolTip(tooltip_text)
        
        # Style du bouton
        button.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 6px;
                background-color: #ecf0f1;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
                color: white;
            }
        """)
        
        return button

# Classe principale pour l'intégration dans l'application EasyCMIR
class BD_gestDialog(QDialog):
    """Dialog principal pour la gestion de matériel - Intégration EasyCMIR."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion de Matériel")
        self.setFixedSize(500, 600)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title_label = QLabel("📦 Gestion de Matériel")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Description
        description = QLabel("""
<b>Gestionnaire de matériel avec base de données intégrée</b><br><br>
<b>Fonctionnalités disponibles :</b><br>
• Ajouter, modifier, supprimer du matériel<br>
• Recherche et filtrage avancés<br>
• Gestion des caractéristiques personnalisées<br>
• Vérification des dates de péremption<br>
• Export PDF des données<br>
• Gestion des ID automatiques (ID-RT-xxx)<br><br>
<b>Base de données :</b> data/materiel.db<br>
<b>Format ID :</b> ID-RT-1, ID-RT-2, etc.
        """)
        description.setStyleSheet("""
            QLabel {
                color: #34495e;
                padding: 15px;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                font-size: 11px;
                line-height: 1.5;
            }
        """)
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        # Bouton pour ouvrir la gestion de matériel
        btn_materiel = QPushButton("🔧 Ouvrir la Gestion de Matériel")
        btn_materiel.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        btn_materiel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_materiel.clicked.connect(self.ouvrir_gestion_materiel)
        
        main_layout.addWidget(btn_materiel)
        
        # Espacement flexible
        main_layout.addStretch()
        
        # Bouton Fermer
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        btn_close = QPushButton("Fermer")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        btn_close.clicked.connect(self.close)
        
        close_layout.addWidget(btn_close)
        main_layout.addLayout(close_layout)

    def show_message(self, title, text, message_type="info"):
        """
        Méthode unifiée pour afficher tous types de messages avec style cohérent.
        
        Args:
            title (str): Titre du popup
            text (str): Texte du message (supporte HTML)
            message_type (str): Type de message ("info", "warning", "error")
        
        Returns:
            QMessageBox.StandardButton: Bouton cliqué par l'utilisateur
        """
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        
        # Configuration selon le type de message
        if message_type == "info":
            msgbox.setIcon(QMessageBox.Icon.Information)
        elif message_type == "warning":
            msgbox.setIcon(QMessageBox.Icon.Warning)
            # Ajouter l'icône d'attention personnalisée
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
        elif message_type == "error":
            msgbox.setIcon(QMessageBox.Icon.Critical)
            # Ajouter l'icône d'attention personnalisée pour les erreurs critiques
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
        
        # Calculer la taille optimale - amélioré pour textes multilignes
        text_length = len(text)
        base_width = 420
        base_height = 180
        
        # Compter les lignes réelles (balises HTML <br> et retours chariot)
        html_breaks = text.count('<br>') + text.count('<br/>') + text.count('<br />')
        real_line_count = text.count('\n') + html_breaks + (text_length // 60)
        
        # Ajuster la largeur pour les textes longs
        if text_length > 80:
            base_width = min(650, base_width + (text_length // 8))
        
        # Ajuster la hauteur pour les textes multi-lignes avec marge supplémentaire
        if real_line_count > 2:
            base_height = min(400, base_height + (real_line_count * 30))
        elif real_line_count > 1:
            base_height = min(320, base_height + (real_line_count * 25))
        
        # Taille minimale optimisée pour un bon rendu sans excès
        msgbox.setMinimumSize(base_width, base_height)
        msgbox.resize(base_width + 40, base_height + 40)
        
        # Style CSS unifié - compact mais professionnel
        msgbox.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 18px;
                min-width: 420px;
                min-height: 180px;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 8px;
                margin: 8px;
                margin-left: 25px;
                margin-top: 10px;
                margin-bottom: 10px;
                max-width: 400px;
                text-align: left;
                line-height: 1.4;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
            QMessageBox QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        return msgbox.exec()

    def show_error_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "error")

    def show_info_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "info")

    def show_warning_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "warning")
    
    def ouvrir_gestion_materiel(self):
        """Ouvre la fenêtre de gestion de matériel."""
        try:
            self.materiel_window = GestionMaterielWindow(self)
            self.materiel_window.show()
        except Exception as e:
            self.show_error_message(
                "Erreur", 
                f"Impossible d'ouvrir la gestion de matériel:\n{str(e)}"
            )


class PeremptionDialog(QDialog):
    """Boîte de dialogue pour définir les critères de vérification des dates de péremption."""
    
    def __init__(self, db_name=None, parent=None):
        super().__init__(parent)
        self.db_name = db_name or get_config_db_path()
        
        self.setWindowTitle("Vérification des dates de péremption")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        # Widgets principaux
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
• <b>Filtrage par statut :</b> Ne sont pris en compte que les appareils avec le statut "En service" ou "non réceptionné"<br>
• Les appareils avec le statut "Hors parc" sont automatiquement exclus<br>
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

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(instructions)
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        main_layout.addWidget(button_box)

    def parse_date(self, date_str):
        """Parse une date depuis différents formats possibles."""
        if not date_str or not isinstance(date_str, str):
            return None
        
        date_str = date_str.strip()
        if not date_str:
            return None
        
        # Formats numériques standards
        formats = [
            "%d/%m/%Y",    # JJ/MM/AAAA
            "%Y-%m-%d",    # AAAA-MM-JJ
            "%d-%m-%Y",    # JJ-MM-AAAA
            "%d.%m.%Y",    # JJ.MM.AAAA
            "%Y/%m/%d",    # AAAA/MM/JJ
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Gestion des formats français avec noms de mois
        mois_fr = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        # Format "1 octobre 2024"
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.match(pattern, date_str, re.IGNORECASE)
        if match:
            jour, mois_nom, annee = match.groups()
            mois_nom_lower = mois_nom.lower()
            if mois_nom_lower in mois_fr:
                try:
                    date_formatted = f"{jour.zfill(2)}/{mois_fr[mois_nom_lower]}/{annee}"
                    return datetime.strptime(date_formatted, "%d/%m/%Y")
                except ValueError:
                    pass
        
        return None

    def generer_rapport_peremption(self):
        """Génère le rapport PDF des matériels en péremption."""
        try:
            delai_annees = self.delai_spinbox.value()
            date_limite = datetime.now() + timedelta(days=delai_annees * 365)
            
            # Rechercher les matériels avec date de péremption
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Rechercher toutes les caractéristiques liées aux dates de péremption
            # avec filtrage sur le statut (exclure "Hors parc")
            query = """
            SELECT DISTINCT m.id, m.nom, m.type, m.usage, m.marque, m.lieu, m.affectation,
                c.valeur_caracteristique as date_peremption
            FROM materiel m
            INNER JOIN caracteristiques c ON m.id = c.materiel_id
            LEFT JOIN caracteristiques statut ON m.id = statut.materiel_id AND statut.nom_caracteristique = 'Statut'
            WHERE (c.nom_caracteristique LIKE '%péremption%' 
            OR c.nom_caracteristique LIKE '%expiration%'
            OR c.nom_caracteristique LIKE '%validité%'
            OR c.nom_caracteristique LIKE '%échéance%'
            OR c.nom_caracteristique LIKE '%fin%'
            OR c.nom_caracteristique LIKE '%expire%'
            OR c.nom_caracteristique LIKE '%date%')
            AND (statut.valeur_caracteristique IS NULL 
                OR statut.valeur_caracteristique NOT LIKE '%Hors parc%'
                OR statut.valeur_caracteristique LIKE '%En service%'
                OR statut.valeur_caracteristique LIKE '%non réceptionné%')
            ORDER BY m.id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            
            # Filtrer et analyser les dates
            materiels_perimes = []
            materiels_non_dates = []
            
            for row in results:
                id_rt, nom, type_mat, usage, marque, lieu, affectation, date_str = row
                
                date_peremption = self.parse_date(date_str)
                
                if date_peremption:
                    jours_restants = (date_peremption - datetime.now()).days
                    if jours_restants <= delai_annees * 365:
                        statut = "PÉRIMÉ" if jours_restants < 0 else f"{jours_restants} jours"
                        materiels_perimes.append([
                            id_rt, nom, type_mat or "", usage or "", marque or "",
                            date_peremption.strftime("%d/%m/%Y"), statut, lieu or "", affectation or ""
                        ])
                else:
                    # Garder trace des matériels avec des dates non parsables
                    materiels_non_dates.append([id_rt, nom, date_str])
            
            if not materiels_perimes:
                self.show_info_message(
                    "Aucun matériel trouvé", 
                    f"Aucun matériel trouvé avec une date de péremption dans les {delai_annees} prochaine(s) année(s).\n\n"
                    f"Matériels analysés: {len(results)}\n"
                    f"Dates non parsables: {len(materiels_non_dates)}"
                )
                return
            
            # Générer le PDF
            self.generer_pdf_peremption(materiels_perimes, delai_annees, materiels_non_dates)
            
            self.accept()
            
        except Exception as e:
            self.show_error_message("Erreur", f"Erreur lors de la génération du rapport: {e}")

    def generer_pdf_peremption(self, materiels, delai_annees, materiels_non_dates):
        """Génère le PDF avec la liste des matériels en péremption."""
        # Dialogue de sélection du fichier de sortie
        filename_default = f"rapport_peremption_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le rapport de péremption",
            filename_default,
            "Fichiers PDF (*.pdf);;Tous les fichiers (*)"
        )
        
        if not filename:  # L'utilisateur a annulé
            return
        
        # Configuration de la page
        page_width, page_height = landscape(letter)
        margins = 36
        available_width = page_width - (2 * margins)
        
        doc = SimpleDocTemplate(filename, pagesize=landscape(letter),
                              leftMargin=margins, rightMargin=margins,
                              topMargin=margins, bottomMargin=margins)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']
        
        # Éléments du document
        elements = []
        
        # Titre
        title = Paragraph(f"<b>Rapport de Péremption - Délai: {delai_annees} an(s)</b>", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Informations générales
        date_rapport = datetime.now().strftime("%d/%m/%Y à %H:%M")
        info_text = f"<b>Date du rapport:</b> {date_rapport}<br/><b>Nombre de matériels concernés:</b> {len(materiels)}"
        info_para = Paragraph(info_text, normal_style)
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        # En-têtes du tableau
        headers = ["ID-RT", "Nom", "Type", "Usage", "Marque", "Date Péremption", "Statut", "Lieu", "Affectation"]
        
        # Données pour le tableau
        table_data = [headers] + materiels
        
        # Largeurs des colonnes adaptées
        col_ratios = [0.8, 1.5, 1.0, 1.0, 1.0, 1.2, 1.0, 1.2, 1.2]
        total_ratio = sum(col_ratios)
        col_widths = [(ratio / total_ratio) * available_width for ratio in col_ratios]
        
        # Créer le tableau
        table = Table(table_data, colWidths=col_widths)
        
        # Style du tableau
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # Alternance de couleurs et mise en évidence des périmés
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
            
            # Mettre en rouge les matériels périmés
            if len(table_data[i]) > 6 and "PÉRIMÉ" in str(table_data[i][6]):
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightcoral))
                table_style.append(('TEXTCOLOR', (0, i), (-1, i), colors.darkred))
        
        style = TableStyle(table_style)
        table.setStyle(style)
        
        elements.append(table)
        
        # Ajouter une note sur les dates non parsables si nécessaire
        if materiels_non_dates:
            elements.append(Spacer(1, 20))
            note_text = f"<b>Note:</b> {len(materiels_non_dates)} matériel(s) avec des dates non analysables ont été ignorés."
            note_para = Paragraph(note_text, normal_style)
            elements.append(note_para)
        
        # Générer le PDF
        doc.build(elements)
        
        # Message de confirmation
        self.show_message(
            "Rapport généré", 
            f"Le rapport de péremption a été généré:\n{filename}\n\n"
            f"Matériels trouvés: {len(materiels)}\n"
            f"Délai: {delai_annees} an(s)",
            "info"
        )

    def show_message(self, title, text, message_type="info"):
        """
        Méthode unifiée pour afficher tous types de messages avec style cohérent.
        
        Args:
            title (str): Titre du popup
            text (str): Texte du message (supporte HTML)
            message_type (str): Type de message ("info", "warning", "error")
        
        Returns:
            QMessageBox.StandardButton: Bouton cliqué par l'utilisateur
        """
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        
        # Configuration selon le type de message
        if message_type == "info":
            msgbox.setIcon(QMessageBox.Icon.Information)
        elif message_type == "warning":
            msgbox.setIcon(QMessageBox.Icon.Warning)
            # Ajouter l'icône d'attention personnalisée
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
        elif message_type == "error":
            msgbox.setIcon(QMessageBox.Icon.Critical)
            # Ajouter l'icône d'attention personnalisée pour les erreurs critiques
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
        
        # Calculer la taille optimale - amélioré pour textes multilignes
        text_length = len(text)
        base_width = 420
        base_height = 180
        
        # Compter les lignes réelles (balises HTML <br> et retours chariot)
        html_breaks = text.count('<br>') + text.count('<br/>') + text.count('<br />')
        real_line_count = text.count('\n') + html_breaks + (text_length // 60)
        
        # Ajuster la largeur pour les textes longs
        if text_length > 80:
            base_width = min(650, base_width + (text_length // 8))
        
        # Ajuster la hauteur pour les textes multi-lignes avec marge supplémentaire
        if real_line_count > 2:
            base_height = min(400, base_height + (real_line_count * 30))
        elif real_line_count > 1:
            base_height = min(320, base_height + (real_line_count * 25))
        
        # Taille minimale optimisée pour un bon rendu sans excès
        msgbox.setMinimumSize(base_width, base_height)
        msgbox.resize(base_width + 40, base_height + 40)
        
        # Style CSS unifié - compact mais professionnel
        msgbox.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 18px;
                min-width: 420px;
                min-height: 180px;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                font-size: 12px;
                padding: 8px;
                margin: 8px;
                margin-left: 25px;
                margin-top: 10px;
                margin-bottom: 10px;
                max-width: 400px;
                text-align: left;
                line-height: 1.4;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
            QMessageBox QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        return msgbox.exec()

    def show_info_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "info")

    def show_error_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "error")

    def show_warning_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "warning")


class GestionMaterielWindow(QMainWindow):
    """Fenêtre principale de gestion du matériel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_name = get_config_db_path()
        self.setWindowTitle("Gestionnaire de Matériel")
        self.setGeometry(100, 100, 1200, 600)

        # Vérifier l'existence de la base de données
        if not check_database_exists(self.db_name):
            self.show_error_message(
                "Base de données manquante", 
                f"La base de données est manquante :\n{self.db_name}\n\n"
                "Veuillez vérifier le chemin dans la configuration ou créer la base de données."
            )
            self.close()
            return

        # Initialiser la base de données si elle existe
        if not initialiser_db(self.db_name):
            self.show_error_message(
                "Erreur de base de données", 
                f"Impossible d'initialiser la base de données :\n{self.db_name}"
            )
            self.close()
            return

        self.setup_ui()
        self.charger_materiel()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher dans tout le matériel (séparez plusieurs filtres par ;)...")
        self.search_input.textChanged.connect(self.filtrer_materiel)

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.setSortingEnabled(True)  # Activer le tri par clic sur les colonnes
        
        # Configuration personnalisée des largeurs de colonnes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSortIndicatorShown(True)  # Afficher les indicateurs de tri
        header.sectionClicked.connect(self.trier_par_colonne)  # Connecter le signal de clic
        
        # Définir les largeurs relatives des colonnes
        # ID-RT, Type, Usage, Modèle, Marque, Numéro de série, Quantité, Statut, CIS affectation, Vecteur
        self.column_widths = [70, 100, 100, 120, 100, 120, 60, 100, 120, 120]  # en pixels

        # Variables pour gérer le tri
        self.current_sort_column = 0  # Colonne ID-RT par défaut
        self.current_sort_order = Qt.SortOrder.AscendingOrder  # Ordre croissant par défaut

        # Création des boutons avec icônes et tooltips
        self.btn_ajouter = self.create_icon_button("ajouter.png", "Ajouter un nouvel équipement")
        self.btn_modifier = self.create_icon_button("reglages.png", "Modifier un équipement")
        self.btn_supprimer = self.create_icon_button("poubelle.png", "Supprimer un équipement")
        self.btn_peremption = self.create_icon_button("calendrier-horloge.png", "Gestion des péremptions")
        self.btn_exporter_pdf = self.create_icon_button("exportation-de-fichiers.png", "Exportation en PDF")

        self.btn_ajouter.clicked.connect(self.ajouter_materiel)
        self.btn_modifier.clicked.connect(self.modifier_materiel)
        self.btn_supprimer.clicked.connect(self.supprimer_materiel)
        self.btn_peremption.clicked.connect(self.verifier_peremption)
        self.btn_exporter_pdf.clicked.connect(self.exporter_pdf)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        search_layout = QHBoxLayout()
        
        # Créer le label avec l'icône de loupe
        search_icon_label = QLabel()
        loupe_icon_path = os.path.join(ICONS_DIR, "rechercher.png")
        if os.path.exists(loupe_icon_path):
            search_icon_label.setPixmap(QIcon(loupe_icon_path).pixmap(20, 20))
        else:
            search_icon_label.setText("🔍")  # Fallback avec emoji
        search_icon_label.setToolTip("Rechercher dans le matériel")
        
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(self.search_input)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_ajouter)
        button_layout.addWidget(self.btn_modifier)
        button_layout.addWidget(self.btn_supprimer)
        # Ajouter un espacement de 40px
        button_layout.addSpacing(40)
        button_layout.addWidget(self.btn_peremption)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_exporter_pdf)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.table_view)
        layout.addLayout(button_layout)

    def charger_materiel(self, filtre=""):
        """Charge les données des matériels depuis la base de données."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Requête complexe pour récupérer toutes les données nécessaires
        query = """
        SELECT 
            m.id,
            m.type,
            m.usage,
            COALESCE(c3.valeur_caracteristique, m.nom) as modele,
            m.marque,
            COALESCE(c4.valeur_caracteristique, '') as numero_serie,
            COALESCE(c2.valeur_caracteristique, '') as quantite,
            COALESCE(c1.valeur_caracteristique, '') as statut,
            m.lieu,
            m.affectation
        FROM materiel m
        LEFT JOIN caracteristiques c1 ON m.id = c1.materiel_id AND c1.nom_caracteristique = 'Statut'
        LEFT JOIN caracteristiques c2 ON m.id = c2.materiel_id AND c2.nom_caracteristique = 'Quantité'
        LEFT JOIN caracteristiques c3 ON m.id = c3.materiel_id AND c3.nom_caracteristique = 'Modèle'
        LEFT JOIN caracteristiques c4 ON m.id = c4.materiel_id AND c4.nom_caracteristique IN ('Numéro de série', 'N° de série', 'Numero de serie', 'Serial', 'SN')
        """
        
        params = []
        
        if filtre:
            # Diviser les filtres par ";"
            filtres = [f.strip() for f in filtre.split(';') if f.strip()]
            if filtres:
                conditions = []
                for terme in filtres:
                    terme_sql = f"%{terme}%"
                    # Recherche dans les champs principaux ET dans toutes les caractéristiques
                    condition = """(m.id LIKE ? OR m.type LIKE ? OR m.usage LIKE ? OR m.marque LIKE ? OR m.lieu LIKE ? OR m.affectation LIKE ? 
                                    OR c1.valeur_caracteristique LIKE ? OR c2.valeur_caracteristique LIKE ? OR c3.valeur_caracteristique LIKE ? OR c4.valeur_caracteristique LIKE ?
                                    OR m.id IN (SELECT materiel_id FROM caracteristiques WHERE valeur_caracteristique LIKE ?))"""
                    conditions.append(condition)
                    params.extend([terme_sql] * 11)  # 11 paramètres maintenant
                
                query += " WHERE " + " AND ".join(conditions)
        
        # Ajouter le tri SQL
        column_mapping = {
            0: "m.id",          # ID-RT
            1: "m.type",        # Type
            2: "m.usage",       # Usage
            3: "modele",        # Modèle
            4: "m.marque",      # Marque
            5: "numero_serie",  # Numéro de série
            6: "quantite",      # Quantité
            7: "statut",        # Statut
            8: "m.lieu",        # CIS affectation
            9: "m.affectation"  # Vecteur
        }
        
        if self.current_sort_column in column_mapping:
            sort_column = column_mapping[self.current_sort_column]
            sort_direction = "ASC" if self.current_sort_order == Qt.SortOrder.AscendingOrder else "DESC"
            query += f" ORDER BY {sort_column} {sort_direction}"
        else:
            query += " ORDER BY m.id ASC"  # Tri par défaut
            
        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()

        if not hasattr(self, 'table_model'):
            self.table_model = MaterielTableModel(data)
            self.table_view.setModel(self.table_model)
            self.configurer_largeurs_colonnes()
        else:
            self.table_model.refresh_data(data)
        
        # Mettre à jour l'indicateur de tri dans l'en-tête
        self.table_view.horizontalHeader().setSortIndicator(self.current_sort_column, self.current_sort_order)

    def configurer_largeurs_colonnes(self):
        """Configure les largeurs personnalisées des colonnes."""
        if hasattr(self, 'column_widths'):
            for i, width in enumerate(self.column_widths):
                if i < self.table_model.columnCount():
                    self.table_view.setColumnWidth(i, width)

    def trier_par_colonne(self, column):
        """Gère le tri par colonne quand l'utilisateur clique sur un en-tête."""
        # Si c'est la même colonne, inverser l'ordre
        if self.current_sort_column == column:
            self.current_sort_order = Qt.SortOrder.DescendingOrder if self.current_sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            # Nouvelle colonne, commencer par ordre croissant
            self.current_sort_column = column
            self.current_sort_order = Qt.SortOrder.AscendingOrder
        
        # Recharger les données avec le nouveau tri
        self.charger_materiel(self.search_input.text())

    def filtrer_materiel(self):
        """Filtre les matériels selon le texte de recherche."""
        self.charger_materiel(self.search_input.text())

    def ajouter_materiel(self):
        """Ouvre le dialogue pour ajouter un nouveau matériel."""
        dialog = MaterielDialog(db_name=self.db_name, parent=self)
        if dialog.exec():
            self.charger_materiel()

    def modifier_materiel(self):
        """Ouvre le dialogue pour modifier le matériel sélectionné."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            self.show_warning_message("Attention", "Veuillez sélectionner un matériel à modifier.")
            return
        
        selected_row = selected_indexes[0].row()
        materiel_id = self.table_model.data(self.table_model.index(selected_row, 0))

        dialog = MaterielDialog(materiel_id=materiel_id, db_name=self.db_name, parent=self)
        if dialog.exec():
            self.charger_materiel(self.search_input.text())

    def supprimer_materiel(self):
        """Supprime le matériel sélectionné après validation."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            self.show_warning_message("Attention", "Veuillez sélectionner un matériel à supprimer.")
            return

        selected_row = selected_indexes[0].row()
        materiel_id = self.table_model.data(self.table_model.index(selected_row, 0))
        materiel_nom = self.table_model.data(self.table_model.index(selected_row, 3))  # Colonne Modèle
        
        # Popup de validation avec détails
        reply = self.show_message(
            "⚠️ Confirmation de suppression",
            f"<b>Êtes-vous sûr de vouloir supprimer cet équipement ?</b><br><br>"
            f"<b>ID-RT :</b> {materiel_id}<br>"
            f"<b>Modèle :</b> {materiel_nom}<br><br>"
            f"<span style='color: red;'><b>⚠️ Cette action est irréversible !</b></span>",
            "question"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM materiel WHERE id=?", (materiel_id,))
                conn.commit()
                conn.close()
                
                # Message de confirmation
                self.show_info_message(
                    "✅ Suppression réussie", 
                    f"L'équipement {materiel_id} a été supprimé avec succès."
                )
                
                self.charger_materiel(self.search_input.text())
            except Exception as e:
                self.show_error_message(
                    "❌ Erreur de suppression", 
                    f"Impossible de supprimer l'équipement :\n{str(e)}"
                )

    def show_message(self, title, text, message_type="info", buttons=None):
        """
        Méthode unifiée pour afficher tous types de messages avec style cohérent.
        
        Args:
            title (str): Titre du popup
            text (str): Texte du message (supporte HTML)
            message_type (str): Type de message ("info", "warning", "error", "question")
            buttons (QMessageBox.StandardButton): Boutons à afficher (par défaut selon le type)
        
        Returns:
            QMessageBox.StandardButton: Bouton cliqué par l'utilisateur
        """
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        
        # Configuration selon le type de message
        if message_type == "info":
            msgbox.setIcon(QMessageBox.Icon.Information)
            if buttons is None:
                buttons = QMessageBox.StandardButton.Ok
        elif message_type == "warning":
            msgbox.setIcon(QMessageBox.Icon.Warning)
            # Ajouter l'icône d'attention personnalisée
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
            if buttons is None:
                buttons = QMessageBox.StandardButton.Ok
        elif message_type == "error":
            msgbox.setIcon(QMessageBox.Icon.Critical)
            # Ajouter l'icône d'attention personnalisée pour les erreurs critiques
            attention_icon_path = os.path.join(ICONS_DIR, "attention.png")
            if os.path.exists(attention_icon_path):
                msgbox.setIconPixmap(QIcon(attention_icon_path).pixmap(48, 48))
            if buttons is None:
                buttons = QMessageBox.StandardButton.Ok
        elif message_type == "question":
            msgbox.setIcon(QMessageBox.Icon.Question)
            if buttons is None:
                buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        
        # Définir les boutons
        msgbox.setStandardButtons(buttons)
        
        # Calculer la taille optimale - amélioré pour textes multilignes
        text_length = len(text)
        base_width = 420
        base_height = 180
        
        # Compter les lignes réelles (balises HTML <br> et retours chariot)
        html_breaks = text.count('<br>') + text.count('<br/>') + text.count('<br />')
        real_line_count = text.count('\n') + html_breaks + (text_length // 60)
        
        # Ajuster la largeur pour les textes longs
        if text_length > 80:
            base_width = min(650, base_width + (text_length // 8))
        
        # Ajuster la hauteur pour les textes multi-lignes avec marge supplémentaire
        if real_line_count > 2:
            base_height = min(400, base_height + (real_line_count * 30))
        elif real_line_count > 1:
            base_height = min(320, base_height + (real_line_count * 25))
        
        # Taille minimale optimisée pour un bon rendu sans excès
        msgbox.setMinimumSize(base_width, base_height)
        msgbox.resize(base_width + 40, base_height + 40)
        
        # Style CSS unifié - compact mais professionnel
        msgbox.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 18px;
                min-width: 420px;
                min-height: 180px;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                font-size: 12px;
                min-height: 100px;
                max-width: 400px;
                text-align: left;
                line-height: 1.4;
            }
            QMessageBox QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
                margin: 5px;
            }
            QMessageBox QPushButton:hover {
                background-color: #2980b9;
            }
            QMessageBox QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        # Pour les questions avec Yes/No, personnaliser les boutons
        if message_type == "question" and buttons == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
            # Récupérer les boutons après les avoir ajoutés
            yes_btn = msgbox.button(QMessageBox.StandardButton.Yes)
            no_btn = msgbox.button(QMessageBox.StandardButton.No)
            
            if yes_btn and no_btn:
                # Charger les icônes personnalisées
                yes_icon_path = os.path.join(ICONS_DIR, "angle-cercle-vers-le-bas.png")
                no_icon_path = os.path.join(ICONS_DIR, "croix-cercle.png")
                
                # Configurer le bouton Oui
                if os.path.exists(yes_icon_path):
                    yes_btn.setIcon(QIcon(yes_icon_path))
                    yes_btn.setText("  Oui")
                    yes_btn.setIconSize(QSize(20, 20))
                else:
                    yes_btn.setText("✓ Oui")
                
                # Configurer le bouton Non
                if os.path.exists(no_icon_path):
                    no_btn.setIcon(QIcon(no_icon_path))
                    no_btn.setText("  Non")
                    no_btn.setIconSize(QSize(20, 20))
                else:
                    no_btn.setText("✗ Non")
                
                # Style spécial pour les boutons de confirmation
                button_style = """
                    QPushButton {
                        padding: 8px 16px;
                        font-weight: bold;
                        border-radius: 4px;
                        border: 2px solid #ccc;
                        background-color: #f8f9fa;
                        color: #333;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border-color: #007bff;
                    }
                    QPushButton:pressed {
                        background-color: #dee2e6;
                    }
                """
                yes_btn.setStyleSheet(button_style)
                no_btn.setStyleSheet(button_style)
                
                # Définir le bouton par défaut
                msgbox.setDefaultButton(no_btn)
        
        return msgbox.exec()

    def show_warning_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "warning")
    
    def show_info_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "info")
    
    def show_error_message(self, title, text):
        """Alias pour compatibilité - utilise show_message."""
        return self.show_message(title, text, "error")

    def verifier_peremption(self):
        """Ouvre la fenêtre de vérification des dates de péremption."""
        dialog = PeremptionDialog(db_name=self.db_name, parent=self)
        dialog.exec()

    def exporter_pdf(self):
        """Exporter les données du tableau en PDF."""
        data_to_export = [self.table_model._headers] + self.table_model._data
        if len(data_to_export) <= 1:
            self.show_info_message("Info", "Aucune donnée à exporter.")
            return
            
        # Dialogue de sélection du fichier de sortie
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'export PDF",
            "export_materiel.pdf",
            "Fichiers PDF (*.pdf);;Tous les fichiers (*)"
        )
        
        if not filename:  # L'utilisateur a annulé
            return
            
        try:
            # Configuration de la page en format paysage
            page_width, page_height = landscape(letter)
            # Marges (gauche, droite, haut, bas)
            margins = 36  # 0.5 pouce de marge de chaque côté
            available_width = page_width - (2 * margins)
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter),
                                leftMargin=margins, rightMargin=margins,
                                topMargin=margins, bottomMargin=margins)
            
            # Calculer les largeurs de colonnes pour s'adapter à la page
            num_cols = len(self.table_model._headers)
            col_widths = None
            if num_cols > 0:
                # Largeurs relatives basées sur le contenu typique de chaque colonne
                # ID-RT, Type, Usage, Modèle, Marque, N°série, Quantité, Statut, CIS affectation, Vecteur
                col_ratios = [0.8, 1.0, 1.0, 1.2, 1.0, 1.2, 0.6, 1.0, 1.2, 1.2]
                total_ratio = sum(col_ratios[:num_cols])
                col_widths = [(ratio / total_ratio) * available_width for ratio in col_ratios[:num_cols]]
            
            # Créer le tableau avec largeurs définies
            table = Table(data_to_export, colWidths=col_widths)
            
            # Style du tableau optimisé
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            
            # Ajouter l'alternance de couleurs pour les lignes de données
            for i in range(1, len(data_to_export)):
                if i % 2 == 0:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
            
            style = TableStyle(table_style)
            table.setStyle(style)
            
            doc.build([table])
            self.show_info_message("Succès", f"Le fichier '{filename}' a été créé en format paysage adapté à la page.")
        except Exception as e:
            self.show_error_message("Erreur", f"Impossible de générer le PDF : {e}")

    def create_icon_button(self, icon_name, tooltip_text):
        """Crée un bouton avec une icône et un tooltip."""
        button = QPushButton()
        
        # Construire le chemin vers l'icône
        icon_path = os.path.join(ICONS_DIR, icon_name)
        
        if os.path.exists(icon_path):
            # Charger l'icône
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(16, 16))  # Taille de l'icône réduite de moitié
        else:
            # Si l'icône n'existe pas, utiliser du texte de fallback
            fallback_text = {
                "ajouter.png": "➕",
                "parametres-curseurs.png": "⚙️",
                "poubelle.png": "🗑️",
                "calendrier-horloge.png": "📅",
                "exportation-de-fichiers.png": "📄"
            }
            button.setText(fallback_text.get(icon_name, "?"))
        
        # Définir le tooltip
        button.setToolTip(tooltip_text)
        
        # Style du bouton
        button.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 6px;
                background-color: #ecf0f1;
                min-width: 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
                color: white;
            }
        """)
        
        return button

# Point d'entrée pour test standalone
if __name__ == "__main__":
    import sys
    import os
    import sqlite3
    import re
    import csv
    
    app = QApplication(sys.argv)
    
    # Vérifier l'existence de la base de données
    db_path = get_config_db_path()
    if not check_database_exists(db_path):
        print(f"ERREUR: Base de données manquante : {db_path}")
        sys.exit(1)
    
    # Initialiser la base de données si elle existe
    if not initialiser_db(db_path):
        print(f"ERREUR: Impossible d'initialiser la base de données : {db_path}")
        sys.exit(1)
    
    window = BD_gestDialog()
    window.show()
    
    sys.exit(app.exec())
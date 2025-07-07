from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QFormLayout, QGroupBox,
    QMessageBox, QHeaderView, QAbstractItemView, QSplitter,
    QFrame, QGridLayout, QFileDialog, QCalendarWidget, QCheckBox,
    QWidget, QTextEdit
)
from PySide6.QtCore import Qt, QDate, QTimer, QSize
from PySide6.QtGui import QIcon, QPixmap
import sqlite3
import os
from datetime import datetime, date
from ..utils.config_manager import config_manager
from ..constants import ICONS_DIR
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import platform

class CRPDialog(QDialog):
    """Dialog pour la gestion des Cellules de Radioprotection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des ressources humaines")
        self.setMinimumSize(1200, 800)
        
        # Enregistrement de la police Calibri
        self.register_calibri_font()
        
        # Initialisation de la base de données
        self.init_database()
        
        # Création de l'interface
        self.setup_ui()
        
        # Chargement des données
        self.load_agents()
        
        # Initialisation de l'affichage des colonnes
        self.update_visible_columns()
    
    def register_calibri_font(self):
        """Enregistre la police Calibri pour ReportLab ou utilise une alternative."""
        try:
            system = platform.system()
            if system == "Windows":
                # Chemin standard de Calibri sur Windows
                calibri_path = r"C:\Windows\Fonts\calibri.ttf"
                calibri_bold_path = r"C:\Windows\Fonts\calibrib.ttf"
                
                if os.path.exists(calibri_path):
                    pdfmetrics.registerFont(TTFont('Calibri', calibri_path))
                    if os.path.exists(calibri_bold_path):
                        pdfmetrics.registerFont(TTFont('Calibri-Bold', calibri_bold_path))
                    else:
                        # Utiliser Calibri normal en gras simulé
                        pdfmetrics.registerFont(TTFont('Calibri-Bold', calibri_path))
                else:
                    # Fallback vers Arial ou Helvetica
                    print("Police Calibri non trouvée, utilisation d'Helvetica")
            else:
                # Pour Linux/Mac, essayer de trouver Calibri ou utiliser des alternatives
                print("Système non-Windows, utilisation d'Helvetica")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de la police Calibri: {e}")
            print("Utilisation d'Helvetica par défaut")
    
    def get_font_name(self, bold=False):
        """Retourne le nom de la police à utiliser (Calibri ou Helvetica en fallback)."""
        try:
            # Vérifier si Calibri est disponible
            if 'Calibri' in pdfmetrics.getRegisteredFontNames():
                return 'Calibri-Bold' if bold else 'Calibri'
            else:
                return 'Helvetica-Bold' if bold else 'Helvetica'
        except:
            return 'Helvetica-Bold' if bold else 'Helvetica'
    
    def add_logo_to_pdf(self, canvas, width, height):
        """Ajoute le logo SDIS71 en haut à gauche du PDF."""
        try:
            # Chemin vers le logo
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   'resources', 'images', 'LOGOSDIS71.png')
            
            if os.path.exists(logo_path):
                # Définir les dimensions du logo (proportions logo d'entreprise)
                logo_width = 3 * 28.35  # 3 cm en points
                logo_height = 2 * 28.35  # 2 cm en points
                
                # Position en haut à gauche
                x_position = 1 * 28.35  # 1 cm du bord gauche
                y_position = height - 3 * 28.35  # 3 cm du haut
                
                # Insérer le logo
                canvas.drawImage(logo_path, x_position, y_position, 
                               width=logo_width, height=logo_height, 
                               preserveAspectRatio=True)
                
                return True
        except Exception as e:
            print(f"Erreur lors de l'ajout du logo: {e}")
            return False
        
        return False
    
    def create_icon_button(self, text, icon_name, tooltip_text):
        """Crée un bouton avec icône et tooltip dans le style de gestion_matériel."""
        button = QPushButton(text)
        
        # Chemin vers l'icône
        icon_path = os.path.join(ICONS_DIR, icon_name)
        
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(16, 16))
        else:
            # Fallback avec emoji si l'icône n'existe pas
            fallback_text = {
                "ajouter.png": "➕",
                "parametres-curseurs.png": "⚙️",
                "poubelle.png": "🗑️",
                "exportation-de-fichiers.png": "📄",
                "calendrier-horloge.png": "📅"
            }
            if icon_name in fallback_text:
                button.setText(f"{fallback_text[icon_name]} {text}")
        
        # Définir le tooltip
        button.setToolTip(tooltip_text)
        
        # Style du bouton
        button.setStyleSheet("""
            QPushButton {
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 6px;
                background-color: #ecf0f1;
                color: #2c3e50;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        
        return button
        
    def init_database(self):
        """Initialise la base de données RH."""
        try:
            # Récupération du chemin de la base RH depuis la configuration
            self.db_path = config_manager.get_rh_database_path()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table des agents
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    date_naissance DATE NOT NULL,
                    grade TEXT NOT NULL,
                    niveau_specialite TEXT NOT NULL,
                    affectation TEXT NOT NULL,
                    statut TEXT DEFAULT 'SPV',
                    en_activite BOOLEAN DEFAULT 1,
                    numero_secu TEXT DEFAULT '',
                    dose_vie REAL DEFAULT 0,
                    dose_annuelle REAL DEFAULT 0,
                    annee_reference INTEGER DEFAULT 2025
                )
            ''')
            
            # Table des expositions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expositions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    date_exposition DATE NOT NULL,
                    dose REAL NOT NULL,
                    type_exposition TEXT NOT NULL,
                    commentaire TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
            
            # Migration : ajouter les nouvelles colonnes si elles n'existent pas
            cursor.execute("PRAGMA table_info(agents)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'grade' not in columns:
                cursor.execute('ALTER TABLE agents ADD COLUMN grade TEXT DEFAULT ""')
            if 'statut' not in columns:
                cursor.execute('ALTER TABLE agents ADD COLUMN statut TEXT DEFAULT "SPV"')
            if 'en_activite' not in columns:
                cursor.execute('ALTER TABLE agents ADD COLUMN en_activite BOOLEAN DEFAULT 1')
            if 'numero_secu' not in columns:
                cursor.execute('ALTER TABLE agents ADD COLUMN numero_secu TEXT DEFAULT ""')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'initialisation de la base de données: {str(e)}")
    
    def setup_ui(self):
        """Création de l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Panel gauche - Liste des agents
        left_panel = self.create_agents_panel()
        main_splitter.addWidget(left_panel)
        
        # Panel droit - Détails et actions
        right_panel = self.create_details_panel()
        main_splitter.addWidget(right_panel)
        
        # Proportions
        main_splitter.setSizes([600, 600])
        
        # Boutons principaux
        buttons_layout = QHBoxLayout()
        
        btn_add = self.create_icon_button("Ajouter Agent", "ajouter.png", "Ajouter un nouvel agent spécialiste RAD")
        btn_add.clicked.connect(self.add_agent)
        buttons_layout.addWidget(btn_add)
        
        btn_modify = self.create_icon_button("Modifier Agent", "parametres-curseurs.png", "Modifier les informations de l'agent sélectionné")
        btn_modify.clicked.connect(self.modify_agent)
        buttons_layout.addWidget(btn_modify)
        
        btn_delete = self.create_icon_button("Supprimer Agent", "poubelle.png", "Supprimer l'agent sélectionné et toutes ses expositions")
        btn_delete.clicked.connect(self.delete_agent)
        buttons_layout.addWidget(btn_delete)
        
        buttons_layout.addStretch()
        
        btn_export_individual = self.create_icon_button("Fiche Agent PDF", "exportation-de-fichiers.png", "Exporter la fiche individuelle de l'agent en PDF")
        btn_export_individual.clicked.connect(self.export_individual_pdf)
        buttons_layout.addWidget(btn_export_individual)
        
        btn_export_collective = self.create_icon_button("Rapport Collectif PDF", "exportation-de-fichiers.png", "Exporter un rapport collectif sur une période en PDF")
        btn_export_collective.clicked.connect(self.export_collective_pdf)
        buttons_layout.addWidget(btn_export_collective)
        
        btn_export_lao = self.create_icon_button("Export LAO PDF", "exportation-de-fichiers.png", "Exporter la Liste d'Aptitude Opérationnelle en PDF")
        btn_export_lao.clicked.connect(self.export_lao_pdf)
        buttons_layout.addWidget(btn_export_lao)
        
        buttons_layout.addStretch()
        
        btn_visibility_rh = self.create_icon_button("Visibilité RH", "parametres-curseurs.png", "Afficher un graphique de répartition du personnel par âge et statut")
        btn_visibility_rh.clicked.connect(self.show_visibility_rh)
        buttons_layout.addWidget(btn_visibility_rh)
        
        layout.addLayout(buttons_layout)
    
    def create_agents_panel(self):
        """Crée le panel de liste des agents."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # Titre
        title = QLabel("Liste des Spécialistes")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Cases à cocher pour les filtres
        filter_checkboxes_layout = QHBoxLayout()
        
        # Label explicite pour la case à cocher
        inactive_label = QLabel("Afficher les agents inactifs:")
        filter_checkboxes_layout.addWidget(inactive_label)
        
        self.show_inactive_checkbox = QCheckBox()
        self.show_inactive_checkbox.setChecked(False)
        self.show_inactive_checkbox.stateChanged.connect(self.filter_agents)
        self.show_inactive_checkbox.setToolTip("Cocher pour afficher également les agents qui ne sont plus en activité")
        filter_checkboxes_layout.addWidget(self.show_inactive_checkbox)
        
        # Menu déroulant pour sélectionner les colonnes à afficher
        columns_label = QLabel("Colonnes:")
        columns_label.setToolTip("Sélectionner quelles colonnes afficher dans le tableau")
        filter_checkboxes_layout.addWidget(columns_label)
        
        self.columns_selector = QComboBox()
        self.columns_selector.setMinimumWidth(200)
        self.columns_selector.setToolTip("Choisir un profil d'affichage des colonnes selon vos besoins")
        
        # Définition des options de colonnes disponibles
        self.column_options = {
            "Essentielles": ["Grade", "Nom", "Prénom", "Niveau", "Affectation"],
            "Complètes": ["Nom", "Prénom", "Naissance", "Grade", "Statut", "Activité", "Niveau", "Affectation", "N° Sécu", "Dose Vie (mSv)", "Dose Annuelle (µSv)"],
            "Identification": ["Nom", "Prénom", "Naissance", "N° Sécu"],
            "Hiérarchie": ["Grade", "Nom", "Prénom", "Statut", "Affectation"],
            "Radioprotection": ["Nom", "Prénom", "Niveau", "Dose Vie (mSv)", "Dose Annuelle (µSv)"],
            "Personnalisées": ["Nom", "Prénom", "Grade", "Niveau", "Affectation"]
        }
        
        self.columns_selector.addItems(list(self.column_options.keys()))
        self.columns_selector.setCurrentText("Essentielles")  # Sélection par défaut
        self.columns_selector.currentTextChanged.connect(self.update_visible_columns)
        filter_checkboxes_layout.addWidget(self.columns_selector)
        
        filter_checkboxes_layout.addStretch()
        layout.addLayout(filter_checkboxes_layout)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        
        # Icône de recherche
        search_icon_label = QLabel()
        loupe_icon_path = os.path.join(ICONS_DIR, "rechercher.png")
        if os.path.exists(loupe_icon_path):
            search_icon_label.setPixmap(QIcon(loupe_icon_path).pixmap(20, 20))
        else:
            search_icon_label.setText("🔍")  # Fallback avec emoji
        search_icon_label.setToolTip("Rechercher un agent par nom, prénom ou affectation")
        
        search_label = QLabel("Rechercher:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom, prénom, affectation...")
        self.search_input.textChanged.connect(self.filter_agents)
        self.search_input.setToolTip("Saisir du texte pour filtrer la liste des agents")
        
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Table des agents
        self.agents_table = QTableWidget()
        self.agents_table.setColumnCount(11)
        self.agents_table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Naissance", "Grade", "Statut", "Activité", "Niveau", "Affectation", "N° Sécu", "Dose Vie (mSv)", "Dose Annuelle (µSv)"
        ])
        
        # Configuration de la table
        header = self.agents_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.agents_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.agents_table.setAlternatingRowColors(True)
        self.agents_table.itemSelectionChanged.connect(self.on_agent_selected)
        
        layout.addWidget(self.agents_table)
        
        return panel
    
    def create_details_panel(self):
        """Crée le panel de détails et actions."""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # Informations de l'agent sélectionné
        info_group = QGroupBox("Informations Agent")
        info_layout = QFormLayout(info_group)
        
        self.info_nom = QLabel("-")
        self.info_prenom = QLabel("-")
        self.info_naissance = QLabel("-")
        self.info_grade = QLabel("-")
        self.info_statut = QLabel("-")
        self.info_activite = QLabel("-")
        self.info_numero_secu = QLabel("-")
        self.info_niveau = QLabel("-")
        self.info_affectation = QLabel("-")
        self.info_dose_vie = QLabel("-")
        self.info_dose_annuelle = QLabel("-")
        
        info_layout.addRow("Nom:", self.info_nom)
        info_layout.addRow("Prénom:", self.info_prenom)
        info_layout.addRow("Date de naissance:", self.info_naissance)
        info_layout.addRow("Grade:", self.info_grade)
        info_layout.addRow("Statut:", self.info_statut)
        info_layout.addRow("En activité:", self.info_activite)
        info_layout.addRow("N° Sécurité Sociale:", self.info_numero_secu)
        info_layout.addRow("Niveau RAD:", self.info_niveau)
        info_layout.addRow("Affectation:", self.info_affectation)
        info_layout.addRow("Dose à vie (mSv):", self.info_dose_vie)
        info_layout.addRow("Dose annuelle (µSv):", self.info_dose_annuelle)
        
        layout.addWidget(info_group)
        
        # Saisie d'exposition
        expo_group = QGroupBox("Saisie d'Exposition")
        expo_layout = QFormLayout(expo_group)
        
        self.expo_date = QDateEdit()
        self.expo_date.setDate(QDate.currentDate())
        self.expo_date.setCalendarPopup(True)
        self.expo_date.setToolTip("Date de l'exposition - par défaut aujourd'hui")
        
        self.expo_dose = QDoubleSpinBox()
        self.expo_dose.setDecimals(3)
        self.expo_dose.setMaximum(999999.999)
        self.expo_dose.setSuffix(" µSv")
        self.expo_dose.setToolTip("Dose d'exposition en microSieverts (µSv)")
        
        self.expo_type = QComboBox()
        self.expo_type.addItems(["Intervention", "Exercice", "Formation", "Maintenance"])
        self.expo_type.setToolTip("Type d'activité ayant causé l'exposition")
        
        self.expo_comment = QLineEdit()
        self.expo_comment.setPlaceholderText("Commentaire optionnel...")
        self.expo_comment.setToolTip("Commentaire libre sur les circonstances de l'exposition")
        
        btn_add_expo = self.create_icon_button("Enregistrer Exposition", "ajouter.png", "Enregistrer cette exposition pour l'agent sélectionné")
        btn_add_expo.clicked.connect(self.add_exposition)
        
        expo_layout.addRow("Date:", self.expo_date)
        expo_layout.addRow("Dose:", self.expo_dose)
        expo_layout.addRow("Type:", self.expo_type)
        expo_layout.addRow("Commentaire:", self.expo_comment)
        expo_layout.addRow("", btn_add_expo)
        
        layout.addWidget(expo_group)
        
        # Historique des expositions
        hist_group = QGroupBox("Historique des Expositions")
        hist_layout = QVBoxLayout(hist_group)
        
        self.expo_table = QTableWidget()
        self.expo_table.setColumnCount(4)
        self.expo_table.setHorizontalHeaderLabels(["Date", "Dose (µSv)", "Type", "Commentaire"])
        
        header = self.expo_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.expo_table.setAlternatingRowColors(True)
        
        hist_layout.addWidget(self.expo_table)
        
        # Bouton pour supprimer une exposition
        btn_delete_expo = self.create_icon_button("Supprimer Exposition Sélectionnée", "poubelle.png", "Supprimer l'exposition sélectionnée dans l'historique")
        btn_delete_expo.clicked.connect(self.delete_exposition)
        hist_layout.addWidget(btn_delete_expo)
        
        layout.addWidget(hist_group)
        
        return panel
    
    def load_agents(self):
        """Charge la liste des agents depuis la base de données."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, nom, prenom, date_naissance, grade, statut, en_activite,
                       niveau_specialite, affectation, numero_secu, dose_vie, dose_annuelle
                FROM agents ORDER BY nom, prenom
            ''')
            
            agents = cursor.fetchall()
            
            self.agents_table.setRowCount(len(agents))
            for row, agent in enumerate(agents):
                self.agents_table.setItem(row, 0, QTableWidgetItem(agent[1]))  # nom
                self.agents_table.setItem(row, 1, QTableWidgetItem(agent[2]))  # prenom
                
                # Formatage de la date de naissance au format DD-MM-YYYY
                date_naissance = agent[3]
                if date_naissance:
                    try:
                        # Si la date est au format DD/MM/YYYY, la convertir en DD-MM-YYYY
                        if '/' in date_naissance:
                            date_parts = date_naissance.split('/')
                            if len(date_parts) == 3:
                                date_naissance = f"{date_parts[0].zfill(2)}-{date_parts[1].zfill(2)}-{date_parts[2]}"
                        # Si la date est au format YYYY-MM-DD, la convertir en DD-MM-YYYY
                        elif '-' in date_naissance and len(date_naissance) == 10:
                            date_parts = date_naissance.split('-')
                            if len(date_parts) == 3:
                                date_naissance = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                        else:
                            # Essayer de parser et reformater la date
                            from datetime import datetime
                            parsed_date = datetime.strptime(date_naissance, '%Y-%m-%d')
                            date_naissance = parsed_date.strftime('%d-%m-%Y')
                    except (ValueError, IndexError):
                        # Si le parsing échoue, garder la date originale
                        pass
                
                self.agents_table.setItem(row, 2, QTableWidgetItem(date_naissance))  # date_naissance
                self.agents_table.setItem(row, 3, QTableWidgetItem(agent[4] or ""))  # grade
                self.agents_table.setItem(row, 4, QTableWidgetItem(agent[5] or "SPV"))  # statut
                self.agents_table.setItem(row, 5, QTableWidgetItem("Oui" if agent[6] else "Non"))  # en_activite
                self.agents_table.setItem(row, 6, QTableWidgetItem(agent[7]))  # niveau
                self.agents_table.setItem(row, 7, QTableWidgetItem(agent[8]))  # affectation
                self.agents_table.setItem(row, 8, QTableWidgetItem(agent[9] or ""))  # numero_secu
                self.agents_table.setItem(row, 9, QTableWidgetItem(f"{agent[10]:.3f}"))  # dose_vie en mSv
                self.agents_table.setItem(row, 10, QTableWidgetItem(f"{agent[11]:.3f}"))  # dose_annuelle en µSv
                
                # Stocker l'ID dans la première colonne (invisible)
                self.agents_table.item(row, 0).setData(Qt.UserRole, agent[0])
            
            conn.close()
            
            # Appliquer les filtres après le chargement
            self.filter_agents()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des agents: {str(e)}")
    
    def filter_agents(self):
        """Filtre la liste des agents selon le texte de recherche et les options de filtrage."""
        # Vérifier que les widgets existent avant de les utiliser
        if not hasattr(self, 'search_input') or not hasattr(self, 'show_inactive_checkbox'):
            return
            
        search_text = self.search_input.text().lower()
        show_inactive = self.show_inactive_checkbox.isChecked()
        
        for row in range(self.agents_table.rowCount()):
            # Vérifier d'abord le statut d'activité (colonne 5)
            activity_item = self.agents_table.item(row, 5)
            is_active = activity_item and activity_item.text() == "Oui"
            
            # Si l'agent est inactif et qu'on ne veut pas les afficher, masquer la ligne
            if not is_active and not show_inactive:
                self.agents_table.setRowHidden(row, True)
                continue
            
            # Sinon, appliquer le filtre de recherche textuelle
            show_row = not search_text  # Si pas de texte de recherche, afficher
            if search_text:
                for col in range(self.agents_table.columnCount()):
                    item = self.agents_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break
            
            self.agents_table.setRowHidden(row, not show_row)
    
    def on_agent_selected(self):
        """Gère la sélection d'un agent."""
        current_row = self.agents_table.currentRow()
        if current_row >= 0:
            # Mise à jour des informations
            self.info_nom.setText(self.agents_table.item(current_row, 0).text())
            self.info_prenom.setText(self.agents_table.item(current_row, 1).text())
            self.info_naissance.setText(self.agents_table.item(current_row, 2).text())
            self.info_grade.setText(self.agents_table.item(current_row, 3).text())
            self.info_statut.setText(self.agents_table.item(current_row, 4).text())
            self.info_activite.setText(self.agents_table.item(current_row, 5).text())
            self.info_niveau.setText(self.agents_table.item(current_row, 6).text())
            self.info_affectation.setText(self.agents_table.item(current_row, 7).text())
            self.info_numero_secu.setText(self.agents_table.item(current_row, 8).text())
            self.info_dose_vie.setText(self.agents_table.item(current_row, 9).text())
            self.info_dose_annuelle.setText(self.agents_table.item(current_row, 10).text())
            
            # Charger l'historique des expositions
            agent_id = self.agents_table.item(current_row, 0).data(Qt.UserRole)
            self.load_expositions(agent_id)
    
    def load_expositions(self, agent_id):
        """Charge l'historique des expositions pour un agent."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date_exposition, dose, type_exposition, commentaire
                FROM expositions 
                WHERE agent_id = ?
                ORDER BY date_exposition DESC
            ''', (agent_id,))
            
            expositions = cursor.fetchall()
            
            self.expo_table.setRowCount(len(expositions))
            for row, expo in enumerate(expositions):
                self.expo_table.setItem(row, 0, QTableWidgetItem(expo[0]))
                self.expo_table.setItem(row, 1, QTableWidgetItem(f"{expo[1]:.3f}"))  # dose en µSv
                self.expo_table.setItem(row, 2, QTableWidgetItem(expo[2]))
                self.expo_table.setItem(row, 3, QTableWidgetItem(expo[3] or ""))
            
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des expositions: {str(e)}")
    
    def add_agent(self):
        """Ouvre le dialogue d'ajout d'agent."""
        dialog = AgentDialog(self)
        if dialog.exec() == QDialog.Accepted:
            agent_data = dialog.get_agent_data()
            self.save_agent(agent_data)
            self.load_agents()
    
    def modify_agent(self):
        """Ouvre le dialogue de modification d'agent."""
        current_row = self.agents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un agent à modifier.")
            return
        
        agent_id = self.agents_table.item(current_row, 0).data(Qt.UserRole)
        agent_data = self.get_agent_data(agent_id)
        
        dialog = AgentDialog(self, agent_data)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_agent_data()
            new_data['id'] = agent_id
            self.save_agent(new_data, update=True)
            self.load_agents()
    
    def delete_agent(self):
        """Supprime un agent après confirmation."""
        current_row = self.agents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un agent à supprimer.")
            return
        
        agent_nom = self.agents_table.item(current_row, 0).text()
        agent_prenom = self.agents_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(self, "Confirmation", 
                                   f"Êtes-vous sûr de vouloir supprimer l'agent {agent_prenom} {agent_nom} ?\n"
                                   "Toutes ses expositions seront également supprimées.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            agent_id = self.agents_table.item(current_row, 0).data(Qt.UserRole)
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Supprimer les expositions
                cursor.execute("DELETE FROM expositions WHERE agent_id = ?", (agent_id,))
                # Supprimer l'agent
                cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
                
                conn.commit()
                conn.close()
                
                self.load_agents()
                self.clear_details()
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def save_agent(self, agent_data, update=False):
        """Sauvegarde un agent dans la base de données."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if update:
                cursor.execute('''
                    UPDATE agents SET nom=?, prenom=?, date_naissance=?, grade=?,
                           statut=?, en_activite=?, numero_secu=?, niveau_specialite=?, affectation=?
                    WHERE id=?
                ''', (agent_data['nom'], agent_data['prenom'], agent_data['date_naissance'],
                      agent_data['grade'], agent_data['statut'], agent_data['en_activite'],
                      agent_data['numero_secu'], agent_data['niveau'], agent_data['affectation'], 
                      agent_data['id']))
            else:
                cursor.execute('''
                    INSERT INTO agents (nom, prenom, date_naissance, grade, statut, en_activite, 
                                      numero_secu, niveau_specialite, affectation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (agent_data['nom'], agent_data['prenom'], agent_data['date_naissance'],
                      agent_data['grade'], agent_data['statut'], agent_data['en_activite'],
                      agent_data['numero_secu'], agent_data['niveau'], agent_data['affectation']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
    
    def get_agent_data(self, agent_id):
        """Récupère les données d'un agent."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT nom, prenom, date_naissance, grade, statut, en_activite, 
                       numero_secu, niveau_specialite, affectation
                FROM agents WHERE id = ?
            ''', (agent_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'nom': result[0],
                    'prenom': result[1],
                    'date_naissance': result[2],
                    'grade': result[3] or "",
                    'statut': result[4] or "SPV",
                    'en_activite': bool(result[5]),
                    'numero_secu': result[6] or "",
                    'niveau': result[7],
                    'affectation': result[8]
                }
            return None
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la récupération des données: {str(e)}")
            return None
    
    def add_exposition(self):
        """Ajoute une exposition pour l'agent sélectionné."""
        current_row = self.agents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un agent.")
            return
        
        if self.expo_dose.value() <= 0:
            QMessageBox.warning(self, "Attention", "Veuillez saisir une dose valide.")
            return
        
        agent_id = self.agents_table.item(current_row, 0).data(Qt.UserRole)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insérer l'exposition
            cursor.execute('''
                INSERT INTO expositions (agent_id, date_exposition, dose, type_exposition, commentaire)
                VALUES (?, ?, ?, ?, ?)
            ''', (agent_id, self.expo_date.date().toString("yyyy-MM-dd"), 
                  self.expo_dose.value(), self.expo_type.currentText(), 
                  self.expo_comment.text()))
            
            # Mettre à jour les doses cumulées
            self.update_cumulative_doses(agent_id, cursor)
            
            conn.commit()
            conn.close()
            
            # Recharger les données
            self.load_agents()
            self.load_expositions(agent_id)
            
            # Réinitialiser les champs
            self.expo_dose.setValue(0)
            self.expo_comment.clear()
            
            QMessageBox.information(self, "Succès", "Exposition enregistrée avec succès.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
    
    def update_cumulative_doses(self, agent_id, cursor):
        """Met à jour les doses cumulées à vie et annuelles."""
        # Dose à vie (somme en µSv convertie en mSv)
        cursor.execute('''
            SELECT SUM(dose) FROM expositions WHERE agent_id = ?
        ''', (agent_id,))
        dose_vie_usv = cursor.fetchone()[0] or 0
        dose_vie_msv = dose_vie_usv / 1000.0  # Conversion µSv -> mSv
        
        # Dose annuelle (année en cours, en µSv)
        current_year = datetime.now().year
        cursor.execute('''
            SELECT SUM(dose) FROM expositions 
            WHERE agent_id = ? AND strftime('%Y', date_exposition) = ?
        ''', (agent_id, str(current_year)))
        dose_annuelle_usv = cursor.fetchone()[0] or 0
        
        # Mise à jour
        cursor.execute('''
            UPDATE agents SET dose_vie = ?, dose_annuelle = ?, annee_reference = ?
            WHERE id = ?
        ''', (dose_vie_msv, dose_annuelle_usv, current_year, agent_id))
    
    def delete_exposition(self):
        """Supprime une exposition sélectionnée."""
        current_expo_row = self.expo_table.currentRow()
        current_agent_row = self.agents_table.currentRow()
        
        if current_expo_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une exposition à supprimer.")
            return
        
        if current_agent_row < 0:
            return
        
        reply = QMessageBox.question(self, "Confirmation", 
                                   "Êtes-vous sûr de vouloir supprimer cette exposition ?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            agent_id = self.agents_table.item(current_agent_row, 0).data(Qt.UserRole)
            date_expo = self.expo_table.item(current_expo_row, 0).text()
            dose_expo = float(self.expo_table.item(current_expo_row, 1).text())
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Supprimer l'exposition (sans LIMIT pour éviter l'erreur SQLite)
                cursor.execute('''
                    DELETE FROM expositions 
                    WHERE agent_id = ? AND date_exposition = ? AND dose = ?
                ''', (agent_id, date_expo, dose_expo))
                
                # Mettre à jour les doses cumulées
                self.update_cumulative_doses(agent_id, cursor)
                
                conn.commit()
                conn.close()
                
                # Recharger les données
                self.load_agents()
                self.load_expositions(agent_id)
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def clear_details(self):
        """Efface les détails affichés."""
        self.info_nom.setText("-")
        self.info_prenom.setText("-")
        self.info_naissance.setText("-")
        self.info_grade.setText("-")
        self.info_statut.setText("-")
        self.info_activite.setText("-")
        self.info_numero_secu.setText("-")
        self.info_niveau.setText("-")
        self.info_affectation.setText("-")
        self.info_dose_vie.setText("-")
        self.info_dose_annuelle.setText("-")
        self.expo_table.setRowCount(0)
    
    def export_individual_pdf(self):
        """Exporte la fiche individuelle d'un agent en PDF."""
        current_row = self.agents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un agent.")
            return
        
        agent_id = self.agents_table.item(current_row, 0).data(Qt.UserRole)
        agent_nom = self.agents_table.item(current_row, 0).text()
        agent_prenom = self.agents_table.item(current_row, 1).text()
        
        # Dialogue de sauvegarde
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            f"Sauvegarder la fiche de {agent_prenom} {agent_nom}",
            f"Fiche_{agent_prenom}_{agent_nom}.pdf",
            "Fichiers PDF (*.pdf)"
        )
        
        if filename:
            try:
                self.generate_individual_pdf(agent_id, filename)
                QMessageBox.information(self, "Succès", f"Fiche exportée vers {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def export_collective_pdf(self):
        """Exporte un rapport collectif en PDF."""
        dialog = CollectiveReportDialog(self)
        if dialog.exec() == QDialog.Accepted:
            date_debut, date_fin = dialog.get_date_range()
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Sauvegarder le rapport collectif",
                f"Rapport_collectif_{date_debut.toString('yyyy-MM-dd')}_{date_fin.toString('yyyy-MM-dd')}.pdf",
                "Fichiers PDF (*.pdf)"
            )
            
            if filename:
                try:
                    self.generate_collective_pdf(date_debut, date_fin, filename)
                    QMessageBox.information(self, "Succès", f"Rapport exporté vers {filename}")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def export_lao_pdf(self):
        """Exporte la Liste d'Aptitude Opérationnelle (LAO) en PDF."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Sauvegarder la LAO",
            f"LAO_{QDate.currentDate().toString('yyyy-MM-dd')}.pdf",
            "Fichiers PDF (*.pdf)"
        )
        
        if filename:
            try:
                self.generate_lao_pdf(filename)
                QMessageBox.information(self, "Succès", f"LAO exportée vers {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def generate_individual_pdf(self, agent_id, filename):
        """Génère un PDF pour un agent individuel."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Ajouter le logo SDIS71 en haut à gauche
        self.add_logo_to_pdf(c, width, height)
        
        # Récupération des données
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Données agent
        cursor.execute('''
            SELECT nom, prenom, date_naissance, grade, statut, en_activite, numero_secu,
                   niveau_specialite, affectation, dose_vie, dose_annuelle
            FROM agents WHERE id = ?
        ''', (agent_id,))
        agent = cursor.fetchone()
        
        # Données expositions
        cursor.execute('''
            SELECT date_exposition, dose, type_exposition, commentaire
            FROM expositions WHERE agent_id = ?
            ORDER BY date_exposition
        ''', (agent_id,))
        expositions = cursor.fetchall()
        
        conn.close()
        
        # En-tête (décalé à droite pour laisser place au logo)
        c.setFont(self.get_font_name(bold=True), 16)
        c.drawString(5*cm, height-2*cm, f"FICHE INDIVIDUELLE DE RADIOPROTECTION")
        
        c.setFont(self.get_font_name(bold=True), 14)
        c.drawString(5*cm, height-3*cm, f"{agent[1]} {agent[0]}")
        
        # Informations personnelles
        c.setFont(self.get_font_name(), 12)
        y_pos = height - 4*cm
        c.drawString(2*cm, y_pos, f"Date de naissance: {agent[2]}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"Grade: {agent[3] or 'Non spécifié'}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"Statut: {agent[4] or 'SPV'}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"En activité: {'Oui' if agent[5] else 'Non'}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"N° Sécurité Sociale: {agent[6] or 'Non renseigné'}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"Niveau RAD: {agent[7]}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"Affectation: {agent[8]}")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"Dose cumulative à vie: {agent[9]:.3f} mSv")
        y_pos -= 0.5*cm
        c.drawString(2*cm, y_pos, f"Dose cumulative annuelle: {agent[10]:.1f} µSv")
        
        # Historique des expositions
        y_pos -= 1.5*cm
        c.setFont(self.get_font_name(bold=True), 12)
        c.drawString(2*cm, y_pos, "HISTORIQUE DES EXPOSITIONS")
        
        y_pos -= 1*cm
        c.setFont(self.get_font_name(), 10)
        c.drawString(2*cm, y_pos, "Date")
        c.drawString(4*cm, y_pos, "Dose (µSv)")
        c.drawString(6*cm, y_pos, "Type")
        c.drawString(10*cm, y_pos, "Commentaire")
        
        y_pos -= 0.5*cm
        for expo in expositions:
            if y_pos < 2*cm:  # Nouvelle page si nécessaire
                c.showPage()
                # Ajouter le logo sur la nouvelle page
                self.add_logo_to_pdf(c, width, height)
                y_pos = height - 2*cm
            
            c.drawString(2*cm, y_pos, expo[0])
            c.drawString(4*cm, y_pos, f"{expo[1]:.1f}")
            c.drawString(6*cm, y_pos, expo[2])
            c.drawString(10*cm, y_pos, expo[3] or "")
            y_pos -= 0.4*cm
        
        c.save()
    
    def generate_collective_pdf(self, date_debut, date_fin, filename):
        """Génère un PDF de rapport collectif."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Ajouter le logo SDIS71 en haut à gauche
        self.add_logo_to_pdf(c, width, height)
        
        # Récupération des données
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.nom, a.prenom, a.grade, a.statut, a.niveau_specialite, a.affectation,
                   SUM(e.dose) as dose_periode
            FROM agents a
            LEFT JOIN expositions e ON a.id = e.agent_id
            WHERE e.date_exposition BETWEEN ? AND ?
            GROUP BY a.id
            ORDER BY a.nom, a.prenom
        ''', (date_debut.toString("yyyy-MM-dd"), date_fin.toString("yyyy-MM-dd")))
        
        agents_data = cursor.fetchall()
        conn.close()
        
        # En-tête (décalé à droite pour laisser place au logo)
        c.setFont(self.get_font_name(bold=True), 16)
        c.drawString(5*cm, height-2*cm, "RAPPORT COLLECTIF DE RADIOPROTECTION")
        
        c.setFont(self.get_font_name(), 12)
        c.drawString(5*cm, height-3*cm, f"Période: du {date_debut.toString('dd/MM/yyyy')} au {date_fin.toString('dd/MM/yyyy')}")
        
        # Tableau
        y_pos = height - 4.5*cm
        c.setFont(self.get_font_name(bold=True), 10)
        c.drawString(2*cm, y_pos, "Nom")
        c.drawString(4*cm, y_pos, "Prénom")
        c.drawString(5.5*cm, y_pos, "Grade")
        c.drawString(7*cm, y_pos, "Statut")
        c.drawString(8.5*cm, y_pos, "Niveau")
        c.drawString(10.5*cm, y_pos, "Affectation")
        c.drawString(15.5*cm, y_pos, "Dose (µSv)")
        
        y_pos -= 0.5*cm
        c.setFont(self.get_font_name(), 9)
        
        for agent in agents_data:
            if y_pos < 2*cm:
                c.showPage()
                # Ajouter le logo sur la nouvelle page
                self.add_logo_to_pdf(c, width, height)
                y_pos = height - 2*cm
            
            c.drawString(2*cm, y_pos, agent[0])
            c.drawString(4*cm, y_pos, agent[1])
            c.drawString(5.5*cm, y_pos, agent[2] or "")
            c.drawString(7*cm, y_pos, agent[3] or "SPV")
            c.drawString(8.5*cm, y_pos, agent[4])
            c.drawString(10.5*cm, y_pos, agent[5])
            c.drawString(15.5*cm, y_pos, f"{agent[6]:.1f}" if agent[6] else "0.0")
            y_pos -= 0.4*cm
        
        c.save()
    
    def generate_lao_pdf(self, filename):
        """Génère un PDF de la Liste d'Aptitude Opérationnelle."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Ajouter le logo SDIS71 en haut à gauche
        self.add_logo_to_pdf(c, width, height)
        
        # Définition de l'ordre hiérarchique des grades
        grade_order = {
            "Contrôleur-Général": 13, "Colonel": 12, "Lieutenant-Colonel": 11, 
            "Commandant": 10, "Capitaine": 9, "Lieutenant": 8,
            "Adjudant-Chef": 7, "Adjudant": 6, "Sergent-Chef": 5, 
            "Sergent": 4, "Caporal-Chef": 3, "Caporal": 2, "Sapeur": 1, "": 0
        }
        
        # Récupération des agents actifs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nom, prenom, grade, niveau_specialite, affectation
            FROM agents 
            WHERE en_activite = 1
            ORDER BY niveau_specialite DESC, nom
        ''')
        
        agents = cursor.fetchall()
        conn.close()
        
        # Tri des agents par niveau puis grade puis nom
        def sort_key(agent):
            nom, prenom, grade, niveau, affectation = agent
            grade_num = grade_order.get(grade or "", 0)
            return (niveau, grade_num, nom)  # niveau desc, grade desc (ordre décroissant), nom asc
        
        agents_sorted = sorted(agents, key=sort_key, reverse=True)
        
        # Groupement par niveau RAD
        levels = {
            "RAD 4": {"title": "RAD 4 - Conseillers techniques", "agents": []},
            "RAD 3": {"title": "RAD 3 - Chefs d'unité", "agents": []},
            "RAD 2": {"title": "RAD 2 - Chefs d'équipe ou équipiers Intervention", "agents": []},
            "RAD 1": {"title": "RAD 1 - Chefs d'équipe ou équipiers reconnaissance", "agents": []}
        }
        
        for agent in agents_sorted:
            niveau = agent[3]
            if niveau in levels:
                levels[niveau]["agents"].append(agent)
        
        # En-tête (décalé à droite pour laisser place au logo)
        c.setFont(self.get_font_name(bold=True), 18)
        c.drawString(5*cm, height-2*cm, "LISTE D'APTITUDE OPÉRATIONNELLE")
        c.drawString(5*cm, height-2.8*cm, "SPÉCIALISTE RAD")
        
        c.setFont(self.get_font_name(), 12)
        c.drawString(5*cm, height-3.5*cm, f"Établie le {QDate.currentDate().toString('dd/MM/yyyy')} par le Lieutenant MOUGIN Judicaël")
        
        y_pos = height - 5*cm
        
        # Génération par niveau
        for level_key in ["RAD 4", "RAD 3", "RAD 2", "RAD 1"]:
            level_data = levels[level_key]
            
            if not level_data["agents"]:
                continue
                
            # Vérifier l'espace disponible
            if y_pos < 4*cm:
                c.showPage()
                # Ajouter le logo sur la nouvelle page
                self.add_logo_to_pdf(c, width, height)
                y_pos = height - 2*cm
            
            # Titre du niveau
            c.setFont(self.get_font_name(bold=True), 14)
            c.drawString(2*cm, y_pos, level_data["title"])
            y_pos -= 0.8*cm
            
            # En-têtes de colonnes
            c.setFont(self.get_font_name(bold=True), 10)
            c.drawString(2*cm, y_pos, "Grade")
            c.drawString(6*cm, y_pos, "Nom")
            c.drawString(9.6*cm, y_pos, "Prénom")
            c.drawString(14.4*cm, y_pos, "Affectation")
            y_pos -= 0.5*cm
            
            # Agents du niveau
            c.setFont(self.get_font_name(), 10)
            for agent in level_data["agents"]:
                if y_pos < 2*cm:
                    c.showPage()
                    # Ajouter le logo sur la nouvelle page
                    self.add_logo_to_pdf(c, width, height)
                    y_pos = height - 2*cm
                
                nom, prenom, grade, niveau, affectation = agent
                c.drawString(2*cm, y_pos, grade or "")
                c.drawString(6*cm, y_pos, nom)
                c.drawString(9.6*cm, y_pos, prenom)
                c.drawString(14.4*cm, y_pos, affectation)
                y_pos -= 0.4*cm
            
            y_pos -= 0.5*cm  # Espace entre les niveaux
        
        c.save()

    def update_visible_columns(self):
        """Met à jour les colonnes visibles selon la sélection."""
        selected_option = self.columns_selector.currentText()
        
        if selected_option not in self.column_options:
            return
        
        # Toutes les colonnes disponibles dans l'ordre de la table
        all_columns = ["Nom", "Prénom", "Naissance", "Grade", "Statut", "Activité", "Niveau", "Affectation", "N° Sécu", "Dose Vie (mSv)", "Dose Annuelle (µSv)"]
        
        # Colonnes à afficher selon la sélection
        visible_columns = self.column_options[selected_option]
        
        # Masquer/afficher chaque colonne
        for i, column_name in enumerate(all_columns):
            if column_name in visible_columns:
                self.agents_table.showColumn(i)
            else:
                self.agents_table.hideColumn(i)
        
        # Recharger les données pour s'assurer que l'affichage est correct
        self.load_agents()

    def show_visibility_rh(self):
        """Affiche la fenêtre de visibilité RH avec graphique par tranches d'âge"""
        dialog = VisibilityRHDialog(self, self.db_path)
        dialog.exec_()


class VisibilityRHDialog(QDialog):
    """Dialogue pour afficher la visibilité RH par tranches d'âge"""
    
    def __init__(self, parent=None, db_path=None):
        super().__init__(parent)
        self.setWindowTitle("Visibilité RH - Répartition du personnel")
        self.setFixedSize(1200, 700)
        self.db_path = db_path  # Stocker le chemin de la base de données
        
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Répartition du personnel par tranches d'âge et statut d'activité")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Zone principale avec les 4 catégories
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(2)
        
        # Récupérer les données des agents
        self.load_agents_data()
        
        # Zone 1: Personnel actif < 40 ans (vert clair)
        zone1 = self.create_age_zone("Personnel actif\n< 40 ans", "#E8F5E8", self.active_under_40)
        main_layout.addWidget(zone1)
        
        # Zone 2: Personnel actif 40-54 ans (jaune clair)
        zone2 = self.create_age_zone("Personnel actif\n40-54 ans", "#FFF9E8", self.active_40_54)
        main_layout.addWidget(zone2)
        
        # Zone 3: Personnel actif ≥ 55 ans (orange clair)
        zone3 = self.create_age_zone("Personnel actif\n≥ 55 ans", "#FFF0E8", self.active_55_plus)
        main_layout.addWidget(zone3)
        
        # Zone 4: Personnel inactif < 55 ans (gris clair)
        zone4 = self.create_age_zone("Personnel inactif\n< 55 ans", "#F5F5F5", self.inactive_under_55)
        main_layout.addWidget(zone4)
        
        layout.addWidget(main_widget)
        
        # Bouton fermer
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def load_agents_data(self):
        """Charge les données des agents et les classe par catégorie"""
        from datetime import datetime
        
        self.active_under_40 = []
        self.active_40_54 = []
        self.active_55_plus = []
        self.inactive_under_55 = []
        
        try:
            conn = sqlite3.connect(self.db_path)  # Utiliser self.db_path au lieu de chemin codé en dur
            cursor = conn.cursor()
            
            # Récupérer tous les agents avec leurs dates de naissance
            cursor.execute("""
                SELECT nom, prenom, date_naissance, en_activite 
                FROM agents 
                WHERE date_naissance IS NOT NULL AND date_naissance != ''
                ORDER BY nom, prenom
            """)
            
            agents = cursor.fetchall()
            current_date = datetime.now()
            
            for nom, prenom, date_naissance, en_activite in agents:
                try:
                    # Calculer l'âge
                    birth_date = datetime.strptime(date_naissance, '%Y-%m-%d')
                    age = current_date.year - birth_date.year
                    if current_date.month < birth_date.month or (current_date.month == birth_date.month and current_date.day < birth_date.day):
                        age -= 1
                    
                    agent_info = f"{nom} {prenom} ({age} ans)"
                    
                    # Classer selon l'âge et le statut
                    if en_activite:
                        if age < 40:
                            self.active_under_40.append(agent_info)
                        elif age < 55:
                            self.active_40_54.append(agent_info)
                        else:
                            self.active_55_plus.append(agent_info)
                    else:
                        if age < 55:
                            self.inactive_under_55.append(agent_info)
                
                except ValueError:
                    # Ignorer les dates de naissance invalides
                    continue
            
            conn.close()
            
        except Exception as e:
            print(f"Erreur lors du chargement des données RH: {e}")
    
    def create_age_zone(self, title, bg_color, agents_list):
        """Crée une zone colorée avec la liste des agents"""
        zone_widget = QWidget()
        zone_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                margin: 2px;
                color: black;
            }}
        """)
        
        layout = QVBoxLayout(zone_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Titre de la zone
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(title_label)
        
        # Compteur
        count_label = QLabel(f"({len(agents_list)} personnes)")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("font-size: 10px; color: #666666; background: transparent; border: none;")
        layout.addWidget(count_label)
        
        # Liste des agents
        if agents_list:
            agents_text = QTextEdit()
            agents_text.setPlainText("\n".join(agents_list))
            agents_text.setReadOnly(True)
            # Suppression de setMaximumHeight pour permettre l'adaptation automatique
            agents_text.setStyleSheet("""
                QTextEdit {
                    background-color: white;
                    border: 1px solid #DDDDDD;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 5px;
                    color: black;
                }
            """)
            layout.addWidget(agents_text)
        else:
            no_data_label = QLabel("Aucune personne")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #999999; font-style: italic; background: transparent; border: none;")
            layout.addWidget(no_data_label)
            layout.addWidget(no_data_label)
        
        return zone_widget


class AgentDialog(QDialog):
    """Dialogue pour ajouter/modifier un agent."""
    
    def __init__(self, parent=None, agent_data=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter Agent" if agent_data is None else "Modifier Agent")
        self.setFixedSize(450, 400)
        
        layout = QFormLayout(self)
        
        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.date_naissance_input = QDateEdit()
        self.date_naissance_input.setCalendarPopup(True)
        self.date_naissance_input.setDate(QDate(1990, 1, 1))
        
        self.grade_input = QComboBox()
        self.grade_input.setEditable(True)
        self.grade_input.addItems([
            "", "Sapeur", "Caporal", "Caporal-Chef", "Sergent", "Sergent-Chef", 
            "Adjudant", "Adjudant-Chef", "Lieutenant", "Capitaine", 
            "Commandant", "Lieutenant-Colonel", "Colonel", "Contrôleur-Général"
        ])
        
        self.statut_input = QComboBox()
        self.statut_input.addItems(["SPV", "SPP"])
        
        self.activite_input = QCheckBox()
        self.activite_input.setChecked(True)
        
        self.numero_secu_input = QLineEdit()
        self.numero_secu_input.setPlaceholderText("1 23 45 67 890 123 45")
        
        self.niveau_input = QComboBox()
        self.niveau_input.addItems(["RAD 1", "RAD 2", "RAD 3", "RAD 4"])
        
        self.affectation_input = QLineEdit()
        
        # Remplir les champs si modification
        if agent_data:
            self.nom_input.setText(agent_data['nom'])
            self.prenom_input.setText(agent_data['prenom'])
            self.date_naissance_input.setDate(QDate.fromString(agent_data['date_naissance'], "yyyy-MM-dd"))
            self.grade_input.setCurrentText(agent_data.get('grade', ''))
            self.statut_input.setCurrentText(agent_data.get('statut', 'SPV'))
            self.activite_input.setChecked(bool(agent_data.get('en_activite', True)))
            self.numero_secu_input.setText(agent_data.get('numero_secu', ''))
            self.niveau_input.setCurrentText(agent_data['niveau'])
            self.affectation_input.setText(agent_data['affectation'])
        
        layout.addRow("Nom:", self.nom_input)
        layout.addRow("Prénom:", self.prenom_input)
        layout.addRow("Date de naissance:", self.date_naissance_input)
        layout.addRow("Grade:", self.grade_input)
        layout.addRow("Statut:", self.statut_input)
        layout.addRow("En activité:", self.activite_input)
        layout.addRow("N° Sécurité Sociale:", self.numero_secu_input)
        layout.addRow("Niveau RAD:", self.niveau_input)
        layout.addRow("Affectation:", self.affectation_input)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Annuler")
        
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addRow("", buttons_layout)
    
    def get_agent_data(self):
        """Retourne les données saisies."""
        return {
            'nom': self.nom_input.text().strip(),
            'prenom': self.prenom_input.text().strip(),
            'date_naissance': self.date_naissance_input.date().toString("yyyy-MM-dd"),
            'grade': self.grade_input.currentText().strip(),
            'statut': self.statut_input.currentText(),
            'en_activite': self.activite_input.isChecked(),
            'numero_secu': self.numero_secu_input.text().strip(),
            'niveau': self.niveau_input.currentText(),
            'affectation': self.affectation_input.text().strip()
        }
    
    def accept(self):
        """Validation avant acceptation."""
        if not all([self.nom_input.text().strip(), self.prenom_input.text().strip(), 
                   self.affectation_input.text().strip()]):
            QMessageBox.warning(self, "Attention", "Veuillez remplir tous les champs obligatoires.")
            return
        
        super().accept()


class CollectiveReportDialog(QDialog):
    """Dialogue pour sélectionner la période du rapport collectif."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rapport Collectif")
        self.setFixedSize(300, 200)
        
        layout = QFormLayout(self)
        
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate().addDays(-365))
        
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        
        layout.addRow("Date de début:", self.date_debut)
        layout.addRow("Date de fin:", self.date_fin)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        btn_ok = QPushButton("Générer")
        btn_cancel = QPushButton("Annuler")
        
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addRow("", buttons_layout)
    
    def get_date_range(self):
        """Retourne la plage de dates sélectionnée."""
        return self.date_debut.date(), self.date_fin.date()

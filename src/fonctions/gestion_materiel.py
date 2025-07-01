import sys
import sqlite3
import csv
import re
import os
from datetime import datetime, timedelta
from PySide6.QtCore import (Qt, QAbstractTableModel, QModelIndex)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QLineEdit, QFormLayout, QDialog,
    QDialogButtonBox, QMessageBox, QHeaderView, QLabel, QSpinBox,
    QFileDialog
)
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


def get_default_db_path():
    """Retourne le chemin par défaut de la base de données."""
    # Obtenir le répertoire racine du projet
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    db_path = os.path.join(project_root, "data", "materiel.db")
    
    # Créer le dossier data s'il n'existe pas
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    return db_path


def initialiser_db(db_name=None):
    """Crée les tables de la BDD avec un ID texte."""
    if db_name is None:
        db_name = get_default_db_path()
    
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


def generer_prochain_id_rt(db_name=None):
    """Génère le prochain ID-RT-xxx en se basant sur le plus grand existant."""
    if db_name is None:
        db_name = get_default_db_path()
    
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
        db_name = get_default_db_path()
    
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
        self.db_name = db_name or get_default_db_path()
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
        self.statut = QLineEdit()
        self.lieu = QLineEdit()
        self.affectation = QLineEdit()
        
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
            self.lieu.setText(res[4] or "")
            self.affectation.setText(res[5] or "")
        
        # Récupérer statut, quantité et numéro de série depuis les caractéristiques
        cursor.execute("SELECT nom_caracteristique, valeur_caracteristique FROM caracteristiques WHERE materiel_id=? AND nom_caracteristique IN ('Statut', 'Quantité', 'Numéro de série', 'N° de série', 'Numero de serie', 'Serial', 'SN')", (self.materiel_id,))
        caracteristiques_speciales = cursor.fetchall()
        
        for nom_car, val_car in caracteristiques_speciales:
            if nom_car == 'Statut':
                self.statut.setText(val_car or "")
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

        data_principales = (self.nom.text(), self.type.text(), self.usage.text(), self.marque.text(), self.lieu.text(), self.affectation.text())

        if self.materiel_id is None:  # Création
            new_id = generer_prochain_id_rt(self.db_name)
            self.materiel_id = new_id
            cursor.execute("INSERT INTO materiel (id, nom, type, usage, marque, lieu, affectation) VALUES (?, ?, ?, ?, ?, ?, ?)", (new_id, *data_principales))
        else:  # Mise à jour
            cursor.execute("UPDATE materiel SET nom=?, type=?, usage=?, marque=?, lieu=?, affectation=? WHERE id=?", (*data_principales, self.materiel_id))
            cursor.execute("DELETE FROM caracteristiques WHERE materiel_id=?", (self.materiel_id,))

        # Sauvegarder Statut, Quantité et Numéro de série comme caractéristiques spéciales
        if self.statut.text():
            cursor.execute("INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique) VALUES (?, ?, ?)", (self.materiel_id, 'Statut', self.statut.text()))
        
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


class PeremptionDialog(QDialog):
    """Boîte de dialogue pour définir les critères de vérification des dates de péremption."""
    
    def __init__(self, db_name=None, parent=None):
        super().__init__(parent)
        self.db_name = db_name or get_default_db_path()
        
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
                QMessageBox.information(
                    self, 
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
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du rapport: {e}")

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
        QMessageBox.information(
            self, 
            "Rapport généré", 
            f"Le rapport de péremption a été généré:\n{filename}\n\n"
            f"Matériels trouvés: {len(materiels)}\n"
            f"Délai: {delai_annees} an(s)"
        )


class GestionMaterielWindow(QMainWindow):
    """Fenêtre principale de gestion du matériel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_name = get_default_db_path()
        self.setWindowTitle("Gestionnaire de Matériel")
        self.setGeometry(100, 100, 1200, 600)

        # Initialiser la base de données
        initialiser_db(self.db_name)

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

        self.btn_ajouter = QPushButton("Ajouter")
        self.btn_modifier = QPushButton("Modifier la sélection")
        self.btn_supprimer = QPushButton("Supprimer la sélection")
        self.btn_peremption = QPushButton("Dates de péremption")
        self.btn_exporter_pdf = QPushButton("Exporter en PDF")

        self.btn_ajouter.clicked.connect(self.ajouter_materiel)
        self.btn_modifier.clicked.connect(self.modifier_materiel)
        self.btn_supprimer.clicked.connect(self.supprimer_materiel)
        self.btn_peremption.clicked.connect(self.verifier_peremption)
        self.btn_exporter_pdf.clicked.connect(self.exporter_pdf)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Filtre:"))
        search_layout.addWidget(self.search_input)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_ajouter)
        button_layout.addWidget(self.btn_modifier)
        button_layout.addWidget(self.btn_supprimer)
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
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un matériel à modifier.")
            return
        
        selected_row = selected_indexes[0].row()
        materiel_id = self.table_model.data(self.table_model.index(selected_row, 0))

        dialog = MaterielDialog(materiel_id=materiel_id, db_name=self.db_name, parent=self)
        if dialog.exec():
            self.charger_materiel(self.search_input.text())

    def supprimer_materiel(self):
        """Supprime le matériel sélectionné."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un matériel à supprimer.")
            return

        selected_row = selected_indexes[0].row()
        materiel_id = self.table_model.data(self.table_model.index(selected_row, 0))
        
        reponse = QMessageBox.question(self, "Confirmation", f"Êtes-vous sûr de vouloir supprimer '{materiel_id}' ?")
        
        if reponse == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM materiel WHERE id=?", (materiel_id,))
            conn.commit()
            conn.close()
            self.charger_materiel(self.search_input.text())

    def verifier_peremption(self):
        """Ouvre la fenêtre de vérification des dates de péremption."""
        dialog = PeremptionDialog(db_name=self.db_name, parent=self)
        dialog.exec()

    def exporter_pdf(self):
        """Exporter les données du tableau en PDF."""
        data_to_export = [self.table_model._headers] + self.table_model._data
        if len(data_to_export) <= 1:
            QMessageBox.information(self, "Info", "Aucune donnée à exporter.")
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
            QMessageBox.information(self, "Succès", f"Le fichier '{filename}' a été créé en format paysage adapté à la page.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de générer le PDF : {e}")


# Point d'entrée pour test standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = GestionMaterielWindow()
    window.show()
    
    sys.exit(app.exec())

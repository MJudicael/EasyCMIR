from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QGroupBox, QFormLayout, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QTimeEdit, QDoubleSpinBox, QComboBox, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QDateTime, QTime, QTimer, Signal
from PySide6.QtGui import QPixmap
import os
from datetime import datetime
from ..constants import ICONS_DIR
from ..utils.config_manager import config_manager

class ClickableLabel(QLabel):
    """Label cliquable personnalisé"""
    clicked = Signal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()

class InterventionDialog(QDialog):
    """Dialog pour les procédures d'intervention."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Suivi d'Intervention")
        self.setMinimumSize(800, 600)
        
        self.current_file = None
        self.layout = QVBoxLayout(self)
        self.start_datetime = datetime.now()
        
        # Layout supérieur pour les deux colonnes
        top_layout = QHBoxLayout()
        
        # Colonne 1 : Intervention et Gestion
        left_column = QVBoxLayout()
        
        # Groupe Intervention
        intervention_group = QGroupBox("Intervention")
        intervention_layout = QVBoxLayout()
        self.start_label = QLabel(f"Début : {self.start_datetime.strftime('%d/%m/%Y à %H:%M')}")
        self.start_label.setAlignment(Qt.AlignCenter)
        intervention_layout.addWidget(self.start_label)
        intervention_group.setLayout(intervention_layout)
        left_column.addWidget(intervention_group)
        
        # Groupe Gestion de l'intervention
        self.create_file_buttons()
        left_column.addWidget(self.file_group)
        
        # Colonne 2 : Formulaire d'entrée/sortie
        right_column = QVBoxLayout()
        self.create_entry_form()
        right_column.addWidget(self.form_group)
        
        # Ajout des colonnes au layout supérieur
        top_layout.addLayout(left_column)
        top_layout.addLayout(right_column)
        
        # Ajout du layout supérieur au layout principal
        self.layout.addLayout(top_layout)
        
        # Section Personnel engagé en bas
        self.create_engaged_view()
        self.layout.addWidget(self.engaged_group)
        
        # Initialisation
        self.engaged_personnel = {}
        self.next_agent_id = 1
        
        # Timer pour mise à jour du temps d'engagement
        self.engagement_timer = QTimer()
        self.engagement_timer.timeout.connect(self.update_engaged_view)
        self.engagement_timer.start(30000)  # 30 secondes
        
        # Créer automatiquement une nouvelle intervention au démarrage
        #self.create_new_intervention()

    def create_file_buttons(self):
        self.file_group = QGroupBox("Gestion de l'intervention")
        file_layout = QVBoxLayout()
        
        # Boutons dans un layout horizontal
        buttons_layout = QHBoxLayout()
        new_btn = QPushButton("Nouvelle intervention")
        new_btn.clicked.connect(self.create_new_intervention)
        
        open_btn = QPushButton("Reprendre une intervention")
        open_btn.clicked.connect(self.open_intervention)
        
        buttons_layout.addWidget(new_btn)
        buttons_layout.addWidget(open_btn)
        
        # Ajout du label date/heure
        self.datetime_label = QLabel()
        self.update_datetime()
        
        # Timer pour mettre à jour la date/heure toutes les secondes
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)  # Mise à jour toutes les secondes
        
        file_layout.addLayout(buttons_layout)
        file_layout.addWidget(self.datetime_label)
        self.file_group.setLayout(file_layout)
        
    def create_entry_form(self):
        """Crée le formulaire d'entrée/sortie"""
        form_group = QGroupBox("Entrée/Sortie Personnel")
        form_layout = QFormLayout()
        
        # Champs de saisie
        self.name_input = QLineEdit()
        self.team_input = QComboBox()
        self.team_input.addItems([f"Binôme {i}" for i in range(1, 11)])
        
        self.entry_time = QTimeEdit()
        self.entry_time.setTime(QTime.currentTime())
        
        self.exit_time = QTimeEdit()
        self.exit_time.setTime(QTime(0, 0))
        self.exit_time.setDisplayFormat("HH:mm")
        self.exit_time.setSpecialValueText(" ")
        
        self.dose_input = QDoubleSpinBox()
        self.dose_input.setDecimals(2)
        self.dose_input.setSuffix(" µSv")
        
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(60)
        
        # Ajout des champs au formulaire
        form_layout.addRow("Nom et Prénom:", self.name_input)
        form_layout.addRow("Équipe:", self.team_input)
        form_layout.addRow("Heure d'entrée:", self.entry_time)
        
        # Créer un layout horizontal pour l'heure de sortie et le bouton
        exit_layout = QHBoxLayout()
        exit_layout.addWidget(self.exit_time)
        
        exit_now_btn = QPushButton("Heure actuelle")
        exit_now_btn.clicked.connect(self.set_current_exit_time)
        exit_layout.addWidget(exit_now_btn)
        
        # Ajouter le layout à la place du widget simple
        form_layout.addRow("Heure de sortie:", exit_layout)
        
        form_layout.addRow("Dose:", self.dose_input)
        form_layout.addRow("Commentaire:", self.comment_input)
        
        # Modifier le bouton de validation
        submit_btn = QPushButton("Enregistrer l'entrée/sortie")
        submit_btn.clicked.connect(self.handle_entry)  # Nouvelle méthode unifiée
        form_layout.addRow(submit_btn)
        
        form_group.setLayout(form_layout)
        self.form_group = form_group
        
    def create_engaged_view(self):
        self.engaged_group = QGroupBox("Personnel engagé")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Définir une hauteur fixe pour le QScrollArea
        scroll.setFixedHeight(200)
        
        container = QWidget()
        self.engaged_layout = QHBoxLayout(container)
        self.engaged_layout.setSpacing(8)  # Espacement plus important pour éviter le chevauchement des bordures
        self.engaged_layout.setContentsMargins(5, 5, 5, 5)  # Marges du conteneur
        
        scroll.setWidget(container)
        
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.engaged_group.setLayout(layout)

    def create_history_view(self):
        history_group = QGroupBox("Historique des entrées/sorties")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels(
            ["Date", "Nom", "Équipe", "Entrée", "Sortie", "Dose", "Mission"]
        )
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SingleSelection)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Désactive l'édition directe
        self.history_table.itemClicked.connect(self.load_history_entry)  # Ajoute le signal de clic
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        self.layout.addWidget(history_group)

    def create_new_intervention(self):
        """Crée une nouvelle intervention après confirmation"""
        if self.current_file:
            reply = QMessageBox.question(
                self,
                "Nouvelle intervention",
                "Voulez-vous créer une nouvelle intervention ?\nL'intervention en cours sera fermée.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # Ajouter une entrée de fin pour l'intervention actuelle
            end_entry = {
                "date": datetime.now().strftime("%d/%m/%Y"),
                "name": "SYSTEM",
                "team": "-",
                "entry": "-",
                "exit": datetime.now().strftime("%H:%M"),
                "dose": "0",
                "comment": f"Intervention du {self.start_datetime.strftime('%d/%m/%Y %H:%M')} terminée"
            }
            
            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(f"{';'.join(end_entry.values())}\n")
        
        # Réinitialiser les données
        self.engaged_personnel.clear()
        self.next_agent_id = 1
        self.start_datetime = datetime.now()
        self.start_label.setText(f"Début : {self.start_datetime.strftime('%d/%m/%Y à %H:%M')}")
        
        # Créer le nouveau fichier
        timestamp = datetime.now().strftime("%d%m%Y%H%M")
        filename = f"intervention_{timestamp}.txt"
        
        # Obtenir le chemin configuré pour les interventions
        interventions_path = config_manager.get_interventions_path()
        if not interventions_path:
            QMessageBox.critical(
                self, 
                "Erreur de configuration", 
                "Le chemin du dossier d'interventions n'est pas configuré.\n"
                "Veuillez configurer le chemin dans les paramètres."
            )
            return
            
        # Créer le dossier s'il n'existe pas
        try:
            os.makedirs(interventions_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erreur de création du dossier", 
                f"Impossible de créer le dossier d'interventions :\n{interventions_path}\n\nErreur : {str(e)}"
            )
            return
            
        self.current_file = os.path.join(interventions_path, filename)
        
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write("Date;Nom;Équipe;Entrée;Sortie;Dose;Commentaire\n")
        
        # Mettre à jour l'affichage
        self.clear_form()
        self.update_engaged_view()

    def open_intervention(self):
        # Obtenir le chemin configuré pour les interventions
        interventions_path = config_manager.get_interventions_path()
        if not interventions_path:
            QMessageBox.critical(
                self, 
                "Erreur de configuration", 
                "Le chemin du dossier d'interventions n'est pas configuré.\n"
                "Veuillez configurer le chemin dans les paramètres."
            )
            return
            
        # Créer le dossier s'il n'existe pas
        try:
            os.makedirs(interventions_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erreur de création du dossier", 
                f"Impossible de créer le dossier d'interventions :\n{interventions_path}\n\nErreur : {str(e)}"
            )
            return
            
        filename, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une intervention", interventions_path, "Fichiers texte (*.txt)"
        )
        
        if filename:
            self.current_file = filename
            self.load_engaged_agents()
            
    def submit_entry(self):
        """Enregistre une nouvelle entrée"""
        if not self.current_file:
            QMessageBox.warning(
                self,
                "Aucune intervention active",
                "Veuillez d'abord créer une nouvelle intervention ou reprendre une intervention existante."
            )
            return
        
        # Vérifier que le nom est renseigné
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Nom manquant",
                "Veuillez saisir le nom et prénom de la personne."
            )
            return
        
        exit_time = self.exit_time.time()
        exit_str = "" if exit_time == QTime(0, 0) else exit_time.toString("HH:mm")
        
        # Création des données d'entrée
        entry_data = {
            "id": self.next_agent_id,
            "date": datetime.now().strftime("%d/%m/%Y"),
            "name": self.name_input.text(),
            "team": self.team_input.currentText(),
            "entry": self.entry_time.time().toString("HH:mm"),
            "exit": exit_str,
            "dose": str(self.dose_input.value()),
            "comment": self.comment_input.toPlainText().replace(";", ",")
        }

        # Si pas d'heure de sortie, ajouter aux agents engagés
        if not exit_str:
            self.engaged_personnel[self.next_agent_id] = entry_data
            self.next_agent_id += 1
            
        # Écriture dans le fichier historique
        with open(self.current_file, 'a', encoding='utf-8') as f:
            values = [str(v) for v in entry_data.values()]
            f.write(f"{';'.join(values[1:])}\n")  # Exclure l'ID de l'historique
    
        self.update_engaged_view()
        self.clear_form()

    def load_engaged_agents(self):
        """Charge uniquement les agents sans heure de sortie"""
        self.engaged_personnel.clear()  # Réinitialiser le dictionnaire
        self.next_agent_id = 1  # Réinitialiser le compteur d'ID
    
        if not self.current_file:
            return
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line in f:
                    data = line.strip().split(';')
                    if len(data) >= 5 and not data[4].strip():  # Vérifie si pas d'heure de sortie
                        # Création d'un dictionnaire pour l'agent
                        agent_data = {
                            "id": self.next_agent_id,
                            "date": data[0],
                            "name": data[1],
                            "team": data[2],
                            "entry": data[3],
                            "exit": "",
                            "dose": data[5] if len(data) > 5 else "0",
                            "comment": data[6] if len(data) > 6 else ""
                        }
                        
                        # Ajouter l'agent au dictionnaire des engagés
                        self.engaged_personnel[self.next_agent_id] = agent_data
                        self.next_agent_id += 1
        
            self.update_engaged_view()
        except Exception as e:
            print(f"Erreur lors du chargement des agents: {str(e)}")

    def update_engaged_view(self):
        """Met à jour l'affichage des agents engagés"""
        # Nettoyer l'ancien contenu
        while self.engaged_layout.count():
            item = self.engaged_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Ajouter un stretch au début pour centrer horizontalement
        self.engaged_layout.addStretch()
        
        for agent_id, agent in self.engaged_personnel.items():
            # Calcul du temps d'engagement
            entry_time = datetime.strptime(agent["entry"], "%H:%M")
            entry_datetime = datetime.combine(datetime.now().date(), entry_time.time())
            elapsed = datetime.now() - entry_datetime
            total_minutes = int(elapsed.total_seconds() // 60)
            
            # Création du widget agent
            agent_widget = QWidget()
            agent_widget.setFixedWidth(130)  # Largeur fixe pour uniformité
            agent_layout = QVBoxLayout(agent_widget)
            agent_layout.setSpacing(2)  # Espacement minimal entre les éléments
            agent_layout.setContentsMargins(5, 5, 5, 5)  # Marges équilibrées
            agent_layout.setAlignment(Qt.AlignCenter)  # Centrer le contenu du layout
            
            # Icône cliquable centrée
            icon_label = ClickableLabel()
            try:
                pixmap = self._get_icon().scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            except:
                # Si l'icône n'existe pas, utiliser un texte de remplacement
                icon_label.setText("👤")
                icon_label.setStyleSheet("font-size: 45px; color: #4a90e2;")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedSize(80, 80)  # Taille légèrement plus grande
            
            def make_callback(aid):
                return lambda: self.select_agent(aid)
            
            icon_label.clicked.connect(make_callback(agent_id))
            agent_layout.addWidget(icon_label, 0, Qt.AlignCenter)  # Centrer explicitement l'icône
            
            # Labels d'information
            for text in [
                agent["name"],
                agent["team"],
                f"{total_minutes} min"
            ]:
                label = QLabel(text)
                label.setAlignment(Qt.AlignCenter)
                label.setWordWrap(True)  # Permettre le retour à la ligne si nécessaire
                label.setFixedWidth(120)  # Largeur fixe pour forcer le centrage
                
                # Déterminer la couleur selon l'état de sélection
                color = '#1565c0' if agent_widget.property('selected') else '#333333'
                
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {color};
                        font-weight: bold;
                        text-align: center;
                        background-color: transparent;
                        padding: 0px;
                        margin: 0px;
                        qproperty-alignment: AlignCenter;
                    }}
                """)
                agent_layout.addWidget(label, 0, Qt.AlignCenter)  # Centrer explicitement chaque label
            
            agent_widget.setProperty("agent_id", agent_id)
            agent_widget.setStyleSheet(self._get_widget_style(False))
            
            self.engaged_layout.addWidget(agent_widget)
    
        # Ajouter un stretch à la fin pour centrer horizontalement
        self.engaged_layout.addStretch()
    
    def clear_form(self):
        """Réinitialise tous les champs du formulaire"""
        self.name_input.clear()
        self.team_input.setCurrentIndex(0)  # Réinitialiser le QComboBox
        self.entry_time.setTime(QTime.currentTime())
        self.exit_time.setTime(QTime(0, 0))
        self.dose_input.setValue(0)
        self.comment_input.clear()

    def edit_engaged_agent(self, item):
        """Charge les données d'un agent engagé dans le formulaire"""
        row = item.row()
        agent_id = self.engaged_table.item(row, 0).data(Qt.UserRole)
        agent = self.engaged_personnel[agent_id]
        
        self.name_input.setText(agent["name"])
        
        index = self.team_input.findText(agent["team"])
        if index >= 0:
            self.team_input.setCurrentIndex(index)
        
        self.entry_time.setTime(QTime.fromString(agent["entry"], "HH:mm"))
        self.comment_input.setPlainText(agent.get("comment", ""))
        
        if hasattr(self, 'update_btn'):
            self.update_btn.deleteLater()
        
        self.update_btn = QPushButton("Mettre à jour l'agent")
        self.update_btn.clicked.connect(lambda: self.update_agent(agent_id))
        self.layout.addWidget(self.update_btn)

    def update_agent(self, agent_id):
        """Met à jour un agent engagé"""
        if agent_id not in self.engaged_personnel:
            return
        
        exit_time = self.exit_time.time()
        exit_str = "" if exit_time == QTime(0, 0) else exit_time.toString("HH:mm")
        
        # Sauvegarder l'ancienne entrée
        old_name = self.engaged_personnel[agent_id]["name"]
        old_entry = self.engaged_personnel[agent_id]["entry"]
        
        # Mettre à jour les données
        updated_data = {
            "id": agent_id,
            "date": self.engaged_personnel[agent_id]["date"],
            "name": self.name_input.text(),
            "team": self.team_input.currentText(),
            "entry": self.entry_time.time().toString("HH:mm"),
            "exit": exit_str,
            "dose": str(self.dose_input.value()),
            "comment": self.comment_input.toPlainText().replace(";", ",")
        }
        
        # Supprimer l'agent si une heure de sortie est définie
        if exit_str:
            del self.engaged_personnel[agent_id]
        else:
            self.engaged_personnel[agent_id] = updated_data
        
        # Mettre à jour le fichier et l'affichage
        self.rewrite_history_file(old_name, old_entry, updated_data)
        self.update_engaged_view()
        self.clear_form()

    def rewrite_history_file(self, old_name, old_entry, updated_data):
        """Réécrit le fichier historique en mettant à jour l'agent modifié"""
        lines = []
        updated = False
        
        # Lire toutes les lignes existantes
        with open(self.current_file, 'r', encoding='utf-8') as f:
            lines.append(next(f))  # Conserver l'en-tête
            for line in f:
                data = line.strip().split(';')
                if (data[1] == old_name and data[3] == old_entry):
                    # Remplacer la ligne de l'agent modifié
                    values = [str(v) for v in updated_data.values()]
                    lines.append(f"{';'.join(values[1:])}\n")
                    updated = True
                else:
                    lines.append(line)
        
        # Si l'agent n'a pas été trouvé, ajouter la nouvelle entrée
        if not updated:
            values = [str(v) for v in updated_data.values()]
            lines.append(f"{';'.join(values[1:])}\n")
        
        # Réécrire le fichier
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def update_history_view(self):
        if not self.current_file:
            return
            
        with open(self.current_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            history_data = [line.strip().split(';') for line in f]
            
        self.history_table.setRowCount(len(history_data))
        for row, data in enumerate(history_data):
            for col, value in enumerate(data[:7]):  # Exclure les commentaires
                self.history_table.setItem(row, col, QTableWidgetItem(value))

    def load_history_entry(self, item):
        """Charge les données d'une entrée historique dans le formulaire"""
        row = item.row()
        history_data = []
        
        with open(self.current_file, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            history_data = [line.strip().split(';') for line in f]
        
        if row < len(history_data):
            data = history_data[row]
            self.name_input.setText(data[1])
            
            # Mettre à jour le QComboBox avec l'équipe de l'historique
            index = self.team_input.findText(data[2])
            if index >= 0:
                self.team_input.setCurrentIndex(index)
            
            # Définir l'heure d'entrée
            entry_time = QTime.fromString(data[3], "HH:mm")
            self.entry_time.setTime(entry_time)
            
            # Définir l'heure de sortie
            if data[4]:
                exit_time = QTime.fromString(data[4], "HH:mm")
                self.exit_time.setTime(exit_time)
            else:
                self.exit_time.setTime(QTime(0, 0))
            
            # Définir la dose si présente
            try:
                self.dose_input.setValue(float(data[5]))
            except (ValueError, IndexError):
                self.dose_input.setValue(0)
            
            # Définir le commentaire s'il existe
            if len(data) > 6:
                self.comment_input.setPlainText(data[6])
            else:
                self.comment_input.clear()
    
    # Nouvelle méthode unifiée
    def handle_entry(self):
        """Gère à la fois les nouvelles entrées et les mises à jour"""
        # Vérifier si un agent est sélectionné
        for i in range(self.engaged_layout.count()):
            widget = self.engaged_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget) and widget.property("selected"):
                # Mode mise à jour
                agent_id = widget.property("agent_id")
                self.update_agent(agent_id)
                return
    
        # Si aucun agent n'est sélectionné, créer une nouvelle entrée
        self.submit_entry()

    def update_datetime(self):
        """Met à jour l'affichage de la date et l'heure."""
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.setText(f"Date et heure : {current_datetime}")
        self.datetime_label.setAlignment(Qt.AlignCenter)

    def show_history(self):
        """Affiche l'historique dans une fenêtre popup."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Historique de l'intervention")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Création de la table d'historique
        history_table = QTableWidget()
        history_table.setColumnCount(7)
        history_table.setHorizontalHeaderLabels(
            ["Date", "Nom", "Équipe", "Entrée", "Sortie", "Dose", "Mission"]
        )
        history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(history_table)
        
        # Chargement des données
        self.load_history_data(history_table)
        
        dialog.setLayout(layout)
        dialog.exec()

    def select_agent(self, agent_id):
        """Sélectionne un agent et charge ses données dans le formulaire"""
        if agent_id in self.engaged_personnel:
            agent = self.engaged_personnel[agent_id]
            
            # Charger les données dans le formulaire
            self.name_input.setText(agent["name"])
            self.team_input.setCurrentText(agent["team"])
            self.entry_time.setTime(QTime.fromString(agent["entry"], "HH:mm"))
            self.dose_input.setValue(float(agent["dose"]))
            self.comment_input.setPlainText(agent.get("comment", ""))
            self.exit_time.setTime(QTime(0, 0))  # Reset l'heure de sortie
            
            # Marquer l'agent comme sélectionné
            for i in range(self.engaged_layout.count()):
                widget = self.engaged_layout.itemAt(i).widget()
                if widget and isinstance(widget, QWidget):
                    selected = widget.property("agent_id") == agent_id
                    widget.setProperty("selected", selected)
                    widget.setStyleSheet(self._get_widget_style(selected))

    def closeEvent(self, event):
        """Gère la fermeture de la fenêtre"""
        # Arrêter le timer
        self.engagement_timer.stop()
        
        if not self.current_file:
            event.accept()
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmation de fermeture",
            "Voulez-vous terminer l'intervention ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Ajouter la fin d'intervention dans l'historique
            end_entry = {
                "date": datetime.now().strftime("%d/%m/%Y"),
                "name": "SYSTEM",
                "team": "-",
                "entry": "-",
                "exit": datetime.now().strftime("%H:%M"),
                "dose": "0",
                "comment": f"Intervention du {self.start_datetime.strftime('%d/%m/%Y %H:%M')} terminée"
            }
            
            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(f"{';'.join(end_entry.values())}\n")
            
            # Accepter l'événement de fermeture
            event.accept()
        else:
            # Ignorer l'événement de fermeture
            event.ignore()

    # Ajouter cette nouvelle méthode
    def set_current_exit_time(self):
        """Définit l'heure de sortie à l'heure actuelle"""
        self.exit_time.setTime(QTime.currentTime())
        
    def _get_widget_style(self, selected):
        """Retourne le style CSS selon l'état de sélection"""
        border_style = "3px solid #4a90e2" if selected else "2px solid #cccccc"
        bg_color = "#e3f2fd" if selected else "#ffffff"
        
        return f"""
            QWidget {{
                border: {border_style};
                border-radius: 8px;
                padding: 5px;
                background-color: {bg_color};
                margin: 0px;
                min-width: 130px;
                max-width: 130px;
                text-align: center;
            }}
            ClickableLabel {{
                border: none;
                background-color: transparent;
                qproperty-alignment: AlignCenter;
            }}
        """

    def _get_icon(self):
        """Retourne le pixmap de l'icône NRBC"""
        icon_path = os.path.join(ICONS_DIR, "pompier.png")
        if os.path.exists(icon_path):
            return QPixmap(icon_path)
        else:
            # Retourner un pixmap vide si l'icône n'existe pas
            return QPixmap()
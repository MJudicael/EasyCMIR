from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QGroupBox, QFormLayout, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QTimeEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDateTime, QTime
import os
from datetime import datetime

class InterventionDialog(QDialog):
    """Dialog pour les procédures d'intervention."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Suivi d'Intervention")
        self.setMinimumSize(800, 600)
        
        self.current_file = None
        self.layout = QVBoxLayout(self)
        
        # Créer automatiquement une nouvelle intervention au démarrage
        self.create_new_intervention()
        
        # Groupe des boutons de gestion de fichier
        self.create_file_buttons()
        
        # Groupe du formulaire de saisie
        self.create_entry_form()
        
        # Groupe de visualisation des agents engagés
        self.create_engaged_view()
        
        # Ajout de l'historique après la vue des engagés
        self.create_history_view()
        
        # Initialisation et chargement des agents engagés
        self.engaged_agents = []
        self.engaged_personnel = {}  # Dictionnaire des agents engagés avec ID unique
        self.next_agent_id = 1  # Pour générer des IDs uniques
        self.load_engaged_agents()
        self.update_history_view()

    def create_file_buttons(self):
        file_group = QGroupBox("Gestion de l'intervention")
        file_layout = QHBoxLayout()
        
        new_btn = QPushButton("Nouvelle intervention")
        new_btn.clicked.connect(self.create_new_intervention)
        
        open_btn = QPushButton("Reprendre une intervention")
        open_btn.clicked.connect(self.open_intervention)
        
        file_layout.addWidget(new_btn)
        file_layout.addWidget(open_btn)
        file_group.setLayout(file_layout)
        self.layout.addWidget(file_group)
        
    def create_entry_form(self):
        form_group = QGroupBox("Entrée/Sortie Personnel")
        form_layout = QFormLayout()
        
        # Champs de saisie
        self.name_input = QLineEdit()
        self.team_input = QLineEdit()
        self.entry_time = QTimeEdit()
        self.entry_time.setTime(QTime.currentTime())
        self.exit_time = QTimeEdit()
        self.exit_time.setTime(QTime.currentTime())
        self.exit_time.setSpecialValueText("Non définie")  # Texte quand vide
        self.dose_input = QDoubleSpinBox()
        self.dose_input.setDecimals(2)
        self.dose_input.setSuffix(" µSv")
        self.mission_input = QLineEdit()
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(60)
        
        # Ajout des champs au formulaire
        form_layout.addRow("Nom et Prénom:", self.name_input)
        form_layout.addRow("Équipe:", self.team_input)
        form_layout.addRow("Heure d'entrée:", self.entry_time)
        
        # Ajout d'un bouton pour effacer l'heure de sortie
        clear_exit_btn = QPushButton("Pas d'heure de sortie")
        clear_exit_btn.clicked.connect(lambda: self.exit_time.setTime(QTime(0, 0)))
        
        # Layout horizontal pour l'heure de sortie et son bouton
        exit_layout = QHBoxLayout()
        exit_layout.addWidget(self.exit_time)
        exit_layout.addWidget(clear_exit_btn)
        
        form_layout.addRow("Heure de sortie:", exit_layout)
        form_layout.addRow("Dose reçue:", self.dose_input)
        form_layout.addRow("Mission:", self.mission_input)
        form_layout.addRow("Commentaire:", self.comment_input)
        
        # Bouton de validation
        submit_btn = QPushButton("Enregistrer l'entrée/sortie")
        submit_btn.clicked.connect(self.submit_entry)
        form_layout.addRow(submit_btn)
        
        form_group.setLayout(form_layout)
        self.layout.addWidget(form_group)
        
    def create_engaged_view(self):
        view_group = QGroupBox("Personnel engagé")
        view_layout = QVBoxLayout()
        
        self.engaged_table = QTableWidget()
        self.engaged_table.setColumnCount(4)
        self.engaged_table.setHorizontalHeaderLabels(["Nom", "Équipe", "Heure d'entrée", "Mission"])
        self.engaged_table.horizontalHeader().setStretchLastSection(True)
        self.engaged_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.engaged_table.setSelectionMode(QTableWidget.SingleSelection)
        self.engaged_table.itemDoubleClicked.connect(self.edit_engaged_agent)
        
        view_layout.addWidget(self.engaged_table)
        view_group.setLayout(view_layout)
        self.layout.addWidget(view_group)

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
        timestamp = datetime.now().strftime("%d%m%Y%H%M")
        filename = f"intervention_{timestamp}.txt"
        
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        interventions_dir = os.path.join(root_dir, "interventions")
        os.makedirs(interventions_dir, exist_ok=True)
        
        self.current_file = os.path.join(interventions_dir, filename)
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write("Date;Nom;Équipe;Entrée;Sortie;Dose;Mission;Commentaire\n")
            
    def open_intervention(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        interventions_dir = os.path.join(root_dir, "interventions")
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une intervention", interventions_dir, "Fichiers texte (*.txt)"
        )
        
        if filename:
            self.current_file = filename
            self.load_engaged_agents()
            
    def submit_entry(self):
        """Enregistre une nouvelle entrée"""
        if not self.current_file:
            return
            
        exit_time = self.exit_time.time()
        exit_str = "" if exit_time == QTime(0, 0) else exit_time.toString("HH:mm")
        
        # Création des données d'entrée
        entry_data = {
            "id": self.next_agent_id,
            "date": datetime.now().strftime("%d/%m/%Y"),
            "name": self.name_input.text(),
            "team": self.team_input.text(),
            "entry": self.entry_time.time().toString("HH:mm"),
            "exit": exit_str,
            "dose": str(self.dose_input.value()),
            "mission": self.mission_input.text(),
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
        self.update_history_view()
        self.clear_form()

    def load_engaged_agents(self):
        """Charge uniquement les agents sans heure de sortie"""
        self.engaged_agents = []
        if not self.current_file:
            return
            
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line in f:
                    data = line.strip().split(';')
                    # Un agent est considéré comme engagé s'il n'a pas d'heure de sortie
                    if len(data) >= 5 and data[4].strip() == "":
                        self.engaged_agents.append(data)
        
            self.update_engaged_view()
        except Exception as e:
            print(f"Erreur lors du chargement des agents: {str(e)}")

    def update_engaged_view(self):
        """Met à jour l'affichage des agents engagés"""
        self.engaged_table.setRowCount(len(self.engaged_personnel))
        
        for row, (agent_id, agent) in enumerate(self.engaged_personnel.items()):
            self.engaged_table.setItem(row, 0, QTableWidgetItem(agent["name"]))
            self.engaged_table.setItem(row, 1, QTableWidgetItem(agent["team"]))
            self.engaged_table.setItem(row, 2, QTableWidgetItem(agent["entry"]))
            self.engaged_table.setItem(row, 3, QTableWidgetItem(agent["mission"]))
            # Stocker l'ID de l'agent dans les données du premier item de la ligne
            self.engaged_table.item(row, 0).setData(Qt.UserRole, agent_id)

    def clear_form(self):
        self.name_input.clear()
        self.team_input.clear()
        self.entry_time.setTime(QTime.currentTime())
        self.exit_time.setTime(QTime.currentTime())
        self.dose_input.setValue(0)
        self.mission_input.clear()
        self.comment_input.clear()
        
    def edit_engaged_agent(self, item):
        """Charge les données d'un agent engagé dans le formulaire"""
        row = item.row()
        agent_id = self.engaged_table.item(row, 0).data(Qt.UserRole)
        agent = self.engaged_personnel[agent_id]
        
        self.name_input.setText(agent["name"])
        self.team_input.setText(agent["team"])
        self.entry_time.setTime(QTime.fromString(agent["entry"], "HH:mm"))
        self.mission_input.setText(agent["mission"])
        
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
        
        # Si une heure de sortie est ajoutée
        if exit_str:
            # Ajouter à l'historique
            entry_data = {
                "date": datetime.now().strftime("%d/%m/%Y"),
                "name": self.name_input.text(),
                "team": self.team_input.text(),
                "entry": self.entry_time.time().toString("HH:mm"),
                "exit": exit_str,
                "dose": str(self.dose_input.value()),
                "mission": self.mission_input.text(),
                "comment": self.comment_input.toPlainText().replace(";", ",")
            }
            
            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(f"{';'.join(entry_data.values())}\n")
            
            # Retirer de la liste des agents engagés
            del self.engaged_personnel[agent_id]
        else:
            # Mettre à jour les informations de l'agent engagé
            self.engaged_personnel[agent_id].update({
                "name": self.name_input.text(),
                "team": self.team_input.text(),
                "entry": self.entry_time.time().toString("HH:mm"),
                "mission": self.mission_input.text(),
            })
        
        self.update_engaged_view()
        self.update_history_view()
        self.clear_form()

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
            self.team_input.setText(data[2])
            
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
            
            # Définir la mission
            self.mission_input.setText(data[6] if len(data) > 6 else "")
            
            # Définir le commentaire s'il existe
            if len(data) > 7:
                self.comment_input.setPlainText(data[7])
            else:
                self.comment_input.clear()
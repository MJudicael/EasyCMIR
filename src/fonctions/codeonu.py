from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QMessageBox, 
    QScrollArea, QWidget, QHBoxLayout, QTabWidget
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from ..utils.icon_manager import IconManager

class CodeONUDialog(QDialog):
    """Dialog pour l'identification des codes ONU et matières."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recherche Codes")
        self.setMinimumWidth(500)
        
        # Initialisation du gestionnaire d'icônes
        self.icon_manager = IconManager()
        
        # Chargement des données
        self.danger_data = self.load_danger_data()
        self.matiere_data = self.load_matiere_data()
        
        # Initialisation des widgets de pictogrammes
        self.picto_scroll = QScrollArea()
        self.picto_widget = QWidget()
        self.picto_layout = QGridLayout(self.picto_widget)
        self.picto_scroll.setWidget(self.picto_widget)
        self.picto_scroll.setWidgetResizable(True)
        self.picto_scroll.setFixedHeight(80)
        self.picto_scroll.setFrameShape(QScrollArea.NoFrame)
        self.picto_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.picto_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Style du QScrollArea
        self.picto_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        
        # Création des onglets
        self.tab_widget = QTabWidget()
        self.create_onu_tab()
        self.create_matiere_tab()
        self.main_layout.addWidget(self.tab_widget)

    def create_onu_tab(self):
        """Crée l'onglet de recherche code ONU"""
        onu_widget = QWidget()
        onu_layout = QVBoxLayout()
        
        # Zone de recherche ONU
        input_group = QGroupBox("Recherche de code danger")
        input_layout = QGridLayout()
        
        # Zone de saisie avec validation
        self.code_label = QLabel("Code :")
        self.code_input = QComboBox()
        self.code_input.setEditable(True)
        self.code_input.setMaxVisibleItems(10)  # Remplace setMaxLength
        self.code_input.currentTextChanged.connect(self.validate_onu_input)
        
        # Limitation de la longueur via la validation
        self.code_input.lineEdit().setMaxLength(4)  # Applique la limitation sur le lineEdit
        self.code_input.addItems(sorted(self.danger_data['CODES_DANGER'].keys()))
        
        # Ajout d'un bouton de recherche
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self.identify_code)
        input_layout.addWidget(search_button, 0, 2)
        
        input_layout.addWidget(self.code_label, 0, 0)
        input_layout.addWidget(self.code_input, 0, 1)
        
        input_group.setLayout(input_layout)
        onu_layout.addWidget(input_group)

        # Zone des résultats et pictogrammes
        self.create_result_widgets(onu_layout)
        
        onu_widget.setLayout(onu_layout)
        self.tab_widget.addTab(onu_widget, "Code ONU")

    def create_matiere_tab(self):
        """Crée l'onglet de recherche code matière"""
        matiere_widget = QWidget()
        matiere_layout = QVBoxLayout()
        
        # Zone de recherche matière avec validation
        input_group = QGroupBox("Recherche de code matière")
        input_layout = QGridLayout()
        
        self.matiere_label = QLabel("Code :")
        self.matiere_input = QComboBox()
        self.matiere_input.setEditable(True)
        self.matiere_input.currentTextChanged.connect(self.validate_matiere_input)
        self.matiere_input.addItems(sorted(self.matiere_data.keys()))
        
        # Ajout d'un bouton de recherche
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self.search_matiere)
        input_layout.addWidget(search_button, 0, 2)

        input_layout.addWidget(self.matiere_label, 0, 0)
        input_layout.addWidget(self.matiere_input, 0, 1)

        input_group.setLayout(input_layout)
        matiere_layout.addWidget(input_group)
        
        # Zone de résultat matière
        result_group = QGroupBox("Description")
        result_layout = QVBoxLayout()
        self.matiere_result = QLabel()
        self.matiere_result.setWordWrap(True)
        result_layout.addWidget(self.matiere_result)
        result_group.setLayout(result_layout)
        matiere_layout.addWidget(result_group)
        
        matiere_widget.setLayout(matiere_layout)
        self.tab_widget.addTab(matiere_widget, "Code Matière")

    def load_matiere_data(self):
        """Charge les données depuis codes_matiere.txt"""
        data = {}
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                "data", "codes_matiere.txt")
        
        # Créer le dossier data s'il n'existe pas
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Créer le fichier s'il n'existe pas
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Format: CODE;DESCRIPTION\n")
                print(f"Fichier créé: {file_path}")
            except Exception as e:
                print(f"Erreur lors de la création du fichier: {e}")
                return data

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.strip() and not line.startswith('#'):
                        code, description = line.strip().split(';', 1)
                        data[code] = description.strip()
        except Exception as e:
            print(f"Erreur lors du chargement des données matières: {e}")
        return data

    def load_danger_data(self):
        """Charge les données depuis le fichier codes_danger.txt"""
        data = {
            'CODES_DANGER': {},
            'PROTECTION_RECOMMENDATIONS': {}
        }
        
        # Chemin vers le fichier de données
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_path, "data", "codes_danger.txt")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                current_section = None
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        if line.startswith('#'):
                            current_section = line[1:]
                        continue
                    
                    key, value = line.split(':', 1)
                    if current_section == 'CODES_DANGER':
                        data['CODES_DANGER'][key] = value.strip()
                    elif current_section == 'PROTECTION_RECOMMENDATIONS':
                        data['PROTECTION_RECOMMENDATIONS'][key] = value.strip().split(':')
        
        except FileNotFoundError:
            print(f"Erreur: Fichier non trouvé: {file_path}")
            raise
        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
            raise
            
        return data

    def create_input_widgets(self):
        """Crée les widgets de saisie."""
        input_group = QGroupBox("Recherche de code danger")
        input_layout = QGridLayout()
        
        # Zone de saisie
        self.code_label = QLabel("Code :")
        self.code_input = QComboBox()
        self.code_input.setEditable(True)
        self.code_input.addItems(sorted(self.danger_data['CODES_DANGER'].keys()))
        
        input_layout.addWidget(self.code_label, 0, 0)
        input_layout.addWidget(self.code_input, 0, 1)
        
        # Bouton de recherche
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self.identify_code)
        input_layout.addWidget(search_button, 1, 0, 1, 2)
        
        input_group.setLayout(input_layout)
        self.main_layout.addWidget(input_group)

    def create_result_widgets(self, parent_layout):
        """Crée les widgets d'affichage des résultats.
        
        Args:
            parent_layout: Layout parent où ajouter les widgets
        """
        # Zone de résultats (identification)
        result_group = QGroupBox("Identification")
        result_layout = QVBoxLayout()
        self.result_danger = QLabel()
        self.result_danger.setWordWrap(True)
        result_layout.addWidget(self.result_danger)
        result_group.setLayout(result_layout)
        parent_layout.addWidget(result_group)
        
        # Zone des pictogrammes
        self.picto_group = QGroupBox("Pictogramme(s)")
        picto_container = QVBoxLayout()
        picto_container.addWidget(self.picto_scroll)
        self.picto_group.setLayout(picto_container)
        parent_layout.addWidget(self.picto_group)
        
        # Zone des mesures de protection
        protection_group = QGroupBox("Mesures de protection")
        protection_layout = QVBoxLayout()
        
        # Tenue de protection
        tenue_layout = QHBoxLayout()
        tenue_label = QLabel("Tenue de protection :")
        tenue_label.setStyleSheet("font-weight: bold;")
        self.result_tenue = QLabel()
        self.result_tenue.setWordWrap(True)
        tenue_layout.addWidget(tenue_label)
        tenue_layout.addWidget(self.result_tenue)
        protection_layout.addLayout(tenue_layout)
        
        # Zone d'exclusion
        zone_layout = QHBoxLayout()
        zone_label = QLabel("Zone d'exclusion :")
        zone_label.setStyleSheet("font-weight: bold;")
        self.result_zone = QLabel()
        self.result_zone.setWordWrap(True)
        zone_layout.addWidget(zone_label)
        zone_layout.addWidget(self.result_zone)
        protection_layout.addLayout(zone_layout)
        
        # Autres recommandations
        other_layout = QVBoxLayout()
        other_label = QLabel("Autres recommandations :")
        other_label.setStyleSheet("font-weight: bold;")
        self.result_other = QLabel()
        self.result_other.setWordWrap(True)
        other_layout.addWidget(other_label)
        other_layout.addWidget(self.result_other)
        protection_layout.addLayout(other_layout)
        
        protection_group.setLayout(protection_layout)
        parent_layout.addWidget(protection_group)

    def validate_onu_input(self, text):
        """Valide l'entrée du code ONU."""
        try:
            # Nettoyer l'entrée
            text = text.strip().upper()
            if text:
                # Vérifier que tous les caractères sont des chiffres
                if not text.isdigit():
                    self.code_input.setStyleSheet("background-color: #FFE4E1;")
                    return
                
                # Vérifier la longueur
                if len(text) > 4:
                    self.code_input.setStyleSheet("background-color: #FFE4E1;")
                    return
                
                self.code_input.setStyleSheet("")
                self.identify_code()  # Recherche automatique
        except Exception as e:
            print(f"Erreur de validation ONU: {e}")

    def validate_matiere_input(self, text):
        """Valide l'entrée du code matière."""
        try:
            # Nettoyer l'entrée
            text = text.strip().upper()
            if text:
                # Vérifier le format (UN suivi de 4 chiffres)
                if not (text.startswith("UN") and text[2:].isdigit() and len(text) <= 6):
                    self.matiere_input.setStyleSheet("background-color: #FFE4E1;")
                    return
                
                self.matiere_input.setStyleSheet("")
                self.search_matiere()  # Recherche automatique
        except Exception as e:
            print(f"Erreur de validation matière: {e}")

    def search_matiere(self):
        """Recherche et affiche les informations sur la matière."""
        try:
            code = self.matiere_input.currentText().strip().upper()
            if code in self.matiere_data:
                self.matiere_result.setText(self.matiere_data[code])
                self.matiere_result.setStyleSheet("")
            else:
                self.matiere_result.setText("Code matière non trouvé")
                self.matiere_result.setStyleSheet("color: red;")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la recherche: {str(e)}")

    def identify_code(self):
        """Identifie le code danger saisi avec gestion d'erreurs améliorée."""
        try:
            code = self.code_input.currentText().strip().upper()
            
            # Validation du code
            if not code:
                raise ValueError("Le code ne peut pas être vide")
            if not code.isdigit():
                raise ValueError("Le code doit contenir uniquement des chiffres")
            if len(code) > 4:
                raise ValueError("Le code ne peut pas dépasser 4 chiffres")

            # Nettoyage des anciens résultats
            self.clear_results()
            
            # Recherche et affichage des résultats
            if code in self.danger_data['CODES_DANGER']:
                self.display_danger_info(code)
            else:
                self.show_not_found_message()
                
        except ValueError as ve:
            QMessageBox.warning(self, "Erreur de validation", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Erreur système", f"Une erreur est survenue: {str(e)}")

    def clear_results(self):
        """Nettoie tous les champs de résultats."""
        self.result_danger.setText("")
        self.result_tenue.setText("")
        self.result_zone.setText("")
        self.result_other.setText("")
        
        for i in reversed(range(self.picto_layout.count())): 
            widget = self.picto_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def display_danger_info(self, code):
        """Affiche les informations de danger pour un code donné."""
        # Affichage de l'identification
        self.result_danger.setText(self.danger_data['CODES_DANGER'][code])
        
        # Mise à jour des pictogrammes
        has_pictograms = self.update_pictograms(code)
        self.picto_group.setVisible(has_pictograms)
        
        # Affichage des recommandations
        self.display_recommendations(code)

    def show_not_found_message(self):
        """Affiche les messages quand un code n'est pas trouvé."""
        self.result_danger.setText("Code danger non répertorié")
        self.result_danger.setStyleSheet("color: red;")
        self.picto_group.hide()
        self.result_tenue.setText("Non spécifiée")
        self.result_zone.setText("Non spécifiée")
        self.result_other.setText("Aucune recommandation disponible")

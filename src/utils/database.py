import os
from datetime import datetime
from PySide6.QtWidgets import QMessageBox
from src.config import ISOTOPES_FILE, HISTORY_FILE

def load_isotopes():
    """Charge les isotopes depuis le fichier texte."""
    isotopes_data = {}
    try:
        with open(ISOTOPES_FILE, "r", encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(';')
                if len(parts) == 9:
                    try:
                        name = parts[0]
                        isotopes_data[name] = {
                            'activite': float(parts[1]),
                            'periode': float(parts[2]),
                            'e1': float(parts[3]),
                            'e2': float(parts[4]),
                            'e3': float(parts[5]),
                            'q1': float(parts[6]),
                            'q2': float(parts[7]),
                            'q3': float(parts[8])
                        }
                    except ValueError:
                        QMessageBox.warning(None, "Ligne Malformée", 
                            f"Ligne malformée ignorée dans isotopes.txt: {line.strip()}")
                else:
                    QMessageBox.warning(None, "Ligne Malformée", 
                        f"Ligne malformée ignorée dans isotopes.txt (nombre incorrect de champs): {line.strip()}")
    except FileNotFoundError:
        QMessageBox.critical(None, "Fichier Non Trouvé", 
            f"Base de données isotopes '{ISOTOPES_FILE}' non trouvée.")
    return isotopes_data

def save_to_history(data_list):
    """Sauvegarde les données dans l'historique."""
    try:
        with open(HISTORY_FILE, "a", encoding='utf-8') as f:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{date};{';'.join(map(str, data_list))}\n")
    except Exception as e:
        QMessageBox.warning(None, "Erreur Historique", 
            f"Erreur lors de la sauvegarde dans l'historique : {e}")
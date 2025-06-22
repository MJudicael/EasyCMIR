from PySide6.QtWidgets import QMessageBox
from datetime import datetime
from ..fonctions.decroissance import DecroissanceCalculator

def calculate_and_plot(self):
    """Calcule et affiche la décroissance radioactive."""
    try:
        # Vérification des entrées
        if not self.activity_input.text() or not self.period_input.text():
            raise ValueError("Veuillez remplir tous les champs")
            
        # Conversion et validation des entrées
        try:
            initial_activity = float(self.activity_input.text().replace(',', '.'))
            half_life = float(self.period_input.text().replace(',', '.'))
        except ValueError:
            raise ValueError("Les valeurs doivent être numériques")
            
        if initial_activity <= 0 or half_life <= 0:
            raise ValueError("Les valeurs doivent être positives")
        
        # Calcul de la décroissance
        start_datetime = datetime.now()
        calculator = DecroissanceCalculator()
        
        # Configuration initiale du calculateur
        calculator.initial_activity = initial_activity
        calculator.half_life = half_life
        calculator.start_datetime = start_datetime
        
        # Calcul des points à 10 périodes
        end_datetime, final_activity = calculator.calculate_ten_periods(
            initial_activity, 
            half_life, 
            start_datetime
        )
        
        # Génération et affichage du graphique
        figure = calculator.plot_decay()
        if hasattr(self, 'canvas'):
            self.canvas.figure = figure
            self.canvas.draw()
        else:
            raise AttributeError("Le widget canvas n'est pas initialisé")
        
        # Mise à jour des résultats avec formatage
        self.result_label.setText(
            f"Après 10 périodes :\n"
            f"Date : {end_datetime.strftime('%d/%m/%Y à %H:%M')}\n"
            f"Activité initiale : {initial_activity:.2e} Bq\n"
            f"Activité restante : {final_activity:.2e} Bq\n"
            f"Période : {half_life:.2f} heures"
        )
        
    except ValueError as e:
        QMessageBox.warning(self, "Erreur de saisie", str(e))
    except AttributeError as e:
        QMessageBox.critical(self, "Erreur technique", str(e))
    except Exception as e:
        QMessageBox.critical(self, "Erreur inattendue", f"Une erreur est survenue : {str(e)}")
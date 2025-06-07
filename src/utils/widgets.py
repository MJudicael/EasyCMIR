from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QLineEdit
from PySide6.QtCore import Qt, QLocale

class ClearingDoubleSpinBox(QDoubleSpinBox):
    """Un QDoubleSpinBox qui accepte les points et les virgules comme séparateur décimal."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Création d'un QLocale qui utilise le point comme séparateur
        locale = QLocale(QLocale.English)
        locale.setNumberOptions(QLocale.NumberOption.RejectGroupSeparator)
        self.setLocale(locale)
        
    def validate(self, text, pos):
        # Remplace la virgule par un point
        text = text.replace(',', '.')
        return super().validate(text, pos)
        
    def textFromValue(self, value):
        # Format le nombre avec un point
        return str(value).replace(',', '.')
        
    def valueFromText(self, text):
        # Convertit le texte en nombre en gérant les virgules
        text = text.replace(',', '.')
        return float(text)
        
    def fixup(self, text):
        # Nettoie le texte en remplaçant les virgules par des points
        return text.replace(',', '.')

class ClearingSpinBox(QSpinBox):
    """SpinBox qui sélectionne tout son contenu lors du focus."""
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()

class ClearingLineEdit(QLineEdit):
    """LineEdit qui sélectionne tout son contenu lors du focus."""
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()
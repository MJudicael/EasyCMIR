#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier les modifications apportées à EasyCMIR
- Suppression du bouton "Code DANGER" 
- Ajout du menu "Gestion" avec raccourcis clavier
"""

import sys
import os

# Ajout du chemin src pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from PySide6.QtWidgets import QApplication
    from src.widgets.main_window import MainWindow
    from src.utils.icon_manager import IconManager
    
    print("✅ Imports réussis")
    
    # Test de l'IconManager
    icon_manager = IconManager()
    print("✅ IconManager initialisé")
    
    # Vérification que "Code DANGER" n'est plus dans le mapping
    if "Code DANGER" not in icon_manager.icon_mapping:
        print("✅ 'Code DANGER' supprimé du mapping des icônes")
    else:
        print("❌ 'Code DANGER' encore présent dans le mapping")
    
    # Vérification que les autres icônes sont présentes
    required_icons = ["Gestion RH", "Matériel", "Décroissance", "Distance"]
    for icon_name in required_icons:
        if icon_name in icon_manager.icon_mapping:
            print(f"✅ Icône '{icon_name}' présente")
        else:
            print(f"❌ Icône '{icon_name}' manquante")
    
    print("\n=== Test de l'interface (fermer la fenêtre pour continuer) ===")
    
    # Test de l'interface graphique
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Vérification des menus
    menubar = window.menuBar()
    menu_names = [action.text() for action in menubar.actions()]
    
    if "Gestion" in menu_names:
        print("✅ Menu 'Gestion' présent")
    else:
        print("❌ Menu 'Gestion' absent")
        
    if "Aide" in menu_names:
        print("✅ Menu 'Aide' présent")
    else:
        print("❌ Menu 'Aide' absent")
    
    window.show()
    
    print("\nTest terminé - vérifiez l'interface graphique:")
    print("- Le bouton 'Code DANGER' ne doit plus être visible")
    print("- Les boutons 'Gestion RH' et 'Matériel' ne doivent plus être dans la grille")
    print("- Le menu 'Gestion' doit être présent avec 'Gestion RH' (Ctrl+R) et 'Matériel' (Ctrl+M)")
    print("- L'interface doit avoir 9 boutons disposés en 3x3")
    
    sys.exit(app.exec())
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous que PySide6 est installé")
except Exception as e:
    print(f"❌ Erreur: {e}")

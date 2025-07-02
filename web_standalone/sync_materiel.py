#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EasyCMIR - Scrip                    materiel = {
                        'id': row['id'],
                        'type': row['type'] or '',
                        'usage': row['usage'] or '',
                        'modele': carac_dict.get('Modèle', ''),
                        'marque': row['marque'] or '',
                        'numero_serie': carac_dict.get('Numéro de série', ''),  # Nom correct avec accent
                        'quantite': int(carac_dict.get('Quantité', '1')) if carac_dict.get('Quantité', '').isdigit() else 1,
                        'statut': carac_dict.get('Statut', ''),
                        'lieu': row['lieu'] or '',
                        'affectation': row['affectation'] or '',
                        'created': '',  # Champ pour compatibilité web
                        'modified': ''  # Champ pour compatibilité web
                    }sation SQLite ↔ JSON
Gère la synchronisation bidirectionnelle entre la base SQLite et l'interface web
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

class MaterielSynchronizer:
    def __init__(self, db_path=None, json_path=None):
        # Chemins par défaut
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "materiel.db"
        if json_path is None:
            json_path = Path(__file__).parent / "materiel.json"
            
        self.db_path = Path(db_path)
        self.json_path = Path(json_path)
        self.status_file = Path(__file__).parent / "sync_status.json"
        
    def get_db_connection(self):
        """Établit une connexion à la base SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Pour avoir des dictionnaires
            return conn
        except sqlite3.Error as e:
            raise Exception(f"Erreur de connexion à la base : {e}")
    
    def sqlite_to_json(self):
        """Exporte les données SQLite vers JSON pour l'interface web"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Récupérer tous les matériels 
                # Structure réelle : table materiel (id, nom, type, usage, marque, lieu, affectation)
                # et table caracteristiques (id, materiel_id, nom_caracteristique, valeur_caracteristique)
                cursor.execute("""
                    SELECT id, nom, type, usage, marque, lieu, affectation
                    FROM materiel
                    ORDER BY id
                """)
                
                rows = cursor.fetchall()
                
                # Convertir en format JSON
                materiels = []
                for row in rows:
                    materiel_id = row['id']
                    
                    # Récupérer les caractéristiques pour ce matériel
                    cursor.execute("""
                        SELECT nom_caracteristique, valeur_caracteristique 
                        FROM caracteristiques 
                        WHERE materiel_id = ?
                    """, (materiel_id,))
                    
                    caracteristiques = cursor.fetchall()
                    
                    # Créer un dictionnaire des caractéristiques
                    carac_dict = {}
                    for carac in caracteristiques:
                        carac_dict[carac['nom_caracteristique']] = carac['valeur_caracteristique']
                    
                    materiel = {
                        'id': materiel_id,
                        'type': row['type'] or '',
                        'usage': row['usage'] or '',
                        'modele': carac_dict.get('Modèle', ''),
                        'marque': row['marque'] or '',
                        'numero_serie': carac_dict.get('Numéro de série', '') or carac_dict.get('N° de série', ''),
                        'quantite': int(carac_dict.get('Quantité', '1')) if carac_dict.get('Quantité', '').isdigit() else 1,
                        'statut': carac_dict.get('Statut', ''),
                        'lieu': row['lieu'] or '',
                        'affectation': row['affectation'] or '',
                        'created': '',  # Champ pour compatibilité web
                        'modified': ''  # Champ pour compatibilité web
                    }
                    materiels.append(materiel)
                
                # Préparer les données JSON
                json_data = {
                    'materiels': materiels,
                    'lastUpdate': datetime.now().isoformat(),
                    'source': 'sqlite',
                    'version': '1.0',
                    'total': len(materiels)
                }
                
                # Sauvegarder le fichier JSON
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Export SQLite → JSON terminé : {len(materiels)} matériels")
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de l'export SQLite → JSON : {e}")
            return False
    
    def json_to_sqlite(self):
        """Importe les modifications JSON vers la base SQLite"""
        try:
            # Vérifier si le fichier JSON existe
            if not self.json_path.exists():
                print("⚠️  Fichier JSON non trouvé, rien à importer")
                return True
            
            # Charger les données JSON
            with open(self.json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            materiels = json_data.get('materiels', [])
            if not materiels:
                print("⚠️  Aucun matériel dans le fichier JSON")
                return True
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # S'assurer que les tables existent
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS materiel (
                        id TEXT PRIMARY KEY,
                        nom TEXT NOT NULL DEFAULT '',
                        type TEXT,
                        usage TEXT,
                        marque TEXT,
                        lieu TEXT,
                        affectation TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS caracteristiques (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        materiel_id TEXT,
                        nom_caracteristique TEXT NOT NULL,
                        valeur_caracteristique TEXT,
                        FOREIGN KEY (materiel_id) REFERENCES materiel (id)
                    )
                """)
                
                # Synchroniser chaque matériel
                updated = 0
                added = 0
                
                for materiel in materiels:
                    materiel_id = materiel['id']
                    
                    # Vérifier si le matériel existe
                    cursor.execute("SELECT id FROM materiel WHERE id = ?", (materiel_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Mettre à jour le matériel principal
                        cursor.execute("""
                            UPDATE materiel SET
                                type = ?, usage = ?, marque = ?, lieu = ?, affectation = ?
                            WHERE id = ?
                        """, (
                            materiel.get('type', ''),
                            materiel.get('usage', ''),
                            materiel.get('marque', ''),
                            materiel.get('lieu', ''),
                            materiel.get('affectation', ''),
                            materiel_id
                        ))
                        updated += 1
                    else:
                        # Ajouter le matériel
                        cursor.execute("""
                            INSERT INTO materiel (id, nom, type, usage, marque, lieu, affectation)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            materiel_id,
                            '',  # nom vide par défaut
                            materiel.get('type', ''),
                            materiel.get('usage', ''),
                            materiel.get('marque', ''),
                            materiel.get('lieu', ''),
                            materiel.get('affectation', '')
                        ))
                        added += 1
                    
                    # Gérer les caractéristiques (supprimer et recréer pour simplifier)
                    cursor.execute("DELETE FROM caracteristiques WHERE materiel_id = ?", (materiel_id,))
                    
                    # Ajouter les caractéristiques
                    caracteristiques = [
                        ('Modèle', materiel.get('modele', '')),
                        ('Numéro de série', materiel.get('numero_serie', '')),  # Nom correct avec accent
                        ('Quantité', str(materiel.get('quantite', 1))),
                        ('Statut', materiel.get('statut', ''))
                    ]
                    
                    for nom_carac, valeur_carac in caracteristiques:
                        if valeur_carac:  # Seulement si la valeur n'est pas vide
                            cursor.execute("""
                                INSERT INTO caracteristiques (materiel_id, nom_caracteristique, valeur_caracteristique)
                                VALUES (?, ?, ?)
                            """, (materiel_id, nom_carac, valeur_carac))
                
                conn.commit()
                print(f"✅ Import JSON → SQLite terminé : {added} ajoutés, {updated} modifiés")
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de l'import JSON → SQLite : {e}")
            return False
    
    def sync_bidirectional(self):
        """Synchronisation bidirectionnelle complète"""
        print("🔄 Début de la synchronisation bidirectionnelle")
        
        # Étape 1 : SQLite → JSON (export pour l'interface web)
        print("\n1️⃣ Export SQLite → JSON")
        if not self.sqlite_to_json():
            return False
        
        # Étape 2 : JSON → SQLite (import des modifications web)
        print("\n2️⃣ Import JSON → SQLite")
        if not self.json_to_sqlite():
            return False
        
        # Étape 3 : Re-export pour s'assurer de la cohérence
        print("\n3️⃣ Re-export pour cohérence")
        if not self.sqlite_to_json():
            return False
        
        # Enregistrer le statut de synchronisation
        self.save_sync_status(True)
        print("\n✅ Synchronisation complète terminée avec succès")
        return True
    
    def save_sync_status(self, success, message=""):
        """Enregistre le statut de la dernière synchronisation"""
        status = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"⚠️  Impossible de sauvegarder le statut : {e}")
    
    def get_sync_status(self):
        """Récupère le statut de la dernière synchronisation"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {
            'success': False,
            'timestamp': None,
            'message': 'Jamais synchronisé'
        }
    
    def check_data_integrity(self):
        """Vérifie l'intégrité des données"""
        print("🔍 Vérification de l'intégrité des données")
        
        try:
            # Compter les matériels dans SQLite
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM materiel")
                sqlite_count = cursor.fetchone()[0]
            
            # Compter les matériels dans JSON
            json_count = 0
            if self.json_path.exists():
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    json_count = len(json_data.get('materiels', []))
            
            print(f"📊 SQLite: {sqlite_count} matériels")
            print(f"📊 JSON: {json_count} matériels")
            
            if sqlite_count == json_count:
                print("✅ Données cohérentes")
                return True
            else:
                print("⚠️  Incohérence détectée, synchronisation recommandée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification : {e}")
            return False


def main():
    """Fonction principale avec gestion des arguments"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python sync_materiel.py export    # SQLite → JSON")
        print("  python sync_materiel.py import    # JSON → SQLite")
        print("  python sync_materiel.py sync      # Synchronisation complète")
        print("  python sync_materiel.py check     # Vérifier l'intégrité")
        print("  python sync_materiel.py status    # Statut de synchronisation")
        return
    
    command = sys.argv[1].lower()
    
    # Initialiser le synchroniseur
    sync = MaterielSynchronizer()
    
    # Vérifier l'existence de la base
    if not sync.db_path.exists():
        print(f"❌ Base de données non trouvée : {sync.db_path}")
        return
    
    # Exécuter la commande demandée
    if command == "export":
        sync.sqlite_to_json()
    elif command == "import":
        sync.json_to_sqlite()
    elif command == "sync":
        sync.sync_bidirectional()
    elif command == "check":
        sync.check_data_integrity()
    elif command == "status":
        status = sync.get_sync_status()
        print(f"📋 Dernière synchronisation :")
        print(f"   ✅ Succès : {status['success']}")
        print(f"   🕐 Date : {status['timestamp']}")
        print(f"   💬 Message : {status['message']}")
    else:
        print(f"❌ Commande inconnue : {command}")


if __name__ == "__main__":
    main()

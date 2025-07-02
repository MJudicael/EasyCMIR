# EasyCMIR - Interface Web Autonome

Interface web moderne pour la gestion du matériel EasyCMIR, fonctionnant **sans serveur** et avec synchronisation bidirectionnelle SQLite ↔ JSON.

## 🎯 **Caractéristiques**

- ✅ **Aucune installation** sur les PC clients (HTML/CSS/JavaScript pur)
- ✅ **Interface moderne** et responsive 
- ✅ **Synchronisation automatique** avec la base SQLite existante
- ✅ **Recherche multi-filtres** avancée (séparateur `;`)
- ✅ **Tri dynamique** sur toutes les colonnes
- ✅ **Export CSV** des données filtrées
- ✅ **Édition en ligne** avec modal
- ✅ **Temps réel** avec rafraîchissement automatique

## 📦 **Gestion de Matériel**

- Ajout, modification et suppression d'équipements
- Recherche avancée avec filtres multiples
- Tri par colonnes
- Export CSV et PDF

## 📜 **Système d'Historique**

Le système d'historique permet de traquer toutes les modifications apportées aux données.

### **Fonctionnalités d'historique**

- **Suivi des actions** : Enregistrement automatique de tous les ajouts, modifications et suppressions
- **Détails des modifications** : Pour chaque modification, affichage des valeurs avant/après
- **Horodatage** : Date et heure précises de chaque action
- **Export d'historique** : Possibilité d'exporter l'historique en CSV
- **Gestion de l'historique** : Option pour vider l'historique si nécessaire

### **Types d'actions trackées**

- ➕ **Ajout** : Nouvel équipement ajouté au système
- ✏️ **Modification** : Modification d'un équipement existant
- 🗑️ **Suppression** : Suppression d'un équipement

### **Accès à l'historique**

1. Cliquez sur le bouton "📜 Historique" dans la barre de contrôles
2. Consultez la liste chronologique des modifications (plus récentes en premier)
3. Exportez l'historique en CSV si nécessaire

### **Stockage**

En mode autonome, l'historique est stocké dans le fichier `historique.json` qui est automatiquement téléchargé lors des modifications.

### **Limitations**

- Limite de 1000 entrées maximum pour éviter un fichier trop volumineux
- En mode autonome, l'historique est stocké localement

## 📁 **Structure**

```
web_standalone/
├── 📄 index.html           # Interface web principale
├── 📄 app.js              # Logique JavaScript
├── 📄 materiel.json       # Données pour l'interface web
├── 🐍 sync_materiel.py    # Script de synchronisation
├── 📊 sync_status.json    # Statut de synchronisation
├── 🚀 LANCER_INTERFACE.bat  # Lancement rapide
└── 🔄 SYNCHRONISER.bat     # Outils de synchronisation
```

## 🚀 **Installation et Utilisation**

### **Méthode 1 : Lancement rapide**

1. **Double-cliquez** sur `LANCER_INTERFACE.bat`
2. **Ouvrez** votre navigateur sur `http://localhost:8000`
3. **Utilisez** l'interface normalement

### **Méthode 2 : Déploiement réseau**

1. **Copiez** le dossier `web_standalone` sur votre serveur de fichiers
2. **Modifiez** le chemin vers `materiel.db` dans `sync_materiel.py`
3. **Lancez** la synchronisation : `python sync_materiel.py sync`
4. **Partagez** l'accès au fichier `index.html` sur le réseau

## 🔄 **Synchronisation**

### **Principe**
- **SQLite → JSON** : Export des données pour l'interface web
- **JSON → SQLite** : Import des modifications faites via l'interface
- **Priorité SQLite** : En cas de conflit, SQLite prévaut

### **Commandes de synchronisation**

```bash
# Export SQLite vers JSON (pour l'interface)
python sync_materiel.py export

# Import JSON vers SQLite (sauvegarder modifications web)
python sync_materiel.py import

# Synchronisation complète bidirectionnelle
python sync_materiel.py sync

# Vérifier l'intégrité des données
python sync_materiel.py check

# Afficher le statut
python sync_materiel.py status
```

### **Interface graphique**
Utilisez `SYNCHRONISER.bat` pour un menu interactif.

## 💻 **Utilisation de l'interface**

### **Recherche avancée**
- **Simple** : `detecteur`
- **Multiple** : `detecteur;en service` (séparez par `;`)
- **Complexe** : `acme;dosimetre;cis nord`

### **Actions disponibles**
- ➕ **Ajouter** : Nouveau matériel
- ✏️ **Modifier** : Édition en place
- 🗑️ **Supprimer** : Avec confirmation
- 📄 **Export CSV** : Données filtrées
- 🔄 **Synchroniser** : Mise à jour temps réel

### **Tri des données**
Cliquez sur les **en-têtes de colonnes** pour trier :
- **Premier clic** : Tri croissant ▲
- **Deuxième clic** : Tri décroissant ▼

## ⚙️ **Configuration réseau**

### **Pour serveur de fichiers**

1. **Copiez** le dossier sur `\\serveur\partage\EasyCMIR_Web\`
2. **Modifiez** dans `sync_materiel.py` :
   ```python
   db_path = Path("\\\\serveur\\partage\\EasyCMIR\\data\\materiel.db")
   ```
3. **Créez** une tâche planifiée pour la synchronisation automatique
4. **Partagez** l'accès : `\\serveur\partage\EasyCMIR_Web\index.html`

### **Pour accès web**

Si vous avez un serveur web (IIS, Apache) :
1. **Copiez** les fichiers dans le répertoire web
2. **Configurez** la synchronisation périodique
3. **Accédez** via `http://serveur/easycmir/`

## 🔧 **Personnalisation**

### **Modifier les types de matériel**
Dans `app.js`, section `editType` :
```javascript
<option value="Nouveau Type">Nouveau Type</option>
```

### **Ajouter des statuts**
Dans `app.js`, section `editStatut` :
```javascript
<option value="Nouveau Statut">Nouveau Statut</option>
```

### **Changer l'apparence**
Modifiez les styles CSS dans `index.html`, section `<style>`.

## 🛠️ **Maintenance**

### **Sauvegarde automatique**
Les modifications sont automatiquement sauvegardées dans le fichier JSON. Utilisez la synchronisation pour persister en base SQLite.

### **Récupération d'erreurs**
En cas de problème :
1. **Vérifiez** le statut : `python sync_materiel.py status`
2. **Re-synchronisez** : `python sync_materiel.py sync`
3. **Vérifiez** l'intégrité : `python sync_materiel.py check`

### **Nettoyage**
- **Supprimer** `materiel.json` pour repartir de la base SQLite
- **Supprimer** `sync_status.json` pour réinitialiser le statut

## 🚨 **Limitations**

- **JavaScript requis** : L'interface nécessite JavaScript activé
- **Fichiers locaux** : Certaines fonctionnalités peuvent être limitées selon le navigateur
- **Synchronisation manuelle** : Nécessite de lancer le script Python périodiquement
- **Accès concurrent** : Attention aux modifications simultanées (priorité SQLite)

## 📞 **Support**

### **Problèmes courants**

1. **"Python n'est pas installé"**
   - Utilisez Python portable ou installez Python

2. **"Base de données non trouvée"**
   - Vérifiez le chemin dans `sync_materiel.py`
   - Assurez-vous que `materiel.db` existe

3. **"Interface ne se charge pas"**
   - Vérifiez que `materiel.json` existe
   - Lancez `python sync_materiel.py export`

4. **"Modifications perdues"**
   - Lancez `python sync_materiel.py import`
   - Vérifiez le statut de synchronisation

### **Contact**
Pour toute question technique, consultez les logs de synchronisation ou vérifiez l'intégrité des données.

---

**EasyCMIR Web Interface v1.0** - Interface autonome sans dépendances serveur

// EasyCMIR - Interface Web Autonome
// Gestion du matériel avec synchronisation JSON/SQLite

class MaterielManager {
    constructor() {
        this.materiels = [];
        this.filteredMateriels = [];
        this.currentSort = { column: 'id', order: 'asc' };
        this.currentFilter = '';
        this.editingId = null;
        this.dataFile = 'materiel.json';
        this.pendingChanges = false;
        
        // === SYSTÈME D'HISTORIQUE ===
        this.historique = [];
        this.historiqueFile = 'historique.json';
        this.maxHistoriqueEntries = 1000; // Limite pour éviter un fichier trop volumineux
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadData();
            await this.loadHistorique(); // Charger l'historique
            this.renderTable();
            this.updateStats();
            this.showMessage('Interface chargée avec succès', 'success');
            this.updateSyncStatus('success', 'Données chargées');
        } catch (error) {
            console.error('Erreur d\'initialisation:', error);
            this.showMessage('Erreur lors du chargement des données', 'error');
            this.updateSyncStatus('error', 'Erreur de chargement');
        }
    }
    
    // === GESTION DES DONNÉES ===
    
    async loadData() {
        try {
            const response = await fetch(this.dataFile);
            if (response.ok) {
                const data = await response.json();
                this.materiels = data.materiels || [];
            } else {
                // Fichier non trouvé, commencer avec une base vide
                this.materiels = [];
                await this.saveData();
            }
            this.filteredMateriels = [...this.materiels];
        } catch (error) {
            console.error('Erreur lors du chargement:', error);
            this.materiels = [];
            this.filteredMateriels = [];
        }
    }
    
    async saveData() {
        try {
            const data = {
                materiels: this.materiels,
                lastUpdate: new Date().toISOString(),
                version: "1.0"
            };
            
            // Dans un environnement réel, ceci nécessiterait un backend
            // Pour cette démo, on simule la sauvegarde
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            // Marquer comme modifié pour la synchronisation
            this.pendingChanges = true;
            this.updateSyncStatus('pending', 'Modifications en attente');
            
            // Simuler une sauvegarde réussie
            setTimeout(() => {
                this.updateSyncStatus('success', 'Sauvegardé localement');
            }, 1000);
            
            console.log('Données sauvegardées (simulation):', data);
            return true;
        } catch (error) {
            console.error('Erreur lors de la sauvegarde:', error);
            this.updateSyncStatus('error', 'Erreur de sauvegarde');
            return false;
        }
    }
    
    // === GESTION DU CRUD ===
    
    addMateriel(materielData) {
        // Vérifier si l'ID existe déjà
        if (this.materiels.find(m => m.id === materielData.id)) {
            this.showMessage(`L'ID ${materielData.id} existe déjà`, 'error');
            return false;
        }
        
        const materiel = {
            id: materielData.id,
            type: materielData.type || '',
            usage: materielData.usage || '',
            modele: materielData.modele || '',
            marque: materielData.marque || '',
            numero_serie: materielData.numero_serie || '',
            quantite: parseInt(materielData.quantite) || 1,
            statut: materielData.statut || '',
            lieu: materielData.lieu || '',
            affectation: materielData.affectation || '',
            created: new Date().toISOString(),
            modified: new Date().toISOString()
        };
        
        this.materiels.push(materiel);
        this.saveData();
        this.refreshDisplay();
        this.showMessage(`Matériel ${materiel.id} ajouté avec succès`, 'success');
        
        // Ajouter à l'historique
        this.ajouterEntreeHistorique('ajouter', materiel.id, null, materiel);
        
        return true;
    }
    
    updateMateriel(id, materielData) {
        const index = this.materiels.findIndex(m => m.id === id);
        if (index === -1) {
            this.showMessage(`Matériel ${id} non trouvé`, 'error');
            return false;
        }
        
        // Si l'ID a changé, vérifier qu'il n'existe pas déjà
        if (materielData.id !== id && this.materiels.find(m => m.id === materielData.id)) {
            this.showMessage(`L'ID ${materielData.id} existe déjà`, 'error');
            return false;
        }
        
        // Préparer l'ancienne valeur pour l'historique
        const ancienMateriel = { ...this.materiels[index] };
        
        this.materiels[index] = {
            ...this.materiels[index],
            id: materielData.id,
            type: materielData.type || '',
            usage: materielData.usage || '',
            modele: materielData.modele || '',
            marque: materielData.marque || '',
            numero_serie: materielData.numero_serie || '',
            quantite: parseInt(materielData.quantite) || 1,
            statut: materielData.statut || '',
            lieu: materielData.lieu || '',
            affectation: materielData.affectation || '',
            modified: new Date().toISOString()
        };
        
        this.saveData();
        this.refreshDisplay();
        this.showMessage(`Matériel ${materielData.id} modifié avec succès`, 'success');
        
        // Ajouter à l'historique
        this.ajouterEntreeHistorique('modifier', materielData.id, ancienMateriel, this.materiels[index]);
        
        return true;
    }
    
    deleteMateriel(id) {
        const index = this.materiels.findIndex(m => m.id === id);
        if (index === -1) {
            this.showMessage(`Matériel ${id} non trouvé`, 'error');
            return false;
        }
        
        if (confirm(`Êtes-vous sûr de vouloir supprimer le matériel ${id} ?`)) {
            // Préparer l'ancienne valeur pour l'historique
            const ancienMateriel = { ...this.materiels[index] };
            
            this.materiels.splice(index, 1);
            this.saveData();
            this.refreshDisplay();
            this.showMessage(`Matériel ${id} supprimé avec succès`, 'success');
            
            // Ajouter à l'historique
            this.ajouterEntreeHistorique('supprimer', id, ancienMateriel, null);
            
            return true;
        }
        return false;
    }
    
    // === FILTRAGE ET TRI ===
    
    filterTable() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
        this.currentFilter = searchTerm;
        
        if (!searchTerm) {
            this.filteredMateriels = [...this.materiels];
        } else {
            // Support des filtres multiples séparés par ';'
            const filters = searchTerm.split(';').map(f => f.trim()).filter(f => f.length > 0);
            
            this.filteredMateriels = this.materiels.filter(materiel => {
                return filters.every(filter => {
                    const searchString = Object.values(materiel).join(' ').toLowerCase();
                    return searchString.includes(filter);
                });
            });
        }
        
        this.applySorting();
        this.renderTable();
        this.updateStats();
    }
    
    sortTable(column) {
        if (this.currentSort.column === column) {
            this.currentSort.order = this.currentSort.order === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort = { column, order: 'asc' };
        }
        
        this.applySorting();
        this.renderTable();
        this.updateSortIndicators();
    }
    
    applySorting() {
        this.filteredMateriels.sort((a, b) => {
            let aVal = a[this.currentSort.column] || '';
            let bVal = b[this.currentSort.column] || '';
            
            // Tri numérique pour la quantité
            if (this.currentSort.column === 'quantite') {
                aVal = parseInt(aVal) || 0;
                bVal = parseInt(bVal) || 0;
                return this.currentSort.order === 'asc' ? aVal - bVal : bVal - aVal;
            }
            
            // Tri alphabétique
            aVal = aVal.toString().toLowerCase();
            bVal = bVal.toString().toLowerCase();
            
            if (this.currentSort.order === 'asc') {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        });
    }
    
    // === AFFICHAGE ===
    
    renderTable() {
        const tbody = document.getElementById('materielsTableBody');
        const emptyState = document.getElementById('emptyState');
        
        if (this.filteredMateriels.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
            document.querySelector('.table-container').style.display = 'none';
            return;
        }
        
        emptyState.style.display = 'none';
        document.querySelector('.table-container').style.display = 'block';
        
        tbody.innerHTML = this.filteredMateriels.map(materiel => `
            <tr>
                <td><strong>${this.escapeHtml(materiel.id)}</strong></td>
                <td>${this.escapeHtml(materiel.type) || '-'}</td>
                <td>${this.escapeHtml(materiel.usage) || '-'}</td>
                <td>${this.escapeHtml(materiel.modele) || '-'}</td>
                <td>${this.escapeHtml(materiel.marque) || '-'}</td>
                <td>${this.escapeHtml(materiel.numero_serie) || '-'}</td>
                <td>${materiel.quantite || '-'}</td>
                <td>${this.renderStatut(materiel.statut)}</td>
                <td>${this.escapeHtml(materiel.lieu) || '-'}</td>
                <td>${this.escapeHtml(materiel.affectation) || '-'}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-primary" title="Modifier" 
                                onclick="app.editMateriel('${materiel.id}')">
                            ✏️
                        </button>
                        <button class="btn btn-danger" title="Supprimer" 
                                onclick="app.deleteMateriel('${materiel.id}')">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    renderStatut(statut) {
        if (!statut) {
            return '<span style="color: #6c757d;">Non défini</span>';
        }
        
        let bgColor, textColor;
        if (statut.includes('En service')) {
            bgColor = '#d4edda';
            textColor = '#155724';
        } else if (statut.includes('Hors parc')) {
            bgColor = '#f8d7da';
            textColor = '#721c24';
        } else {
            bgColor = '#fff3cd';
            textColor = '#856404';
        }
        
        return `<span style="padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background: ${bgColor}; color: ${textColor};">
                    ${this.escapeHtml(statut)}
                </span>`;
    }
    
    updateStats() {
        const total = this.filteredMateriels.length;
        const active = this.filteredMateriels.filter(m => m.statut === 'En service').length;
        const undefined = this.filteredMateriels.filter(m => !m.statut || m.statut === '').length;
        
        document.getElementById('totalCount').textContent = total;
        document.getElementById('activeCount').textContent = active;
        document.getElementById('undefinedCount').textContent = undefined;
    }
    
    updateSortIndicators() {
        // Réinitialiser tous les indicateurs
        document.querySelectorAll('th.sortable').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Ajouter l'indicateur approprié
        const currentTh = document.querySelector(`th.sortable[onclick="sortTable('${this.currentSort.column}')"]`);
        if (currentTh) {
            currentTh.classList.add(this.currentSort.order === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    }
    
    refreshDisplay() {
        this.filterTable(); // Refiltre et re-rend
    }
    
    // === MODAL ET FORMULAIRES ===
    
    openAddModal() {
        this.editingId = null;
        document.getElementById('modalTitle').textContent = 'Ajouter du matériel';
        document.getElementById('editForm').reset();
        document.getElementById('editModal').style.display = 'block';
    }
    
    editMateriel(id) {
        const materiel = this.materiels.find(m => m.id === id);
        if (!materiel) return;
        
        this.editingId = id;
        document.getElementById('modalTitle').textContent = 'Modifier le matériel';
        
        // Remplir le formulaire
        document.getElementById('editId').value = materiel.id;
        document.getElementById('editType').value = materiel.type || '';
        document.getElementById('editUsage').value = materiel.usage || '';
        document.getElementById('editModele').value = materiel.modele || '';
        document.getElementById('editMarque').value = materiel.marque || '';
        document.getElementById('editNumeroSerie').value = materiel.numero_serie || '';
        document.getElementById('editQuantite').value = materiel.quantite || 1;
        document.getElementById('editStatut').value = materiel.statut || '';
        document.getElementById('editLieu').value = materiel.lieu || '';
        document.getElementById('editAffectation').value = materiel.affectation || '';
        
        document.getElementById('editModal').style.display = 'block';
    }
    
    closeModal() {
        document.getElementById('editModal').style.display = 'none';
        this.editingId = null;
    }
    
    // === SYNCHRONISATION ===
    
    syncData() {
        this.updateSyncStatus('pending', 'Synchronisation en cours...');
        
        // Simuler la synchronisation avec le script Python
        setTimeout(() => {
            this.pendingChanges = false;
            this.updateSyncStatus('success', 'Synchronisation terminée');
            this.showMessage('Données synchronisées avec la base SQLite', 'info');
        }, 2000);
    }
    
    updateSyncStatus(type, message) {
        const status = document.getElementById('syncStatus');
        status.className = `sync-status sync-${type}`;
        status.textContent = `🔄 ${message}`;
        status.style.display = 'block';
        
        // Masquer automatiquement après 5 secondes
        setTimeout(() => {
            if (status.classList.contains(`sync-${type}`)) {
                status.style.display = 'none';
            }
        }, 5000);
    }
    
    // === EXPORT ===
    
    exportData() {
        try {
            const headers = ['ID-RT', 'Type', 'Usage', 'Modèle', 'Marque', 'N° série', 'Quantité', 'Statut', 'CIS affectation', 'Vecteur'];
            const csvContent = [
                headers.join(','),
                ...this.filteredMateriels.map(m => [
                    this.escapeCsv(m.id),
                    this.escapeCsv(m.type),
                    this.escapeCsv(m.usage),
                    this.escapeCsv(m.modele),
                    this.escapeCsv(m.marque),
                    this.escapeCsv(m.numero_serie),
                    m.quantite || '',
                    this.escapeCsv(m.statut),
                    this.escapeCsv(m.lieu),
                    this.escapeCsv(m.affectation)
                ].join(','))
            ].join('\n');
            
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `materiel_${new Date().toISOString().split('T')[0]}.csv`;
            link.click();
            
            this.showMessage('Export CSV téléchargé avec succès', 'success');
        } catch (error) {
            console.error('Erreur lors de l\'export:', error);
            this.showMessage('Erreur lors de l\'export', 'error');
        }
    }
    
    // === HISTORIQUE ===
    
    async loadHistorique() {
        try {
            const response = await fetch(this.historiqueFile);
            if (response.ok) {
                const data = await response.json();
                this.historique = data.historique || [];
            } else {
                this.historique = [];
            }
        } catch (error) {
            console.error('Erreur lors du chargement de l\'historique:', error);
            this.historique = [];
        }
    }
    
    async saveHistorique() {
        try {
            // Limiter la taille de l'historique
            if (this.historique.length > this.maxHistoriqueEntries) {
                this.historique = this.historique.slice(-this.maxHistoriqueEntries);
            }
            
            const data = {
                historique: this.historique,
                derniere_mise_a_jour: new Date().toISOString()
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = this.historiqueFile;
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erreur lors de la sauvegarde de l\'historique:', error);
        }
    }
    
    ajouterEntreeHistorique(action, materielId, ancien = null, nouveau = null) {
        const entree = {
            id: Date.now() + Math.random(), // ID unique
            timestamp: new Date().toISOString(),
            date_lisible: new Date().toLocaleString('fr-FR'),
            action: action, // 'ajouter', 'modifier', 'supprimer'
            materiel_id: materielId,
            utilisateur: 'Web Interface', // Peut être étendu pour gérer plusieurs utilisateurs
            details: {
                ancien: ancien,
                nouveau: nouveau
            }
        };
        
        this.historique.push(entree);
        
        // Sauvegarder automatiquement l'historique
        // Note: En mode autonome, cela téléchargera le fichier
        // Dans une vraie application web, cela serait envoyé au serveur
    }
    
    // === GESTION DE L'HISTORIQUE - INTERFACE ===
    
    openHistoriqueModal() {
        const modal = document.getElementById('historiqueModal');
        this.renderHistoriqueTable();
        modal.style.display = 'block';
    }
    
    closeHistoriqueModal() {
        document.getElementById('historiqueModal').style.display = 'none';
    }
    
    renderHistoriqueTable() {
        const tbody = document.getElementById('historiqueTableBody');
        tbody.innerHTML = '';
        
        if (this.historique.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6c757d;">Aucune entrée dans l\'historique</td></tr>';
            return;
        }
        
        // Trier par date décroissante (plus récent en premier)
        const historiqueTrié = [...this.historique].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        historiqueTrié.forEach(entree => {
            const row = document.createElement('tr');
            
            // Formater l'action avec un emoji
            let actionFormatee = entree.action;
            let actionClass = '';
            switch(entree.action) {
                case 'ajouter':
                    actionFormatee = '➕ Ajout';
                    actionClass = 'action-add';
                    break;
                case 'modifier':
                    actionFormatee = '✏️ Modification';
                    actionClass = 'action-edit';
                    break;
                case 'supprimer':
                    actionFormatee = '🗑️ Suppression';
                    actionClass = 'action-delete';
                    break;
            }
            
            // Créer les détails de modification
            let details = '';
            if (entree.action === 'modifier' && entree.details.ancien && entree.details.nouveau) {
                const ancien = entree.details.ancien;
                const nouveau = entree.details.nouveau;
                const modifications = [];
                
                // Comparer les champs
                ['type', 'usage', 'modele', 'marque', 'numero_serie', 'quantite', 'statut', 'lieu', 'affectation'].forEach(champ => {
                    if (ancien[champ] !== nouveau[champ]) {
                        modifications.push(`${champ}: "${ancien[champ] || 'vide'}" → "${nouveau[champ] || 'vide'}"`);
                    }
                });
                
                details = modifications.length > 0 ? modifications.join('<br>') : 'Aucune modification détectée';
            } else if (entree.action === 'ajouter' && entree.details.nouveau) {
                const nouveau = entree.details.nouveau;
                details = `Nouveau matériel: ${nouveau.type || 'N/A'} - ${nouveau.modele || 'N/A'} (${nouveau.marque || 'N/A'})`;
            } else if (entree.action === 'supprimer' && entree.details.ancien) {
                const ancien = entree.details.ancien;
                details = `Matériel supprimé: ${ancien.type || 'N/A'} - ${ancien.modele || 'N/A'} (${ancien.marque || 'N/A'})`;
            }
            
            row.innerHTML = `
                <td><small>${entree.date_lisible}</small></td>
                <td><span class="action-badge ${actionClass}">${actionFormatee}</span></td>
                <td><strong>${this.escapeHtml(entree.materiel_id)}</strong></td>
                <td><small>${this.escapeHtml(entree.utilisateur)}</small></td>
                <td><small>${details}</small></td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    exportHistorique() {
        if (this.historique.length === 0) {
            this.showMessage('Aucune donnée d\'historique à exporter', 'error');
            return;
        }
        
        // Préparer les données CSV
        const headers = ['Date', 'Action', 'ID Matériel', 'Utilisateur', 'Détails'];
        let csvContent = headers.join(',') + '\n';
        
        const historiqueTrié = [...this.historique].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        historiqueTrié.forEach(entree => {
            let details = '';
            if (entree.action === 'modifier' && entree.details.ancien && entree.details.nouveau) {
                const ancien = entree.details.ancien;
                const nouveau = entree.details.nouveau;
                const modifications = [];
                
                ['type', 'usage', 'modele', 'marque', 'numero_serie', 'quantite', 'statut', 'lieu', 'affectation'].forEach(champ => {
                    if (ancien[champ] !== nouveau[champ]) {
                        modifications.push(`${champ}: "${ancien[champ] || 'vide'}" → "${nouveau[champ] || 'vide'}"`);
                    }
                });
                
                details = modifications.join('; ');
            } else if (entree.action === 'ajouter' && entree.details.nouveau) {
                const nouveau = entree.details.nouveau;
                details = `Nouveau: ${nouveau.type || 'N/A'} - ${nouveau.modele || 'N/A'}`;
            } else if (entree.action === 'supprimer' && entree.details.ancien) {
                const ancien = entree.details.ancien;
                details = `Supprimé: ${ancien.type || 'N/A'} - ${ancien.modele || 'N/A'}`;
            }
            
            const row = [
                this.escapeCsv(entree.date_lisible),
                this.escapeCsv(entree.action),
                this.escapeCsv(entree.materiel_id),
                this.escapeCsv(entree.utilisateur),
                this.escapeCsv(details)
            ];
            
            csvContent += row.join(',') + '\n';
        });
        
        // Télécharger le fichier
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.download = `historique_easycmir_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(url);
        
        this.showMessage('Historique exporté avec succès', 'success');
    }
    
    // === UTILITAIRES ===
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    escapeCsv(text) {
        if (!text) return '';
        const escaped = text.toString().replace(/"/g, '""');
        return `"${escaped}"`;
    }
    
    showMessage(message, type = 'info') {
        const flashContainer = document.getElementById('flashMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `flash-message flash-${type}`;
        messageDiv.textContent = message;
        
        flashContainer.appendChild(messageDiv);
        
        // Supprimer le message après 5 secondes
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }
}

// === ÉVÉNEMENTS GLOBAUX ===

// Initialisation
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new MaterielManager();
});

// Fonctions globales pour les événements HTML
function sortTable(column) {
    app.sortTable(column);
}

function filterTable() {
    app.filterTable();
}

function openAddModal() {
    app.openAddModal();
}

function closeModal() {
    app.closeModal();
}

function syncData() {
    app.syncData();
}

function exportData() {
    app.exportData();
}

function exportPDF() {
    if (typeof exportPDF !== 'undefined' && window.exportPDF) {
        window.exportPDF();
    } else {
        // Fallback si la fonction n'est pas encore chargée
        setTimeout(() => {
            if (window.exportPDF) {
                window.exportPDF();
            } else {
                app.showMessage('Fonction d\'export PDF non disponible', 'error');
            }
        }, 100);
    }
}

function openHistoriqueModal() {
    app.openHistoriqueModal();
}

function closeHistoriqueModal() {
    app.closeHistoriqueModal();
}

function exportHistorique() {
    app.exportHistorique();
}

// Auto-resize table on window resize
window.addEventListener('resize', function() {
    // Réajuster le tableau si nécessaire
    const table = document.getElementById('materielsTable');
    if (table) {
        // Force recalcul des largeurs
        table.style.width = '100%';
    }
});

// Gestion du formulaire
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('editForm').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const formData = {
            id: document.getElementById('editId').value.trim(),
            type: document.getElementById('editType').value,
            usage: document.getElementById('editUsage').value.trim(),
            modele: document.getElementById('editModele').value.trim(),
            marque: document.getElementById('editMarque').value.trim(),
            numero_serie: document.getElementById('editNumeroSerie').value.trim(),
            quantite: document.getElementById('editQuantite').value,
            statut: document.getElementById('editStatut').value,
            lieu: document.getElementById('editLieu').value.trim(),
            affectation: document.getElementById('editAffectation').value.trim()
        };
        
        if (!formData.id) {
            app.showMessage('L\'ID-RT est obligatoire', 'error');
            return;
        }
        
        let success;
        if (app.editingId) {
            success = app.updateMateriel(app.editingId, formData);
        } else {
            success = app.addMateriel(formData);
        }
        
        if (success) {
            app.closeModal();
        }
    });
    
    // Fermer modal en cliquant à l'extérieur
    document.getElementById('editModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('editModal')) {
            app.closeModal();
        }
    });
    
    // Recherche en temps réel
    document.getElementById('searchInput').addEventListener('input', () => {
        clearTimeout(window.searchTimeout);
        window.searchTimeout = setTimeout(() => {
            app.filterTable();
        }, 300);
    });
});

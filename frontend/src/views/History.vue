<template>
  <div class="history-view">
    <h1 class="page-title">Historique des analyses</h1>
    
    <Card class="history-card">
      <template #content>
        <div v-if="loading" class="loading-container">
          <ProgressBar mode="indeterminate" />
          <p class="loading-text">Chargement de l'historique...</p>
        </div>
        
        <div v-else-if="error" class="error-container">
          <i class="pi pi-exclamation-triangle error-icon"></i>
          <h3>Une erreur est survenue</h3>
          <p>{{ error }}</p>
          <Button label="Réessayer" icon="pi pi-refresh" @click="loadHistory" />
        </div>
        
        <div v-else-if="analyses.length === 0" class="empty-container">
          <i class="pi pi-info-circle info-icon"></i>
          <p>Aucune analyse n'a été effectuée</p>
          <Button label="Commencer une analyse" icon="pi pi-file" @click="$router.push('/analysis')" />
        </div>
        
        <div v-else class="history-list">
          <DataTable :value="analyses" :paginator="true" :rows="10" 
                    paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
                    :rowsPerPageOptions="[5,10,25]"
                    responsiveLayout="scroll">
            <Column field="id" header="ID" :sortable="true" style="width: 10%"></Column>
            <Column field="document_id" header="Document" :sortable="true" style="width: 25%">
              <template #body="slotProps">
                {{ getDocumentName(slotProps.data) }}
              </template>
            </Column>
            <Column field="document_type" header="Type" :sortable="true" style="width: 15%">
              <template #body="slotProps">
                <Tag :value="getDocumentTypeLabel(slotProps.data.document_type)" severity="info" />
              </template>
            </Column>
            <Column field="created_at" header="Date" :sortable="true" style="width: 15%">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column field="status" header="Statut" :sortable="true" style="width: 15%">
              <template #body="slotProps">
                <Tag :value="getStatusLabel(slotProps.data.status)" :severity="getStatusSeverity(slotProps.data.status)" />
              </template>
            </Column>
            <Column header="Actions" style="width: 20%">
              <template #body="slotProps">
                <Button icon="pi pi-eye" class="p-button-rounded p-button-info p-button-sm" 
                        @click="viewAnalysis(slotProps.data.id)" 
                        :disabled="slotProps.data.status !== 'completed'" />
                <Button icon="pi pi-refresh" class="p-button-rounded p-button-warning p-button-sm ml-2" 
                        @click="retryAnalysis(slotProps.data.id)" 
                        :disabled="slotProps.data.status !== 'failed'" />
                <Button icon="pi pi-trash" class="p-button-rounded p-button-danger p-button-sm ml-2" 
                        @click="confirmDelete(slotProps.data.id)" />
              </template>
            </Column>
          </DataTable>
        </div>
      </template>
    </Card>
    
    <Dialog v-model:visible="deleteDialog" header="Confirmation" :style="{width: '450px'}" :modal="true">
      <div class="confirmation-content">
        <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
        <span>Êtes-vous sûr de vouloir supprimer cette analyse ?</span>
      </div>
      <template #footer>
        <Button label="Non" icon="pi pi-times" class="p-button-text" @click="deleteDialog = false" />
        <Button label="Oui" icon="pi pi-check" class="p-button-danger" @click="deleteAnalysis" />
      </template>
    </Dialog>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'HistoryView',
  data() {
    return {
      analyses: [],
      loading: true,
      error: null,
      deleteDialog: false,
      analysisToDelete: null
    }
  },
  created() {
    this.loadHistory();
  },
  methods: {
    loadHistory() {
      this.loading = true;
      this.error = null;
      
      ApiService.getAnalysisHistory()
        .then(response => {
          this.analyses = response;
          this.loading = false;
        })
        .catch(error => {
          this.error = "Erreur lors du chargement de l'historique: " + error.message;
          this.loading = false;
        });
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    },
    
    getDocumentTypeLabel(type) {
      const types = {
        'employment': 'Contrat de travail',
        'service': 'Contrat de prestation',
        'partnership': 'Contrat de partenariat',
        'nda': 'Confidentialité',
        'other': 'Autre'
      };
      return types[type] || type;
    },

    getDocumentName(analysis) {
  // Essayer d'obtenir le nom du document de différentes façons possibles
  if (analysis.document_name) {
    return analysis.document_name;
  } else if (analysis.metadata && analysis.metadata.filename) {
    return analysis.metadata.filename;
  } else if (analysis.results && analysis.results.metadata && analysis.results.metadata.filename) {
    return analysis.results.metadata.filename;
  } else {
    return `Document ${analysis.document_id.substring(0, 8)}...`;
  }
},
    
    getStatusLabel(status) {
      const statuses = {
        'pending': 'En attente',
        'in_progress': 'En cours',
        'completed': 'Terminé',
        'failed': 'Échoué'
      };
      return statuses[status] || status;
    },
    
    getStatusSeverity(status) {
      const severities = {
        'pending': 'info',
        'in_progress': 'warning',
        'completed': 'success',
        'failed': 'danger'
      };
      return severities[status] || 'info';
    },
    
    viewAnalysis(id) {
      this.$router.push({ path: `/analysis/${id}` });
    },
    
    retryAnalysis(id) {
      this.loading = true;
      
      ApiService.retryAnalysis(id)
        .then(() => {
          this.$toast.add({
            severity: 'success',
            summary: 'Analyse relancée',
            detail: 'L\'analyse a été relancée avec succès',
            life: 3000
          });
          this.loadHistory();
        })
        .catch(error => {
          this.error = "Erreur lors de la relance de l'analyse: " + error.message;
          this.loading = false;
        });
    },
    
    confirmDelete(id) {
      this.analysisToDelete = id;
      this.deleteDialog = true;
    },
    
    deleteAnalysis() {
      if (!this.analysisToDelete) return;
      
      this.loading = true;
      this.deleteDialog = false;
      
      ApiService.deleteAnalysis(this.analysisToDelete)
        .then(() => {
          this.$toast.add({
            severity: 'success',
            summary: 'Analyse supprimée',
            detail: 'L\'analyse a été supprimée avec succès',
            life: 3000
          });
          this.loadHistory();
        })
        .catch(error => {
          this.error = "Erreur lors de la suppression de l'analyse: " + error.message;
          this.loading = false;
        });
    }
  }
}
</script>

<style scoped>
.history-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  color: #1e3a8a;
  margin-bottom: 2rem;
  font-size: 2rem;
}

.history-card {
  margin-bottom: 2rem;
}

.loading-container, .error-container, .empty-container {
  padding: 2rem;
  text-align: center;
}

.loading-text {
  margin-top: 1rem;
  color: #6c757d;
}

.error-icon, .info-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-container {
  color: #ef4444;
}

.confirmation-content {
  display: flex;
  align-items: center;
}
</style>

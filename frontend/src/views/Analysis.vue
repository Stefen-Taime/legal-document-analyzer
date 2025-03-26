<template>
  <div class="analysis-view">
    <h1 class="page-title">Analyse de document juridique</h1>
    
    <div v-if="!analysisStarted">
      <DocumentUpload @analysis-started="startAnalysis" />
    </div>
    
    <div v-else>
      <AnalysisResults 
        :results="analysisResults" 
        :loading="loading" 
        :error="error"
        @new-analysis="resetAnalysis"
        @retry="retryAnalysis"
      />
      
      <!-- Section de débogage (à supprimer en production) -->
      <div v-if="debug" class="debug-section">
        <h3>Informations de débogage</h3>
        <p><strong>Statut de l'analyse:</strong> {{ debugInfo.status }}</p>
        <p><strong>ID de l'analyse:</strong> {{ analysisId }}</p>
        <p><strong>Dernière mise à jour:</strong> {{ debugInfo.lastUpdate }}</p>
        <pre>{{ JSON.stringify(debugInfo.lastResponse, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import DocumentUpload from '@/components/DocumentUpload.vue';
import AnalysisResults from '@/components/AnalysisResults.vue';
import ApiService from '@/services/ApiService';

export default {
  name: 'AnalysisView',
  components: {
    DocumentUpload,
    AnalysisResults
  },
  data() {
    return {
      analysisStarted: false,
      analysisId: null,
      analysisResults: null,
      loading: false,
      error: null,
      pollingInterval: null,
      debug: true, // Activer le débogage (désactiver en production)
      debugInfo: {
        status: 'idle',
        lastUpdate: null,
        lastResponse: null,
        pollCount: 0
      }
    }
  },
  methods: {
    startAnalysis(data) {
      console.log('Démarrage de l\'analyse avec données:', data);
      this.loading = true;
      this.analysisStarted = true;
      this.error = null;
      
      // Mise à jour du statut de débogage
      this.debugInfo.status = 'starting';
      this.debugInfo.lastUpdate = new Date().toLocaleTimeString();
      
      if (data.id) {
        // Si l'API a renvoyé directement un ID d'analyse
        this.analysisId = data.id;
        console.log('ID d\'analyse reçu directement:', this.analysisId);
        this.startPolling();
      } else {
        // Sinon, on doit faire la requête de démarrage
        ApiService.startAnalysis(data.document_id || data.documentId, data.document_type || data.documentType)
          .then(response => {
            console.log('Réponse du démarrage d\'analyse:', response);
            // Mise à jour du débogage
            this.debugInfo.lastResponse = response;
            this.debugInfo.lastUpdate = new Date().toLocaleTimeString();
            
            // Récupérer l'ID d'analyse (adapter selon la structure de votre API)
            this.analysisId = response.id || response.analysis_id;
            
            if (!this.analysisId) {
              throw new Error('ID d\'analyse non trouvé dans la réponse');
            }
            
            console.log('ID d\'analyse obtenu:', this.analysisId);
            this.debugInfo.status = 'polling';
            this.startPolling();
          })
          .catch(error => {
            console.error('Erreur lors du démarrage:', error);
            this.error = "Erreur lors du démarrage de l'analyse: " + error.message;
            this.loading = false;
            this.debugInfo.status = 'error';
          });
      }
    },
    
    startPolling() {
      console.log('Démarrage du polling pour l\'ID:', this.analysisId);
      this.debugInfo.pollCount = 0;
      
      this.pollingInterval = setInterval(() => {
        this.checkAnalysisStatus();
      }, 3000); // Vérifier toutes les 3 secondes
    },
    
    checkAnalysisStatus() {
      this.debugInfo.pollCount++;
      console.log(`Vérification du statut #${this.debugInfo.pollCount} pour l'ID: ${this.analysisId}`);
      
      ApiService.getAnalysisStatus(this.analysisId)
        .then(response => {
          console.log('Réponse du statut:', response);
          
          // Mise à jour du débogage
          this.debugInfo.lastResponse = response;
          this.debugInfo.lastUpdate = new Date().toLocaleTimeString();
          
          if (response.status === 'completed') {
            console.log('Analyse terminée avec succès');
            this.loading = false;
            this.analysisResults = response.results;
            this.debugInfo.status = 'completed';
            this.stopPolling();
          } else if (response.status === 'failed') {
            console.log('Analyse échouée');
            this.loading = false;
            this.error = "L'analyse a échoué: " + (response.error || 'Raison inconnue');
            this.debugInfo.status = 'failed';
            this.stopPolling();
          } else {
            console.log('Analyse toujours en cours:', response.status);
            this.debugInfo.status = response.status;
            // Si progress est disponible, on peut l'afficher
            if (response.progress) {
              console.log('Progression:', response.progress);
            }
          }
        })
        .catch(error => {
          console.error('Erreur lors de la vérification du statut:', error);
          this.loading = false;
          this.error = "Erreur lors de la vérification du statut: " + error.message;
          this.debugInfo.status = 'error';
          this.stopPolling();
        });
    },
    
    stopPolling() {
      console.log('Arrêt du polling');
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
    },
    
    resetAnalysis() {
      console.log('Réinitialisation de l\'analyse');
      this.analysisStarted = false;
      this.analysisId = null;
      this.analysisResults = null;
      this.loading = false;
      this.error = null;
      this.debugInfo.status = 'idle';
      this.stopPolling();
    },
    
    retryAnalysis() {
      console.log('Tentative de relance de l\'analyse:', this.analysisId);
      if (this.analysisId) {
        this.loading = true;
        this.error = null;
        this.debugInfo.status = 'retrying';
        
        // Option 1: Simplement reprendre le polling
        this.startPolling();
        
        // Option 2: Appeler l'API pour relancer explicitement l'analyse
        /*
        ApiService.retryAnalysis(this.analysisId)
          .then(response => {
            console.log('Relance réussie:', response);
            this.startPolling();
          })
          .catch(error => {
            console.error('Erreur lors de la relance:', error);
            this.error = "Erreur lors de la relance de l'analyse: " + error.message;
            this.loading = false;
          });
        */
      }
    }
  },
  beforeUnmount() {
    this.stopPolling();
  }
}
</script>

<style scoped>
.analysis-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  color: #1e3a8a;
  margin-bottom: 2rem;
  font-size: 2rem;
}

/* Styles pour le débogage */
.debug-section {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px dashed #ccc;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.debug-section h3 {
  color: #6c757d;
  margin-top: 0;
}

.debug-section pre {
  background-color: #f1f1f1;
  padding: 0.5rem;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
<template>
  <div class="document-upload">
    <Card class="upload-card">
      <template #title>
        Télécharger un document juridique
      </template>
      <template #content>
        <FileUpload
          name="document"
          :url="uploadUrl"
          @upload="onUpload"
          @select="onSelect"
          @error="onError"
          :multiple="false"
          accept=".pdf,.docx,.doc,.txt"
          :maxFileSize="10000000"
          chooseLabel="Sélectionner"
          uploadLabel="Télécharger"
          cancelLabel="Annuler"
        >
          <template #empty>
            <div class="upload-placeholder">
              <i class="pi pi-file-pdf upload-icon"></i>
              <p>Glissez et déposez votre document juridique ici</p>
              <p class="upload-hint">Formats acceptés: PDF, DOCX, DOC, TXT (max 10MB)</p>
            </div>
          </template>
        </FileUpload>
        
        <div class="document-type-selector">
          <h3>Type de document</h3>
          <Dropdown
            v-model="selectedDocumentType"
            :options="documentTypes"
            optionLabel="name"
            placeholder="Sélectionnez le type de document"
            class="w-full"
          />
        </div>
        
        <div class="upload-actions">
          <Button
            label="Analyser le document"
            icon="pi pi-search"
            class="p-button-primary"
            :disabled="!canAnalyze"
            @click="startAnalysis"
          />
        </div>
        
        <!-- Section de débogage - à supprimer en production -->
        <div class="debug-info" style="margin-top: 1rem; font-size: 0.8rem; color: #6c757d;">
          <p>État du téléchargement: {{ uploadedDocument ? 'Document téléchargé' : 'Aucun document' }}</p>
          <p>Nom du fichier: {{ selectedFile ? selectedFile.name : 'Aucun fichier' }}</p>
          <p>Type sélectionné: {{ selectedDocumentType ? selectedDocumentType.name : 'Non sélectionné' }}</p>
          <p>Bouton d'analyse: {{ canAnalyze ? 'Activé' : 'Désactivé' }}</p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script>
export default {
  name: 'DocumentUpload',
  data() {
    return {
      uploadUrl: '/api/documents/upload',
      selectedDocumentType: null,
      uploadedDocument: null,
      selectedFile: null,
      documentTypes: [
        { name: 'Contrat de travail', code: 'employment' },
        { name: 'Contrat de prestation', code: 'service' },
        { name: 'Contrat de partenariat', code: 'partnership' },
        { name: 'Contrat de confidentialité', code: 'nda' },
        { name: 'Autre contrat', code: 'other' }
      ],
      // Configuration d'API
      apiBaseUrl: '/api'
    }
  },
  computed: {
    canAnalyze() {
      // Activer le bouton si un fichier est sélectionné OU uploadedDocument existe, ET un type est sélectionné
      return (this.selectedFile || this.uploadedDocument) && this.selectedDocumentType;
    }
  },
  methods: {
    onSelect(event) {
      // Lorsqu'un fichier est sélectionné mais pas encore téléchargé
      if (event.files && event.files.length > 0) {
        this.selectedFile = event.files[0];
      }
    },
    onUpload(event) {
      try {
        const response = JSON.parse(event.xhr.response);
        console.log('Réponse de téléchargement:', response); // Pour débogage
        
        if (response && response.document) {
          this.uploadedDocument = response.document;
          this.$toast.add({
            severity: 'success',
            summary: 'Document téléchargé',
            detail: 'Le document a été téléchargé avec succès',
            life: 3000
          });
        } else {
          // Si la réponse n'a pas le format attendu, on utilise quand même le fichier sélectionné
          this.uploadedDocument = { 
            id: this.generateTempId(),
            name: this.selectedFile ? this.selectedFile.name : 'document.pdf'
          };
          console.warn('Format de réponse inattendu, utilisation des données du fichier local:', response);
          this.$toast.add({
            severity: 'info',
            summary: 'Document prêt',
            detail: 'Le document est prêt pour analyse',
            life: 3000
          });
        }
      } catch (error) {
        console.error('Erreur lors du traitement de la réponse:', error);
        // En cas d'erreur, on utilise quand même le fichier sélectionné
        if (this.selectedFile) {
          this.uploadedDocument = { 
            id: this.generateTempId(),
            name: this.selectedFile.name
          };
          this.$toast.add({
            severity: 'info',
            summary: 'Document prêt',
            detail: 'Le document est prêt pour analyse malgré l\'erreur de serveur',
            life: 3000
          });
        } else {
          this.$toast.add({
            severity: 'error',
            summary: 'Erreur',
            detail: 'Erreur lors du traitement de la réponse du serveur',
            life: 3000
          });
        }
      }
    },
    onError(error) {
      console.error('Erreur de téléchargement:', error);
      // Même en cas d'erreur, on active le bouton d'analyse si un fichier a été sélectionné
      if (this.selectedFile) {
        this.uploadedDocument = { 
          id: this.generateTempId(),
          name: this.selectedFile.name
        };
        this.$toast.add({
          severity: 'warn',
          summary: 'Téléchargement incomplet',
          detail: 'Le document pourra être analysé en mode local',
          life: 3000
        });
      } else {
        this.$toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: 'Une erreur est survenue lors du téléchargement',
          life: 3000
        });
      }
    },
    generateTempId() {
      // Crée un ID temporaire si l'API ne retourne pas d'ID
      return 'temp_' + Math.random().toString(36).substring(2, 15);
    },
    startAnalysis() {
  if (!this.canAnalyze) return;
  
  // Créer un objet FormData pour envoyer les données au format attendu par le backend
  const formData = new FormData();
  
  // Ajouter l'ID du document
  formData.append('document_id', this.uploadedDocument ? this.uploadedDocument.id : 'local_file');
  
  // Ajouter le type de document
  formData.append('document_type', this.selectedDocumentType.code);
  
  // Si c'est un document local et que nous avons le fichier, l'ajouter à la requête
  if ((this.uploadedDocument?.id === 'local_file' || !this.uploadedDocument) && this.selectedFile) {
    formData.append('file', this.selectedFile);
    
    console.log('Démarrage de l\'analyse avec fichier local:', {
      document_id: 'local_file',
      document_type: this.selectedDocumentType.code,
      file: this.selectedFile.name
    });
  } else {
    console.log('Démarrage de l\'analyse avec FormData:', {
      document_id: this.uploadedDocument ? this.uploadedDocument.id : 'local_file',
      document_type: this.selectedDocumentType.code
    });
  }
  
  // Appeler l'API directement depuis le composant
  fetch(`${this.apiBaseUrl}/analysis/document`, {
    method: 'POST',
    body: formData
  })
  .then(response => {
    if (!response.ok) {
      return response.json().then(data => {
        // Afficher le détail de l'erreur du serveur
        throw new Error(`Erreur HTTP ${response.status}: ${data.detail || 'Erreur inconnue'}`);
      });
    }
    return response.json();
  })
  .then(data => {
    console.log('Analyse démarrée avec succès:', data);
    this.$toast.add({
      severity: 'success',
      summary: 'Analyse démarrée',
      detail: 'L\'analyse du document a été démarrée avec succès',
      life: 3000
    });
    
    // Émettre l'événement pour informer le composant parent
    this.$emit('analysis-started', data);
  })
  .catch(error => {
    console.error('Erreur lors du démarrage de l\'analyse:', error);
    this.$toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: error.message || 'Une erreur est survenue lors du démarrage de l\'analyse',
      life: 3000
    });
  });
}
  },
  watch: {
    // Observateurs pour le débogage
    selectedDocumentType(newVal) {
      console.log('Type de document sélectionné:', newVal);
    },
    uploadedDocument(newVal) {
      console.log('Document téléchargé mis à jour:', newVal);
    },
    selectedFile(newVal) {
      console.log('Fichier sélectionné:', newVal ? newVal.name : 'aucun');
    }
  }
}
</script>

<style scoped>
.upload-card {
  margin-bottom: 2rem;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  border: 2px dashed #ced4da;
  border-radius: 6px;
  background-color: #f8f9fa;
  text-align: center;
}

.upload-icon {
  font-size: 3rem;
  color: #64748b;
  margin-bottom: 1rem;
}

.upload-hint {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.5rem;
}

.document-type-selector {
  margin-top: 2rem;
}

.document-type-selector h3 {
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
  color: #1e3a8a;
}

.upload-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
}

/* Section de débogage - à supprimer en production */
.debug-info {
  border-top: 1px dashed #ced4da;
  padding-top: 1rem;
  margin-top: 2rem;
}
</style>
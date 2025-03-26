<template>
  <div class="analysis-results">
    <Card class="results-card">
      <template #title>
        Résultats de l'analyse
      </template>
      <template #content>
        <div v-if="loading" class="loading-container">
          <ProgressBar mode="indeterminate" />
          <p class="loading-text">Analyse en cours, veuillez patienter...</p>
        </div>
        
        <div v-else-if="error" class="error-container">
          <i class="pi pi-exclamation-triangle error-icon"></i>
          <h3>Une erreur est survenue</h3>
          <p>{{ error }}</p>
          <Button label="Réessayer" icon="pi pi-refresh" @click="$emit('retry')" />
        </div>
        
        <div v-else-if="results" class="results-container">
          <TabView>
            <TabPanel header="Clauses critiques">
              <div class="clauses-section">
                <div v-for="(clause, index) in results.clauses" :key="index" class="clause-item">
                  <div class="clause-header">
                    <h3>{{ clause.title }}</h3>
                    <div class="clause-tags">
                      <Tag :severity="getRiskSeverity(clause.risk_level)" :value="getRiskLabel(clause.risk_level)" />
                      <Tag severity="info" :value="clause.type" />
                    </div>
                  </div>
                  <p class="clause-content">{{ clause.content }}</p>
                  <div class="clause-analysis">
                    <h4>Analyse</h4>
                    <p>{{ clause.analysis }}</p>
                  </div>
                  <Divider />
                </div>
              </div>
            </TabPanel>
            
            <TabPanel header="Recommandations">
              <div class="recommendations-section">
                <div v-for="(recommendation, index) in results.recommendations" :key="index" class="recommendation-item">
                  <div class="recommendation-header">
                    <h3>{{ recommendation.title }}</h3>
                    <Tag :severity="getPrioritySeverity(recommendation.priority)" :value="getPriorityLabel(recommendation.priority)" />
                  </div>
                  <p>{{ recommendation.description }}</p>
                  <div v-if="recommendation.suggested_text" class="suggested-text">
                    <h4>Proposition de formulation</h4>
                    <p>{{ recommendation.suggested_text }}</p>
                  </div>
                  <div v-if="recommendation.related_clauses && recommendation.related_clauses.length > 0" class="related-clauses">
                    <h4>Clauses concernées</h4>
                    <div class="related-clauses-list">
                      <Chip v-for="(clause, i) in recommendation.related_clauses" :key="i" :label="clause" class="mr-2 mb-2" />
                    </div>
                  </div>
                  <Divider />
                </div>
              </div>
            </TabPanel>
            
            <TabPanel header="Risques juridiques">
              <div class="risks-section">
                <div v-for="(risk, index) in results.risks" :key="index" class="risk-item">
                  <div class="risk-header">
                    <h3>{{ risk.title }}</h3>
                    <Tag :severity="getRiskSeverity(risk.level)" :value="getRiskLabel(risk.level)" />
                  </div>
                  <p>{{ risk.description }}</p>
                  <div class="risk-impact">
                    <h4>Impact potentiel</h4>
                    <p>{{ risk.impact }}</p>
                  </div>
                  <div v-if="risk.mitigation" class="risk-mitigation">
                    <h4>Pistes de mitigation</h4>
                    <p>{{ risk.mitigation }}</p>
                  </div>
                  <Divider />
                </div>
              </div>
            </TabPanel>
            
            <TabPanel header="Précédents juridiques">
              <div class="precedents-section">
                <div v-for="(precedent, index) in results.precedents" :key="index" class="precedent-item">
                  <div class="precedent-header">
                    <h3>{{ precedent.title }}</h3>
                    <Tag severity="info" :value="precedent.type" />
                  </div>
                  <p>{{ precedent.description }}</p>
                  <div class="precedent-relevance">
                    <h4>Pertinence</h4>
                    <p>{{ precedent.relevance }}</p>
                  </div>
                  <div v-if="precedent.source" class="precedent-source">
                    <h4>Source</h4>
                    <p>{{ precedent.source }}</p>
                  </div>
                  <Divider />
                </div>
              </div>
            </TabPanel>
          </TabView>
          
          <div class="results-actions">
            <Button label="Exporter en PDF" icon="pi pi-file-pdf" class="p-button-secondary" @click="exportPDF" />
            <Button label="Exporter en JSON" icon="pi pi-file-export" class="p-button-secondary" @click="exportJSON" />
            <Button label="Nouvelle analyse" icon="pi pi-plus" class="p-button-primary" @click="$emit('new-analysis')" />
          </div>
        </div>
        
        <div v-else class="no-results">
          <i class="pi pi-info-circle info-icon"></i>
          <p>Aucun résultat d'analyse disponible</p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script>
export default {
  name: 'AnalysisResults',
  props: {
    results: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  methods: {
    getRiskSeverity(level) {
      const map = {
        1: 'success',
        2: 'info',
        3: 'warning',
        4: 'danger',
        5: 'danger'
      };
      return map[level] || 'info';
    },
    getRiskLabel(level) {
      const map = {
        1: 'Très faible',
        2: 'Faible',
        3: 'Moyen',
        4: 'Élevé',
        5: 'Très élevé'
      };
      return map[level] || 'Inconnu';
    },
    getPrioritySeverity(priority) {
      const map = {
        1: 'info',
        2: 'warning',
        3: 'danger'
      };
      return map[priority] || 'info';
    },
    getPriorityLabel(priority) {
      const map = {
        1: 'Basse',
        2: 'Moyenne',
        3: 'Haute'
      };
      return map[priority] || 'Inconnue';
    },
    exportPDF() {
      // Logique d'export PDF à implémenter
      this.$toast.add({
        severity: 'info',
        summary: 'Export PDF',
        detail: 'Fonctionnalité à implémenter',
        life: 3000
      });
    },
    exportJSON() {
      // Logique d'export JSON à implémenter
      const dataStr = JSON.stringify(this.results, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = 'analysis-results.json';
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    }
  }
}
</script>

<style scoped>
.results-card {
  margin-bottom: 2rem;
}

.loading-container {
  padding: 2rem;
  text-align: center;
}

.loading-text {
  margin-top: 1rem;
  color: #6c757d;
}

.error-container {
  padding: 2rem;
  text-align: center;
  color: #ef4444;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.no-results {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.info-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.results-container {
  padding: 1rem 0;
}

.clause-item, .recommendation-item, .risk-item, .precedent-item {
  margin-bottom: 1.5rem;
}

.clause-header, .recommendation-header, .risk-header, .precedent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.clause-header h3, .recommendation-header h3, .risk-header h3, .precedent-header h3 {
  margin: 0;
  color: #1e3a8a;
  font-size: 1.2rem;
}

.clause-tags {
  display: flex;
  gap: 0.5rem;
}

.clause-content {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  font-style: italic;
  margin: 0.5rem 0;
}

.clause-analysis h4, .risk-impact h4, .precedent-relevance h4 {
  color: #64748b;
  margin: 0.5rem 0;
  font-size: 1rem;
}

.suggested-text {
  background-color: #f0f9ff;
  padding: 1rem;
  border-radius: 4px;
  margin: 0.5rem 0;
}

.suggested-text h4 {
  color: #0284c7;
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.related-clauses h4 {
  color: #64748b;
  margin: 0.5rem 0;
  font-size: 1rem;
}

.related-clauses-list {
  display: flex;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.risk-mitigation {
  background-color: #f0f9ef;
  padding: 1rem;
  border-radius: 4px;
  margin: 0.5rem 0;
}

.risk-mitigation h4 {
  color: #16a34a;
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.precedent-source {
  background-color: #f0f7f4;
  padding: 1rem;
  border-radius: 4px;
  margin: 0.5rem 0;
}

.precedent-source h4 {
  color: #047857;
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.results-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}
</style>
<template>
  <div class="clauses-list">
    <div v-if="clauses && clauses.length > 0">
      <div v-for="(clause, index) in clauses" :key="index" class="clause-item">
        <div class="clause-header">
          <h3>{{ clause.title }}</h3>
          <div class="clause-tags">
            <Tag :severity="getRiskSeverity(clause.risk_level)" :value="getRiskLabel(clause.risk_level)" />
            <Tag severity="info" :value="getClauseTypeLabel(clause.type)" />
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
    <div v-else class="no-clauses">
      <i class="pi pi-info-circle" style="font-size: 2rem; color: #64748b; margin-bottom: 1rem;"></i>
      <p>Aucune clause explicite n'a été extraite de ce document.</p>
      <p class="sub-message">Consultez les onglets "Risques juridiques" et "Recommandations" pour obtenir des suggestions d'amélioration.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ClausesList',
  props: {
    clauses: {
      type: Array,
      default: () => []
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
    getClauseTypeLabel(type) {
      const types = {
        'obligation': 'Obligation',
        'restriction': 'Restriction',
        'right': 'Droit',
        'termination': 'Résiliation',
        'confidentiality': 'Confidentialité',
        'intellectual_property': 'Propriété intellectuelle',
        'liability': 'Responsabilité',
        'payment': 'Paiement',
        'duration': 'Durée',
        'other': 'Autre'
      };
      return types[type] || type;
    }
  }
}
</script>

<style scoped>
.clause-item {
  margin-bottom: 1.5rem;
}

.clause-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.clause-header h3 {
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

.clause-analysis h4 {
  color: #64748b;
  margin: 0.5rem 0;
  font-size: 1rem;
}

.no-clauses {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
}
</style>

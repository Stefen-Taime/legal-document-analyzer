<template>
  <div class="recommendations">
    <div v-if="recommendations && recommendations.length > 0">
      <div v-for="(recommendation, index) in recommendations" :key="index" class="recommendation-item">
        <div class="recommendation-header">
          <h3>{{ recommendation.title }}</h3>
          <Tag :severity="getPrioritySeverity(recommendation.priority)" :value="getPriorityLabel(recommendation.priority)" />
        </div>
        <p>{{ recommendation.description }}</p>
        <div v-if="recommendation.suggested_text" class="suggested-text">
          <h4>Texte suggéré</h4>
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
    <div v-else class="no-recommendations">
      <p>Aucune recommandation n'a été générée</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Recommendations',
  props: {
    recommendations: {
      type: Array,
      default: () => []
    }
  },
  methods: {
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
    }
  }
}
</script>

<style scoped>
.recommendation-item {
  margin-bottom: 1.5rem;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.recommendation-header h3 {
  margin: 0;
  color: #1e3a8a;
  font-size: 1.2rem;
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

.no-recommendations {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
}
</style>

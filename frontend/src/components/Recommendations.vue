<template>
  <div class="precedents">
    <div v-if="precedents && precedents.length > 0">
      <div v-for="(precedent, index) in precedents" :key="index" class="precedent-item">
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
    <div v-else class="no-precedents">
      <p>Aucun précédent juridique n'a été trouvé</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Precedents',
  props: {
    precedents: {
      type: Array,
      default: () => []
    }
  }
}
</script>

<style scoped>
.precedent-item {
  margin-bottom: 1.5rem;
}

.precedent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.precedent-header h3 {
  margin: 0;
  color: #1e3a8a;
  font-size: 1.2rem;
}

.precedent-relevance, .precedent-source {
  background-color: #f0f9ff;
  padding: 1rem;
  border-radius: 4px;
  margin: 0.5rem 0;
}

.precedent-relevance h4, .precedent-source h4 {
  color: #0284c7;
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.precedent-source {
  background-color: #f0f7f4;
}

.precedent-source h4 {
  color: #047857;
}

.no-precedents {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
}
</style>
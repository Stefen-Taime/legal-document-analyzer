<template>
  <div class="home-view">
    <div class="hero-section">
      <Card>
        <template #title>
          <h1 class="hero-title">Analyseur de Documents Juridiques</h1>
        </template>
        <template #content>
          <div class="hero-content">
            <p class="hero-description">
              Notre solution d'intelligence artificielle analyse vos contrats juridiques pour identifier les clauses critiques, 
              évaluer les risques et proposer des recommandations personnalisées.
            </p>
            <div class="hero-actions">
              <Button 
                label="Commencer une analyse" 
                icon="pi pi-file" 
                class="p-button-primary p-button-lg"
                @click="$router.push('/analysis')"
              />
              <Button 
                label="Voir l'historique" 
                icon="pi pi-history" 
                class="p-button-secondary p-button-lg"
                @click="$router.push('/history')"
              />
            </div>
          </div>
        </template>
      </Card>
    </div>

    <div class="features-section">
      <h2 class="section-title">Fonctionnalités principales</h2>
      <div class="features-grid">
        <Card class="feature-card">
          <template #header>
            <div class="feature-icon">
              <i class="pi pi-search"></i>
            </div>
          </template>
          <template #title>
            Extraction de clauses
          </template>
          <template #content>
            <p>Identification et extraction automatique des clauses critiques de vos contrats juridiques.</p>
          </template>
        </Card>

        <Card class="feature-card">
          <template #header>
            <div class="feature-icon">
              <i class="pi pi-database"></i>
            </div>
          </template>
          <template #title>
            Recherche de précédents
          </template>
          <template #content>
            <p>Interrogation d'une base de données vectorielle pour trouver des jurisprudences similaires.</p>
          </template>
        </Card>

        <Card class="feature-card">
          <template #header>
            <div class="feature-icon">
              <i class="pi pi-chart-bar"></i>
            </div>
          </template>
          <template #title>
            Évaluation des risques
          </template>
          <template #content>
            <p>Identification et quantification des risques juridiques potentiels dans vos documents.</p>
          </template>
        </Card>

        <Card class="feature-card">
          <template #header>
            <div class="feature-icon">
              <i class="pi pi-check-circle"></i>
            </div>
          </template>
          <template #title>
            Recommandations
          </template>
          <template #content>
            <p>Suggestions de modifications ou d'actions basées sur l'analyse approfondie de vos contrats.</p>
          </template>
        </Card>
      </div>
    </div>

    <div class="workflow-section">
      <h2 class="section-title">Comment ça marche</h2>
      <div class="workflow-steps">
        <div class="workflow-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h3>Téléchargement</h3>
            <p>Téléchargez votre document juridique (PDF, DOCX, TXT) et sélectionnez son type.</p>
          </div>
        </div>
        
        <div class="workflow-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h3>Analyse</h3>
            <p>Notre IA analyse le document, extrait les clauses critiques et recherche des précédents juridiques.</p>
          </div>
        </div>
        
        <div class="workflow-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h3>Résultats</h3>
            <p>Consultez les clauses extraites, les risques identifiés et les recommandations proposées.</p>
          </div>
        </div>
        
        <div class="workflow-step">
          <div class="step-number">4</div>
          <div class="step-content">
            <h3>Action</h3>
            <p>Exportez les résultats en PDF ou JSON et prenez des décisions éclairées.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  margin-bottom: 3rem;
}

.hero-title {
  color: #1e3a8a;
  margin: 0;
  font-size: 2rem;
}

.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.hero-description {
  font-size: 1.2rem;
  line-height: 1.6;
  margin-bottom: 2rem;
  max-width: 800px;
}

.hero-actions {
  display: flex;
  gap: 1rem;
}

.section-title {
  text-align: center;
  color: #1e3a8a;
  margin-bottom: 2rem;
  font-size: 1.8rem;
}

.features-section {
  margin-bottom: 3rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  height: 100%;
}

.feature-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80px;
  font-size: 2.5rem;
  color: #1e3a8a;
}

.workflow-section {
  margin-bottom: 3rem;
}

.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.workflow-step {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
}

.step-number {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 40px;
  height: 40px;
  background-color: #1e3a8a;
  color: white;
  border-radius: 50%;
  font-weight: bold;
  font-size: 1.2rem;
}

.step-content h3 {
  margin: 0 0 0.5rem 0;
  color: #1e3a8a;
}

.step-content p {
  margin: 0;
}

@media (max-width: 768px) {
  .hero-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .workflow-step {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>

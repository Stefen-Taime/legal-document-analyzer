<template>
  <div class="app-container">
    <Toast />
    <ConfirmDialog />
    
    <header class="app-header">
      <div class="logo">
        <h1>Analyseur de Documents Juridiques</h1>
      </div>
      <div class="nav-menu">
        <router-link to="/">Accueil</router-link>
        <router-link to="/analysis">Analyse</router-link>
        <router-link to="/history">Historique</router-link>
      </div>
    </header>
    
    <main class="app-content">
      <router-view />
    </main>
    
    <footer class="app-footer">
      <p>&copy; 2025 Legal Document Analyzer - PoC</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  components: {
  },
  data() {
    return {
    }
  },
  methods: {
  }
}
</script>

<style>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  font-family: 'Roboto', sans-serif;
}

.app-header {
  background-color: #1e3a8a;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo h1 {
  margin: 0;
  font-size: 1.5rem;
}

.nav-menu {
  display: flex;
  gap: 1.5rem;
}

.nav-menu a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 0;
  border-bottom: 2px solid transparent;
  transition: border-color 0.3s;
}

.nav-menu a:hover,
.nav-menu a.router-link-active {
  border-color: white;
}

.app-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background-color: #f8f9fa;
  padding: 1rem 2rem;
  text-align: center;
  color: #6c757d;
}

/* Styles globaux */
body {
  margin: 0;
  padding: 0;
  background-color: #f5f7fb;
}

.card-container {
  margin-bottom: 2rem;
}

.section-title {
  color: #1e3a8a;
  margin-bottom: 1.5rem;
}

.p-button.p-button-primary {
  background-color: #1e3a8a;
}

.p-button.p-button-secondary {
  background-color: #64748b;
}

.p-button.p-button-success {
  background-color: #10b981;
}

.p-button.p-button-danger {
  background-color: #ef4444;
}

.p-button.p-button-warning {
  background-color: #f59e0b;
}
</style>

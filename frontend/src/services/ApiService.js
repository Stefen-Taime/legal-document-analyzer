import axios from 'axios';

// Création d'une instance axios avec une configuration de base
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Service API pour communiquer avec le backend
const ApiService = {
  // Documents
  getDocuments() {
    return apiClient.get('/documents').then(response => response.data);
  },
  
  getDocument(documentId) {
    return apiClient.get(`/documents/${documentId}`).then(response => response.data);
  },
  
  uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(response => response.data);
  },
  
  updateDocumentType(documentId, documentType) {
    return apiClient.put(`/documents/${documentId}/type?document_type=${documentType}`)
      .then(response => response.data);
  },
  
  deleteDocument(documentId) {
    return apiClient.delete(`/documents/${documentId}`).then(response => response.data);
  },
  
  // Analyses
  startAnalysis(documentId, documentType, file = null) {
    const formData = new FormData();
    formData.append('document_id', documentId);
    formData.append('document_type', documentType);
    
    if (file) {
      formData.append('file', file);
    }
    
    return apiClient.post('/analysis/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then(response => response.data);
  },
  
  getAnalysisStatus(analysisId) {
    return apiClient.get(`/analysis/${analysisId}/status`).then(response => response.data);
  },
  
  getAnalysisResults(analysisId) {
    return apiClient.get(`/analysis/${analysisId}/results`).then(response => response.data);
  },
  
  getAnalysisHistory() {
    return apiClient.get('/analysis/history').then(response => response.data);
  },
  
  retryAnalysis(analysisId) {
    return apiClient.post(`/analysis/${analysisId}/retry`).then(response => response.data);
  },
  
  deleteAnalysis(analysisId) {
    return apiClient.delete(`/analysis/${analysisId}`).then(response => response.data);
  },
  
  // Précédents juridiques
  searchPrecedents(query) {
    return apiClient.get(`/precedents/search?query=${encodeURIComponent(query)}`)
      .then(response => response.data);
  },
  
  getPrecedentDetails(precedentId) {
    return apiClient.get(`/precedents/${precedentId}`).then(response => response.data);
  },
  
  // Santé de l'API
  healthCheck() {
    return apiClient.get('/health').then(response => response.data);
  }
};

export default ApiService;

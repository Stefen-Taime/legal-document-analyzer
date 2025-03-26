import { createStore } from 'vuex';
import ApiService from '@/services/ApiService';

export default createStore({
  state: {
    documents: [],
    analyses: [],
    currentDocument: null,
    currentAnalysis: null,
    loading: false,
    error: null
  },
  getters: {
    getDocuments: state => state.documents,
    getAnalyses: state => state.analyses,
    getCurrentDocument: state => state.currentDocument,
    getCurrentAnalysis: state => state.currentAnalysis,
    isLoading: state => state.loading,
    getError: state => state.error
  },
  mutations: {
    SET_DOCUMENTS(state, documents) {
      state.documents = documents;
    },
    SET_ANALYSES(state, analyses) {
      state.analyses = analyses;
    },
    SET_CURRENT_DOCUMENT(state, document) {
      state.currentDocument = document;
    },
    SET_CURRENT_ANALYSIS(state, analysis) {
      state.currentAnalysis = analysis;
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    }
  },
  actions: {
    // Actions pour les documents
    async fetchDocuments({ commit }) {
      commit('SET_LOADING', true);
      try {
        const documents = await ApiService.getDocuments();
        commit('SET_DOCUMENTS', documents);
      } catch (error) {
        commit('SET_ERROR', error.message);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchDocument({ commit }, documentId) {
      commit('SET_LOADING', true);
      try {
        const document = await ApiService.getDocument(documentId);
        commit('SET_CURRENT_DOCUMENT', document);
      } catch (error) {
        commit('SET_ERROR', error.message);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async uploadDocument({ commit }, file) {
      commit('SET_LOADING', true);
      try {
        const document = await ApiService.uploadDocument(file);
        commit('SET_CURRENT_DOCUMENT', document);
        return document;
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async deleteDocument({ commit, state }, documentId) {
      commit('SET_LOADING', true);
      try {
        await ApiService.deleteDocument(documentId);
        // Mettre à jour la liste des documents
        const updatedDocuments = state.documents.filter(doc => doc.id !== documentId);
        commit('SET_DOCUMENTS', updatedDocuments);
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    // Actions pour les analyses
    async fetchAnalyses({ commit }) {
      commit('SET_LOADING', true);
      try {
        const analyses = await ApiService.getAnalysisHistory();
        commit('SET_ANALYSES', analyses);
      } catch (error) {
        commit('SET_ERROR', error.message);
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchAnalysis({ commit }, analysisId) {
      commit('SET_LOADING', true);
      try {
        const analysis = await ApiService.getAnalysisResults(analysisId);
        commit('SET_CURRENT_ANALYSIS', analysis);
        return analysis;
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async startAnalysis({ commit }, { documentId, documentType }) {
      commit('SET_LOADING', true);
      try {
        const analysis = await ApiService.startAnalysis(documentId, documentType);
        commit('SET_CURRENT_ANALYSIS', analysis);
        return analysis;
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async checkAnalysisStatus({ commit }, analysisId) {
      try {
        const status = await ApiService.getAnalysisStatus(analysisId);
        if (status.status === 'completed') {
          commit('SET_CURRENT_ANALYSIS', status);
        }
        return status;
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      }
    },
    async retryAnalysis({ commit }, analysisId) {
      commit('SET_LOADING', true);
      try {
        const analysis = await ApiService.retryAnalysis(analysisId);
        return analysis;
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async deleteAnalysis({ commit, state }, analysisId) {
      commit('SET_LOADING', true);
      try {
        await ApiService.deleteAnalysis(analysisId);
        // Mettre à jour la liste des analyses
        const updatedAnalyses = state.analyses.filter(analysis => analysis.id !== analysisId);
        commit('SET_ANALYSES', updatedAnalyses);
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    // Actions pour les précédents juridiques
    async searchPrecedents({ commit }, query) {
      commit('SET_LOADING', true);
      try {
        const precedents = await ApiService.searchPrecedents(query);
        return precedents;
      } catch (error) {
        commit('SET_ERROR', error.message);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    // Actions générales
    clearError({ commit }) {
      commit('SET_ERROR', null);
    }
  }
});

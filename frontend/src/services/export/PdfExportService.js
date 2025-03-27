// src/services/export/PdfExportService.js
import html2pdf from 'html2pdf.js';

class PdfExportService {
  /**
   * Exporte les résultats d'analyse au format PDF
   * @param {Object} results - Les résultats d'analyse à exporter
   * @param {String} filename - Nom du fichier PDF (sans extension)
   */
  async exportAnalysisResults(results, filename = 'analyse-juridique') {
    // Créer un élément HTML temporaire pour le contenu du PDF
    const element = document.createElement('div');
    element.className = 'pdf-container';
    element.innerHTML = this.generatePdfContent(results);
    
    // Ajouter des styles pour le PDF
    const style = document.createElement('style');
    style.textContent = this.getPdfStyles();
    element.appendChild(style);
    
    // Ajouter à la page (invisible)

    document.body.appendChild(element);

    // Options pour html2pdf
    const options = {
      margin: 10,
      filename: `${filename}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    try {
      // Générer le PDF
      await html2pdf().from(element).set(options).save();
      console.log('PDF généré avec succès');
    } catch (error) {
      console.error('Erreur lors de la génération du PDF:', error);
      throw error;
    } finally {
      // Nettoyage: supprimer l'élément
      document.body.removeChild(element);
    }
  }

  /**
   * Génère le contenu HTML du PDF
   * @param {Object} results - Les résultats d'analyse
   * @returns {String} - Le contenu HTML formaté
   */
  generatePdfContent(results) {
    const date = new Date().toLocaleDateString('fr-FR');
    
    let html = `
      <div class="pdf-header">
        <h1>Analyse juridique de document</h1>
        <p class="pdf-date">Date: ${date}</p>
      </div>
    `;

    // Section Clauses
    if (results.clauses && results.clauses.length > 0) {
      html += `
        <div class="pdf-section">
          <h2>Clauses critiques</h2>
          ${results.clauses.map(clause => `
            <div class="pdf-item">
              <div class="pdf-item-header">
                <h3>${clause.title}</h3>
                <div class="pdf-tags">
                  <span class="pdf-tag pdf-tag-${this.getRiskClass(clause.risk_level)}">${this.getRiskLabel(clause.risk_level)}</span>
                  <span class="pdf-tag">${clause.type}</span>
                </div>
              </div>
              <div class="pdf-content">${clause.content}</div>
              <div class="pdf-analysis">
                <h4>Analyse</h4>
                <p>${clause.analysis}</p>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    // Section Recommandations
    if (results.recommendations && results.recommendations.length > 0) {
      html += `
        <div class="pdf-section">
          <h2>Recommandations</h2>
          ${results.recommendations.map(rec => `
            <div class="pdf-item">
              <div class="pdf-item-header">
                <h3>${rec.title}</h3>
                <span class="pdf-tag pdf-tag-${this.getPriorityClass(rec.priority)}">${this.getPriorityLabel(rec.priority)}</span>
              </div>
              <p>${rec.description}</p>
              ${rec.suggested_text ? `
                <div class="pdf-suggestion">
                  <h4>Proposition de formulation</h4>
                  <p>${rec.suggested_text}</p>
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `;
    }

    // Section Risques
    if (results.risks && results.risks.length > 0) {
      html += `
        <div class="pdf-section">
          <h2>Risques juridiques</h2>
          ${results.risks.map(risk => `
            <div class="pdf-item">
              <div class="pdf-item-header">
                <h3>${risk.title}</h3>
                <span class="pdf-tag pdf-tag-${this.getRiskClass(risk.level)}">${this.getRiskLabel(risk.level)}</span>
              </div>
              <p>${risk.description}</p>
              <div class="pdf-impact">
                <h4>Impact potentiel</h4>
                <p>${risk.impact}</p>
              </div>
              ${risk.mitigation ? `
                <div class="pdf-mitigation">
                  <h4>Pistes de mitigation</h4>
                  <p>${risk.mitigation}</p>
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `;
    }

    // Section Précédents juridiques
    if (results.precedents && results.precedents.length > 0) {
      html += `
        <div class="pdf-section">
          <h2>Précédents juridiques</h2>
          ${results.precedents.map(precedent => `
            <div class="pdf-item">
              <div class="pdf-item-header">
                <h3>${precedent.title}</h3>
                <span class="pdf-tag">${precedent.type}</span>
              </div>
              <p>${precedent.description}</p>
              <div class="pdf-relevance">
                <h4>Pertinence</h4>
                <p>${precedent.relevance}</p>
              </div>
              ${precedent.source ? `
                <div class="pdf-source">
                  <h4>Source</h4>
                  <p>${precedent.source}</p>
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `;
    }

    // Résumé si disponible
    if (results.summary) {
      html += `
        <div class="pdf-section">
          <h2>Résumé de l'analyse</h2>
          <div class="pdf-summary">
            ${results.summary.replace(/\n/g, '<br>')}
          </div>
        </div>
      `;
    }

    // Pied de page
    html += `
      <div class="pdf-footer">
        <p>Document généré automatiquement - Confidentiel</p>
      </div>
    `;

    return html;
  }

  /**
   * Génère les styles CSS pour le PDF
   */
  getPdfStyles() {
    return `
      .pdf-container {
        font-family: Arial, sans-serif;
        color: #333;
        line-height: 1.5;
      }
      .pdf-header {
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #1e3a8a;
      }
      .pdf-header h1 {
        color: #1e3a8a;
        margin: 0 0 10px 0;
      }
      .pdf-date {
        color: #666;
        font-style: italic;
      }
      .pdf-section {
        margin-bottom: 20px;
        page-break-inside: avoid;
      }
      .pdf-section h2 {
        color: #1e3a8a;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
      }
      .pdf-item {
        margin-bottom: 15px;
        page-break-inside: avoid;
      }
      .pdf-item-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
      }
      .pdf-item-header h3 {
        margin: 0;
        color: #2563eb;
      }
      .pdf-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-left: 5px;
        background-color: #e5e7eb;
      }
      .pdf-tag-success { background-color: #d1fae5; color: #047857; }
      .pdf-tag-info { background-color: #dbeafe; color: #1e40af; }
      .pdf-tag-warning { background-color: #fef3c7; color: #92400e; }
      .pdf-tag-danger { background-color: #fee2e2; color: #b91c1c; }
      .pdf-content {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
        font-style: italic;
      }
      .pdf-analysis, .pdf-impact, .pdf-relevance, .pdf-source {
        margin: 10px 0;
      }
      .pdf-analysis h4, .pdf-impact h4, .pdf-relevance h4, .pdf-source h4 {
        color: #64748b;
        margin: 5px 0;
        font-size: 14px;
      }
      .pdf-suggestion {
        background-color: #f0f9ff;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
      }
      .pdf-suggestion h4 {
        color: #0284c7;
        margin: 0 0 5px 0;
        font-size: 14px;
      }
      .pdf-mitigation {
        background-color: #f0f9ef;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
      }
      .pdf-mitigation h4 {
        color: #16a34a;
        margin: 0 0 5px 0;
        font-size: 14px;
      }
      .pdf-source {
        background-color: #f0f7f4;
        padding: 10px;
        border-radius: 4px;
      }
      .pdf-source h4 {
        color: #047857;
        margin: 0 0 5px 0;
        font-size: 14px;
      }
      .pdf-summary {
        background-color: #f9fafb;
        padding: 15px;
        border-radius: 4px;
        border-left: 4px solid #1e3a8a;
      }
      .pdf-footer {
        margin-top: 30px;
        text-align: center;
        font-size: 12px;
        color: #666;
      }
    `;
  }

  /**
   * Helper functions pour les labels et classes
   */
  getRiskLabel(level) {
    const map = {
      1: 'Très faible',
      2: 'Faible',
      3: 'Moyen',
      4: 'Élevé',
      5: 'Très élevé'
    };
    return map[level] || 'Inconnu';
  }

  getRiskClass(level) {
    const map = {
      1: 'success',
      2: 'info',
      3: 'warning',
      4: 'danger',
      5: 'danger'
    };
    return map[level] || 'info';
  }

  getPriorityLabel(priority) {
    const map = {
      1: 'Basse',
      2: 'Moyenne',
      3: 'Haute'
    };
    return map[priority] || 'Inconnue';
  }

  getPriorityClass(priority) {
    const map = {
      1: 'info',
      2: 'warning',
      3: 'danger'
    };
    return map[priority] || 'info';
  }
}

export default new PdfExportService();
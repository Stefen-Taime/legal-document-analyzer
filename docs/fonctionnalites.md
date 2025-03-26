# Guide d'utilisation des fonctionnalités

Ce document décrit les fonctionnalités principales du PoC d'analyse de documents juridiques et explique comment les utiliser.

## Table des matières

1. [Interface utilisateur](#interface-utilisateur)
2. [Téléchargement de documents](#téléchargement-de-documents)
3. [Analyse de documents](#analyse-de-documents)
4. [Consultation des résultats](#consultation-des-résultats)
5. [Recherche de précédents juridiques](#recherche-de-précédents-juridiques)
6. [Historique des analyses](#historique-des-analyses)
7. [Exportation des résultats](#exportation-des-résultats)

## Interface utilisateur

L'interface utilisateur du PoC est organisée en trois pages principales :

### Page d'accueil

La page d'accueil présente le service d'analyse juridique et permet de télécharger un document. Elle contient :

- Une présentation du service
- Un formulaire de téléchargement de document (drag & drop)
- Un sélecteur de type de document (contrat de travail, prestation, etc.)
- Un bouton pour lancer l'analyse

Pour accéder à la page d'accueil, naviguez vers `http://localhost/` après avoir démarré l'application.

### Page d'analyse

La page d'analyse affiche les résultats de l'analyse d'un document. Elle contient :

- Les clauses extraites avec leur niveau d'importance et de risque
- Les recommandations avec leurs priorités
- Une visualisation du document original avec mise en évidence des clauses importantes
- Des options pour exporter les résultats

Pour accéder à la page d'analyse, téléchargez un document depuis la page d'accueil et lancez l'analyse, ou sélectionnez une analyse existante dans l'historique.

### Page d'historique

La page d'historique liste les analyses précédentes. Elle contient :

- La liste des analyses effectuées
- Le statut de chaque analyse (terminée, en cours, erreur)
- Des options pour relancer une analyse ou comparer des résultats

Pour accéder à la page d'historique, cliquez sur "Historique" dans le menu de navigation.

## Téléchargement de documents

### Types de documents supportés

Le système prend en charge les formats de documents suivants :
- PDF (.pdf)
- Word (.docx, .doc)
- Texte brut (.txt)

### Procédure de téléchargement

1. Accédez à la page d'accueil (`http://localhost/`)
2. Faites glisser votre document dans la zone de téléchargement ou cliquez sur la zone pour sélectionner un fichier
3. Sélectionnez le type de document dans le menu déroulant :
   - Contrat de travail
   - Contrat de prestation
   - Contrat de partenariat
   - Autre type de contrat
4. Cliquez sur "Télécharger"

Le document sera téléchargé et stocké dans le système. Vous serez automatiquement redirigé vers la page d'analyse.

### Limites et restrictions

- Taille maximale de fichier : 10 Mo
- Nombre maximal de pages : 100
- Langues supportées : Français, Anglais

## Analyse de documents

### Lancement d'une analyse

Après avoir téléchargé un document, vous pouvez lancer son analyse :

1. Vérifiez que le document a été correctement téléchargé
2. Cliquez sur le bouton "Analyser"
3. Attendez que l'analyse soit terminée (cela peut prendre quelques minutes selon la taille du document)

### Types d'analyses disponibles

Le système propose plusieurs types d'analyses :

- **Analyse standard** : Extraction des clauses, identification des risques et recommandations
- **Analyse approfondie** : Analyse standard + recherche de précédents juridiques et analyse contextuelle
- **Analyse comparative** : Comparaison avec un document de référence

Pour sélectionner un type d'analyse, utilisez le menu déroulant avant de lancer l'analyse.

### Suivi de l'avancement

Pendant l'analyse, vous pouvez suivre son avancement :

- Une barre de progression indique l'état d'avancement global
- Des messages détaillent les étapes en cours (extraction de texte, analyse des clauses, etc.)
- Vous pouvez annuler l'analyse à tout moment en cliquant sur "Annuler"

## Consultation des résultats

### Clauses extraites

Les clauses extraites sont présentées sous forme de liste, avec pour chaque clause :

- Le titre de la clause
- Le texte extrait
- Le niveau d'importance (faible, moyen, élevé)
- Le niveau de risque (faible, moyen, élevé)
- Des indicateurs visuels (icônes et couleurs) pour faciliter la lecture

Pour voir le détail d'une clause, cliquez dessus pour l'ouvrir dans un panneau latéral.

### Recommandations

Les recommandations sont présentées sous forme de liste, avec pour chaque recommandation :

- Le titre de la recommandation
- La description détaillée
- La priorité (faible, moyenne, élevée)
- La clause concernée (avec lien vers la clause)
- Des actions suggérées

Pour appliquer une recommandation, cliquez sur le bouton "Appliquer" à côté de la recommandation.

### Visualisation du document

Le document original est affiché avec une mise en évidence des clauses importantes :

- Les clauses à risque élevé sont surlignées en rouge
- Les clauses à risque moyen sont surlignées en orange
- Les clauses à risque faible sont surlignées en jaune

Pour naviguer dans le document, utilisez la barre de défilement ou les boutons de navigation.

## Recherche de précédents juridiques

### Lancement d'une recherche

Vous pouvez rechercher des précédents juridiques similaires à une clause spécifique :

1. Dans la liste des clauses, cliquez sur le bouton "Rechercher des précédents" à côté de la clause
2. Le système recherchera des précédents juridiques similaires dans sa base de données
3. Les résultats seront affichés dans un panneau latéral

### Consultation des précédents

Les précédents juridiques sont présentés sous forme de liste, avec pour chaque précédent :

- Le titre du précédent
- La description
- La source (jurisprudence, doctrine, etc.)
- La pertinence par rapport à la clause (faible, moyenne, élevée)

Pour voir le détail d'un précédent, cliquez dessus pour l'ouvrir dans un panneau latéral.

## Historique des analyses

### Consultation de l'historique

Pour consulter l'historique des analyses :

1. Cliquez sur "Historique" dans le menu de navigation
2. La liste des analyses effectuées s'affiche, avec pour chaque analyse :
   - Le nom du document
   - La date de l'analyse
   - Le statut (terminée, en cours, erreur)
   - Le type d'analyse effectuée

### Actions sur les analyses

Depuis la page d'historique, vous pouvez effectuer plusieurs actions :

- **Voir les résultats** : Cliquez sur "Voir les résultats" pour consulter les résultats d'une analyse terminée
- **Relancer l'analyse** : Cliquez sur "Relancer" pour effectuer une nouvelle analyse du document
- **Supprimer l'analyse** : Cliquez sur "Supprimer" pour supprimer l'analyse de l'historique
- **Comparer des analyses** : Sélectionnez deux analyses et cliquez sur "Comparer" pour voir les différences

## Exportation des résultats

### Formats d'exportation disponibles

Les résultats d'analyse peuvent être exportés dans plusieurs formats :

- **PDF** : Rapport complet avec mise en page professionnelle
- **JSON** : Données structurées pour intégration avec d'autres systèmes
- **DOCX** : Document Word avec annotations et commentaires
- **HTML** : Page web interactive

### Procédure d'exportation

Pour exporter les résultats d'une analyse :

1. Depuis la page d'analyse, cliquez sur "Exporter"
2. Sélectionnez le format d'exportation souhaité
3. Choisissez les éléments à inclure dans l'export :
   - Clauses extraites
   - Recommandations
   - Précédents juridiques
   - Document original
4. Cliquez sur "Télécharger"

Le fichier d'export sera généré et téléchargé automatiquement.

### Personnalisation des exports

Pour les exports PDF et DOCX, vous pouvez personnaliser le rapport :

1. Cliquez sur "Personnaliser" avant de lancer l'export
2. Choisissez un modèle de rapport (standard, détaillé, résumé)
3. Ajoutez un logo et des informations d'en-tête
4. Sélectionnez les sections à inclure et leur ordre
5. Cliquez sur "Appliquer" pour générer l'export personnalisé

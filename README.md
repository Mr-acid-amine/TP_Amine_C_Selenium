# 🩺 Scraper Doctolib avec Selenium

Ce script Python utilise Selenium pour rechercher des professionnels de santé sur Doctolib, filtrer les résultats selon plusieurs critères (lieu, assurance, prix, type de consultation) et exporter les données dans un fichier CSV.

## 🔧 Fonctionnement

- Lance une recherche avec les critères fournis en ligne de commande.
- Récupère la **date de disponibilité directement sur la page principale**.
- Utilise la méthode `click()` pour ouvrir chaque fiche médecin, en extraire les informations (nom, prix, assurance, adresse, etc.), puis retourne à la liste.
- Filtre les résultats selon les options de l'utilisateur et les sauvegarde dans `medecins.csv`.

## ⚠️ Problèmes rencontrés

Des **problèmes de sélecteurs CSS** empêchent l’extraction complète de certaines informations, ce qui bloque leur transfert dans le fichier CSV.

## ▶️ Exemple d'exécution

```bash
python scraping_doctolib.py `
  --max_results 10 `
  --start_date 10/05/2025 `
  --end_date 15/05/2025 `
  --speciality ophtalmologue `
  --insurance "secteur 1" `
  --consultation "sur place" `
  --price_min 20 `
  --price_max 90 `
  --address_keyword "Bastille Paris"

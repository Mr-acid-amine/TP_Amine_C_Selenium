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
python doctolib.py --query "généraliste" --location "Paris" --start_date "2024-05-01" --end_date "2024-05-31" --max_results 10

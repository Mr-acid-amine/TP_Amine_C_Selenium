# Import des bibliothèques nécessaires
import argparse
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration et initialisation du navigateur Chrome avec Selenium
def setup_driver():
    chrome_options = Options() 
    chrome_options.add_argument("--no-sandbox")  # Nécessaire pour certains environnements Linux
    chrome_options.add_argument("--disable-dev-shm-usage")  # Évite les problèmes de mémoire partagée
    service = Service(executable_path="C:/Users/amino/OneDrive/Bureau/M1/TP_02/chromedriver.exe")
    return webdriver.Chrome(service=service, options=chrome_options)

# Lecture et définition des arguments de la ligne de commande
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_results", type=int, default=10)  # Nombre max de médecins à extraire
    parser.add_argument("--start_date", type=str, required=True)  # Date de début (non utilisée dans ce code)
    parser.add_argument("--end_date", type=str, required=True)  # Date de fin (non utilisée dans ce code)
    parser.add_argument("--query", type=str, required=True)  # Spécialité recherchée (ex: dermatologue)
    parser.add_argument("--assurance", choices=["secteur 1", "secteur 2", "non conventionné"], default=None)
    parser.add_argument("--consultation", choices=["visio", "sur place"], default=None)
    parser.add_argument("--price_min", type=float, default=0.0)  # Prix minimum
    parser.add_argument("--price_max", type=float, default=1000.0)  # Prix maximum
    parser.add_argument("--location", type=str, required=True)  # Ville ou localisation
    return parser.parse_args()

# Fonction pour effectuer la recherche sur Doctolib avec les critères utilisateur
def search_doctolib(driver, query, location):
    driver.get("https://www.doctolib.fr/")
    wait = WebDriverWait(driver, 20)  # Attente explicite

    try:
        # Champ de recherche de spécialité
        search_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input"))
        )
        search_input.clear()
        search_input.send_keys(query)
        search_input.send_keys(Keys.TAB)
        time.sleep(1)

        # Champ de recherche de localisation
        location_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-place-input"))
        )
        location_input.clear()
        location_input.send_keys(location)
        location_input.send_keys(Keys.RETURN)
        time.sleep(3)

        print("[DEBUG] En attente de l'élément des résultats...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dl-card-content")))

    except Exception as e:
        print(f"[ERROR] Erreur lors de la recherche : {e}")

# Fonction principale pour extraire les informations depuis les cartes de résultats
def extract_results(driver, max_results):
    results = []

    # Récupère les cartes de médecins affichées
    cards = driver.find_elements(By.CSS_SELECTOR, "div.dl-card-content")[:max_results]
    print(f"[DEBUG] Nombre de cartes trouvées : {len(cards)}")

    for card in cards:
        print(card.text)

        # Tente de cliquer sur le bouton/titre du médecin pour voir les détails
        boutton_element = card.find_element(By.CSS_SELECTOR, "h2") 
        boutton_element.click()
        time.sleep(5)

        # Extraction du nom
        try:
            name = boutton_element.find_element(By.CSS_SELECTOR, ".profile-name-with-title").text
            print(f"Nom: {name}")
        except Exception as e:
            print(f"Erreur lors de l'extraction du nom: {e}")
            name = "Inconnu"

        # Extraction des disponibilités
        try:
            availability_block = card.find_element(By.CSS_SELECTOR, ".availabilities-days")
            availability_name = availability_block.find_element(By.CSS_SELECTOR, ".availabilities-day-name").text
            availability_date = availability_block.find_element(By.CSS_SELECTOR, ".availabilities-day-date").text
            availability_time = availability_block.find_element(By.CSS_SELECTOR, ".Tappable-inactive.availabilities-slot").text
        except Exception as e:
            print(f"Erreur lors de l'extraction de la disponibilité: {e}")
            availability_name = availability_date = availability_time = "Inconnue"

        # Extraction de l'adresse depuis la page de détail
        try: 
            adresse_block = boutton_element.find_element(By.CSS_SELECTOR, ".dl-profile-pratice-name").text
            lines = adresse_block.split(",")
            street = lines[0].strip()
            postal_code = lines[1].split(" ")[0].strip()
            city = " ".join(lines[1].split(" ")[1:]).strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction de l'adresse: {e}")
            street = postal_code = city = "Inconnus"

        # Extraction de l'information sur l'assurance
        try:
            assurance = card.find_element(By.CSS_SELECTOR, ".t-sector").text
        except Exception as e:
            print(f"Erreur lors de l'extraction de l'assurance: {e}")
            assurance = "Inconnu"

        # Extraction du prix
        try:
            price_block = card.find_element(By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-s.dl-text-neutral-130") 
            price = card.find_element(By.CSS_SELECTOR, ".t-fee").text.replace("€", "").strip()
        except Exception as e:
            print(f"Erreur lors de l'extraction du prix: {e}")
            price = "Inconnu"

        # (Redondant) Ré-extraction de l'adresse depuis le résumé de la carte
        try:
            address_block = card.find_element(By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-s.dl-text-neutral-130").text
            lines = address_block.split("\n")
            street = lines[0]
            postal_code = lines[1].split(" ")[0]
            city = " ".join(lines[1].split(" ")[1:])
        except Exception as e:
            print(f"Erreur lors de l'extraction de l'adresse: {e}")
            street = postal_code = city = "Inconnus"

        # Construction de l’objet résultat
        results.append({
            "Nom": name,
            "Disponibilité": f"{availability_name} {availability_date} {availability_time}",
            "Consultation": "visio ou sur place",  # À remplacer par la vraie info si disponible
            "Assurance": assurance,
            "Prix (€)": price,
            "Rue": street,
            "Code Postal": postal_code,
            "Ville": city
        })

        # Retour à la page précédente
        driver.back()

    return results

# Sauvegarde des résultats dans un fichier CSV
def save_to_csv(results):
    with open("medecins.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Nom", "Disponibilité", "Consultation", "Assurance", "Prix (€)", "Rue", "Code Postal", "Ville"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(res)
            print("je suis la")
            print(f"[DEBUG] Écriture dans le CSV : {res}")

# Fonction principale de contrôle du programme
def main():
    args = parse_arguments()  # Récupération des paramètres utilisateur
    driver = setup_driver()  # Initialisation de Selenium

    try:
        search_doctolib(driver, args.query, args.location)
        scraped = extract_results(driver, args.max_results)

        # Application des filtres demandés par l'utilisateur
        filtered = []
        for med in scraped:
            if args.assurance and args.assurance.lower() not in med["Assurance"].lower():
                continue
            if args.consultation and args.consultation not in med["Consultation"].lower():
                continue
            try:
                prix = float(med["Prix (€)"])
                if not (args.price_min <= prix <= args.price_max):
                    continue
            except ValueError:
                print(f"[ERROR] Prix invalide pour {med['Nom']}: {med['Prix (€)']}")

            filtered.append(med)

        # Sauvegarde finale
        save_to_csv(filtered)
        print(f"{len(filtered)} résultats sauvegardés dans 'medecins.csv'")

    finally:
        driver.quit()  # Fermeture du navigateur

# Point d'entrée du script
if __name__ == "__main__":
    main()

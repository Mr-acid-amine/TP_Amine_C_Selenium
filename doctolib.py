import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import argparse
import re

def parse_arguments():
    """
    Analyse les arguments passés en ligne de commande.
    """
    parser = argparse.ArgumentParser(description='Scraping Doctolib avec Selenium')
    parser.add_argument('--max_results', type=int, default=10, help='Nombre max de résultats')
    parser.add_argument('--start_date', required=True, help='Date début JJ/MM/AAAA')
    parser.add_argument('--end_date', required=True, help='Date fin JJ/MM/AAAA')
    parser.add_argument('--speciality', required=True, help='Spécialité médicale recherchée (ex: dermatologue)')
    parser.add_argument('--insurance', required=True, choices=['secteur 1', 'secteur 2', 'non conventionné'], help='Type d’assurance accepté')
    parser.add_argument('--consultation', required=True, choices=['video', 'sur place'], help='Type de consultation')
    parser.add_argument('--price_min', type=int, default=0, help='Prix minimum')
    parser.add_argument('--price_max', type=int, default=999, help='Prix maximum')
    parser.add_argument('--address_keyword', required=True, help='Mot-clé pour la localisation')
    return parser.parse_args()

def init_chrome_driver():
    """
    Initialise le navigateur Chrome avec les bons paramètres.
    """
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    browser = webdriver.Chrome(service=chrome_service, options=chrome_options)
    browser.maximize_window()
    return browser

def launch_doctolib_search(browser, user_args):
    """
    Lance la recherche sur Doctolib selon les critères définis.
    """
    browser.get('https://www.doctolib.fr')
    wait = WebDriverWait(browser, 15)

    # Accepter les cookies si présent
    try:
        accept_cookies_button = wait.until(EC.element_to_be_clickable((By.ID, 'didomi-notice-agree-button')))
        accept_cookies_button.click()
    except:
        pass  # Pas de popup de cookies

    # Entrer la spécialité
    speciality_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.searchbar-query-input')))
    speciality_input.send_keys(user_args.speciality)
    time.sleep(2)
    speciality_input.send_keys(Keys.ARROW_DOWN, Keys.ENTER)

    # Entrer l'adresse
    address_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Où ?"]')))
    address_input.clear()
    address_input.send_keys(user_args.address_keyword)
    
    time.sleep(2)
    address_input.send_keys(Keys.ARROW_DOWN, Keys.ENTER)
    address_input.send_keys(Keys.RETURN)

    # Attente du chargement des cartes de résultats
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.dl-card')))
    except:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'dl-search-result-presentation')))

    time.sleep(2)
    browser.execute_script("window.scrollBy(0, 600);")
    
    time.sleep(2)

def extract_doctor_cards(browser, max_results):
    """
    Extrait les données des cartes de médecins.
    """
    time.sleep(2)
    doctor_cards = browser.find_elements(By.CSS_SELECTOR, "div.dl-card")[:max_results]
    search_results = []

    for card in doctor_cards:
        try:
            full_name = card.find_element(By.CSS_SELECTOR, "h2").text.strip()
        except:
            continue  # Carte sans nom valide, on ignore

        try:
            paragraph_elements = card.find_elements(By.CSS_SELECTOR, 'p[data-design-system-component="Paragraph"]')
            paragraph_texts = [p.text.strip() for p in paragraph_elements]

            # Détection spécialité
            speciality = next((t for t in paragraph_texts if any(m in t.lower() for m in ['dermatologue', 'ophtalmologue', 'allergologue'])), "Centre de santé")

            # Adresse : rue
            address_line = next((t for t in paragraph_texts if re.search(r'\d+.*(rue|avenue|boulevard|place|chemin)', t.lower())), "NA")

            # Code postal et ville
            postal_city = next((t for t in paragraph_texts if re.match(r'\d{5}\s', t)), "NA NA")
            postal_parts = postal_city.split(" ", 1)
            
            postal_code = postal_parts[0]
            city = postal_parts[1] if len(postal_parts) > 1 else "NA"

            # Conventionnement / secteur
            raw_insurance_text = next((t for t in paragraph_texts if 'conventionné' in t.lower()), "NA")
            is_conventionne = "Oui" if "conventionné" in raw_insurance_text.lower() else "Non"

            if "secteur 1" in raw_insurance_text.lower():
                insurance_sector = "1"
            elif "secteur 2" in raw_insurance_text.lower():
                insurance_sector = "2"
            else:
                insurance_sector = "Non précisé"

        except:
            speciality, address_line, postal_code, city, is_conventionne, insurance_sector = "NA", "NA", "NA", "NA", "NA", "NA"

        # Type de consultation
        consultation_type = "video" if card.find_elements(By.CSS_SELECTOR, '[data-test-id="telehealth-icon"]') else "sur place"

        # Prochaine disponibilité
        try:
            availability_container = card.find_element(By.CSS_SELECTOR, '[data-test-id="availabilities-container"]')
            availability_text = availability_container.text.strip().replace("\n", " ")
            date_match = re.search(r"(?:[Ll]e\s)?(\d{1,2}\s\w+\s\d{4})", availability_text)
            next_availability = date_match.group(1) if date_match else availability_text[:50]
        except:
            next_availability = "Non précisée"

        # Construction de la ligne de résultat
        search_results.append({
            "Nom complet": full_name,
            "Spécialité": speciality,
            "Consultation": consultation_type,
            "Conventionné": is_conventionne,
            "Secteur": insurance_sector,
            "Prochaine dispo": next_availability,
            "Rue": address_line,
            "Code postal": postal_code,
            "Ville": city
        })

    return pd.DataFrame(search_results)

def main():
    """
    Point d’entrée principal.
    """
    user_args = parse_arguments()
    browser = init_chrome_driver()

    try:
        launch_doctolib_search(browser, user_args)
        dataframe = extract_doctor_cards(browser, user_args.max_results)
        file_name = f'doctolib_{user_args.speciality}_{user_args.address_keyword}.csv'
        dataframe.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f'Fichier CSV sauvegardé : {file_name}')
    finally:
        browser.quit()

if __name__ == "__main__":
    main()

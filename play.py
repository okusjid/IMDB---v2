import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def modify_image_url(image_url):
    """Remove resizing parameters from the image URL and keep the '@', returning the full-size image URL."""
    if '_V1_' in image_url:
        image_url = image_url.split('_V1_')[0]
    if '@' in image_url:
        image_url = image_url.split('@')[0] + '@.jpg'
    return image_url

def scroll_to_element(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
    except Exception as e:
        print(f"Error scrolling to element: {e}")

def extract_personal_info(session, actor_url):
    """Extract personal info from the actor's page using requests and BeautifulSoup."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = session.get(actor_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        personal_details_section = soup.find('section', {'data-testid': 'PersonalDetails'})
        
        if personal_details_section is None:
            print(f"No personal details section found for {actor_url}")
            return None

        personal_info = {}
        list_items = personal_details_section.find_all('li', class_='ipc-metadata-list__item')

        for item in list_items:
            label_element = item.find('span', class_='ipc-metadata-list-item__label')
            content_element = item.find('div', class_='ipc-metadata-list-item__content-container')

            if label_element and content_element:
                label = label_element.get_text(strip=True)
                content = ' '.join(content_element.get_text(separator=' ').split())
                personal_info[label] = content

        return personal_info

    except Exception as e:
        print(f"Error while parsing personal details: {e}")
        return None

def extract_actor_data(session, driver, actor_url, full_size_image_url, actor_name):
    """Extract actor's name, image URL, and personal details."""
    try:
        actor_data = {
            "name": actor_name,
            "image_url": full_size_image_url,
            "url": actor_url
        }
        
        personal_details_html = extract_personal_info(session, actor_url)
        if personal_details_html:
            actor_data['personal_details'] = personal_details_html
        
        return actor_data
    except Exception as e:
        print(f"Error extracting data for actor at {actor_url}: {e}")
        return None

def extract_actor_image_and_link(driver, session, batch_size=10):
    """Extract the image URL and actor link from the IMDb full cast page, process actor data in batches, and save the data."""
    actor_batch = []
    actors_data = []

    try:
        rows = driver.find_elements(By.XPATH, '//*[@id="fullcredits_content"]/table[3]/tbody/tr')
        x = 2
        placeholder = "https://m.media-amazon.com/images/S/sash/N1QWYSqAfSJV62Y.png"
        
        for index, row in enumerate(rows):
            try:
                if index % 2 == 1:
                    scroll_to_element(driver, row)
                    image_element = row.find_element(By.XPATH, f'//*[@id="fullcredits_content"]/table[3]/tbody/tr[{x}]/td[1]/a/img')
                    image_url = image_element.get_attribute('src')

                    count = 0   
                    while image_url == placeholder:
                        count += 1
                        if count == 3:
                            break
                        time.sleep(1)
                        image_element = row.find_element(By.XPATH, f'//*[@id="fullcredits_content"]/table[3]/tbody/tr[{x}]/td[1]/a/img')
                        image_url = image_element.get_attribute('src')

                    full_size_image_url = modify_image_url(image_url)
                    actor_link_element = row.find_element(By.XPATH, f'//*[@id="fullcredits_content"]/table[3]/tbody/tr[{x}]/td[2]/a')
                    actor_link = actor_link_element.get_attribute('href')
                    actor_name = actor_link_element.text.strip()

                    actor_data = extract_actor_data(session, driver, actor_link, full_size_image_url, actor_name)
                    
                    if actor_data:
                        actors_data.append(actor_data)

                    x += 2

                    if len(actors_data) >= batch_size:
                        save_to_json(actors_data)
                        actors_data = []

                    if index == 31:
                        break
            except Exception as e:
                print(f"Error extracting image and link for row {index}: {e}")
    
        if actors_data:
            save_to_json(actors_data)

    except Exception as e:
        print(f"Error extracting actor image and link: {e}")
    
    return actors_data


def save_to_json(data, filename='actor_data.json'):
    """Save the given data to the JSON file."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r+', encoding='utf-8') as file:
                current_data = json.load(file)
                current_data.extend(data)  # Append new data to existing JSON
                file.seek(0)
                json.dump(current_data, file, indent=4)
        else:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
        print(f"Saved data for {len(data)} actors to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

def main():
    try:
        driver = webdriver.Chrome()
        driver.maximize_window()
        session = requests.Session()
        url = "https://www.imdb.com/title/tt0421463/fullcredits?ref_=ttfc_ql_1"
        driver.get(url)

        extract_actor_image_and_link(driver, session)

    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

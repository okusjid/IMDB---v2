import os
import json
import requests
import threading
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Provide specific HTTP error
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")  # Handle connection errors
        return None
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")  # Handle timeouts
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"General error occurred: {req_err}")  # Handle all other requests-related errors
        return None
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        personal_details_section = soup.find('section', {'data-testid': 'PersonalDetails'})
        
        if personal_details_section is None:
            print(f"No personal details section found for {actor_url}")
            return None

        personal_info = {}
        list_items = personal_details_section.find_all('li', class_='ipc-metadata-list__item')

        if not list_items:
            print("No list items found in personal details section.")
            return None

        # Loop through each list item and extract the label and content
        for item in list_items:
            label_element = item.find('span', class_='ipc-metadata-list-item__label')
            content_element = item.find('div', class_='ipc-metadata-list-item__content-container')

            if label_element and content_element:
                label = label_element.get_text(strip=True)
                content = ' '.join(content_element.get_text(separator=' ').split())
                personal_info[label] = content

        # Extract official sites if present
        official_sites_section = personal_details_section.find('li', {'data-testid': 'details-officialsites'})
        if official_sites_section:
            official_sites = official_sites_section.find_all('a', class_='ipc-metadata-list-item__list-content-item')
            official_site_links = [site.get('href') for site in official_sites if site.get('href')]
            if official_site_links:
                personal_info['Official Sites'] = official_site_links
            else:
                print("No official site links found.")
        else:
            print("No official sites section found.")

        # Display extracted personal info
        if personal_info:
            for key, value in personal_info.items():
                print(f"{key}: {value}")
            return personal_info
        else:
            print("No personal information could be extracted.")
            return None

    except Exception as e:
        print(f"Error while parsing personal details: {e}")
        return None

def extract_actor_data(session, driver, actor_url, full_size_image_url):
    """Extract actor's name, image URL, and personal details."""
    try:
        driver.get(actor_url)
        actor_data = {}
        actor_data['url'] = actor_url
        actor_data['image'] = full_size_image_url
        # Fetch the personal details section using requests and BeautifulSoup
        personal_details_html = extract_personal_info(session, actor_url)
        if personal_details_html:
            actor_data['personal_details'] = personal_details_html
        return actor_data
    except Exception as e:
        print(f"Error extracting data for actor at {actor_url}: {e}")
        return None

def extract_actor_image_and_link(driver, session, batch_size=10):
    """Extract the image URL and actor link from the IMDb full cast page, process actor data in batches, and save the data."""
    image_and_links = []
    actor_batch = []

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
                    actor_link_element = row.find_element(By.XPATH, '//*[@id="fullcredits_content"]/table[3]/tbody/tr[2]/td[2]/a')
                    actor_link = actor_link_element.get_attribute('href')
                    print("-------------------")
                    print("Index:", index)
                    print("Full-size image URL:", full_size_image_url)
                    print("Actor link:", actor_link)
                    print("----------------")
                    x += 2
                    image_and_links.append((full_size_image_url, actor_link))

                    # Add to the batch
                    actor_batch.append((full_size_image_url, actor_link))

                    # Once the batch size is reached, process the batch
                    if len(actor_batch) >= batch_size:
                        process_actor_batch(session, actor_batch)
                        actor_batch = []  # Clear the batch after processing

            except Exception as e:
                print(f"Error extracting image and link for row {index}: {e}")
    
        # Process any remaining actors after the loop
        if actor_batch:
            process_actor_batch(session, actor_batch)

    except Exception as e:
        print(f"Error extracting actor image and link: {e}")
    
    return image_and_links


def process_actor_batch(session, actor_batch):
    """Process a batch of actors by creating a new WebDriver for each actor."""
    for full_size_image_url, actor_link in actor_batch:
        try:
            # Create a new WebDriver for each actor
            driver = webdriver.Chrome()

            # Extract the actor data with the new WebDriver instance
            actor_data = extract_actor_data(session, driver, actor_link, full_size_image_url)
            
            # Process or save the actor data as required (e.g., save to a database or file)
            # save_actor_data(actor_data)  # Example function to save data
            
            driver.quit()  # Close the WebDriver instance after processing

        except Exception as e:
            print(f"Error processing actor data for {actor_link}: {e}")
            if driver:
                driver.quit()  # Ensure the driver is closed on error

def save_to_json(data, filename='actor_data.json'):
    """Save the given data to the JSON file, including the image URL."""
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
        # url = "https://www.imdb.com/title/tt0421463/fullcredits?ref_=ttfc_ql_1"
        # driver.get(url)

        # Extract actor image URLs and profile links and process them
        # extract_actor_image_and_link(driver, session)


        extract_personal_info(session, "https://www.imdb.com/name/nm3150183/?ref_=ttfc_fc_cl_t211")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

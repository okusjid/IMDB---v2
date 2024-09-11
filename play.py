import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
def modify_image_url(image_url):
    """
    Remove resizing parameters from the image URL and keep the '@', 
    returning the full-size image URL.
    """
    # Find the part before the resizing parameters
    if '_V1_' in image_url:
        image_url = image_url.split('_V1_')[0]
    
    # Ensure the '@' part is correctly added to the end
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
    try:
        response = session.get(actor_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        personal_details_section = soup.find('section', {'data-testid': 'PersonalDetails'})
        if personal_details_section:
            # Extract personal details HTML for now
            return personal_details_section.prettify()
        else:
            print(f"No personal details found for {actor_url}")
            return None
    except Exception as e:
        print(f"Error fetching personal details for {actor_url}: {e}")
        return None

def extract_actor_data(session, driver, actor_url, full_size_image_url):
    """Extract actor's name, image URL, and personal details."""
    try:
        driver.get(actor_url)
        actor_data = {}

        # Extract the actor's name
        name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1/span[1]'))
        )
        name = name_element.text
        actor_data['name'] = name
        print(f"Extracting data for {name}")

        # Include the full-size image URL in the actor data
        actor_data['image_url'] = full_size_image_url

        # Fetch the personal details section using requests and BeautifulSoup
        personal_details_html = extract_personal_info(session, actor_url)
        if personal_details_html:
            actor_data['personal_details'] = personal_details_html

        return actor_data
    except Exception as e:
        print(f"Error extracting data for actor at {actor_url}: {e}")

def extract_actor_image_and_link(driver):
    """Extract the image URL and actor link from the IMDb full cast page, skipping every alternate row."""
    image_and_links = []
    try:
        # Locate all the rows in the table
        rows = driver.find_elements(By.XPATH, '//*[@id="fullcredits_content"]/table[3]/tbody/tr')
        
        # Loop over rows and process every alternate row (i.e., skip one, process one)
        x = 2
        placeholder = "https://m.media-amazon.com/images/S/sash/N1QWYSqAfSJV62Y.png"
        for index, row in enumerate(rows):
            try:
                # Only process even indexed rows (i.e., skip odd-indexed rows)
                if index % 2 == 1:
                    scroll_to_element(driver, row)
                    # Using f-string to dynamically insert 'x' into the XPath expression
                    image_element = row.find_element(By.XPATH, f'//*[@id="fullcredits_content"]/table[3]/tbody/tr[{x}]/td[1]/a/img')
                    image_url = image_element.get_attribute('src')
                    # look thrice for the image url
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
                    
                    # Append the image and actor link to the results
                    x += 2
                    image_and_links.append((full_size_image_url, actor_link))
            except Exception as e:
                print(f"Error extracting image and link for row {index}: {e}")
    except Exception as e:
        print(f"Error extracting actor image and link: {e}")
    
    return image_and_links


def save_to_json(data, filename='actor_data.json'):
    """Save the given data to the JSON file, including the image URL."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r+', encoding='utf-8') as file:
                current_data = json.load(file)
                current_data.append(data)  # Append new data to existing JSON
                file.seek(0)
                json.dump(current_data, file, indent=4)
        else:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump([data], file, indent=4)
        print(f"Saved data for {data['name']} (image: {data['image_url']}) to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

def main():
    try:
        driver = webdriver.Chrome()
        driver.maximize_window()
        session = requests.Session()
        url = "https://www.imdb.com/title/tt0421463/fullcredits?ref_=ttfc_ql_1"
        driver.get(url)

        # Extract actor image URLs and profile links
        image_and_links = extract_actor_image_and_link(driver)
        print(f"Total actors extracted: {len(image_and_links)}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(extract_actor_data, session, driver, actor_link, full_size_image_url )
                for full_size_image_url, actor_link in image_and_links
            ]
            for future in as_completed(futures):
                actor_data = future.result()
                if actor_data:
                    # Save each actor's data to the JSON file after extraction
                    save_to_json(actor_data)

    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

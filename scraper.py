import requests
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime

# Replace these with your actual API key and CSE ID
API_KEY = 'AIzaSyCQr3QQQYtE4g0mt1DQquPgiqH3vzGox7E'
CSE_ID = '54141c91774764303'

scraping_status = {
    "is_running": False,
    "progress": 0,
    "results": [],
    "stop_requested": False,
    "websites_scraped": 0,
    "log": []
}

def google_search(query, num_results=99):
    links = []
    num_per_query = 10  # Google Custom Search API returns a maximum of 10 results per query
    for start in range(1, num_results + 1, num_per_query):
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={CSE_ID}&key={API_KEY}&num={min(num_per_query, num_results - start + 1)}&start={start}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            continue

        results = response.json()
        if 'items' in results:
            for item in results['items']:
                href = item['link']
                # Skip Wikipedia and Yell.com pages
                if "wikipedia.org" in href or "yell.com" in href:
                    continue
                links.append(href)
        
        if len(links) >= num_results or scraping_status["stop_requested"]:
            break
    
    return links[:num_results]

def extract_emails_from_url(url):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    service = Service('./chromedriver')  # Path to your chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print(f"Extracting emails from: {url}")
        driver.get(url)
        time.sleep(3)  # Allow time for the page to load completely
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract emails from mailto links
        mailto_links = soup.select('a[href^=mailto]')
        emails = set()
        for link in mailto_links:
            email = link.get('href').replace('mailto:', '').strip().split('?')[0]
            if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', email):
                emails.add(email)
        
        # Check for "Powered by Yell Business" text anywhere on the page
        if 'powered by yell business' in soup.get_text().lower():
            print(f"Found emails: {emails} in {url}")
            return list(emails)  # Return all found emails
        else:
            print(f"No 'Powered by Yell Business' found in the page for: {url}")
            return []
    except Exception as e:
        print(f"Error extracting emails from {url}: {e}")
        return []
    finally:
        driver.quit()

def save_to_csv(data, filename='emails.csv'):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Website URL", "Email Address", "Business Type"])
        for row in data:
            writer.writerow(row)

def run_scraper(status_object, query, num_websites):
    global scraping_status
    scraping_status = status_object
    scraping_status["is_running"] = True
    scraping_status["progress"] = 0
    scraping_status["results"] = []
    scraping_status["stop_requested"] = False
    scraping_status["websites_scraped"] = 0
    scraping_status["log"] = []

    original_query = query  # Store the original query
    query = f'"powered by Yell Business" {query}'
    print(f"Query: {query}")  # Debugging statement
    links = google_search(query, num_websites)
    
    if not links:
        print(f"No links found in Google search for {query}.")
        scraping_status["log"].append({"timestamp": datetime.now().strftime("%H:%M:%S"), "website": "N/A", "email": "No links found in Google search."})
        scraping_status["is_running"] = False
        return
    
    data = []
    total_links = len(links)
    
    for i, link in enumerate(links):
        if scraping_status["stop_requested"]:
            break
        emails = extract_emails_from_url(link)
        scraping_status["websites_scraped"] += 1
        
        websites_scraped_text = "website scraped" if scraping_status["websites_scraped"] == 1 else "websites scraped"
        status_text = f"{scraping_status['websites_scraped']} {websites_scraped_text}"
        
        if emails:
            for email in emails:
                data.append((link, email, original_query))  # Use original_query here
                scraping_status["results"].append(f"{query}: {email}")
                scraping_status["log"].append({"timestamp": datetime.now().strftime("%H:%M:%S"), "website": link, "email": email, "status": status_text})
        else:
            scraping_status["log"].append({"timestamp": datetime.now().strftime("%H:%M:%S"), "website": link, "email": "No email found", "status": status_text})
        
        scraping_status["progress"] = int((i + 1) / total_links * 100)
    
    # Save all data to CSV file at the end of scraping
    save_to_csv(data)

    print(f"Scraping completed. Data saved to emails.csv")
    scraping_status["is_running"] = False
    scraping_status["progress"] = 100
    final_status_text = f"{scraping_status['websites_scraped']} {'website scraped' if scraping_status['websites_scraped'] == 1 else 'websites scraped'}"
    scraping_status["log"].append({"timestamp": datetime.now().strftime("%H:%M:%S"), "website": "N/A", "email": "Scraping completed.", "status": final_status_text})
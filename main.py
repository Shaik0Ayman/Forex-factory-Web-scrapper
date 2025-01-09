import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv

# Function to scrape using requests
def scrape_with_requests(url):
    print("Attempting to scrape with requests...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("Successfully retrieved the page.")
            soup = BeautifulSoup(response.content, 'html.parser')
            return parse_calendar(soup)
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error during requests scraping: {e}")
        return []

# Function to scrape using Selenium
def scrape_with_selenium(url):
    print("Attempting to scrape with Selenium...")
    try:
        options = Options()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        # Initialize the Selenium WebDriver
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # Get the page source and parse with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        driver.quit()

        return parse_calendar(soup)
    except Exception as e:
        print(f"Error during Selenium scraping: {e}")
        return []

# Function to parse the Forex Factory calendar
def parse_calendar(soup):
    data = []
    calendar_table = soup.find('table')  # Replace with a more specific selector if needed

    if calendar_table:
        print("Parsing the calendar table...")
        for row in calendar_table.find_all('tr'):
            try:
                impact_cell = row.find('td', {'class': 'calendar__cell calendar__impact'})
                impact = 'N/A'
    
                if impact_cell:
                    # Access the span with the title attribute
                    impact_span = impact_cell.find('span', {'title': True})
    
                    if impact_span and 'title' in impact_span.attrs:
                        # Extract impact level by parsing the title attribute
                        impact_title = impact_span['title']
                        impact = impact_title.split()[0]  # Assuming the first word indicates the level (e.g., "High")
                
                # Extract data (adjust selectors based on actual structure)
                currency = row.find('td', {'class': 'calendar__cell calendar__currency'}).get_text(strip=True) if row.find('td', {'class': 'calendar__cell calendar__currency'}) else "N/A"
                date = row.find('td', {'class': 'calendar__cell calendar__date'}).get_text(strip=True) if row.find('td', {'class': 'calendar__cell calendar__date'}) else "N/A"
                event = row.find('td', {'class': 'event'}).get_text(strip=True) if row.find('td', {'class': 'event'}) else "N/A"
                time = row.find('td', {'class': 'calendar__cell calendar__time'}).get_text(strip=True) if row.find('td', {'class': 'calendar__cell calendar__time'}) else "N/A"
                
                # Append the data to the list
                data.append([currency, date, time, event, impact])
            except Exception as e:
                print(f"Error parsing row: {e}")
    else:
        print("Calendar table not found.")
    
    return data

# Function to save the parsed data to a CSV file
def save_to_csv(data, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['CURRENCY','DATE', 'TIME', 'EVENT', 'IMPACT'])  # Write the header
        writer.writerows(data)  # Write the data rows

# Main function
def main():
    url = 'https://www.forexfactory.com/calendar'
    filename = 'forex_calendar.csv'
    high_impact_filename = 'high_impact_events.csv'

    # First, try scraping with requests
    data = scrape_with_requests(url)

    # If requests fails or returns no data, try using Selenium
    if not data:
        print("If requests failed, switching to Selenium...")
        data = scrape_with_selenium(url)

    if data:
        # Save all data to CSV
        save_to_csv(data, filename)
        # Filter high impact events
        high_impact_events = [row for row in data if row[4] == 'High']
        # Save high impact events to another CSV
        save_to_csv(high_impact_events, high_impact_filename)
        print(f"Data saved to {filename} and high impact events saved to {high_impact_filename}")
    else:
        print("Failed to scrape data.")

if __name__ == "__main__":
    main()
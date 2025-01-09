import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import tkinter as tk
from tkinter import messagebox, ttk
import os

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
    last_valid_date = "N/A"

    if calendar_table:
        print("Parsing the calendar table...")
        for row in calendar_table.find_all('tr'):
            try:
                impact_cell = row.find('td', {'class': 'calendar__cell calendar__impact'})
                impact = 'N/A'
    
                if impact_cell:
                    impact_span = impact_cell.find('span', {'title': True})
    
                    if impact_span and 'title' in impact_span.attrs:
                        impact_title = impact_span['title']
                        impact = impact_title.split()[0]
                
                currency = row.find('td', {'class': 'calendar__cell calendar__currency'}).get_text(strip=True) if row.find('td', {'class': 'calendar__cell calendar__currency'}) else "N/A"
                date = row.find('td', {'class': 'calendar__cell calendar__date'}).get_text(strip=True) if row.find('td', {'class': 'calendar__cell calendar__date'}) else "N/A"
                
                if date != "N/A":
                    last_valid_date = date
                else:
                    date = last_valid_date
                
                event = row.find('td', {'class': 'event'}).get_text(strip=True) if row.find('td', {'class': 'event'}) else "N/A"
                time = row.find('td', {'class': 'calendar__cell calendar__time'}).get_text(strip=True) if row.find('td', {'class': 'calendar__cell calendar__time'}) else "N/A"
                
                data.append([currency, date, time, event, impact])
            except Exception as e:
                print(f"Error parsing row: {e}")
    else:
        print("Calendar table not found.")
    
    return data

# Function to save data to CSV file
def save_to_csv(data, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['CURRENCY', 'DATE', 'TIME', 'EVENT', 'IMPACT'])
        writer.writerows(data)

# Start scraping and display success/failure message
def start_scraping():
    url = 'https://www.forexfactory.com/calendar'
    filename = 'forex_calendar.csv'
    high_impact_filename = 'high_impact_events.csv'
    
    data = scrape_with_selenium(url)

    if data:
        # Save all data to CSV
        save_to_csv(data, filename)
        messagebox.showinfo("Success", f"Data saved to {filename}")
        
        # Filter high impact events and save to another CSV
        high_impact_events = [row for row in data if row[4] == 'High']
        save_to_csv(high_impact_events, high_impact_filename)
        print(f"High impact data saved to {high_impact_filename}")
    else:
        messagebox.showerror("Error", "Failed to scrape data.")

# Display CSV data in a window
def display_csv_data(filename):
    if not os.path.exists(filename):
        messagebox.showerror("Error", f"File {filename} not found.")
        return
    
    data_window = tk.Toplevel()
    data_window.title(f"Data: {filename}")

    tree = ttk.Treeview(data_window, columns=('CURRENCY', 'DATE', 'TIME', 'EVENT', 'IMPACT'), show='headings')
    for col in ('CURRENCY', 'DATE', 'TIME', 'EVENT', 'IMPACT'):
        tree.heading(col, text=col)
    tree.pack(expand=True, fill='both')

    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            tree.insert("", tk.END, values=row)

# Main function for the Tkinter GUI
# ...existing code...

# Main function for the Tkinter GUI
def main():
    root = tk.Tk()
    root.title("Forex Factory Scraper")
    root.configure(bg='black')  # Set background color to black

    welcome_label = tk.Label(root, text="Welcome to Forex Factory Web Scraper", bg='black', fg='white')
    welcome_label.pack(pady=10)

    scrape_button = tk.Button(root, text="Start Web Scraping", command=start_scraping, bg='blue', fg='white')
    scrape_button.pack(pady=5)

    show_forex_button = tk.Button(root, text="Show Forex Calendar", command=lambda: display_csv_data('forex_calendar.csv'), bg='dark green', fg='white')
    show_forex_button.pack(pady=5)
    
    show_high_impact_button = tk.Button(root, text="Show High Impact Events", command=lambda: display_csv_data('high_impact_events.csv'), bg='dark red', fg='white')
    show_high_impact_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
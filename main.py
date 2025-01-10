import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import tkinter as tk
from tkinter import messagebox, ttk
import os
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# Add the scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    """ Authorizes Google account using OAuth 2.0 """
    creds = None
    # token.pickle stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

import datetime

def add_events_to_google_calendar(data):
    """Adds events to Google Calendar"""
    creds = authenticate_google()
    service = build('calendar', 'v3', credentials=creds)
    
    for event in data:
        currency, date, time, description, impact = event

        # Format the date string correctly
        date_str = date[:3] + ' ' + date[3:]    # This ensures there's a space between day and month
        time_str = time.strip().replace(':', '')  # Normalize time formats

        try:
            # Handle "All Day" event
            if not time_str or time_str.lower() == "all day":
                start_datetime = datetime.datetime.strptime(date_str, '%a %b %d %Y')
                end_datetime = start_datetime + datetime.timedelta(days=1)
            else:
                # Handling 12-hour format time
                if 'am' in time_str.lower() or 'pm' in time_str.lower():
                    # Zero-padding if necessary, e.g., `100pm` -> `0100pm`
                    if len(time_str) < 4:
                        time_str = f"0{time_str}"  # Add leading zero if necessary
                    start_time_str = f"{date_str} {time_str.lower()}"
                    start_datetime = datetime.datetime.strptime(start_time_str, '%a %b %d %Y %I%M%p')
                    start_datetime = start_datetime.replace(year=2025)
                else:
                    # Assume times are in 24-hour format if not AM/PM
                    start_time_str = f"{date_str} {time_str}:00"  # format it correctly
                    start_datetime = datetime.datetime.strptime(start_time_str, '%a %b %d %Y %H%M:%S')
                    start_datetime = start_datetime.replace(year=2025)
                end_datetime = start_datetime + datetime.timedelta(hours=1)

        except ValueError as ve:
            print(f"Date/time parsing error for event '{description}': {ve}")
            continue
        
        event_body = {
            'summary': f"{currency} - {description} ({impact} Impact)",
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC',  # Adjust as needed
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC',  # Adjust as needed
            },
        }
        
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        print(f'Event created: {event.get("htmlLink")}')
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
    calendar_table = soup.find('table', {'class': 'calendar__table'})  # Adjust selector as needed
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
                    
                date += " 2025" 
                
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
    global high_impact_filename 
    high_impact_filename = 'high_impact_events.csv'
    
    data = scrape_with_selenium(url)

    if data:
        # Save all data to CSV
        save_to_csv(data, filename)
        messagebox.showinfo("Success", f"Data saved to {filename}")
        
        # Filter high impact events and save to another CSV
        global high_impact_events
        high_impact_events = [row for row in data if row[4] == 'High']
        save_to_csv(high_impact_events, high_impact_filename)
        print(f"High impact data saved to {high_impact_filename}")
        
        # Add high impact events to Google Calendar
        #add_events_to_google_calendar(high_impact_events)
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
    
    add_to_calendar_button = tk.Button(root, text="Add High Impact Events to Google Calendar", command=lambda: add_events_to_google_calendar(high_impact_events), bg='purple', fg='white')
    add_to_calendar_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
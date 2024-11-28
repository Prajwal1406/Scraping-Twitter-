import time
import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

# Function to log in to Twitter
def login_to_twitter(driver, url, twitter_username, twitter_password):
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        wait = WebDriverWait(driver, 5)
        username = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete=username]'))
        )
        username.send_keys(twitter_username)

        login_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[role=button].r-13qz1uu'))
        )
        login_button.click()

        password = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[type=password]'))
        )
        password.send_keys(twitter_password)

        login_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid*=Login_Button]'))
        )
        login_button.click()

        time.sleep(5)  # Wait for the login process to complete
    except Exception as e:
        print(f"Error during login: {e}")

# Function to extract profile details
def extract_profile_details(driver):
    details = {}
    try:
        details['Bio'] = driver.find_element(By.XPATH, '//div[@data-testid="UserDescription"]').text
    except:
        details['Bio'] = 'N/A'

    try:
        details['Following Count'] = driver.find_element(By.XPATH, '//a[contains(@href, "/following")]/span/span').text
    except:
        details['Following Count'] = 'N/A'

    try:
        details['Followers Count'] = driver.find_element(By.XPATH, '//a[contains(@href, "/followers")]/span/span').text
    except:
        details['Followers Count'] = 'N/A'

    try:
        details['Location'] = driver.find_element(By.XPATH, '//span[@data-testid="UserLocation"]').text
    except:
        details['Location'] = 'N/A'

    try:
        details['Website'] = driver.find_element(By.XPATH, '//a[@data-testid="UserUrl"]').text
    except:
        details['Website'] = 'N/A'

    return details

# Function to scrape Twitter profile
def scrape_twitter_profile(driver, url, twitter_username, twitter_password):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Log in to Twitter if not already logged in
    if "login" in driver.current_url:
        login_to_twitter(driver, url, twitter_username, twitter_password)
        time.sleep(5)  # Wait for the login process to complete

    return extract_profile_details(driver)

# Function to insert profile details into MySQL database
def insert_profile_details_to_db(connection, profile):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO twitter_profiles (bio, following_count, followers_count, location, website)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            profile['Bio'], 
            profile['Following Count'], 
            profile['Followers Count'], 
            profile['Location'], 
            profile['Website']
        ))
        connection.commit()
    except Error as e:
        print(f"Error inserting data: {e}")

# Function to create the database if it doesn't exist
def create_database_if_not_exists(cursor, db_name):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitter_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bio VARCHAR(255),
                following_count VARCHAR(255),
                followers_count VARCHAR(255),
                location VARCHAR(255),
                website VARCHAR(255)
            )
        """)
    except Error as e:
        print(f"Error creating database or table: {e}")

# Main script
def main():
    # Twitter credentials
    twitter_username = os.getenv("twitter_username")
    twitter_password = os.getenv("twitter_password")

    # Database credentials
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    # Initialize the WebDriver
    chrome_options = Options()
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Read Twitter URLs from CSV
    input_csv = 'twitter_urls.csv'
    urls_df = pd.read_csv(input_csv)

    # Extract usernames from URLs
    urls_df['Username'] = urls_df['URL'].apply(lambda x: x.split('/')[-1])

    # Connect to MySQL database
    try:
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        if connection.is_connected():
            cursor = connection.cursor()
            create_database_if_not_exists(cursor, db_name)
            print("Connected to MySQL database and database checked/created")

            # Scrape profiles and insert into MySQL database
            for username in urls_df['Username']:
                profile = scrape_twitter_profile(driver, f"https://twitter.com/{username}", twitter_username, twitter_password)
                if profile:
                    insert_profile_details_to_db(connection, profile)

            print("Data inserted successfully.")
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            print("MySQL connection closed.")

    # Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    main()

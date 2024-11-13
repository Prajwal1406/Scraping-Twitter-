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

load_dotenv()

# Function to log in to Twitter
def login_to_twitter(driver,url, twitter_username, twitter_password):
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

        # direct_message_link = wait.until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid=AppTabBar_DirectMessage_Link]'))
        # )
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
        login_to_twitter(driver,url, twitter_username, twitter_password)
        time.sleep(5)  # Wait for the login process to complete

    return extract_profile_details(driver)

# Main script
def main():
    # Twitter credentials
    twitter_username = os.getenv("twitter_username")
    twitter_password = os.getenv("twitter_password")

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

    # Scrape profiles and save to CSV
    profiles = []
    for username in urls_df['Username']:
        profile = scrape_twitter_profile(driver, f"https://twitter.com/{username}", twitter_username, twitter_password)
        if profile:
            print(profile)
            profiles.append(profile)

    # Create DataFrame and save to CSV
    output_csv = 'twitter_profiles.csv'
    df = pd.DataFrame(profiles)
    df.to_csv(output_csv, index=False)
    print("CSV file created successfully.")

    # Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    main()

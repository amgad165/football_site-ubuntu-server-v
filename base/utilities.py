from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from .models import team_data_modes , PlayerInfo
import os
from django.conf import settings
from selenium.webdriver.chrome.options import Options

################################################# teams functions########################################

def get_team_link(team_name):
    # Specify the path to the GeckoDriver executable
    geckodriver_path = os.path.join(settings.STATICFILES_DIRS[0], 'geckodriver')  # Replace with the actual path to geckodriver

    # Create a Firefox service with the executable path
    firefox_service = FirefoxService(geckodriver_path)
    firefox_options = FirefoxOptions()
    firefox_options.headless = True
       
    # Initialize the Firefox WebDriver with the service
    driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

   
    try:
        # Create a Google search query
        search_query = f"{team_name} worldfootball"
    
        # Perform a Google search
        driver.get("https://www.google.com/")
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
    
        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "g")))
    
        # Click on the first link (WorldFootball)
        search_results = driver.find_elements(By.CLASS_NAME, "g")
    
        if search_results:
            first_result = search_results[0]
            link = first_result.find_element(By.TAG_NAME, "a")
            # Extract the href attribute value from the <a> tag
            worldfootball_url = link.get_attribute("href")
            driver.quit()
            return worldfootball_url
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.quit()


        
def get_team_data_scrape(team_name,teams_df):
    
    if teams_df[teams_df['name'].str.contains(team_name)].any(axis=None):

        print("helloooo")
        worldfootball_url =  teams_df.loc[teams_df['name'].str.contains(team_name), 'links'].iloc[0]

    else:
        print('nenenee')
        worldfootball_url = get_team_link(team_name)


    
    # Specify the path to the GeckoDriver executable
    # geckodriver_path = os.path.join(settings.STATICFILES_DIRS[0], 'geckodriver')  # Replace with the actual path to geckodriver

    # Create a Firefox service with the executable path
    # firefox_service = FirefoxService(geckodriver_path)
    
    # # Create Firefox options
    # firefox_options = FirefoxOptions()
    # firefox_options.set_preference("javascript.enabled", False)  # Disable JavaScript

    # firefox_options.headless = True


    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run Chrome in headless mode
    chrome_options.add_argument("window-size=1400,1500")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("enable-automation")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})

    driver = webdriver.Chrome(options=chrome_options)

    try:

        # Navigate directly to the extracted URL
        driver.get(worldfootball_url)

        # Wait for the WorldFootball page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "navibox2")))

        # Locate the "Players from A-Z" link and click on it
        div_element = driver.find_element(By.CLASS_NAME, "navibox2")
        li_elements = div_element.find_elements(By.TAG_NAME, "li")
        for li_element in li_elements:
            a_element = li_element.find_element(By.TAG_NAME, "a")
            if "Players from A-Z" in a_element.text:
                a_element.click()
                break

        # get the club name from the website
        club_name = driver.find_element(By.CSS_SELECTOR, ".emblemwrapper .head")
        club_name = club_name.text
        print(club_name,'hhhhhhhhhhhh')
        # Wait for the players page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//tr")))

        # Extract player information from the page
        player_info = []

        # Find the section with player information
        player_rows = driver.find_elements(By.XPATH, "//div[@class='data']//table[@class='standard_tabelle']//tr")
        for row in player_rows:
            # Find the first <td> with class "hell" in each row and get the player name
            try:
                player_name_td = row.find_element(By.CSS_SELECTOR, "td")
                player_name = player_name_td.text.strip()
                    # Find all <td> elements in each row
                player_data_tds = row.find_elements(By.TAG_NAME, "td")
                
                # Process each <td> element and add it to the player_info list
                player_data = [td.text.strip() for td in player_data_tds if td.text.strip()]

                if len(player_name) > 2:
                    player_info.append(player_data)
            except:
                pass

        return player_info , club_name

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        driver.quit()

def get_common_players_scrape(clubs_list,csv_url):
    team_df = pd.read_csv(csv_url)
    # Initialize a dictionary to store player information for each club
    club_players_list = []
    clubs = []
    # Iterate through the list of clubs
    for club_name in clubs_list:
        # Get players for the current club using the get_players_for_team function
        players, club = get_team_data_scrape(club_name,team_df)
        clubs.append(club)
    
        # Store the players in the dictionary using the club name as the key
        club_players_list.append(players)
    

    
    # Create a DataFrame for each club's player data
    club_dataframes = [pd.DataFrame(data, columns=["Player", "Country","Position","Born"]) for data in club_players_list]

    for i, df in enumerate(club_dataframes):
        club_dataframes[i] = df.drop_duplicates(subset=['Player', 'Born'])

    # Merge DataFrames on the specified columns with 'inner' join
    common_data = pd.concat([df.set_index(['Player', 'Born']) for df in club_dataframes], axis=1, join='inner').reset_index()

    # Drop duplicate columns
    common_data = common_data.loc[:, ~common_data.columns.duplicated(keep='first')]

    # Remove duplicates based on the specified columns
    common_data = common_data.drop_duplicates(subset=['Player', 'Born'])
    return common_data,clubs



def get_team_data_db(team_name):
    # Query the PlayerInfo model to filter data by team_name
    team_data = PlayerInfo.objects.filter(Club=team_name)

    # Initialize lists to store data
    data_list = []
    club_name = ""

    # Loop through the queryset and extract data
    for player in team_data:
        # Extract relevant fields from the model
        player_name = player.Player
        country = player.Country
        position = player.Position
        born = player.Born

        # Append the data as a list
        data_list.append([player_name, country, position, born])

        # Get the club name (assuming it's the same for all players)
        club_name = player.Club

    return data_list, club_name


def get_common_players_db(clubs_list):

    # Initialize a dictionary to store player information for each club
    club_players_list = []
    clubs = []
    # Iterate through the list of clubs
    for club_name in clubs_list:
        # Get players for the current club using the get_players_for_team function
        players, club = get_team_data_db(club_name)
        clubs.append(club)
    
        # Store the players in the dictionary using the club name as the key
        club_players_list.append(players)
    

    
    # Create a DataFrame for each club's player data
    club_dataframes = [pd.DataFrame(data, columns=["Player", "Country","Position","Born"]) for data in club_players_list]

    for i, df in enumerate(club_dataframes):
        club_dataframes[i] = df.drop_duplicates(subset=['Player', 'Born'])
        
    # Merge DataFrames on the specified columns with 'inner' join
    common_data = pd.concat([df.set_index(['Player', 'Born']) for df in club_dataframes], axis=1, join='inner').reset_index()

    # Drop duplicate columns
    common_data = common_data.loc[:, ~common_data.columns.duplicated(keep='first')]

    # Remove duplicates based on the specified columns
    common_data = common_data.drop_duplicates(subset=['Player', 'Born'])
    return common_data,clubs


def parse_date(date_str):
    # Try different date formats
    formats_to_try = ['%d/%m/%Y','%Y-%m-%d', '%Y/%m/%d','%b-%y', '%m/%Y','%Y']
    
    for date_format in formats_to_try:
        try:
            return datetime.strptime(date_str, date_format).date()
        except ValueError:
            continue
    
    # If none of the formats match, return None or some other default value
    return None

################################################# players functions########################################

def scrape_player_info(search_query):
    # Initialize the Firefox WebDriver
    geckodriver_path = os.path.join(settings.STATICFILES_DIRS[0], 'geckodriver')  # Replace with the actual path to geckodriver
    
    # Create a Firefox service with the executable path
    firefox_service = FirefoxService(geckodriver_path)
    
    # Create Firefox options
    firefox_options = FirefoxOptions()
    firefox_options.headless = True
    firefox_options.binary_location = r'/usr/bin/firefox/firefox'
    firefox_options.add_argument(argument="--no-sandbox")
    firefox_options.add_argument(argument="--headless")
    firefox_options.add_argument(argument="--disable-gpu")
    firefox_options.add_argument(argument="--window-size=1920,1080")

    # Initialize the Firefox WebDriver with the service
    driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

    # Open the Wikipedia homepage
    driver.get("https://en.wikipedia.org/wiki/Special:Search?")

    # Find the search input element and enter the search query
    search_box = driver.find_element(By.ID, "ooui-php-1")
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    # Wait for the search results to load (you may need to adjust the sleep duration)
    import time
    time.sleep(1)


    # Wait for the search results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "mw-search-result-heading"))
    )

    # Find the first search result link
    search_results = driver.find_elements(By.CLASS_NAME, "mw-search-result-heading")
    
    if search_results:
        first_result = search_results[0].find_element(By.TAG_NAME, "a")
        first_result.click()

        # Get the page source
        player_page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(player_page_source, "html.parser")

        # Extract the player's name from the title
        player_name = soup.find("h1", {"class": "firstHeading"}).text.strip()

        def extract_section_data(section_name):
            section_data = []
            infobox = soup.find("table", {"class": "infobox"})
            if infobox:
                rows = infobox.find_all("tr")
                section_found = False
                for row in rows:
                    header = row.find("th", {"colspan": "4", "class": "infobox-header"})
                    if header and section_name in header.text:
                        section_found = True
                    elif section_found:
                        label = row.find("th", {"scope": "row"})
                        data = row.find("td")
                        if label and data:
                            label_text = label.text.strip()
                            data_text = data.text.strip()
                            # Exclude rows with "Years" as the label and "Team" as the data
                            if not ((label_text == "Years" and data_text == "Team") or label_text == "Total"):
                                section_data.append((label_text, data_text))
                        elif not label:
                            # Stop when we reach a row without a "scope" attribute (usually indicating the end of the section)
                            break

            return section_data

        # Extract "Youth career" and "Senior career" section data combined as "Career"
        career_data = extract_section_data("Youth career") + extract_section_data("Senior career")
        
        driver.quit()
        return player_name, career_data

    return None, None

def compare_players(player_search):

    player_info_dict = {}
    
    players=[]
    for player in player_search:
        player_name, career_data = scrape_player_info(player)
        if player_name:
            players.append(player_name)
            player_info_dict[player_name] = {"Career": career_data}


    
    if len(players) < 2:
        print("Please provide at least two players for comparison.")
    else:
        common_clubs = set()
        common_periods = {}
    
        # Create a set of all clubs for each player
        all_player_clubs = [set() for _ in range(len(players))]
    
        for i, player_name in enumerate(players):
            player_info = player_info_dict.get(player_name, {})
            player_career_data = player_info.get("Career", [])
    
            for _, club in player_career_data:
                all_player_clubs[i].add(club)
    
        # Find the common clubs among all players
        common_clubs = set.intersection(*all_player_clubs)
        
        if common_clubs:
            # Create a dictionary to store the filtered and unfiltered periods for each common club
            club_periods = {club: ([], []) for club in common_clubs}
    
            # Iterate through the players and collect their periods for common clubs
            for player_name in players:
                player_info = player_info_dict.get(player_name, {})
                player_career_data = player_info.get("Career", [])
    
                for date, player_club in player_career_data:
                    if player_club in common_clubs:
                        period = date.split('–')
                        start, end = int(period[0]), int(period[1]) if period[1].strip() else int(datetime.now().year)
                        club_periods[player_club][0].append((player_name, start, end))
    
            # Filter the periods that have overlapping years
            for club, (periods, _) in club_periods.items():
                filtered_periods = []
                
                for player, start, end in periods:
                    for other_player , p_start , p_end in periods:
    
                        if player != other_player and (start <= p_end and end >= p_start) and all(end >= p_start for _, p_start, p_end in periods) :
    
                            filtered_periods.append((player, start, end))
                            
                if filtered_periods:
                    filtered_periods = list(dict.fromkeys(filtered_periods))
                    club_periods[club] = (filtered_periods, periods)            

    
            # Check if all players played together in the same periods for each common club
            
            
            
            for club, (filtered_periods, _) in club_periods.items():
                common_start = max(start for _, start, _ in filtered_periods)
                
                common_end = min(end for _, _, end in filtered_periods)
               
                
                if common_start <= common_end:
                    common_periods[club] = (common_start, common_end)
    
            if common_periods:
                result = f"Common clubs for {', '.join(players)}:"
                for club, (start, end) in common_periods.items():
                    result += f"\n  - {club} ({start}–{end})"
                return(result)
            else:
                return(f"Players : {', '.join(players)} played in clubs :{common_clubs} but in different periods")
        else:
            return(f"No common clubs found for {', '.join(players)}.")
        
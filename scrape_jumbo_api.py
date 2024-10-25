import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI()

chrome_driver_path = 'chromedriver.exe'
domain = "https://www.jumbo.ae"
url = domain + "/clearance-sale"

# Set up ChromeDriver (Selenium)
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
driver = webdriver.Chrome(service=service, options=options)

# Function to scrape the website
def scrape_jumbo(url):
    try:
        # Open the webpage
        driver.get(url)

        # Wait for the product section to load
        time.sleep(10)

        # Scroll to the bottom of the page
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to the bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for the page to load
            time.sleep(2)
            
            # Calculate new scroll height and compare with last height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # If the heights are the same, break out of the loop (we're at the bottom)
                break
            
            last_height = new_height

        print("Reached the bottom of the page.")

        # Once the content is fully loaded, extract the HTML
        page_source = driver.page_source

        # Use BeautifulSoup to parse the fully loaded page content
        soup = BeautifulSoup(page_source, 'html.parser')

        return soup

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while scraping: {str(e)}")

# Function to process the data from the scraped page
def process_data(soup):
    try:
        container_div = soup.find("div", id="cms-page")
        sub_containers = container_div.find_all('div', class_="tab-slider bg-cl-secondary pt50")

        # Create a list to store the product data
        products = []

        # Looping through all the components
        for sub_container in sub_containers[1:]:
            section_divs = sub_container.find_all('div', class_="container")
            section_div = section_divs[1]
            products_div = section_div.find_all("div", class_="col-xs-6 col-sm-4 col-md-3")
            
            # Looping through all the product divs and extracting information
            for product_div in products_div:
                title = product_div.find('h3').text.strip()
                link = domain + product_div.find('a').get('href')
                current_price = product_div.find('span', class_="price-special").text.strip()
                
                try:
                    actual_price = product_div.find('span', class_="discount-price").text.strip()
                except:
                    actual_price = ''

                # Append the product data to the list in the desired format
                products.append({
                    'title': title,
                    'current_price': current_price,
                    'actual_price': actual_price,
                    'link': link
                })

        return products  # Return the list of products

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while processing data: {str(e)}")


# FastAPI route to trigger the scraping process and return the JSON response
@app.get("/scrape")
async def scrape_jumbo_data():
    try:
        soup = scrape_jumbo(url)
        data = process_data(soup)
        return JSONResponse(content=data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")


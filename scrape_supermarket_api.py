from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# FastAPI app instance
app = FastAPI()

# Domain and URL for scraping
chrome_driver_path = 'chromedriver.exe'
domain = "https://www.supermart.ae"
url = domain + "/offers-discounts"

# Set up ChromeDriver (Selenium)
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
driver = webdriver.Chrome(service=service, options=options)

def scrape_supermarket(url):
    # Open the webpage
    driver.get(url)

    # Wait for the product section to load (you may need to adjust the waiting time or element)
    time.sleep(20)

    # Scroll to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait for the page to load
        time.sleep(2)  # Adjust the sleep time depending on how fast the page loads
        
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

def process_data(soup):
    current_prices = []
    actual_prices = []
    products_names = []
    links = []

    products_wrapper_div = soup.find('div', class_="products-grid")
    
    # Check if the products wrapper is found
    if not products_wrapper_div:
        raise HTTPException(status_code=404, detail="Products section not found")

    products_div = products_wrapper_div.find_all('div', class_="js-product-miniature-wrapper")

    for product_div in products_div:
        link = product_div.find('a', class_="thumbnail product-thumbnail").get('href')
        current_price = product_div.find('span', class_="product-price").text.strip()
        actual_price = product_div.find('span', class_="regular-price").text.strip()
        product_name = product_div.find('h2', class_="product-title").text.strip()

        current_prices.append(current_price)
        actual_prices.append(actual_price)
        products_names.append(product_name)
        links.append(link)
        
    # Instead of returning a DataFrame, return a list of dictionaries
    products = [
        {
            'name': products_names[i],
            'current_price': current_prices[i],
            'actual_price': actual_prices[i],
            'link': links[i]
        }
        for i in range(len(products_names))
    ]

    return products

@app.get("/scrape")
async def scrape_supermarket_data():
    try:
        soup = scrape_supermarket(url)
        data = process_data(soup)  # This will now be a list of dictionaries
        return JSONResponse(content=data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

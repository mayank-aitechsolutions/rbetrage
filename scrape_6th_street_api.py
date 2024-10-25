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
domain = "https://en-ae.6thstreet.com"
url = domain + "/all-bestsellers.html"

# Set up ChromeDriver (Selenium)
service = Service(chrome_driver_path)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
driver = webdriver.Chrome(service=service, options=options)

def scrape_street(url):
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
    links = []
    products_names = []
    products_desc = []
    current_prices = []

    # Locate the main product items container
    product_item_div = soup.find('ul', class_="ProductItems")
    
    # Check if the product section is found
    if not product_item_div:
        raise HTTPException(status_code=404, detail="Product section not found")

    product_items = product_item_div.find_all('li', class_="ProductItem")

    # Looping through the products
    for product_item in product_items:
        # Fetching url of the product
        product_url = product_item.find('a', class_="ProductItem-ImgBlock").get('href')
        url = domain + product_url

        # Fetching product descriptions
        product_desc_div = product_item.find('div', class_="product-description-block")
        product_name = product_desc_div.find('h2', class_="ProductItem-Brand").text.strip()
        product_desc = product_desc_div.find('p', class_="ProductItem-Title").text.strip()
        product_price = product_desc_div.find('div', class_="Price").text.strip()

        # Appending all the values in the lists
        links.append(url)
        products_names.append(product_name)
        products_desc.append(product_desc)
        current_prices.append(product_price)

    # Instead of returning a DataFrame, return a list of dictionaries
    products = [
        {
            'name': products_names[i],
            'description': products_desc[i],
            'current_price': current_prices[i],
            'link': links[i]
        }
        for i in range(len(products_names))
    ]

    return products

@app.get("/scrape")
async def scrape_6thstreet_data():
    try:
        soup = scrape_street(url)
        data = process_data(soup)  # This will now be a list of dictionaries
        return JSONResponse(content=data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

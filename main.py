import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
DOCUMENT_URL = 'https://www.scribd.com/document/631408297/Mathematical-Methods-by-SM-Yusuf-com-pdf' 
# ---------------------

print("Launching browser...")
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # Uncomment to run without opening a visible browser window
driver = webdriver.Chrome(options=options)

image_urls = []

try:
    driver.get(DOCUMENT_URL)
    print("Page loaded. Starting incremental scroll to catch EVERY page...")
    
    # Give the initial page a moment to load
    time.sleep(2)

    # Get the height of the browser window
    viewport_height = driver.execute_script("return window.innerHeight")
    current_scroll_position = 0

    while True:
        # Scroll down by one screen height
        current_scroll_position += viewport_height
        driver.execute_script(f"window.scrollTo(0, {current_scroll_position});")
        
        # Pause briefly to let the Intersection Observer trigger the image load
        time.sleep(0.5) 
        
        # Check the total height of the document
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # If our scroll position has reached or passed the bottom
        if current_scroll_position >= total_height:
            # Wait a second and check if the page dynamically expanded
            time.sleep(1)
            new_total_height = driver.execute_script("return document.body.scrollHeight")
            if current_scroll_position >= new_total_height:
                print("Reached the true bottom of the document!")
                break

    print("Extracting image URLs...")
    image_elements = driver.find_elements(By.CLASS_NAME, 'absimg')
    
    for img in image_elements:
        url = img.get_attribute('src') or img.get_attribute('orig')
        if url and 'scribd' in url:
            # Force secure assets domain
            url = url.replace('http://html.scribd.com', 'https://html.scribdassets.com')
            # Add to list if it's not already there (preserves order and removes duplicates)
            if url not in image_urls:
                image_urls.append(url)

    print(f"Found {len(image_urls)} unique pages!")

finally:
    # Always close the browser, even if an error occurs
    driver.quit()

# --- DOWNLOAD & STITCH INTO PDF ---
if image_urls:
    images = []
    for i, url in enumerate(image_urls):
        print(f"Downloading page {i + 1} of {len(image_urls)}...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content)).convert('RGB')
                images.append(img)
            else:
                print(f"Failed to download page {i + 1} - Status {response.status_code}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    if images:
        output_filename = "Full_Scraped_Document.pdf"
        print(f"\nStitching {len(images)} images into {output_filename}...")
        
        images[0].save(
            output_filename,
            save_all=True,
            append_images=images[1:]
        )
        print("PDF successfully generated! You got all the pages.")
else:
    print("No images were found. Double check the URL.")
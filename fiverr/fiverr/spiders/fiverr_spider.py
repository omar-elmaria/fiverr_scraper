# Load the packages
import scrapy
from scraper_api import ScraperAPIClient
from dotenv import load_dotenv
import os
import re

# Load the environment variables
load_dotenv()

# Get the scraper API key
client = ScraperAPIClient(api_key = os.getenv("SCRAPER_API_KEY")) 

# Define the dictionary that contains the custom settings of the spiders. This will be used in all other spiders
custom_settings_dict = {
    "FEED_EXPORT_ENCODING": "utf-8", # UTF-8 deals with all types of characters
    "RETRY_TIMES": 5, # Retry failed requests up to 5 times (5 instead of 3 because Fiverr is a hard site to scrape)
    "AUTOTHROTTLE_ENABLED": False, # Disables the AutoThrottle extension (recommended to be used with proxy services unless the website is tough to crawl)
    "RANDOMIZE_DOWNLOAD_DELAY": False, # If enabled, Scrapy will wait a random amount of time (between 0.5 * DOWNLOAD_DELAY and 1.5 * DOWNLOAD_DELAY) while fetching requests from the same website
    "CONCURRENT_REQUESTS": 5, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed by the Scrapy downloader
    "DOWNLOAD_TIMEOUT": 60 # Setting the timeout parameter to 60 seconds as per the ScraperAPI documentation
}

# Define the spider class
class FiverrSpiderSync(scrapy.Spider):
    name = 'fiverr_spider_sync' # Name of the spider
    allowed_domains = ['fiverr.com'] # Allowed domains to crawl
    custom_settings = custom_settings_dict # Standard custom settings of the spider
    custom_settings["FEEDS"] = {"gig_data_sync.json":{"format": "json", "overwrite": True}} # Export to a JSON file with an overwrite functionality
    master_url = "https://www.fiverr.com/categories/data/data-processing/data-mining-scraping?source=category_filters"

    def start_requests(self):
        yield scrapy.Request(
            client.scrapyGet(url = FiverrSpiderSync.master_url, country_code = "de", render = True, premium = True), # Must add the premium proxy parameter because Fiverr is hard to scrape
            callback = self.parse,
            dont_filter = True
        )
    
    def parse(self, response):
        sellers = response.xpath("//div[contains(@class, 'gig-wrapper')]")
        for gig in sellers:
            # Some gigs are without reviews, so we need to handle that case
            try:
                gig_rating = float(gig.css("div.content-info > div.rating-wrapper").xpath("./span[contains(@class, 'gig-rating')]/text()").get())
            except TypeError:
                gig_rating = None
            
            try:
                num_reviews = gig.css("div.content-info > div.rating-wrapper").xpath("./span[contains(@class, 'gig-rating')]/span/text()").get().replace("(", "").replace(")", "")
                # Num reviews should be integer, but some gigs have num_reviews in a string format (e.g., 1k+). Change any num_reviews with a string format to integer
                if num_reviews == "1k+":
                    num_reviews = "1000" # Assume the seller has 1000 reviews so that we can change the format to integer later
                else:
                    pass

                # Change the format of num_reviews to integer
                num_reviews = int(num_reviews)
            except (TypeError, AttributeError):
                num_reviews = None

            # Price points before and after the decimal point are shown separately. We treat this case here  
            gig_starting_price_before_decimal = re.findall(pattern = "\d+", string = gig.css("footer > div.price-wrapper > a > span::text").get())[0]
            gig_starting_price_after_decimal = gig.css("footer > div.price-wrapper > a > span > sup::text").get()
            gig_starting_price = float(gig_starting_price_before_decimal + "." + gig_starting_price_after_decimal)

            # Create the data dictionary
            data_dict = {
                "seller_name": gig.xpath("./div[contains(@class, 'seller-info')]").css("div.inner-wrapper > div.seller-identifiers > div.seller-name-and-country > div.seller-name > a::text").get(),
                "seller_url": "https://www.fiverr.com" + gig.css("h3 > a::attr(href)").get(),
                "seller_level": gig.xpath("./div[contains(@class, 'seller-info')]").css("div.inner-wrapper > div.seller-identifiers").xpath("./span[contains(@class, 'level')]//span/text()").get(),
                "gig_title": gig.css("h3 > a::attr(title)").get(),
                "gig_rating": gig_rating,
                "num_reviews": num_reviews,
                "gig_starting_price": gig_starting_price
            }

            # Return the data
            yield data_dict     

        # Add pagination logic (synchronous)
        next_page = response.css("li.pagination-arrows > a::attr(href)").get()
        current_page = response.css("li.page-number.active-page > span::text").get()
        if next_page is not None and int(current_page) <= 10:
            yield scrapy.Request(
                client.scrapyGet(url = next_page, country_code = "de", render = True),
                callback = self.parse,
                dont_filter = True
            )
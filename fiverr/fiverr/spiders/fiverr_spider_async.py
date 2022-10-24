# Load the packages
import scrapy
import re
from fiverr.spiders.fiverr_spider_sync import custom_settings_dict
from fiverr.spiders.fiverr_spider_sync import client

# Define the spider class
class FiverrSpiderAsync(scrapy.Spider):
    name = 'fiverr_spider_async' # Name of the spider
    allowed_domains = ['fiverr.com'] # Allowed domains to crawl
    custom_settings = custom_settings_dict # Standard custom settings of the spider
    custom_settings["FEEDS"] = {"gig_data_async.json":{"format": "json", "overwrite": True}} # Export to a JSON file with an overwrite functionality
    master_url = "https://www.fiverr.com/categories/data/data-processing/data-mining-scraping?source=pagination&page={}&offset=-16"

    def start_requests(self):
        for i in range(1,10):
            yield scrapy.Request(
                client.scrapyGet(url = FiverrSpiderAsync.master_url.format(i), country_code = "de", render = True, premium = True),
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
            except:
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

# fiverr_scraper
This repo contains a Python script that crawls gig information from the "Data Processing" category on Fiverr

# Objective of the Project
The aim of this project was to scrape the "Data Processing" category on Fiverr and extract **gig information** from the listing page.

![image](https://user-images.githubusercontent.com/98691360/198831106-e30af12c-5275-4740-81f9-8f22da3fbc6a.png)

These are the fields that could be extracted from the listing page:
- seller_name
- gig_url
- seller_level (if it exists)
- gig_title
- gig rating (if it exists)
- number_of_reviews (if it exists)
- gig_starting_price

# Scraping Methodology
I used the ```scrapy``` framework in Python to crawl this information from the **first ten pages** under the "Data Processing" category. Fiverr is a difficult website to scrape and employs

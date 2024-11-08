"""
This example run script shows how to run the Glassdoor.com scraper defined in ./glassdoor.py
It scrapes job, review and salary (TODO OVERVIEW?) data and saves it to ./results/

To run this script set the env variable $SCRAPFLY_KEY with your scrapfly API key:
$ export $SCRAPFLY_KEY="your key from https://scrapfly.io/dashboard"
"""
import asyncio
import json
from pathlib import Path
import glassdoor
from glassdoor import find_companies

output = Path(__file__).parent / "results"
output.mkdir(exist_ok=True)

async def run():
    # enable scrapfly cache for basic use
    glassdoor.BASE_CONFIG["cache"] = True

    print("running Glassdoor scrape and saving results to ./results directory")
    
    company = await glassdoor.find_companies("ebay")    
    if company:
        url = "https://www.glassdoor.sg/Reviews/Impinj-Reviews-E14174.htm"
        result_reviews = await glassdoor.scrape_reviews(url, max_pages=1)
        output.joinpath("PI_reviews.json").write_text(json.dumps(result_reviews, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())

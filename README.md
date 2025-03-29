# About

This project investigates the relationship between toxic leadership traits and their impact on financial performance, public perception, and reported misconduct among Fortune 500 companies. Developed in collaboration with a McKinsey specialist, the project supports a PhD dissertation by applying sentiment analysis and financial modeling to data sources such as SEC 10-K filings and Glassdoor reviews. Using Python, NumPy, SQL, and REST APIs, the project streamlines a data pipeline that clusters keywords from corporate filings and employee reviews to quantify Dark Triad personality traits—narcissism, Machiavellianism, and psychopathy—across leadership narratives.

The project draws data from the following sources:

SEC 10-K/Q Filings: Scraped and parsed using the SEC-API and custom logic to extract specific sections like Forward-Looking Statements (FLS) and Item 7 ("Management’s Discussion and Analysis").

Glassdoor: Employee-submitted company reviews are used to quantify public sentiment and possible red flags in workplace culture.

The ultimate goal is to surface patterns between leadership communication, financial trajectory, and internal company culture, providing a data-driven lens into leadership accountability in high-profile firms.

# Challenges

1. Extracting 10-K Filings with Forward-Looking Statements (FLS)
Challenge: Struggled to accurately extract the full FLS section due to inconsistent document structure.

Solution: Initially tried scraping between “Table of Contents” and “Section 1”, but realized the misunderstanding was with targeting the FLS notes instead of the actual FLS passage. Resolved this by using the SEC-API to directly grab the FLS content and Item 7. Additional text cleaning was done to remove broken characters before LIWC processing.

2. Glassdoor Ratings Scraping
Challenge: Bypassing Glassdoor’s aggressive anti-scraping protections.

Solution: Attempted various technical methods (IP rotation, headless browsers, session spoofing). Eventually adopted a paid scraping service that automated proxy rotation and session management, enabling the successful extraction of Glassdoor data for the top 100 market cap companies.

3. Financial Data Table Extraction
Challenge: SEC-API lacked built-in support for pulling financial table values, and free APIs with 10+ years of historical financials were either unreliable or extremely expensive.

Solution: Parsed over 2,400 locally stored filings, extracting financial sections manually. The major hurdle was inconsistent labeling of fields like “Revenue” across companies (“Total Revenue”, “Interest Income”, “Gas Revenue”, etc.). Built a custom dictionary to standardize and map all relevant terms, and validated outputs with external financial sources to ensure accuracy.

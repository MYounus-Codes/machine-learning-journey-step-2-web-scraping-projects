import csv

import requests
from bs4 import BeautifulSoup


url = "https://quotes.toscrape.com/?utm_source=chatgpt.com"
soup = BeautifulSoup(requests.get(url).text, "html.parser")

rows = []

seen_authors = set()
quotes = soup.find_all("div", class_="quote")

for quote in quotes:
    author_link = quote.find("a")
    author = quote.find("small", class_="author").get_text(strip=True)
    about_page_url = f"https://quotes.toscrape.com{author_link.get('href')}"

    # if about_page_url in seen_authors:
    #     continue

    seen_authors.add(about_page_url)
    about_page_soup = BeautifulSoup(requests.get(about_page_url).text, "html.parser")
    about_text = about_page_soup.find("div", class_="author-description").get_text(strip=True)

    rows.append(
        {
            "Author": author,
            "About": about_text,
        }
    )

with open("authors_about.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["Author", "About"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} authors' about info to authors_about.csv")
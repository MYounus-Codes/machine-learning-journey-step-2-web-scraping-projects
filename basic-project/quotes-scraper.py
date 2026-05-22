import csv

import requests
from bs4 import BeautifulSoup


url = "https://quotes.toscrape.com/?utm_source=chatgpt.com"
soup = BeautifulSoup(requests.get(url).text, "html.parser")

rows = []
quotes = soup.find_all("div", class_="quote")

for quote in quotes:
    quote_text = quote.find("span", class_="text").get_text(strip=True)
    author = quote.find("small", class_="author").get_text(strip=True)
    tags = [tag.get_text(strip=True) for tag in quote.find_all("a", class_="tag")]

    rows.append(
        {
            "Author": author,
            "Quotes": quote_text,
            "Tag": ", ".join(tags),
        }
    )

with open("quotes.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["Author", "Quotes", "Tag"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} quotes to quotes.csv")

import csv

import requests
from bs4 import BeautifulSoup

rows = []
page_number = 1

while True:
    if page_number == 1:
        url = "https://books.toscrape.com/?utm_source=chatgpt.com"
    else:
        url = f"https://books.toscrape.com/catalogue/page-{page_number}.html"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("li", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3")

    if not books:
        break

    for book in books:
        title = book.find("h3").find("a")["title"]
        price = book.find("p", class_="price_color").get_text(strip=True)
        availability = book.find("p", class_="instock availability").get_text(strip=True)

        rows.append(
            {
                "Page": page_number,
                "Title": title,
                "Price": price,
                "Availability": availability,
            }
        )

    page_number += 1

with open("books.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["Page", "Title", "Price", "Availability"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} books to books.csv")
    
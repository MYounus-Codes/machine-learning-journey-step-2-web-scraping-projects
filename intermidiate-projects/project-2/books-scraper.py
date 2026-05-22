import csv
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

rows = []
page_number = 1
request_timeout = 30

while True:
    if page_number == 1:
        url = "https://books.toscrape.com/?utm_source=chatgpt.com"
    else:
        url = f"https://books.toscrape.com/catalogue/page-{page_number}.html"

    response = requests.get(url, timeout=request_timeout)
    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("li", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3")

    if not books:
        break

    for book in books:
        image = book.find("img")
        title = book.find("h3").find("a")["title"]
        price = book.find("p", class_="price_color").get_text(strip=True)
        availability = book.find("p", class_="instock availability").get_text(strip=True)
        image_url = urljoin("https://books.toscrape.com/", image.get("src")) if image else ""

        rows.append(
            {
                "Page": page_number,
                "Title": title,
                "Price": price,
                "Availability": availability,
                "Image": image_url,
            }
        )

    page_number += 1

with open("books.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["Page", "Title", "Price", "Availability", "Image"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} books to books.csv")
    
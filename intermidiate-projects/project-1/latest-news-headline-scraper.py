import csv

import requests
from bs4 import BeautifulSoup


url = "https://www.bbc.com/news?utm_source=chatgpt.com"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

rows = []
seen_links = set()

news_tags = soup.find_all("span", attrs={"data-testid": "card-metadata-tag"})

for tag in news_tags:
    category = tag.get_text(strip=True)
    card = tag.find_parent(["a", "div"], attrs={"data-testid": "internal-link"}) or tag.find_parent(
        "div", class_=True
    )

    if not card:
        continue

    headline_el = card.find(["h1", "h2", "h3", "h4"], attrs={"data-testid": "card-headline"})
    headline = headline_el.get_text(strip=True) if headline_el else "Headline not found"

    link_el = card if card.name == "a" else card.find("a", href=True)
    href = link_el.get("href") if link_el else None
    if not href:
        continue

    full_link = href if href.startswith("http") else f"https://www.bbc.com{href}"
    if full_link in seen_links:
        continue

    seen_links.add(full_link)
    rows.append({"Headline": headline, "Category": category, "Link": full_link})

with open("latest_news.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["Headline", "Category", "Link"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} news links to latest_news.csv")


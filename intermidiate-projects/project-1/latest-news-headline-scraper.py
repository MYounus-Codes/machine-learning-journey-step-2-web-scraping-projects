import csv
from urllib.parse import urljoin

import requests
from lxml import html


url = "https://www.bbc.com/news?utm_source=chatgpt.com"
response = requests.get(url)
tree = html.fromstring(response.content)

rows = []
seen_links = set()

for article_link in tree.xpath("//a[contains(@href, '/news/articles/')]"):
    href = article_link.get("href")
    if not href:
        continue

    full_link = urljoin("https://www.bbc.com", href)
    if full_link in seen_links:
        continue

    headline_parts = article_link.xpath(".//h2//text()")
    headline = " ".join(part.strip() for part in headline_parts if part.strip())
    if not headline:
        headline = article_link.text_content().strip()
    if not headline:
        continue

    seen_links.add(full_link)
    rows.append({"Headline": headline, "Link": full_link})

with open("latest_news.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["Headline", "Link"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} news links to latest_news.csv")


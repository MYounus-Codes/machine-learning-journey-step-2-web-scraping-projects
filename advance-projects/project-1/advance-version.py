import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://weworkremotely.com"
LISTING_URL = "https://weworkremotely.com/?utm_source=chatgpt.com"
OUTPUT_FILE = Path(__file__).with_name("weworkremotely_jobs.csv")
HEADERS = {
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
		"AppleWebKit/537.36 (KHTML, like Gecko) "
		"Chrome/124.0.0.0 Safari/537.36"
	)
}


def fetch_soup(session: requests.Session, url: str) -> BeautifulSoup:
	response = session.get(url, headers=HEADERS, timeout=30)
	response.raise_for_status()
	return BeautifulSoup(response.text, "html.parser")


def clean_text(element) -> str:
	return element.get_text(" ", strip=True) if element else ""


def first_text(soup: BeautifulSoup, selector: str) -> str:
	return clean_text(soup.select_one(selector))


def first_attr(soup: BeautifulSoup, selector: str, attribute: str) -> str:
	element = soup.select_one(selector)
	if not element:
		return ""
	value = element.get(attribute, "")
	if attribute == "href" and value:
		return urljoin(BASE_URL, value)
	return value


def extract_job_details(session: requests.Session, job_url: str) -> dict[str, str]:
	soup = fetch_soup(session, job_url)
	details = soup.select_one("div#job-details")

	description_text = clean_text(details)
	skill_items = []
	if details:
		skill_items = [clean_text(item) for item in details.select("li") if clean_text(item)]

	return {
		"job_url": job_url,
		"job_title": first_text(soup, "div.listing-header-container h1"),
		"company_name": first_text(soup, ".lis-container__header__hero__company-info a"),
		"company_website": first_attr(soup, ".lis-container__header__hero__company-info a", "href"),
		"company_logo": first_attr(soup, ".lis-container__header__hero__company-logo img", "src"),
		"post_date": first_attr(soup, "time", "datetime") or first_text(soup, "time"),
		"job_type": first_text(soup, ".listing-tag"),
		"category": first_text(soup, ".listing-header-container a[href*='/categories/']"),
		"region": first_text(soup, ".listing-header-container .region") or first_text(soup, ".region"),
		"job_description": description_text,
		"skills": " | ".join(skill_items),
		"apply_link": first_attr(soup, "#apply-button", "href"),
	}


def main() -> None:
	session = requests.Session()
	listing_soup = fetch_soup(session, LISTING_URL)

	job_links = []
	seen_links = set()
	for anchor in listing_soup.select("section.jobs li > a"):
		href = anchor.get("href")
		if not href:
			continue
		job_url = urljoin(BASE_URL, href)
		if "/remote-jobs/" not in job_url:
			continue
		if job_url in seen_links:
			continue
		seen_links.add(job_url)
		job_links.append(job_url)

	fieldnames = [
		"job_url",
		"job_title",
		"company_name",
		"company_website",
		"company_logo",
		"post_date",
		"job_type",
		"category",
		"region",
		"job_description",
		"skills",
		"apply_link",
	]

	with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(file, fieldnames=fieldnames)
		writer.writeheader()

		for index, job_url in enumerate(job_links, start=1):
			try:
				job_data = extract_job_details(session, job_url)
				writer.writerow(job_data)
				print(f"[{index}/{len(job_links)}] Saved {job_data['job_title'] or job_url}")
			except requests.RequestException as exc:
				print(f"[{index}/{len(job_links)}] Skipped {job_url}: {exc}")
			time.sleep(1.5)

	print(f"Saved {len(job_links)} jobs to {OUTPUT_FILE.name}")


if __name__ == "__main__":
	main()

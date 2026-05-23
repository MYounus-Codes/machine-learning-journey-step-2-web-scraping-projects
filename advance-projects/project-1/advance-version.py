import csv
import json
from html import unescape
import re
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


def parse_json_ld(soup: BeautifulSoup) -> list[dict]:
	items = []
	for script in soup.select('script[type="application/ld+json"]'):
		if not script.string:
			continue
		try:
			data = json.loads(script.string)
		except json.JSONDecodeError:
			continue
		if isinstance(data, list):
			items.extend(item for item in data if isinstance(item, dict))
		elif isinstance(data, dict):
			items.append(data)
	return items


def job_posting_data(soup: BeautifulSoup) -> dict:
	for item in parse_json_ld(soup):
		if item.get("@type") == "JobPosting":
			return item
	return {}


def extract_style_url(value: str) -> str:
	match = re.search(r"url\(['\"]?(.*?)['\"]?\)", value or "")
	return match.group(1) if match else ""


def normalize_company_website(value) -> str:
	if isinstance(value, list):
		value = value[0] if value else ""
	if not value:
		return ""
	website = str(value)
	return "" if "weworkremotely.com" in website else website


def extract_job_links(listing_soup: BeautifulSoup) -> list[str]:
	job_links = []
	seen_links = set()
	for anchor in listing_soup.select("section.jobs a.listing-link--unlocked[href^='/remote-jobs/']"):
		href = anchor.get("href")
		if not href:
			continue
		job_url = urljoin(BASE_URL, href)
		if job_url in seen_links:
			continue
		seen_links.add(job_url)
		job_links.append(job_url)
	return job_links


def parse_job_details(soup: BeautifulSoup, job_url: str) -> dict[str, str]:
	job_data = job_posting_data(soup)
	company_data = job_data.get("hiringOrganization") if isinstance(job_data.get("hiringOrganization"), dict) else {}
	description_html = soup.select_one(".lis-container__job__content__description")
	skills = [clean_text(item) for item in soup.select(".lis-container__job__sidebar__job-about__list__item .boxes .box--multi.box--blue") if clean_text(item)]
	company_logo_style = first_attr(soup, ".lis-container__header__hero__company-logo", "style")
	company_logo = job_data.get("image", "") or extract_style_url(company_logo_style) or first_attr(soup, 'meta[property="og:image"]', "content")
	company_website = normalize_company_website(company_data.get("sameAs", "") or company_data.get("url", "") or job_data.get("url", ""))

	return {
		"job_url": job_url,
		"job_title": unescape(str(job_data.get("title", "") or first_text(soup, ".lis-container__header__hero__company-info__title"))),
		"company_name": str(company_data.get("name", "") or first_text(soup, ".lis-container__job__sidebar__companyDetails__info__title h3")),
		"company_website": company_website,
		"company_logo": str(company_logo),
		"post_date": str(job_data.get("datePosted", "") or first_text(soup, ".lis-container__header__hero__company-info__icons__item span") or first_text(soup, ".lis-container__job__sidebar__job-about__list__item span")),
		"job_type": str(job_data.get("employmentType", "") or first_text(soup, ".box--jobType")),
		"category": str(job_data.get("occupationalCategory", "") or first_text(soup, ".lis-container__job__sidebar__job-about__list__item .box--blue")),
		"region": first_text(soup, ".box--region"),
		"job_description": clean_text(description_html),
		"skills": " | ".join(skills),
		"apply_link": first_attr(soup, "#job-cta-alt", "href") or first_attr(soup, "#apply-button", "href"),
	}


def extract_job_details(session: requests.Session, job_url: str) -> dict[str, str]:
	soup = fetch_soup(session, job_url)
	return parse_job_details(soup, job_url)


def main() -> None:
	session = requests.Session()
	listing_soup = fetch_soup(session, LISTING_URL)
	job_links = extract_job_links(listing_soup)

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

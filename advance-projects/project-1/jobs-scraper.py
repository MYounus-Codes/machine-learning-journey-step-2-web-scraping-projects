import csv

import requests
from bs4 import BeautifulSoup


url = "https://weworkremotely.com/?utm_source=chatgpt.com"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# I wrote this code while testing the scraper, but I will comment it out to avoid cluttering the output. You can uncomment it if you want to see the scraped data in the console.

# print("Job Titles:")
# for job in soup.find_all("span", class_="new-listing__header__title__text"):
#     print(job.text.strip()) 

# print("\nCompany Names:")
# for company in soup.find_all("p", class_="new-listing__company-name"):
#     print(company.text.strip())

# print("\nJob Categories:")
# for category in soup.find_all("div", class_="new-listing__categories"):
#     print(category.text.strip())



# now saving the data to a CSV file
with open("weworkremotely_jobs.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Job Title", "Company Name", "Job Category"])
    
    for job, company, category in zip(
        soup.find_all("span", class_="new-listing__header__title__text"),
        soup.find_all("p", class_="new-listing__company-name"),
        soup.find_all("div", class_="new-listing__categories")
    ):
        writer.writerow([job.text.strip(), company.text.strip(), category.text.strip()])

print("\nData has been saved to weworkremotely_jobs.csv")


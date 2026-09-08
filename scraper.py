# Fetches listings from Salon Apprentice and returns them in a usable form.
# Called by daily_alert.py.

import re
import urllib.parse

from bs4 import BeautifulSoup
import requests

BASE = 'https://www.salonapprentice.com/free-salon-services/SalonApprentice_list.php?q=(city~equals~'

CITIES = [
    "Atlanta",
    "Austin",
    "Boston",
    "Charlotte, NC",
    "Chicago",
    "Columbus, OH",
    "Dallas",
    "Denver",
    "Houston, TX",
    "Jersey City, NJ",
    "London (England)",
    "Los Angeles",
    "Miami",
    "Minneapolis / St Paul",
    "Montréal (Québec, Canada)",
    "Nashville, TN",
    "New York",
    "Philadelphia",
    "San Diego, CA",
    "San Francisco",
    "San Jose, CA",
    "Scottsdale, AZ",
    "Seattle",
    "St. Louis",
    "Sydney (Australia)",
    "Toronto (Ontario, Canada)",
    "Vancouver (British Columbia, Canada)",
    "Washington DC",
    "las Vegas",
]


def get_soup(url, header_info=''):
    headers = {'user-agent' : header_info}
    req = requests.get(url, headers=headers)

    src = req.text
    soup = BeautifulSoup(src, 'html.parser')

    return soup


def get_ads(url):
    soup = get_soup(url)

    rows = soup.find_all("tr", class_="r-gridrow")

    ads = []

    for row in rows:
        link = row.find("a", href=re.compile(r"editid1=\d+"))
        edit_id = re.search(r"editid1=(\d+)", link["href"]).group(1)
        title = row.find(attrs={"data-field": "ad_title"}).get_text(strip=True)
        service_type = row.find(attrs={"data-field": "service_type"}).get_text(strip=True)
        fee = row.find(attrs={"data-field": "fee"}).get_text(strip=True)
        salon = row.find(attrs={"data-field": "salon"}).get_text(strip=True)
        neighborhood = row.find(attrs={"data-field": "neighborhood"}).get_text(strip=True)
        next_service_date = row.find(attrs={"data-field": "service_date"}).get_text(strip=True)

        ad = {
            "edit_id": edit_id,
            "title": title,
            "service_type": service_type,
            "fee": fee,
            "salon": salon,
            "neighborhood": neighborhood,
            "next_service_date": next_service_date,
        }

        ads.append(ad)

    return ads


def loop_cities():
    all_ads = []

    for city in CITIES:
        city = urllib.parse.quote(city)
        url = BASE + city + ')'
        all_ads.extend(get_ads(url))

    return all_ads
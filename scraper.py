# Fetches listings from Salon Apprentice and returns them in a usable form.
# Called by daily_alert.py.

def scraper(url, header_info=''):
    # Scrape website
    headers = {'user-agent' : header_info}
    req = requests.get(url, headers=headers)

    # Convert
    src = req.text
    soup = BeautifulSoup(src, 'html.parser')

    return soup
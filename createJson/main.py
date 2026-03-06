import requests
from bs4 import BeautifulSoup
import re
import json
import time

URL = "https://www.febcentral.ca/ChurchbyName"
GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "feb-church-scraper"
}

# Canadian postal code
POSTAL = r"[A-Z]\d[A-Z]\s?\d[A-Z]\d"

def is_address(line):
    """
    Detect a valid street address line
    """
    if re.search(POSTAL, line) and re.search(r"\d", line):
        return True
    return False


def geocode(address):

    params = {
        "q": address + ", Canada",
        "format": "json",
        "limit": 1
    }

    r = requests.get(GEOCODE_URL, params=params, headers=HEADERS)

    if r.status_code != 200:
        return None, None

    data = r.json()

    if not data:
        return None, None

    return float(data[0]["lat"]), float(data[0]["lon"])


def parse_churches():

    r = requests.get(URL)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    churches = []

    for h3 in soup.find_all("h3"):

        name = h3.get_text(strip=True)

        website = None
        a = h3.find("a")
        if a:
            website = a.get("href")

        phone = None
        address = None

        node = h3.next_sibling

        while node:

            if getattr(node, "name", None) == "h3":
                break

            text = ""

            if hasattr(node, "get_text"):
                text = node.get_text(" ", strip=True)
            else:
                text = str(node).strip()

            if not text:
                node = node.next_sibling
                continue

            # phone
            m = re.search(r"\[ph\]\s*([\d\-]+)", text)
            if m:
                phone = m.group(1)

            # address
            if is_address(text):
                address = text.replace("Mtg at:", "").replace("c/o", "").strip()
                break

            node = node.next_sibling

        churches.append({
            "name": name,
            "website": website,
            "phone": phone,
            "address": address
        })

    return churches


def add_coordinates(churches):

    addresses = {c["address"] for c in churches if c["address"]}

    cache = {}

    print("Geocoding", len(addresses), "unique addresses")

    for i, addr in enumerate(addresses, start=1):

        lat, lon = geocode(addr)

        cache[addr] = (lat, lon)

        print(i, addr, lat, lon)

        time.sleep(1)

    for c in churches:
        lat, lon = cache.get(c["address"], (None, None))
        c["latitude"] = lat
        c["longitude"] = lon

    return churches


if __name__ == "__main__":

    churches = parse_churches()

    churches = add_coordinates(churches)

    with open("feb_churches.json", "w") as f:
        json.dump(churches, f, indent=2)

    print("Done:", len(churches))

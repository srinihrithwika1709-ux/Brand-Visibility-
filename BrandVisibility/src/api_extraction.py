import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SERPAPI_KEY")


def fetch_google_shopping(keyword):

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_shopping",
        "q": keyword,
        "api_key": API_KEY,
        "gl": "us",
        "hl": "en"
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":

    keyword = "iphone"

    data = fetch_google_shopping(keyword)

    print("API request successful")

    print("Number of results:",
          len(data.get("shopping_results", [])))

    with open(
        "data/raw/api_raw_data.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )

    print("Raw API data saved successfully")
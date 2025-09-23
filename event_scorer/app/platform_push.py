import requests
import os

API_KEY = os.getenv("PLATFORM_API_KEY", "API_KEY not set")
ENDPOINT = os.getenv("PLATFORM_ENDPOINT", "PLATFORM_ENDPOINT not set")

def platform_push(payload):
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "x-api-key": API_KEY
    }

    transformed = payload.apply(transform_row, axis=1).tolist()

    # Temporary filter as platform does not accept these sites
    unsupported_sites = ["familiejournal.dk", "svenskdam.se", "udeoghjemme.dk"]
    filtered_payload = [
        row for row in transformed
        if row["audience_site"] not in unsupported_sites
    ]

    response = requests.post(ENDPOINT, json=filtered_payload, headers=headers)

    print(f"AI Platform Status Code: {response.status_code}")

    return payload


def transform_row(row):
    return {
        "id": row["id"],
        "entities": [{"type": "PERSON", "name": e} for e in row["entities"]],
        "pageview_range": {
            "min": row["pageview_range"][0],
            "max": row["pageview_range"][1]
        },
        "potential_quartile": str(int(row["potential_quartile"])),
        "relevance": row["score"],
        "audience_site": row["site_domain"]
    }

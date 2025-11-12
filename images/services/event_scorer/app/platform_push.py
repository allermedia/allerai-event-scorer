import requests
import os
import logging

logger = logging.getLogger(__name__)

API_KEY = os.getenv("PLATFORM_API_KEY", "API_KEY not set")
ENDPOINT = os.getenv("PLATFORM_ENDPOINT", "PLATFORM_ENDPOINT not set")

def platform_push(payload):
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "x-api-key": API_KEY
    }

    transformed = payload.apply(transform_row, axis=1).tolist()

    # Temporary filter as platform does not accept these sites
    supported_sites = [
        "allas.se",
        "billedbladet.dk",
        "dagbladet.no",
        "elbil24.no",
        "elle.se",
        "femina.dk",
        "femina.se",
        "hant.se",
        "isabellas.dk",
        "kk.no",
        "mabra.com",
        "residencemagazine.se",
        "seher.no",
        "seiska.fi",
        "seoghoer.dk",
        "sol.no",
        "vielskerserier.dk"
    ]
    filtered_payload = [
        row for row in transformed
        if row["audience_site"] in supported_sites
    ]

    response = requests.post(ENDPOINT, json=filtered_payload, headers=headers)
    logger.info(f"AI Platform Status Code: {response.status_code}")
    logger.info(f"AI Platform Response Content: {response.content.decode('utf-8')}")

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

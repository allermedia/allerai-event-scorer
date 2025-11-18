import requests
import os

PLATFORM_API_KEY = os.environ.get('PLATFORM_API_KEY', 'Missing environment variable')
PLATFORM_TRAFFIC_ENDPOINT = os.environ.get('PLATFORM_TRAFFIC_ENDPOINT', 'Missing environment variable')

class PlatformService:
    def init(self):
        pass

    def post_article_traffic_to_platform(data, url):
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "x-api-key": PLATFORM_API_KEY
        }

        response = requests.post(PLATFORM_TRAFFIC_ENDPOINT, json=data, headers=headers)

        print(f"AI Platform Status Code: {response.status_code}")
        print(f"AI Platform Response Content: {response.content.decode('utf-8')}")  

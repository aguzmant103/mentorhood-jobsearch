import requests
import time
from datetime import datetime

def check_health(url):
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            print(f"[{datetime.now()}] Service is healthy: {response.json()}")
        else:
            print(f"[{datetime.now()}] Service returned status code: {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now()}] Error checking health: {str(e)}")

if __name__ == "__main__":
    url = "https://mentorhood-jobsearch-production.up.railway.app/"  # Your actual Railway URL
    while True:
        check_health(url)
        time.sleep(60)  # Check every minute 
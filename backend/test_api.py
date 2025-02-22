import requests

def test_endpoints(base_url):
    endpoints = [
        "/",
        "/health",
        "/test/jobs"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"\nTesting {endpoint}:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error testing {endpoint}: {str(e)}")

if __name__ == "__main__":
    base_url = "https://mentorhood-jobsearch-production.up.railway.app"
    test_endpoints(base_url) 
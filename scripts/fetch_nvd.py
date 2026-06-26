import requests, json, os
from dotenv import load_dotenv

load_dotenv()

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OUTPUT_PATH = "data/cve_sample.json"

def fetch_cves(results_per_page=50, start_index=0):
    params = {
        "resultsPerPage": results_per_page,
        "startIndex": start_index,
        "cvssV3Severity": "CRITICAL"  # Sadece kritik CVE'ler
    }
    headers = {}
    api_key = os.getenv("NVD_API_KEY")
    if api_key:
        headers["apiKey"] = api_key

    response = requests.get(NVD_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def main():
    os.makedirs("data", exist_ok=True)
    print("NVD'den CVE çekiliyor...")
    data = fetch_cves(results_per_page=50)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = data.get("totalResults", 0)
    fetched = len(data.get("vulnerabilities", []))
    print(f"Tamamlandı. Toplam: {total}, Çekilen: {fetched}")
    print(f"Kaydedildi: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

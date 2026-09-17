import requests
import zipfile
import io
import json
from datetime import datetime, timedelta

# Configuration
TARGET_CPV = "45233120"  # Example: Road construction works
# The API provides data by day; querying yesterday ensures the day's archive is fully compiled
TARGET_DATE = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
API_URL = "https://oeffentlichevergabe.de/api/notice-exports"

def fetch_and_filter_tenders(cpv_code, pub_day):
    print(f"Fetching public tenders for {pub_day}...")
    
    # Request the daily export in OCDS ZIP format
    params = {
        "pubDay": pub_day,
        "format": "ocds.zip"
    }
    
    try:
        response = requests.get(API_URL, params=params, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download data: {e}")
        return

    print("Download complete. Analyzing notices in memory...")
    matching_tenders = []
    
    try:
        # Load the ZIP file directly into memory to save disk I/O
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            json_files = [name for name in archive.namelist() if name.endswith('.json')]
            
            for file_name in json_files:
                with archive.open(file_name) as file:
                    try:
                        data = json.load(file)
                        
                        # OCDS structures notices inside a "releases" array
                        for release in data.get('releases', []):
                            tender = release.get('tender', {})
                            
                            # Extract all CPV codes listed under the tender's items
                            cpvs = []
                            for item in tender.get('items', []):
                                classification = item.get('classification', {})
                                if 'id' in classification:
                                    cpvs.append(classification['id'])
                            
                            # Match prefix so '45' will match '45233120'
                            if any(cpv.startswith(cpv_code) for cpv in cpvs):
                                buyer = release.get('buyer', {}).get('name', 'Unknown Buyer')
                                matching_tenders.append({
                                    "id": release.get('id', 'N/A'),
                                    "title": tender.get('title', 'No Title'),
                                    "buyer": buyer,
                                    "cpvs": list(set(cpvs)) # Deduplicate
                                })
                                
                    except json.JSONDecodeError:
                        continue 
                        
    except zipfile.BadZipFile:
        print("Failed to parse the downloaded file. It may not be a valid ZIP archive.")
        return

    # Output the results
    print(f"\nFound {len(matching_tenders)} tenders matching CPV {cpv_code}:")
    for idx, t in enumerate(matching_tenders, 1):
        print(f"{idx}. {t['title']}")
        print(f"   Buyer: {t['buyer']}")
        print(f"   CPVs: {', '.join(t['cpvs'])}")
        print(f"   ID: {t['id']}\n")

if __name__ == "__main__":
    fetch_and_filter_tenders(TARGET_CPV, TARGET_DATE)
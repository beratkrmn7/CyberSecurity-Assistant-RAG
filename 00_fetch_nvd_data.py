import requests
import json
import os
import time

def fetch_cve_data(limit=50):
    # NVD API V2 üzerinden sadece CRITICAL olanları çekiyoruz
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cvssV3Severity=CRITICAL&resultsPerPage={limit}"
    print(f"[!] NVD API'den en güncel {limit} adet 'CRITICAL' (Kritik) seviye zafiyet çekiliyor...")
    print("Not: NVD API genel erişimde hız sınırlarına (rate limit) sahip olabilir. Lütfen bekleyin...")
    
    headers = {
        "User-Agent": "CyberSecurity-RAG-Assistant/1.0"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code in [403, 429]:
            print("[-] NVD API hız sınırına (rate limit) takıldınız. Lütfen 1-2 dakika bekleyip tekrar deneyin.")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        cve_list = []
        vulnerabilities = data.get("vulnerabilities", [])
        
        for item in vulnerabilities:
            cve_data = item.get("cve", {})
            cve_id = cve_data.get("id", "UNKNOWN")
            
            # İngilizce açıklama metnini çıkar
            descriptions = cve_data.get("descriptions", [])
            desc_text = "Açıklama bulunamadı."
            for desc in descriptions:
                if desc.get("lang") == "en":
                    desc_text = desc.get("value")
                    break
                    
            # CVSS Skorunu ve önem derecesini çıkar
            metrics = cve_data.get("metrics", {})
            cvss_score = 0.0
            severity = "CRITICAL"
            
            if "cvssMetricV31" in metrics:
                cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0.0)
                severity = cvss_data.get("baseSeverity", "CRITICAL")
            elif "cvssMetricV30" in metrics:
                cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0.0)
                severity = cvss_data.get("baseSeverity", "CRITICAL")
                
            published_date = cve_data.get("published", "").split("T")[0] if "published" in cve_data else "Bilinmiyor"
            
            cve_list.append({
                "cve_id": cve_id,
                "description": desc_text,
                "severity": severity,
                "cvss_score": cvss_score,
                "published_date": published_date
            })
            
        return cve_list
        
    except requests.exceptions.Timeout:
        print("[-] API isteği zaman aşımına uğradı. (NVD sunucuları yavaş olabilir).")
        return None
    except Exception as e:
        print(f"[-] API isteği sırasında bir hata oluştu: {e}")
        return None

def main():
    os.makedirs("data", exist_ok=True)
    
    print("==================================================")
    print("Siber Guvenlik Veri Toplama Araci (NVD API)")
    print("==================================================")
    
    # Gerçek dünya senaryosu için 50 adet kritik zafiyet çekiyoruz
    cve_data = fetch_cve_data(limit=50)
    
    if cve_data and len(cve_data) > 0:
        output_file = "data/cve_sample.json"
        
        # Mevcut veriyi okuyup birleştirme opsiyonu da eklenebilir ama 
        # şimdilik temiz bir 50'lik set ile üzerine yazıyoruz.
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cve_data, f, indent=4, ensure_ascii=False)
            
        print(f"\n[+] Başarılı! {len(cve_data)} adet gerçek ve güncel CVE kaydı '{output_file}' dosyasına kaydedildi.")
        print("[!] RAG sistemini bu yeni verilerle güncellemek için sıradaki adım:")
        print("    > python 01_data_ingestion.py")
    else:
        print("\n[-] Veri çekilemediği için mevcut data/cve_sample.json dosyası değiştirilmedi.")

if __name__ == "__main__":
    main()

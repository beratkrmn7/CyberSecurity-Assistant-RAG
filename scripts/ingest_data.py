import json, sqlite3, os, numpy as np
from dotenv import load_dotenv
from foundry_local_sdk import Configuration, FoundryLocalManager
import PyPDF2

load_dotenv()

DB_PATH     = os.getenv("DB_PATH", "knowledge_base.db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "qwen3-embedding-0.6b")
REPORTS_DIR = "data/reports"
CVE_PATH    = "data/cve_sample.json"

# ── Veritabanı kurulumu ──────────────────────────────────────────
def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            source    TEXT,        -- 'nvd' veya pdf dosya adı
            source_id TEXT,        -- CVE-ID veya pdf_sayfa_no
            severity  TEXT,        -- CRITICAL/HIGH/MEDIUM/LOW veya NULL
            chunk_text TEXT,
            embedding  TEXT        -- JSON string olarak saklanır
        )
    """)
    conn.commit()

# ── Embedding üretimi ────────────────────────────────────────────
def get_embedding(embed_client, text):
    vector_result = embed_client.generate_embedding(text)
    return vector_result.data[0].embedding

# ── CVE işleme ───────────────────────────────────────────────────
def ingest_cves(conn, embed_client):
    if not os.path.exists(CVE_PATH):
        print(f"UYARI: {CVE_PATH} bulunamadı. Önce 00_fetch_nvd_data.py çalıştır.")
        return

    with open(CVE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    vulns = []
    if isinstance(data, dict):
        vulns = data.get("vulnerabilities", [])
    elif isinstance(data, list):
        vulns = data
        
    print(f"{len(vulns)} CVE işleniyor...")

    for item in vulns:
        # NVD formatı: item.get("cve", {})
        # Eski formatımız: item (doğrudan cve bilgileri)
        cve = item.get("cve", item)
        cve_id = cve.get("id", cve.get("cve_id", "UNKNOWN"))

        # Description
        descriptions = cve.get("descriptions", [])
        if descriptions:
            desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")
        else:
            desc = cve.get("description", "")
            
        if not desc:
            continue

        # CVSS severity
        metrics = cve.get("metrics", {})
        severity = cve.get("severity", None) # Eski json'dan geliyorsa
        
        for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if key in metrics and metrics[key]:
                severity = metrics[key][0].get("cvssData", {}).get("baseSeverity", severity)
                break

        chunk_text = f"CVE ID: {cve_id}\nSeverity: {severity}\n\n{desc}"
        embedding  = get_embedding(embed_client, chunk_text)

        conn.execute(
            "INSERT INTO chunks (source, source_id, severity, chunk_text, embedding) VALUES (?,?,?,?,?)",
            ("nvd", cve_id, severity, chunk_text, json.dumps(embedding))
        )

    conn.commit()
    print(f"CVE ingestion tamamlandı.")

# ── PDF işleme ───────────────────────────────────────────────────
def chunk_text(text, chunk_size=150, overlap=30):
    """Metni overlap'li parçalara böler. (Daha hızlı okuma için küçültüldü)"""
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def ingest_pdfs(conn, embed_client):
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        print(f"'{REPORTS_DIR}' klasörü oluşturuldu. PDF'leri buraya ekle.")
        return

    pdf_files = [f for f in os.listdir(REPORTS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"'{REPORTS_DIR}' klasöründe PDF bulunamadı.")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(REPORTS_DIR, pdf_file)
        print(f"PDF işleniyor: {pdf_file}")

        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

        chunks = chunk_text(full_text, chunk_size=150, overlap=30)
        print(f"  {len(chunks)} chunk oluşturuldu.")

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:   # Boş/çok kısa chunk'ları atla
                continue
            embedding = get_embedding(embed_client, chunk)
            conn.execute(
                "INSERT INTO chunks (source, source_id, severity, chunk_text, embedding) VALUES (?,?,?,?,?)",
                (pdf_file, f"chunk_{i}", None, chunk, json.dumps(embedding))
            )

        conn.commit()
        print(f"  '{pdf_file}' tamamlandı.")

# ── Ana akış ─────────────────────────────────────────────────────
def main():
    print("Model yükleniyor...")
    config = Configuration(app_name="cybersec-rag-assistant")
    try:
        FoundryLocalManager.initialize(config)
    except Exception:
        pass
    manager = FoundryLocalManager.instance
    
    # Doğru API çağrısı
    embed_model = manager.catalog.get_model(EMBED_MODEL)
    embed_model.load()
    embed_client = embed_model.get_embedding_client()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Eski verileri temizle (yeniden çalıştırma için)
    conn.execute("DELETE FROM chunks")
    conn.commit()
    print("Veritabanı temizlendi.")

    ingest_cves(conn, embed_client)
    ingest_pdfs(conn, embed_client)

    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"\nTamamlandı. Toplam chunk: {total}")
    conn.close()

if __name__ == "__main__":
    main()

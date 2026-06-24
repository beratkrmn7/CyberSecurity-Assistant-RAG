import json
import sqlite3
import os
import math

# Not: Foundry Local SDK sistemde bulunamadığı için, embedding işlemini 
# yerel çalışan HuggingFace SentenceTransformers ile DOĞRUDAN yapıyoruz (Langchain olmadan).
from sentence_transformers import SentenceTransformer

DB_NAME = "knowledge_base.db"

def init_db():
    """SQLite veritabanını ve tabloyu oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Mevcut tabloyu temizle (Her ingestion işleminde baştan oluşturmak için)
    cursor.execute("DROP TABLE IF EXISTS documents")
    
    # İsterlere uygun SQLite tablosu: id, text_chunk, embedding_vector (JSON string olarak saklanacak)
    cursor.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cve_id TEXT,
            text_chunk TEXT,
            embedding_vector TEXT
        )
    """)
    conn.commit()
    return conn

def chunk_text(text, chunk_size=500, overlap=50):
    """Basit bir karakter bazlı metin parçalama (chunking) fonksiyonu."""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start += (chunk_size - overlap)
    return chunks

def load_data(file_path):
    """JSON dosyasından verileri okur ve birleştirilmiş metinlere çevirir."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    documents = []
    for item in data:
        text = f"CVE ID: {item['cve_id']}\n"
        text += f"Severity: {item['severity']} (Score: {item['cvss_score']})\n"
        text += f"Published Date: {item['published_date']}\n"
        text += f"Description: {item['description']}\n"
        
        doc = {"page_content": text, "metadata": {"cve_id": item['cve_id']}}
        documents.append(doc)
        
    return documents

def main():
    print("1. SQLite Veritabanı hazırlanıyor...")
    conn = init_db()
    cursor = conn.cursor()
    
    print("2. Veriler yükleniyor...")
    documents = load_data("data/cve_sample.json")
    print(f"Toplam {len(documents)} adet CVE kaydı okundu.\n")
    
    print("3. Metinler RAG için parçalara (chunks) ayrılıyor...")
    all_chunks = []
    for doc in documents:
        text_chunks = chunk_text(doc["page_content"], chunk_size=500, overlap=50)
        for chunk_str in text_chunks:
            all_chunks.append({"text": chunk_str, "metadata": doc["metadata"]})
            
    print(f"Toplam {len(all_chunks)} parça (chunk) oluştu.\n")
    
    print("4. Embedding (Vektör) modeli yükleniyor... (Local / Offline)")
    embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("\n5. Vektörler hesaplanıp SQLite veritabanına kaydediliyor...")
    for chunk in all_chunks:
        # Metni vektöre çevir
        vector = embeddings_model.encode(chunk["text"]).tolist()
        
        # Vektörü SQLite'da tutabilmek için JSON string'e çeviriyoruz
        vector_json = json.dumps(vector)
        
        # Veritabanına kaydet
        cursor.execute(
            "INSERT INTO documents (cve_id, text_chunk, embedding_vector) VALUES (?, ?, ?)",
            (chunk["metadata"].get("cve_id", "UNKNOWN"), chunk["text"], vector_json)
        )
        
    conn.commit()
    conn.close()
    
    print("\n[OK] İşlem tamamlandı! Veriler, metin parçacıkları ve vektörleriyle birlikte")
    print(f"'{DB_NAME}' adlı yerel SQLite veritabanına başarıyla kaydedildi.")

if __name__ == "__main__":
    main()

import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import requests

DB_NAME = "knowledge_base.db"

def compute_cosine_similarity(vec1, vec2):
    """İki vektör arasındaki Kosinüs Benzerliğini (Cosine Similarity) hesaplar."""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def get_top_chunks(query, top_k=2):
    """
    SQLite veritabanından tüm embedding'leri çeker, kullanıcının sorgusuyla 
    kosinüs benzerliğini hesaplar ve en ilgili (en yüksek skorlu) parçaları döndürür.
    Bu tam olarak PDF'te istenen 'Search for similar vectors in SQLite' aşamasıdır.
    """
    # 1. Sorguyu embed et
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vector = model.encode(query).tolist()
    
    # 2. Veritabanındaki tüm vektörleri çek
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT cve_id, text_chunk, embedding_vector FROM documents")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        print(f"HATA: '{DB_NAME}' veritabanı bulunamadı. Lütfen önce '01_data_ingestion.py' çalıştırın.")
        return []
    finally:
        conn.close()
        
    # 3. Benzerlikleri hesapla
    scored_chunks = []
    for row in rows:
        cve_id, text_chunk, vec_json = row
        db_vector = json.loads(vec_json)
        
        sim_score = compute_cosine_similarity(query_vector, db_vector)
        scored_chunks.append({
            "cve_id": cve_id,
            "text": text_chunk,
            "score": sim_score
        })
        
    # 4. En yüksek skorlu ilk K parçayı döndür
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]

def call_local_llm(context_text, user_question):
    """
    Yerel LLM modelini çağırır. 
    Not: Projede Microsoft Foundry Local SDK istenmektedir ancak kurulu olmadığı için
    şimdilik yerel Ollama API (localhost:11434) ile simüle ediyoruz.
    Foundry Local SDK kurulduğunda buraya `foundry_local.completeChat(...)` entegre edilmelidir.
    """
    system_prompt = (
        "Sen uzman bir siber güvenlik asistanısın. Aşağıdaki bağlam (context) bilgilerini "
        "kullanarak kullanıcının sorusunu cevapla. Eğer cevap bağlamda yoksa 'Bilmiyorum' de."
    )
    
    full_prompt = f"Bağlam:\n{context_text}\n\nSoru: {user_question}\nCevap:"
    
    # Ollama REST API çağrısı
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi3", # veya sahip olduğunuz başka bir model (örn: llama3)
        "prompt": full_prompt,
        "system": system_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "Cevap üretilemedi.")
    except Exception as e:
        return f"LLM bağlantı hatası: {e}\nNot: Lütfen bilgisayarınızda yerel modelin çalıştığından emin olun."

def main():
    print("==================================================")
    print("🤖 Siber Güvenlik Asistanı (SQLite & Local RAG)")
    print("==================================================\n")
    
    while True:
        user_query = input("\nSorunuz (Çıkmak için 'q'): ")
        if user_query.lower() in ['q', 'quit', 'exit']:
            print("Görüşmek üzere!")
            break
            
        print("\n[!] Veritabanında (SQLite) kosinüs benzerliği (cosine similarity) ile taranıyor...")
        top_chunks = get_top_chunks(user_query, top_k=2)
        
        if not top_chunks:
            print("Hata: İlgili bilgi bulunamadı veya veritabanı boş.")
            continue
            
        print(f"[+] En yüksek benzerliğe sahip {len(top_chunks)} belge parçası bulundu.")
        
        # Bağlamı birleştir
        context_text = "\n\n".join([chunk["text"] for chunk in top_chunks])
        
        print("\n[!] Yerel LLM'e (Offline) bağlanıp cevap üretiliyor...")
        answer = call_local_llm(context_text, user_query)
        
        print("\n🤖 Asistanın Cevabı:")
        print(answer)
        
        print("\n[Faydalanılan Kaynaklar (SQLite)]:")
        for i, chunk in enumerate(top_chunks):
            print(f"- Kaynak {i+1} | Skor: %{chunk['score']*100:.1f} | CVE ID: {chunk['cve_id']}")

if __name__ == "__main__":
    main()

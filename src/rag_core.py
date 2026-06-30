import json, sqlite3, os, numpy as np
from dotenv import load_dotenv
from foundry_local_sdk import Configuration, FoundryLocalManager
import streamlit as st
import PyPDF2

load_dotenv()

DB_PATH    = os.getenv("DB_PATH", "knowledge_base.db")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5-1.5b")
EMBED_MODEL= os.getenv("EMBED_MODEL", "qwen3-embedding-0.6b")
TOP_K      = int(os.getenv("TOP_K", 3))

@st.cache_resource(show_spinner="Yapay Zeka Modelleri Yükleniyor (Bir kez beklenecek)...")
def get_manager_and_clients():
    config = Configuration(app_name="cybersec-rag-assistant")
    try:
        FoundryLocalManager.initialize(config)
    except Exception:
        pass
    manager = FoundryLocalManager.instance
    
    # Embed client yükle
    embed_model = manager.catalog.get_model(EMBED_MODEL)
    embed_model.load()
    embed_client = embed_model.get_embedding_client()
    
    # Chat client yükle
    chat_model = manager.catalog.get_model(MODEL_NAME)
    chat_model.load()
    chat_client = chat_model.get_chat_client() if hasattr(chat_model, "get_chat_client") else chat_model.create_chat_client()

    return manager, chat_client, embed_client

@st.cache_data(show_spinner=False)
def load_all_embeddings():
    """Tüm veritabanını başlangıçta RAM'e yükle."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT source, source_id, severity, chunk_text, embedding FROM chunks"
    ).fetchall()
    conn.close()
    return [
        (r[0], r[1], r[2], r[3], json.loads(r[4]))
        for r in rows
    ]

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

def get_top_chunks(query: str, top_k: int = TOP_K):
    _, _, embed_client = get_manager_and_clients()
    
    vector_result = embed_client.generate_embedding(query)
    query_emb = np.array(vector_result.data[0].embedding)

    rows = load_all_embeddings()
    if not rows:
        return []

    # Matris işlemleri (Claude'un önerdiği hızlandırma)
    chunk_matrix = np.array([r[4] for r in rows])
    
    norms = np.linalg.norm(chunk_matrix, axis=1) * np.linalg.norm(query_emb)
    scores = np.dot(chunk_matrix, query_emb) / (norms + 1e-10)

    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in top_idx:
        source, source_id, severity, chunk_text, _ = rows[i]
        results.append((float(scores[i]), source, source_id, severity, chunk_text))

    return results

def chunk_text(text, chunk_size=150, overlap=30):
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def ingest_single_pdf(pdf_path: str):
    """Tek bir PDF dosyasını okur, parçalar, vektörler ve veritabanına ekler."""
    _, _, embed_client = get_manager_and_clients()
    conn = sqlite3.connect(DB_PATH)
    
    # Read PDF
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
            
    # Chunking
    chunks = chunk_text(full_text, chunk_size=150, overlap=30)
    pdf_file = os.path.basename(pdf_path)
    
    # Embedding and Inserting
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 50:
            continue
        vector_result = embed_client.generate_embedding(chunk)
        embedding = vector_result.data[0].embedding
        conn.execute(
            "INSERT INTO chunks (source, source_id, severity, chunk_text, embedding) VALUES (?,?,?,?,?)",
            (pdf_file, f"chunk_{i}", None, chunk, json.dumps(embedding))
        )
        
    conn.commit()
    conn.close()
    
    # Ön belleği temizle ki yeni vektörler aramaya dahil olsun
    load_all_embeddings.clear()

def answer_query(question: str, chat_history: list = None) -> dict:
    """
    Soru alır, ilgili chunk'ları bulur, LLM'e sorar.
    """
    _, chat_client, _ = get_manager_and_clients()
    top_chunks = get_top_chunks(question)

    if not top_chunks:
        return {
            "answer": "Veritabanında ilgili bilgi bulunamadı. Lütfen önce veritabanını oluşturun.",
            "sources": []
        }

    # Context oluştur
    context_parts = []
    sources       = []
    for score, source, source_id, severity, chunk_text in top_chunks:
        context_parts.append(f"[Kaynak: {source} | {source_id}]\n{chunk_text}")
        sources.append({"source": source, "id": source_id, "severity": severity, "score": round(score, 3)})

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """Sen deneyimli bir siber güvenlik analistisin.
Görevin: Aşağıdaki bağlam belgelerine dayanarak soruları TÜRKÇE, net ve detaylı yanıtlamak.

Kurallar:
- YALNIZCA verilen bağlam bilgisini kullan
- Bağlamda bilgi varsa mutlaka detaylı açıkla, "daha fazla bilgi gerekiyor" deme
- Teknik terimleri Türkçe açıkla
- Cevabın sonunda hangi kaynaktan bilgi aldığını belirt
- Bağlamda gerçekten bilgi yoksa "Bu konuda veritabanımda bilgi bulunmuyor." de"""

    user_prompt = f"""Bağlam belgeler:
{context}

Soru: {question}

Lütfen bağlamdaki bilgilere dayanarak detaylı bir Türkçe yanıt ver."""

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        # Sadece son 6 mesajı (3 tur) al ki context sınırı aşılmasın
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": user_prompt})

    # Doğru Foundry Local API kullanımı
    chat_client.settings.max_tokens = 600
    chat_client.settings.temperature = 0.7  
    if hasattr(chat_client.settings, "top_p"):
        chat_client.settings.top_p = 0.95
    if hasattr(chat_client.settings, "frequency_penalty"):
        chat_client.settings.frequency_penalty = 1.0  # Aynı kelimeyi tekrar etmeyi kesin engeller
    if hasattr(chat_client.settings, "presence_penalty"):
        chat_client.settings.presence_penalty = 1.0
        
    try:
        response_obj = chat_client.complete_chat(messages)
        if hasattr(response_obj, "choices") and response_obj.choices:
            answer = response_obj.choices[0].message.content or ""
        else:
            answer = "Cevap üretilemedi."
    except Exception as e:
        if "cancelled" in str(e).lower() or "canceled" in str(e).lower():
            answer = f"Model yanıt üretirken işlem iptal edildi veya zaman aşımına uğradı (Timeout). Lütfen soruyu tekrar sorun."
        else:
            answer = f"Model yanıt verirken bir hata oluştu: {str(e)}"

    return {"answer": answer, "sources": sources}

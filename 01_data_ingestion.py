import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    documents = []
    for item in data:
        # Metni LLM'in okuyabileceği formatta birleştirerek oluşturuyoruz
        text = f"CVE ID: {item['cve_id']}\n"
        text += f"Severity: {item['severity']} (Score: {item['cvss_score']})\n"
        text += f"Published Date: {item['published_date']}\n"
        text += f"Description: {item['description']}\n"
        
        # Meta veriler (ileride spesifik bir CVE'yi filtrelemek için kullanılabilir)
        metadata = {
            "cve_id": item['cve_id'],
            "severity": item['severity'],
            "cvss_score": item['cvss_score']
        }
        
        doc = Document(page_content=text, metadata=metadata)
        documents.append(doc)
        
    return documents

def main():
    print("1. Veriler yükleniyor...")
    documents = load_data("data/cve_sample.json")
    print(f"Toplam {len(documents)} adet CVE kaydı okundu.\n")
    
    # Text splitter (Çok uzun dokümanları RAG'in daha rahat sindirebileceği küçük parçalara ayırmak için)
    print("2. Metinler parçalara (chunks) ayrılıyor...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"Toplam {len(chunks)} parça (chunk) oluştu.\n")
    
    # Embedding modeli (Metinleri matematiksel vektörlere çevirecek model)
    # "all-MiniLM-L6-v2" çok hafif ve hızlı, ücretsiz bir SentenceTransformer modelidir.
    print("3. Embedding modeli yükleniyor... (Bu işlem ilk çalışmada modeli internetten indirebilir)")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Vektör Veritabanı oluşturma ve diske kaydetme
    print("\n4. Vektör veritabanı (ChromaDB) oluşturuluyor...")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    print("\nIslem tamamlandi! Vektor veritabani './chroma_db' klasorune kaydedildi.")

if __name__ == "__main__":
    main()

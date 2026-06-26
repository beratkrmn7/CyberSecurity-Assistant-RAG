# Siber Güvenlik Asistanı (Local LLM RAG)

Bu proje, yerel bir LLM (Büyük Dil Modeli) ve RAG (Retrieval-Augmented Generation) mimarisi kullanılarak geliştirilmiş bir Uzman Siber Güvenlik Asistanıdır. 
Asistan sadece güncel CVE (Ortak Güvenlik Açıkları ve Etkilenmeler) kayıtlarını sorgulamakla kalmaz, aynı zamanda `data/reports/` dizinine eklediğiniz APT veya Siber Tehdit İstihbarat (CTI) PDF raporlarını da okuyup özetleyerek kullanıcılara güvenli, yerel ve hızlı cevaplar sunar.

Microsoft Yaz Stajı "Azure Foundry Local LLM" projesi kapsamında geliştirilmektedir.

## Kullanılan Teknolojiler

- **Python**
- **Streamlit**: Modern ve kullanıcı dostu web arayüzü için.
- **Microsoft Foundry Local SDK**: Yerel LLM (`qwen2.5-1.5b`) ve Embedding (`qwen3-embedding-0.6b`) modellerinin yönetimi için.
- **SQLite**: Vektör veritabanı olarak metin parçacıklarını ve embedding vektörlerini saklamak için.
- **NumPy**: Vektörler arası kosinüs benzerliği (cosine similarity) hesaplamaları için.
- **PyPDF2**: Yüklenen yerel PDF raporlarını metne dönüştürmek için.

*(Not: Projede LangChain veya ChromaDB yerine tamamen Foundry Local SDK ve yerel SQLite entegrasyonu kullanılmıştır.)*

## Proje Yapısı

```
CyberSecurity-Assistant-RAG/
├── 00_fetch_nvd_data.py
├── 01_data_ingestion.py       # PDF + CVE verilerini veritabanına işler
├── 02_rag_assistant.py        # Terminal üzerinden test betiği
├── app.py                     # Streamlit web arayüzü
├── rag_core.py                # Ortak RAG (retrieval + LLM) mantığı
├── knowledge_base.db          # SQLite vektör veritabanı
├── .env / .env.example
├── requirements.txt
└── data/
    ├── cve_sample.json        # 00_fetch_nvd_data ile çekilen veriler
    └── reports/               # İstihbarat PDF'lerini atacağınız klasör
```

## Kurulum ve Çalıştırma Sırası

1. Depoyu klonlayın ve klasöre girin:
```bash
git clone https://github.com/beratkrmn7/CyberSecurity-Assistant-RAG.git
cd CyberSecurity-Assistant-RAG
```

2. Sanal ortam oluşturup bağımlılıkları yükleyin:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Çevre değişkenlerini `.env.example` dosyasından kopyalayarak oluşturun:
```bash
copy .env.example .env
```
*(Windows için `copy`, Linux/Mac için `cp` kullanın. NVD_API_KEY değerinizi `.env` dosyasına ekleyebilirsiniz.)*

4. NVD API üzerinden güncel CVE zafiyet verilerini çekin:
```bash
python scripts/fetch_nvd.py
```

5. (İsteğe Bağlı) Okunmasını istediğiniz Tehdit İstihbarat raporlarını veya güvenlik yönergelerini (PDF formatında) `data/reports/` klasörünün içine atın. 

6. Ardından veritabanını oluşturmak ve verileri (CVE + PDF) vektörlemek için veri yükleme betiğini çalıştırın:
```bash
python scripts/ingest_data.py
```

7. RAG sistemini terminalden hızlıca test edin:
```bash
CLI Arayüzü: `python cli_app.py`
```

8. Her şey hazır olduğunda asistanın modern web arayüzünü başlatın:
```bash
streamlit run app.py
```

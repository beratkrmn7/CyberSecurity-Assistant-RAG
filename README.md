# Siber Güvenlik Asistanı (Local LLM RAG)

Bu proje, yerel bir LLM (Büyük Dil Modeli) ve RAG (Retrieval-Augmented Generation) mimarisi kullanılarak geliştirilmiş bir Siber Güvenlik Asistanıdır. Amacı, güncel CVE (Ortak Güvenlik Açıkları ve Etkilenmeler) kayıtlarını ve siber tehdit istihbarat raporlarını analiz ederek kullanıcılara güvenli, yerel ve hızlı cevaplar sunmaktır.

Microsoft Yaz Stajı "Azure Foundry Local LLM" projesi kapsamında geliştirilmektedir.

## Kullanılan Teknolojiler

- **Python**
- **Streamlit**: Modern ve kullanıcı dostu web arayüzü için.
- **Microsoft Foundry Local SDK**: Yerel LLM (`qwen2.5-1.5b`) ve Embedding (`qwen3-embedding-0.6b`) modellerinin yönetimi için.
- **SQLite**: Vektör veritabanı olarak metin parçacıklarını ve embedding vektörlerini saklamak için.
- **NumPy**: Vektörler arası kosinüs benzerliği (cosine similarity) hesaplamaları için.

*(Not: Projede LangChain veya ChromaDB yerine tamamen Foundry Local SDK ve yerel SQLite entegrasyonu kullanılmıştır.)*

## Proje Yapısı

- `00_fetch_nvd_data.py`: (Opsiyonel ama Önerilen) NVD API (Ulusal Zafiyet Veritabanı) üzerinden en güncel ve kritik 50 CVE kaydını çekerek `data/cve_sample.json` dosyasını otomatik günceller.
- `01_data_ingestion.py`: JSON formatındaki CVE verilerini işleme, parçalama (chunking), embedding oluşturma ve SQLite veritabanına kaydetme adımlarını içerir. Gerekli dil modellerini de yerel ortama indirir.
- `app.py`: Streamlit tabanlı, modern web arayüzü. Yerel LLM ile sohbet ve vektör tabanlı bilgi araması burada gerçekleşir.
- `02_rag_assistant.py`: (Opsiyonel) CLI üzerinden temel RAG sistemini test etmek için betik.

## Kurulum

1. Depoyu klonlayın ve klasöre girin:
```bash
git clone https://github.com/beratkrmn7/CyberSecurity-Assistant-RAG.git
cd CyberSecurity-Assistant-RAG
```

2. Sanal ortam oluşturup aktif edin ve gereksinimleri yükleyin (Windows):
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Kullanım

1. *(Opsiyonel)* NVD API üzerinden güncel zafiyetleri çekip veri setinizi zenginleştirmek için önce şu betiği çalıştırın:
```bash
python 00_fetch_nvd_data.py
```

2. Ardından veritabanını (`knowledge_base.db`) oluşturmak ve LLM modellerini indirmek için veri yükleme betiğini çalıştırın:
```bash
python 01_data_ingestion.py
```

2. İşlem tamamlandıktan sonra asistanın web arayüzünü başlatın:
```bash
streamlit run app.py
```

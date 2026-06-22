# Siber Güvenlik Asistanı (Local LLM RAG)

Bu proje, yerel bir LLM (Büyük Dil Modeli) ve RAG (Retrieval-Augmented Generation) mimarisi kullanılarak geliştirilmiş bir Siber Güvenlik Asistanıdır. Amacı, güncel CVE (Ortak Güvenlik Açıkları ve Etkilenmeler) kayıtlarını ve siber tehdit istihbarat raporlarını analiz ederek kullanıcılara güvenli, yerel ve hızlı cevaplar sunmaktır.

Microsoft Yaz Stajı "Azure Foundry Local LLM" projesi kapsamında geliştirilmektedir.

## Kullanılan Teknolojiler

- Python
- LangChain
- ChromaDB (Vektör Veritabanı)
- Ollama / Yerel LLM

## Kurulum

1. Depoyu klonlayın:
```bash
git clone <repo-url>
```

2. Sanal ortamı aktif edin ve gereksinimleri yükleyin:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

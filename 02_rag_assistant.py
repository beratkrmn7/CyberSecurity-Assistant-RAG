from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def main():
    print("1. Vektor veritabani (ChromaDB) yukleniyor...")
    # Verileri kaydederken kullandigimiz ayni embedding modelini yukluyoruz
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Diskteki ChromaDB veritabanina baglaniyoruz
    vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    # Veritabaninda arama yapacak mekanizma (En benzer 2 parcayi getir)
    retriever = vector_db.as_retriever(search_kwargs={"k": 2})
    
    print("2. Yerel LLM (Ollama - Phi-3) baglantisi kuruluyor...")
    # Bilgisayarinizda arka planda calisan Ollama'ya baglanir
    llm = Ollama(model="phi3")
    
    print("3. Siber Guvenlik Asistani Hazirlaniyor...\n")
    # Asistana nasil davranmasi gerektigini soyleyen Sistem Promptu
    template = """Sen uzman bir siber guvenlik asistanisin. Sana verilen asagidaki sistem baglami (context) bilgilerini kullanarak kullanicinin sorusunu cevapla. Eger cevabi asagidaki baglamda bulamazsan, "Bununla ilgili yerel veritabanimda bilgi bulunmamaktadir" de ve uydurma yapma.

Baglam (Context):
{context}

Kullanicinin Sorusu: {question}

Uzman Cevabi:"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    
    # Modern LCEL RAG Mimarisi
    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | QA_CHAIN_PROMPT
        | llm
        | StrOutputParser()
    )
    
    rag_chain_with_source = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)
    
    # Kullanici ile sohbet (CLI) dongusu
    print("==================================================")
    print("🤖 Siber Guvenlik Asistani Aktif (Cikmak icin 'q' yazin)")
    print("==================================================\n")
    
    while True:
        user_query = input("\nSorunuz (Orn: Log4j zafiyeti nasil calisir?): ")
        if user_query.lower() in ['q', 'quit', 'cikis', 'exit']:
            print("Gorusmek uzere! Guvende kalin.")
            break
            
        print("\n[!] Veritabaninda taranip asistan tarafindan isleniyor, lutfen bekleyin...")
        
        # Asistana soruyu gonderiyoruz
        result = rag_chain_with_source.invoke(user_query)
        
        # Cevabi yazdiriyoruz
        print("\n🤖 Asistanin Cevabi:")
        print(result["answer"])
        
        # Yapay zekanin bu cevabi verirken okudugu gercek belgeleri listeleyelim (Seffaflik icin onemli)
        print("\n[Faydalanilan Kaynaklar]:")
        for i, doc in enumerate(result["context"]):
            print(f"- Kaynak {i+1} | CVE ID: {doc.metadata.get('cve_id')}")

if __name__ == "__main__":
    main()

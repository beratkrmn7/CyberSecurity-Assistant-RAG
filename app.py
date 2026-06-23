import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Sayfa ayarlarini yapiyoruz
st.set_page_config(page_title="Siber Güvenlik Asistanı", page_icon="🛡️", layout="centered")

st.title("🛡️ Siber Güvenlik Asistanı (Local RAG)")
st.markdown("**Microsoft Yaz Stajı Projesi** - *Ollama (Phi-3) ve ChromaDB Destekli*")
st.divider()

# RAG Sistemini baslatiyoruz ve onbellege aliyoruz (Her seferinde bastan yuklenmemesi icin)
@st.cache_resource
def init_rag_system():
    # Embedding
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Vector DB
    vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vector_db.as_retriever(search_kwargs={"k": 2})
    
    # LLM (Arka planda Ollama calismalidir)
    llm = Ollama(model="phi3")
    
    # Prompt
    template = """Sen uzman bir siber guvenlik asistanisin. Asagidaki baglam (context) bilgilerini kullanarak kullanicinin sorusunu cevapla. Cevabi bulamazsan "Bilmiyorum" de.
    
Baglam:
{context}

Soru: {question}

Cevap:"""
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | QA_CHAIN_PROMPT
        | llm
        | StrOutputParser()
    )
    
    rag_chain_with_source = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)
    
    return rag_chain_with_source

# Asistani Baslat
try:
    with st.spinner("Yapay Zeka Modelleri Yükleniyor... Lütfen bekleyin."):
        qa_chain = init_rag_system()
except Exception as e:
    st.error(f"Sistem baslatilirken hata olustu: {e}")
    st.stop()

# Chat gecmisi (Oturum kayitlari)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba! Ben yerel siber güvenlik asistanınızım. CVE kayıtları hakkında bana soru sorabilirsiniz."}]

# Gecmis mesajlari ekranda goster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Kaynaklari Gor"):
                for source in message["sources"]:
                    st.write(f"- {source}")

# Kullanici giris alani
if prompt := st.chat_input("Log4j nedir? Nasil onlem alinir?"):
    # Kullanici mesajini ekrana ve gecmise ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Asistan cevabi
    with st.chat_message("assistant"):
        with st.spinner("Veritabaninda taranip cevap üretiliyor..."):
            response = qa_chain.invoke(prompt)
            answer = response["answer"]
            docs = response["context"]
            
            # Cevabi ekranda goster
            st.markdown(answer)
            
            # Kaynaklari hazirla ve goster
            source_list = [f"Kayıt İncelemesi: {doc.metadata.get('cve_id')}" for doc in docs]
            if source_list:
                with st.expander("📚 Kaynaklari Gor"):
                    for source in source_list:
                        st.write(f"- {source}")
                    
    # Asistan mesajini gecmise ekle
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": source_list})

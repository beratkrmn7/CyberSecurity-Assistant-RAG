import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Sayfa ayarlarini yapiyoruz
st.set_page_config(page_title="Siber Güvenlik Asistanı", page_icon="🛡️", layout="wide")

# Modern, Premium CSS Tasarimi Enjekte Ediyoruz
st.markdown("""
<style>
    /* Ana arka plan */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e2e8f0;
    }
    
    /* Baslik stili */
    h1 {
        color: #38bdf8 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 800 !important;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        padding-bottom: 0.5rem;
    }
    
    /* Alt baslik */
    .subtitle {
        color: #94a3b8;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Asistanin mesaj kutulari (Glassmorphism) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background: rgba(56, 189, 248, 0.05) !important;
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Kullanicinin mesaj kutulari */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }

    /* Girdi Kutusu */
    .stChatInputContainer {
        border-radius: 20px !important;
        border: 1px solid #38bdf8 !important;
        background: rgba(15, 23, 42, 0.8) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Siber Güvenlik Asistanı")
st.markdown("<p class='subtitle'>Microsoft Yaz Stajı Projesi - Yerel Phi-3 & ChromaDB Destekli</p>", unsafe_allow_html=True)
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
    template = """Sen uzman bir siber guvenlik asistanisin. LUTFEN SADECE TURKCE DILINDE VE COK AKICI, ANLASILIR BIR DILLE YANIT VER.
Asagidaki baglam (context) bilgilerini okuyarak kullanicinin sorusunu en iyi sekilde acikla. Cevabi bulamazsan "Bilmiyorum" de ve uydurma yapma.
    
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
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba! Ben yerel siber güvenlik asistanınızım. Sisteminize yüklenen zafiyet belgeleri hakkında bana Türkçe sorular sorabilirsiniz."}]

# Gecmis mesajlari ekranda goster
for message in st.session_state.messages:
    avatar = "🛡️" if message["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Kaynaklari Gor"):
                for source in message["sources"]:
                    st.write(f"- {source}")

# Kullanici giris alani
if prompt := st.chat_input("Log4j (Log4Shell) zafiyeti nasil calisir? Nasil onlem alinir?"):
    # Kullanici mesajini ekrana ve gecmise ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
        
    # Asistan cevabi
    with st.chat_message("assistant", avatar="🛡️"):
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

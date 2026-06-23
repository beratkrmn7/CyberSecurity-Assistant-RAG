import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Sayfa ayarlarini yapiyoruz
st.set_page_config(page_title="Siber Güvenlik Asistanı", layout="wide")

# Temiz, Minimalist Tasarim (Gemini Benzeri)
st.markdown("""
<style>
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Basligi ortalama */
    .main-header {
        text-align: center;
        font-weight: 500;
        font-size: 2.5rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }

    /* Girdi Kutusu */
    .stChatInputContainer {
        border-radius: 24px !important;
        padding: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>Siber Güvenlik Asistanı</div>", unsafe_allow_html=True)
st.divider()

# RAG Sistemini baslatiyoruz ve onbellege aliyoruz (Her seferinde bastan yuklenmemesi icin)
@st.cache_resource
def init_rag_system():
    # Embedding
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Vector DB
    vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vector_db.as_retriever(search_kwargs={"k": 2})
    
    # LLM (Arka planda Ollama calismalidir) - Halusinasyonu onlemek icin temperature=0.0
    llm = ChatOllama(model="phi3", temperature=0.0)
    
    # Prompt - Phi-3 icin Chat formatinda
    system_template = """Sen uzman bir siber güvenlik asistanısın. Görevin, sana verilen 'Bağlam' (Context) bilgilerini kullanarak kullanıcının sorusunu SADECE TÜRKÇE, kısa, net ve anlaşılır bir şekilde cevaplamaktır. 
    Eğer sorunun cevabı bağlamda yoksa kesinlikle uydurma yapma ve "Bu bilgiye sahip değilim." de. Asla kendi kendine soru üretme veya şıklar (A, B, C) oluşturma.
    
Bağlam:
{context}"""

    QA_CHAIN_PROMPT = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", "{question}")
    ])
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | QA_CHAIN_PROMPT
        | llm
        | StrOutputParser()
    )
    
    return rag_chain_from_docs, retriever

# Asistani Baslat
try:
    with st.spinner("Yapay Zeka Modelleri Yüklendi... Lütfen bekleyin."):
        qa_chain_base, retriever = init_rag_system()
except Exception as e:
    st.error(f"Sistem baslatilirken hata olustu: {e}")
    st.stop()

# Chat gecmisi (Oturum kayitlari)
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Merhaba. Ben siber güvenlik asistanıyım. Sistemdeki zafiyet belgeleri hakkında bana sorular sorabilirsiniz."}]

# Gecmis mesajlari ekranda goster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Kaynakları Gör"):
                for source in message["sources"]:
                    st.write(f"- {source}")

# Kullanici giris alani
if prompt := st.chat_input("Log4j (Log4Shell) zafiyeti nasıl çalışır? Nasıl önlem alınır?"):
    # Kullanici mesajini ekrana ve gecmise ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Asistan cevabi
    with st.chat_message("assistant"):
        docs = retriever.invoke(prompt)
        
        response_placeholder = st.empty()
        full_response = ""
        
        # Streaming (Kelime kelime yazdirma)
        for chunk in qa_chain_base.stream({"context": docs, "question": prompt}):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
            
        # Imleci kaldir ve son metni koy
        response_placeholder.markdown(full_response)
        
        # Kaynaklari hazirla ve goster
        source_list = [f"Kayıt İncelemesi: {doc.metadata.get('cve_id')}" for doc in docs]
        if source_list:
            with st.expander("Kaynakları Gör"):
                for source in source_list:
                    st.write(f"- {source}")
                    
    # Asistan mesajini gecmise ekle
    st.session_state.messages.append({"role": "assistant", "content": full_response, "sources": source_list})

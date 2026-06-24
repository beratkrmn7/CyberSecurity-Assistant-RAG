import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv() # .env dosyasından API anahtarını yükler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Sayfa ayarlarini yapiyoruz
st.set_page_config(page_title="Siber Güvenlik Asistanı", layout="wide")

# Temiz, Minimalist Tasarim (Gemini Benzeri)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500&display=swap');
    
    .stApp {
        font-family: 'Outfit', sans-serif;
        background: radial-gradient(circle at 50% 50%, rgba(227, 242, 253, 0.4) 0%, rgba(255, 255, 255, 1) 50%);
    }
    
    /* Yan menü arka planı bembeyaz */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    
    /* Yeni sohbet butonu pill şeklinde ve üstte */
    [data-testid="stSidebar"] button[kind="secondary"] {
        border-radius: 20px;
        text-align: left;
        border: none;
        background-color: #f0f4f9; 
        color: #1f1f1f;
        font-weight: 500;
        padding: 10px 15px;
        margin-bottom: 10px;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #e8eaed;
    }
    
    /* Geçmiş aramalar listesi */
    [data-testid="stSidebar"] button[kind="tertiary"] {
        text-align: left;
        font-weight: 400;
        font-size: 0.9rem;
        color: #444746;
        padding-left: 10px;
        border-radius: 20px !important;
        transition: background-color 0.2s ease;
    }
    [data-testid="stSidebar"] button[kind="tertiary"]:hover {
        background-color: #f0f4f9 !important;
    }
    
    /* Popover (3 nokta) içindeki varsayılan aşağı okunu (chevron) gizle */
    [data-testid="stPopover"] button svg {
        display: none !important;
    }
    
    .main-header {
        text-align: center;
        font-weight: 400;
        font-size: 2.2rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
        color: #1f1f1f;
    }
    
    .stChatInputContainer {
        border-radius: 24px !important;
        border: 1px solid #e0e0e0 !important;
        background-color: white !important;
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
    
    # LLM (Arka planda Groq API calismalidir) - Halusinasyonu onlemek icin temperature=0.0
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)
    
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

# Chat gecmisi (Oturum kayitlari) ve Gecmis Oturumlar
if "sessions" not in st.session_state:
    st.session_state.sessions = []
if "pinned_sessions" not in st.session_state:
    st.session_state.pinned_sessions = []

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

# Yan Menü (Sidebar) - Gemini Tarzı (En sonda olmalı ki anında güncellensin)
with st.sidebar:
    # Yeni sohbet butonu en üstte
    if st.button("Yeni sohbet", use_container_width=True, type="secondary"):
        # Eğer mevcut sohbette mesaj varsa ve daha önce kaydedilmemişse geçmişe ekle
        active_user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if active_user_msgs and st.session_state.messages not in st.session_state.sessions:
            st.session_state.sessions.insert(0, list(st.session_state.messages))
            
        # Ekranı temizle
        st.session_state.messages = [{"role": "assistant", "content": "Merhaba. Ben siber güvenlik asistanıyım. Sistemdeki zafiyet belgeleri hakkında bana sorular sorabilirsiniz."}]
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Son Kullanılanlar")
    
    # Tüm oturumları toplayalım (Aktif oturum + Geçmiş oturumlar)
    display_list = []
    
    # 1. Aktif oturumu ekle (eğer içi boş değilse)
    active_user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    if active_user_msgs:
        display_list.append(st.session_state.messages)
        
    # 2. Geçmiş oturumları ekle (aktif oturumla birebir aynı olmayanları)
    for s in st.session_state.sessions:
        if s != st.session_state.messages:
            display_list.append(s)
            
    # Sabitlenenler ve Sabitlenmeyenler olarak ayır
    pinned = []
    unpinned = []
    for s in display_list:
        if s in st.session_state.pinned_sessions:
            pinned.append(s)
        else:
            unpinned.append(s)
            
    sorted_display_list = pinned + unpinned
            
    if not sorted_display_list:
        st.write("Henüz bir arama yapmadınız.")
    else:
        for i, session_msgs in enumerate(sorted_display_list):
            s_user_msgs = [m["content"] for m in session_msgs if m["role"] == "user"]
            if s_user_msgs:
                title = s_user_msgs[0]
                short_title = title[:18] + "..." if len(title) > 18 else title
                
                is_pinned = session_msgs in st.session_state.pinned_sessions
                if is_pinned:
                    short_title = "[Sabitlendi] " + short_title
                
                # Başlık ve seçenekler butonu (popover) için yan yana iki kolon
                col1, col2 = st.columns([6, 1], gap="small")
                
                with col1:
                    # Tıklanan oturumu geri yükleme
                    if st.button(short_title, key=f"session_btn_{i}_{short_title}", use_container_width=True, type="tertiary"):
                        current_active_user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
                        if current_active_user_msgs and st.session_state.messages not in st.session_state.sessions:
                            st.session_state.sessions.insert(0, list(st.session_state.messages))
                        st.session_state.messages = list(session_msgs)
                        st.rerun()
                
                with col2:
                    # Üç nokta popover menüsü
                    with st.popover("⋮", use_container_width=True):
                        # Sabitleme Butonu
                        pin_label = "Sabitlemeyi Kaldır" if is_pinned else "Sabitle"
                        if st.button(pin_label, key=f"pin_btn_{i}_{short_title}", use_container_width=True):
                            if is_pinned:
                                st.session_state.pinned_sessions.remove(session_msgs)
                            else:
                                st.session_state.pinned_sessions.append(session_msgs)
                            st.rerun()
                            
                        # Silme Butonu
                        if st.button("Sil", key=f"del2_btn_{i}_{short_title}", use_container_width=True):
                            if session_msgs == st.session_state.messages:
                                st.session_state.messages = [{"role": "assistant", "content": "Merhaba. Ben siber güvenlik asistanıyım. Sistemdeki zafiyet belgeleri hakkında bana sorular sorabilirsiniz."}]
                                if session_msgs in st.session_state.sessions:
                                    st.session_state.sessions.remove(session_msgs)
                            else:
                                st.session_state.sessions.remove(session_msgs)
                            if session_msgs in st.session_state.pinned_sessions:
                                st.session_state.pinned_sessions.remove(session_msgs)
                            st.rerun()

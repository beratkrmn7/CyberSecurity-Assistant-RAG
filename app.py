import streamlit as st
import sqlite3
import json
import numpy as np
from foundry_local_sdk import Configuration, FoundryLocalManager
import os
from dotenv import load_dotenv

load_dotenv()

# Sayfa ayarlarini yapiyoruz
st.set_page_config(page_title="Siber Güvenlik Asistanı", layout="wide", page_icon="🛡️")

# Modern Koyu Tema - Siber Güvenlik Estetiği
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ─── GENEL ZEMIN ─── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Ana içerik alanı arka planı */
    .main .block-container {
        padding-top: 2rem;
    }

    /* ─── SIDEBAR ─── */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem;
    }

    /* Yeni Sohbet butonu */
    [data-testid="stSidebar"] button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
        background-color: var(--secondary-background-color) !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        padding: 8px 14px !important;
        margin-bottom: 8px;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        border-color: var(--primary-color) !important;
    }

    /* Geçmiş oturum butonları */
    [data-testid="stSidebar"] button[kind="tertiary"] {
        text-align: left !important;
        font-size: 0.82rem !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        transition: all 0.15s ease !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stSidebar"] button[kind="tertiary"]:hover {
        background-color: rgba(128, 128, 128, 0.1) !important;
    }

    /* Popover Buton Stili (3 Nokta Menüsü için) */
    [data-testid="stPopover"] > button {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        padding: 4px !important;
        color: var(--text-color) !important;
    }
    [data-testid="stPopover"] > button:hover {
        background-color: rgba(128, 128, 128, 0.1) !important;
    }
    /* Popover chevron (ok) gizleme */
    [data-testid="stPopover"] > button svg {
        display: none !important;
    }

    /* ─── BAŞLIK ─── */
    .main-header {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.75rem;
        letter-spacing: -0.02em;
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }

    .main-subtitle {
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: var(--primary-color);
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }

    /* ─── DIVIDER ─── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(128, 128, 128, 0.2) !important;
        margin: 0.5rem 0 1.5rem 0 !important;
    }

    /* ─── CHAT MESAJLARI ─── */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0.6rem 0 !important;
    }
    
    /* Kullanıcı mesajı baloncuğu */
    [data-testid="stChatMessage"][data-testid*="user"] .stMarkdown,
    .stChatMessage:has([data-testid="chatAvatarIcon-user"]) .stMarkdown p {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 10px 14px;
    }

    /* Asistan mesaj metni */
    [data-testid="stChatMessage"] .stMarkdown p {
        font-size: 0.92rem;
        line-height: 1.7;
    }

    /* Avatar ikonları */
    [data-testid="chatAvatarIcon-assistant"] {
        background: rgba(88, 166, 255, 0.1) !important;
        border: 1px solid #58A6FF !important;
        border-radius: 8px !important;
        color: #58A6FF !important;
    }
    [data-testid="chatAvatarIcon-user"] {
        background: rgba(63, 185, 80, 0.1) !important;
        border: 1px solid #3FB950 !important;
        border-radius: 8px !important;
        color: #3FB950 !important;
    }

    /* ─── EXPANDER (Kaynaklar) ─── */
    [data-testid="stExpander"] {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary {
        color: #58A6FF !important;
        font-size: 0.8rem !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    [data-testid="stExpander"] p, [data-testid="stExpander"] div {
        font-size: 0.82rem !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ─── CHAT INPUT ─── */
    [data-testid="stChatInput"] textarea {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stChatInput"] button {
        background-color: var(--primary-color) !important;
        border-radius: 8px !important;
    }

    /* ─── SPINNER ─── */
    [data-testid="stSpinner"] p {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
    }

    /* Caption */
    .stCaption, [data-testid="stCaption"] {
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-family: 'JetBrains Mono', monospace !important;
        opacity: 0.6;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.3); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(128, 128, 128, 0.5); }

    /* ─── PULSE ÇIZGISI (SOL KENAR SİGNATURE ELEMENTİ) ─── */
    [data-testid="stSidebar"]::after {
        content: '';
        position: absolute;
        top: 0;
        right: -1px;
        width: 1px;
        height: 100%;
        background: linear-gradient(180deg, transparent 0%, #58A6FF 30%, #3FB950 70%, transparent 100%);
        opacity: 0.4;
        animation: pulse-line 4s ease-in-out infinite;
    }
    @keyframes pulse-line {
        0%, 100% { opacity: 0.2; }
        50% { opacity: 0.6; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='main-header'>🛡️ Siber Güvenlik Asistanı</div>
<div class='main-subtitle'>Threat Intelligence · CVE Analysis · RAG-Powered</div>
""", unsafe_allow_html=True)
st.divider()

# Foundry Local Kurulumu
config = Configuration(app_name="cybersec-rag-assistant")
try:
    FoundryLocalManager.initialize(config)
except Exception:
    pass # Zaten initialize edilmiş olabilir
manager = FoundryLocalManager.instance

# Modeli önbelleğe alıyoruz
@st.cache_resource
def load_embedding_model():
    model = manager.catalog.get_model("qwen3-embedding-0.6b")
    model.load()
    return model.get_embedding_client()

try:
    with st.spinner("Foundry Local Embedding Modeli Yükleniyor... Lütfen bekleyin."):
        embed_client = load_embedding_model()
except Exception as e:
    st.error(f"Sistem başlatılırken hata oluştu: {e}")
    st.stop()

def compute_cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    if norm_a == 0 or norm_b == 0: return 0.0
    return dot_product / (norm_a * norm_b)

def get_top_chunks(query, top_k=2):
    vector_result = embed_client.generate_embedding(query)
    query_vector = vector_result.data[0].embedding
    
    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cve_id, text_chunk, embedding_vector FROM documents")
        rows = cursor.fetchall()
    except Exception:
        return []
    finally:
        conn.close()
        
    scored_chunks = []
    for row in rows:
        cve_id, text_chunk, vec_json = row
        db_vector = json.loads(vec_json)
        sim_score = compute_cosine_similarity(query_vector, db_vector)
        scored_chunks.append({"cve_id": cve_id, "text": text_chunk, "score": sim_score})
        
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]

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
        # Model hızlandığı için daha fazla bilgi okuyabilmesi adına top_k'yı tekrar 2 yapıyoruz
        top_chunks = get_top_chunks(prompt, top_k=2)
        
        if not top_chunks:
            full_response = "Yerel veritabanında (SQLite) bu soruya uygun bir bilgi bulunamadı. Lütfen önce '01_data_ingestion.py' çalıştırarak veritabanını oluşturun."
            st.markdown(full_response)
            source_list = []
        else:
            context_text = "\n\n".join([chunk["text"] for chunk in top_chunks])
            system_prompt = "Sen uzman bir siber güvenlik asistanısın. Aşağıdaki bağlam (context) bilgilerini kullanarak kullanıcının sorusunu SADECE TÜRKÇE, kısa, net ve anlaşılır bir şekilde cevaplamaktır. Eğer sorunun cevabı bağlamda yoksa kesinlikle uydurma yapma ve 'Bu bilgiye sahip değilim.' de."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Bağlam:\n{context_text}\n\nSoru: {prompt}"}
            ]
            
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                # 0.5B model çok saçmaladığı için, hem hızlı hem de daha zeki olan 1.5 Milyar parametreli modele geçiyoruz
                chat_model = manager.catalog.get_model("qwen2.5-1.5b")
                
                # Modelin daha önceden (01_data_ingestion.py ile) indirildiğini varsayıyoruz
                chat_model.load()
                
                # get_chat_client() veya create_chat_client() kullanılıyor
                chat_client = chat_model.create_chat_client() if hasattr(chat_model, "create_chat_client") else chat_model.get_chat_client()
                
                # Modelin cevabı çok uzatıp CPU'yu kilitlememesi için kelime sayısını 200 ile sınırlıyoruz
                chat_client.settings.max_tokens = 200
                # Modelin halüsinasyonunu engellemek için sadece temperature kullanıyoruz.
                chat_client.settings.temperature = 0.1
                
                # Harf harf (streaming) yerine tek seferde cevap almak için complete_chat kullanıyoruz
                # Streamlit arayüzünü her harfte yenilemek CPU'yu çok yorduğu için bu yöntem çok daha hızlı olacaktır.
                with st.spinner("Asistan cevabı hazırlıyor, lütfen bekleyin..."):
                    response_obj = chat_client.complete_chat(messages)
                    if hasattr(response_obj, "choices") and response_obj.choices:
                        full_response = response_obj.choices[0].message.content or ""
                    else:
                        full_response = "Cevap üretilemedi."
                        
                    response_placeholder.markdown(full_response)
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                full_response = f"Yerel LLM (Foundry Local) bağlantısı kurulamadı. Hata detayları:\n\n```python\n{error_details}\n```\n\nLütfen arka planda Microsoft Foundry Local'ın çalıştığından emin olun."
                
            # Imleci kaldir ve son metni koy
            response_placeholder.markdown(full_response)
            
            # Kaynaklari hazirla ve goster (SQLite log)
            source_list = [f"SQLite'tan Çekildi: {chunk['cve_id']} (Benzerlik Skoru: %{chunk['score']*100:.1f})" for chunk in top_chunks]
            if source_list:
                with st.expander("Kaynakları Gör (Yerel Veritabanı)"):
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
                    # Üç nokta popover menüsü (Material Icon)
                    with st.popover("", icon=":material/more_vert:", use_container_width=True):
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
import streamlit as st
from src.rag_core import answer_query

st.set_page_config(
    page_title="Siber Güvenlik Asistanı",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Siber Güvenlik RAG Asistanı")
st.caption("CVE veritabanı ve tehdit istihbarat raporlarını sorgula — tamamen yerel, internet bağlantısı gerekmez.")

# Sidebar — filtre
with st.sidebar:
    st.header("Ayarlar")
    show_sources = st.toggle("Kaynakları göster", value=True)
    st.markdown("---")
    st.markdown("**Örnek sorular:**")
    examples = [
        "Apache'yi etkileyen kritik zafiyetler neler?",
        "Lazarus grubu hangi teknikleri kullanıyor?",
        "CVSS skoru 9 üzeri Windows zafiyetleri?",
        "Fidye yazılımı saldırılarında kullanılan CVE'ler?"
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["query"] = ex

# Sohbet geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Girdi
query = st.chat_input("Bir zafiyet veya tehdit hakkında sor...")
if "query" in st.session_state:
    query = st.session_state.pop("query")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("Model yanıt üretiyor... (Donanım hızına bağlı olarak 30-50sn sürebilir)"):
            result = answer_query(query)

        st.write(result["answer"])

        if show_sources and result["sources"]:
            st.markdown("---")
            st.caption("📎 Kullanılan kaynaklar:")
            for src in result["sources"]:
                sev = f" | Severity: `{src['severity']}`" if src["severity"] else ""
                st.caption(f"• **{src['source']}** — {src['id']}{sev} (skor: {src['score']})")

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
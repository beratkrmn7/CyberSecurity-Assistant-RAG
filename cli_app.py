from src.rag_core import answer_query

def main():
    print("Siber Güvenlik RAG Asistanı (CLI)")
    print("Çıkmak için 'q' yaz.\n")
    while True:
        query = input("Soru: ").strip()
        if query.lower() == "q":
            break
        if not query:
            continue
        result = answer_query(query)
        print(f"\nCevap:\n{result['answer']}")
        print("\nKaynaklar:")
        for src in result["sources"]:
            print(f"  - {src['source']} | {src['id']} | {src['severity']} | skor: {src['score']}")
        print()

if __name__ == "__main__":
    main()

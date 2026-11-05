# core/rag.py
import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings  # Import atualizado
from langchain_text_splitters import RecursiveCharacterTextSplitter

KNOWLEDGE_DIR = "knowledge"
INDEX_DIR = "knowledge/faiss_index"

# Modelo de embedding local (roda no PC, sem custo de API)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def _ensure_dirs():
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    os.makedirs(INDEX_DIR, exist_ok=True)

def build_index():
    """Lê todos os PDFs e TXTs da pasta knowledge e cria o índice vetorial."""
    _ensure_dirs()
    documentos = []

    # Carrega PDFs
    for pdf_file in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.pdf")):
        try:
            loader = PyPDFLoader(pdf_file)
            documentos.extend(loader.load())
        except Exception as e:
            print(f"Erro ao ler {pdf_file}: {e}")

    # Carrega TXTs
    for txt_file in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.txt")):
        try:
            loader = TextLoader(txt_file, encoding="utf-8")
            documentos.extend(loader.load())
        except Exception as e:
            print(f"Erro ao ler {txt_file}: {e}")

    if not documentos:
        return False, "Nenhum arquivo encontrado na pasta 'knowledge'."

    # Divide em pedaços menores
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(documentos)

    # Cria e salva o índice
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(INDEX_DIR)
    
    return True, f"Indexados {len(chunks)} pedaços de texto de {len(documentos)} páginas/arquivos."

def search_knowledge(query: str, k: int = 3) -> str:
    """Busca no índice vetorial os trechos mais relevantes para a pergunta."""
    _ensure_dirs()
    if not os.path.exists(os.path.join(INDEX_DIR, "index.faiss")):
        return ""  # Índice ainda não foi criado
    
    try:
        db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        docs = db.similarity_search(query, k=k)
        
        if not docs:
            return ""
            
        contexto = "\n\n--- Trechos da Base de Conhecimento ---\n"
        for d in docs:
            contexto += f"\n{d.page_content}\n"
        return contexto
    except Exception as e:
        print(f"Erro na busca vetorial: {e}")
        return ""
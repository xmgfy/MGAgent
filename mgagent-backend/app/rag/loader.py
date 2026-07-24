from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document

class DocumentLoader:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "：", ".", "!", "?", ";", ":", " ", ""]
        )
    
    def load_file(self, file_path: str) -> List[Document]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_ext = path.suffix.lower()
        
        if file_ext == ".pdf":
            loader = PyPDFLoader(str(path))
        elif file_ext == ".txt":
            loader = TextLoader(str(path), encoding="utf-8")
        elif file_ext == ".docx":
            loader = Docx2txtLoader(str(path))
        elif file_ext == ".md":
            loader = TextLoader(str(path), encoding="utf-8")
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        documents = loader.load()
        return self.text_splitter.split_documents(documents)
    
    def load_directory(self, dir_path: str) -> List[Document]:
        dir = Path(dir_path)
        if not dir.exists() or not dir.is_dir():
            raise FileNotFoundError(f"目录不存在: {dir_path}")
        
        all_documents = []
        supported_extensions = [".pdf", ".txt", ".docx", ".md"]
        
        for file in dir.iterdir():
            if file.is_file() and file.suffix.lower() in supported_extensions:
                try:
                    documents = loader.load_file(str(file))
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"加载文件失败 {file.name}: {e}")
        
        return all_documents
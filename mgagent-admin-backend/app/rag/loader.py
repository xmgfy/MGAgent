from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Optional, Dict

DEFAULT_SEPARATORS: List[str] = [
    "\n\n", "\n", "。", "！", "？", "；", "：", ".", "!", "?", ";", ":", " ", ""
]

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".php", ".swift", ".kt", ".scala",
}

SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".docx", ".md",
    ".xlsx", ".xls", ".csv", ".json",
    *CODE_EXTENSIONS,
}


def _language_from_ext(ext: str) -> str:
    ext_to_lang = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
        ".go": "go", ".rb": "ruby", ".c": "c", ".cpp": "cpp",
        ".h": "c", ".hpp": "cpp", ".cs": "csharp", ".rs": "rust",
        ".php": "php", ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
    }
    return ext_to_lang.get(ext, "text")


def _update_markdown_heading_path(chunk: Document, stack: List[str]) -> None:
    import re
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    for m in heading_pattern.finditer(chunk.page_content):
        level = len(m.group(1))
        title = m.group(2).strip()
        while len(stack) >= level:
            stack.pop()
        stack.append(title)


class DocumentLoader:
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=separators if separators is not None else DEFAULT_SEPARATORS,
        )

    def load_file(self, file_path: str) -> List[Document]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_ext = path.suffix.lower()
        base_meta = {"source": str(path), "filename": path.name}

        if file_ext == ".pdf":
            loader = PyPDFLoader(str(path))
            docs = loader.load()
        elif file_ext in (".xlsx", ".xls"):
            docs = self._load_excel(str(path), base_meta)
        elif file_ext == ".csv":
            docs = self._load_csv(str(path), base_meta)
        elif file_ext == ".json":
            docs = self._load_json(str(path), base_meta)
        elif file_ext == ".docx":
            loader = Docx2txtLoader(str(path))
            docs = loader.load()
        elif file_ext == ".md" or file_ext in CODE_EXTENSIONS or file_ext == ".txt":
            loader = TextLoader(str(path), encoding="utf-8")
            docs = loader.load()
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        for doc in docs:
            if not hasattr(doc, "metadata"):
                continue
            doc.metadata.setdefault("source", base_meta["source"])
            doc.metadata.setdefault("filename", base_meta["filename"])
            if file_ext in CODE_EXTENSIONS:
                doc.metadata["language"] = _language_from_ext(file_ext)
            doc.metadata["file_type"] = file_ext

        chunks = self.text_splitter.split_documents(docs)

        heading_stack: List[str] = []
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["total_chunks"] = len(chunks)
            chunk.metadata["char_count"] = len(chunk.page_content)
            if file_ext == ".md":
                _update_markdown_heading_path(chunk, heading_stack)
                chunk.metadata["heading_path"] = "/".join(heading_stack) if heading_stack else ""

        return chunks

    def _load_excel(self, file_path: str, base_meta: Dict) -> List[Document]:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("读取 Excel 需要 pandas，请 pip install pandas openpyxl")

        try:
            sheets = pd.read_excel(file_path, sheet_name=None)
        except Exception as e:
            raise ImportError(f"读取 Excel 失败: {e}。可能需要 pip install openpyxl")

        docs = []
        for sheet_name, df in sheets.items():
            if df.empty:
                continue
            text = df.to_string(index=False, na_rep="")
            meta = {**base_meta, "sheet_name": sheet_name, "rows": len(df)}
            docs.append(Document(page_content=text, metadata=meta))
        return docs

    def _load_csv(self, file_path: str, base_meta: Dict) -> List[Document]:
        import csv
        with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            rows = list(csv.reader(f))
        if not rows:
            return []
        header = rows[0]
        docs = []
        chunk_size = 30
        for i in range(1, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            lines = ["\t".join(header)]
            lines.extend("\t".join(r) for r in chunk)
            text = "\n".join(lines)
            meta = {**base_meta, "row_start": i, "row_end": i + len(chunk) - 1}
            docs.append(Document(page_content=text, metadata=meta))
        return docs

    def _load_json(self, file_path: str, base_meta: Dict) -> List[Document]:
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            docs = []
            for i, item in enumerate(data):
                text = json.dumps(item, ensure_ascii=False, indent=2)
                meta = {**base_meta, "item_index": i, "total_items": len(data)}
                docs.append(Document(page_content=text, metadata=meta))
            return docs
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return [Document(page_content=text, metadata=base_meta)]

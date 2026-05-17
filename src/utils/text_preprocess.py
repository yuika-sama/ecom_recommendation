"""
Tien xu ly van ban tieng Viet: lam sach, chuan hoa teencode, tach tu, loai stopwords.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

try:
    from underthesea import word_tokenize

    UNDERTHESEA_AVAILABLE = True
except Exception:
    UNDERTHESEA_AVAILABLE = False


DEFAULT_TEENCODE = {
    "sp": "sản phẩm",
    "ko": "không",
    "k": "không",
    "ok": "được",
    "gh": "giao hàng",
    "ship": "giao hàng",
    "vs": "với",
    "dc": "được",
    "đc": "được",
    "bt": "bình thường",
    "cx": "cũng",
    "nx": "nữa",
    "mn": "mọi người",
    "ae": "anh em",
    "mk": "tôi",
    "ms": "mới",
    "ad": "admin",
}

DEFAULT_STOPWORDS = {
    "và",
    "là",
    "của",
    "có",
    "trong",
    "để",
    "với",
    "một",
    "được",
    "cho",
    "những",
    "này",
    "đã",
    "tôi",
    "mình",
    "bạn",
    "rất",
    "cũng",
    "từ",
    "như",
    "nhưng",
    "khi",
    "về",
    "thì",
    "không",
    "nên",
    "phải",
    "vì",
    "lại",
    "đây",
    "thế",
    "các",
    "mà",
    "đó",
    "cái",
    "hay",
    "vẫn",
    "đều",
    "hơn",
    "ra",
    "thôi",
    "nào",
    "lắm",
    "luôn",
    "ai",
    "gì",
    "bao",
    "tuy",
    "dù",
    "vậy",
    "xong",
    "sẽ",
    "đang",
    "bị",
}

RE_HTML = re.compile(r"<[^>]+>")
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_EMAIL = re.compile(r"\S+@\S+")
RE_EMOJI = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
RE_SPECIAL_CHARS = re.compile(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]")
RE_WHITESPACE = re.compile(r"\s+")


def load_stopwords(
    file_path: str | Path | None = None,
    extra_stopwords: Iterable[str] | None = None,
) -> set[str]:
    """
    Tải danh sách stopwords từ file và kết hợp với danh sách mặc định.
    
    Args:
        file_path: Đường dẫn đến file txt chứa stopwords (mỗi từ một dòng).
        extra_stopwords: Danh sách các từ cần thêm vào tập stopwords.
        
    Returns:
        Tập hợp (set) các stopwords đã được tải.
    """
    stopwords = set(DEFAULT_STOPWORDS)
    if file_path:
        path = Path(file_path)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    token = line.strip()
                    if token:
                        stopwords.add(token)
    if extra_stopwords:
        stopwords.update(extra_stopwords)
    return stopwords


def clean_text(text: str) -> str:
    """
    Làm sạch văn bản cơ bản: loại bỏ HTML, URL, email, emoji và ký tự đặc biệt.
    
    Args:
        text: Văn bản gốc.
        
    Returns:
        Văn bản đã làm sạch và chuyển thành chữ thường.
    """
    if not isinstance(text, str):
        return ""
    text = RE_HTML.sub(" ", text)
    text = RE_URL.sub(" ", text)
    text = RE_EMAIL.sub(" ", text)
    text = RE_EMOJI.sub(" ", text)
    text = text.lower()
    text = RE_SPECIAL_CHARS.sub(" ", text)
    text = RE_WHITESPACE.sub(" ", text)
    return text.strip()


def normalize_teencode(text: str, dictionary: dict[str, str] | None = None) -> str:
    """
    Chuẩn hóa các từ viết tắt (teencode) thành từ vựng đầy đủ.
    
    Args:
        text: Văn bản cần chuẩn hóa.
        dictionary: Từ điển ánh xạ teencode. Nếu None sẽ dùng DEFAULT_TEENCODE.
        
    Returns:
        Văn bản sau khi đã chuẩn hóa các từ viết tắt.
    """
    mapping = dictionary or DEFAULT_TEENCODE
    words = text.split()
    return " ".join(mapping.get(w, w) for w in words)


def tokenize_vietnamese(text: str, use_underthesea: bool = True) -> str:
    """
    Tách từ (word segmentation) cho tiếng Việt sử dụng thư viện underthesea.
    
    Args:
        text: Văn bản đầu vào.
        use_underthesea: Cờ cho phép sử dụng underthesea. Nếu False hoặc thư viện không khả dụng, trả về văn bản gốc.
        
    Returns:
        Văn bản sau khi đã được tách từ (các từ ghép nối bằng dấu gạch dưới).
    """
    if use_underthesea and UNDERTHESEA_AVAILABLE:
        try:
            return word_tokenize(text, format="text")
        except Exception:
            return text
    return text


def remove_stopwords(text: str, stopwords: set[str] | None = None) -> str:
    """
    Loại bỏ các từ dừng (stopwords) khỏi văn bản.
    
    Args:
        text: Văn bản đầu vào.
        stopwords: Tập hợp các từ dừng. Nếu None sẽ dùng DEFAULT_STOPWORDS.
        
    Returns:
        Văn bản sau khi đã loại bỏ từ dừng và các từ có độ dài = 1.
    """
    sw = stopwords or DEFAULT_STOPWORDS
    return " ".join(w for w in text.split() if w not in sw and len(w) > 1)


def preprocess_text(
    text: str,
    stopwords: set[str] | None = None,
    use_underthesea: bool = True,
    teencode_dict: dict[str, str] | None = None,
) -> str:
    """
    Pipeline tiền xử lý văn bản tiếng Việt hoàn chỉnh.
    Các bước: Làm sạch -> Chuẩn hóa teencode -> Tách từ -> Loại stopwords.
    
    Args:
        text: Văn bản gốc cần xử lý.
        stopwords: Danh sách từ dừng cần loại bỏ.
        use_underthesea: Bật/tắt tính năng tách từ (segmentation).
        teencode_dict: Từ điển tùy chỉnh để chuẩn hóa viết tắt.
        
    Returns:
        Văn bản sau khi tiền xử lý, sẵn sàng cho feature extraction (TF-IDF, etc.).
    """
    cleaned = clean_text(text)
    normalized = normalize_teencode(cleaned, teencode_dict)
    tokenized = tokenize_vietnamese(normalized, use_underthesea=use_underthesea)
    return remove_stopwords(tokenized, stopwords)

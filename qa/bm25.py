"""Nhiệm vụ 4: Hỏi đáp quy định nghĩa vụ quân sự bằng BM25.

Quy trình:
1. Xây dựng chỉ mục BM25 (Okapi BM25) với biểu diễn văn bản đầy đủ (tên văn bản, số Điều, tên Điều, Khoản, nội dung).
2. Tiền xử lý tiếng Việt: tách từ unigram, bigram âm tiết, lọc từ dừng.
3. Truy hồi top các Điều / Khoản liên quan nhất với câu hỏi (có mở rộng ngữ cảnh cấp Điều).
4. Đưa các đoạn trích liên quan vào prompt của LLM theo cùng định dạng với Long-context.
5. Trả về kết quả cùng dạng: answer, refused, citations, retrieved, usage, seconds.
"""
import math
import re
from collections import Counter

from .core import load_chunks_cached, run

# Số lượng chunk tối đa đưa vào prompt
TOP_K = 8

# Danh sách từ dừng tiếng Việt (hư từ phổ biến trong câu hỏi tra cứu pháp luật)
STOPWORDS = {
    "là", "và", "của", "các", "những", "được", "trong", "có", "thì", "khi",
    "cho", "ở", "bởi", "do", "với", "theo", "nào", "gì", "sao", "thế_nào",
    "ra_sao", "như_thế_nào", "hãy", "cho_biết", "quy_định", "về", "một",
    "người", "như", "đã", "đang", "sẽ", "tại", "này", "đó", "đây", "tôi", "cho_tôi"
}

# Tên văn bản và từ khóa đồng nghĩa để lập chỉ mục tìm kiếm
DOC_ALIASES = {
    "LUAT_NVQS/2015": "luật nghĩa vụ quân sự luật nvqs 2015 luật 78 2015 qh13",
    "TT148/2018": "thông tư 148 2018 tt bqp thông tư 68 2025 tt bqp 36 vbhn tuyển chọn gọi công dân nhập ngũ tuyển quân",
    "TT105/2023": "thông tư 105 2023 tt bqp thông tư 106 2025 tt bqp 88 vbhn tiêu chuẩn sức khỏe khám sức khỏe phân loại sức khỏe",
}


def tokenize(text, remove_stopwords=False):
    """Tách từ, tạo unigrams và bigrams âm tiết tiếng Việt, giữ lại số thực (như 1.5, 29.9, 18.0)."""
    text_lower = text.lower()
    # Nhận diện số thực hoặc từ ngữ
    tokens = re.findall(r"\d+(?:[.,]\d+)?|\w+", text_lower)
    tokens = [t.replace(",", ".") for t in tokens]
    
    # Cặp âm tiết (bigrams) để bắt các cụm từ pháp lý: tạm_hoãn, độ_tuổi, cận_thị, sức_khỏe
    bigrams = [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    all_tokens = tokens + bigrams
    
    if remove_stopwords:
        filtered = [t for t in all_tokens if t not in STOPWORDS]
        # Nếu sau khi lọc còn token thì dùng filtered, nếu rỗng thì dùng all_tokens
        return filtered if filtered else all_tokens
    return all_tokens


def build_search_text(chunk):
    """Xây dựng trường văn bản tìm kiếm toàn diện cho chunk gồm tên VB, số Điều, tên Điều, Khoản và nội dung."""
    vb = chunk.get("van_ban", "")
    alias = DOC_ALIASES.get(vb, vb)
    dieu = f"điều {chunk.get('dieu', '')}"
    dieu_ten = chunk.get("dieu_ten", "")
    khoan = f"khoản {chunk.get('khoan', '')}" if chunk.get("khoan") else ""
    nhan = chunk.get("nhan", "")
    noi_dung = chunk.get("noi_dung", "")
    return f"{alias} {dieu} {dieu_ten} {khoan} {nhan} {noi_dung}"


class BM25Index:
    """Chỉ mục Okapi BM25 được tính sẵn và lưu trong bộ nhớ để truy vấn nhanh."""
    
    def __init__(self, chunks, k1=1.5, b=0.35):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.n = len(chunks)
        
        # Tiền xử lý toàn bộ tài liệu
        self.docs = [tokenize(build_search_text(c), remove_stopwords=True) for c in chunks]
        self.doc_lens = [len(d) for d in self.docs]
        self.avg_dl = sum(self.doc_lens) / (self.n or 1)
        
        # Xây dựng Inverted Index (từ khóa -> danh sách (doc_id, tf))
        self.inverted_index = {}
        for doc_id, doc in enumerate(self.docs):
            tf = Counter(doc)
            for term, count in tf.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((doc_id, count))
        
        # Tính IDF theo công thức Okapi BM25 chuẩn
        self.idf = {}
        for term, postings in self.inverted_index.items():
            df = len(postings)
            self.idf[term] = math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def retrieve(self, question, k=TOP_K, expand_article=True):
        """Tính điểm BM25 và trả về danh sách các chunks liên quan nhất."""
        q_tokens = tokenize(question, remove_stopwords=True)
        if not q_tokens:
            return []
        
        scores = [0.0] * self.n
        for term in set(q_tokens):
            if term not in self.inverted_index:
                continue
            term_idf = self.idf[term]
            for doc_id, count in self.inverted_index[term]:
                dl = self.doc_lens[doc_id]
                tf_weight = (count * (self.k1 + 1)) / (count + self.k1 * (1 - self.b + self.b * dl / self.avg_dl))
                scores[doc_id] += term_idf * tf_weight
        
        scored = [(scores[i], self.chunks[i]) for i in range(self.n) if scores[i] > 0]
        scored.sort(key=lambda x: -x[0])
        
        if not scored:
            return []
        
        top_chunks = [c for s, c in scored[:k]]
        
        if not expand_article:
            return top_chunks
            
        # Context Expansion (Mở rộng ngữ cảnh cấp Điều):
        # Yêu cầu đề bài: Tìm các Điều liên quan. Nếu một Điều có Khoản điểm cao trong top,
        # mở rộng thêm các Khoản khác cùng Điều để LLM có ngữ cảnh pháp lý toàn diện.
        seen_keys = set()
        result = []
        top_articles = set()
        for s, c in scored[:min(4, len(scored))]:
            top_articles.add((c["van_ban"], c["dieu"]))
            
        for s, c in scored[:k]:
            key = c["nhan"]
            if key not in seen_keys:
                seen_keys.add(key)
                result.append(c)
                
        # Bổ sung các Khoản cùng Điều liên quan (giới hạn tối đa k + 4 chunks)
        max_total = k + 4
        for c in self.chunks:
            if (c["van_ban"], c["dieu"]) in top_articles:
                key = c["nhan"]
                if key not in seen_keys and len(result) < max_total:
                    seen_keys.add(key)
                    result.append(c)
                    
        return result


# Cache chỉ mục BM25 toàn cục để không phải lập lại chỉ mục ở mỗi lượt hỏi
_BM25_INDEX_CACHE = None


def get_index(chunks):
    """Lấy hoặc khởi tạo chỉ mục BM25 từ chunks (singleton pattern)."""
    global _BM25_INDEX_CACHE
    if _BM25_INDEX_CACHE is None or len(_BM25_INDEX_CACHE.chunks) != len(chunks):
        _BM25_INDEX_CACHE = BM25Index(chunks)
    return _BM25_INDEX_CACHE


def retrieve(question, chunks=None, k=TOP_K, k1=1.5, b=0.35):
    """Hàm truy hồi BM25 phục vụ bên ngoài và unit test."""
    if chunks is None:
        chunks = load_chunks_cached()
    index = get_index(chunks)
    return index.retrieve(question, k=k, expand_article=True)


def answer(question):
    """Hỏi đáp quy định NVQS bằng phương pháp BM25 + LLM."""
    chunks = load_chunks_cached()
    found = retrieve(question, chunks)
    return run("bm25", question, found, cache=False,
               retrieved=[c["nhan"] for c in found])

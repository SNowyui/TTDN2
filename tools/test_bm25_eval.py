import json
import math
import re
from collections import Counter
from pathlib import Path

STOPWORDS = {
    "là", "và", "của", "các", "những", "được", "trong", "có", "thì", "khi",
    "cho", "ở", "bởi", "do", "với", "theo", "nào", "gì", "sao", "thế_nào",
    "ra_sao", "như_thế_nào", "hãy", "cho_biết", "quy_định", "về", "một",
    "người", "như", "đã", "đang", "sẽ", "tại", "này", "đó", "đây"
}

DOC_ALIASES = {
    "LUAT_NVQS/2015": "luật nghĩa vụ quân sự luật nvqs 2015 luật 78 2015 qh13",
    "TT148/2018": "thông tư 148 2018 tt bqp thông tư 68 2025 tt bqp 36 vbhn tuyển chọn gọi công dân nhập ngũ tuyển quân",
    "TT105/2023": "thông tư 105 2023 tt bqp thông tư 106 2025 tt bqp 88 vbhn tiêu chuẩn sức khỏe khám sức khỏe phân loại sức khỏe",
}


def tokenize(text, remove_stopwords=False):
    text_lower = text.lower()
    # Tìm cả số thực như 1.5, 29.9 hoặc từ ngữ thông thường
    tokens = re.findall(r"\d+(?:[.,]\d+)?|\w+", text_lower)
    tokens = [t.replace(",", ".") for t in tokens]
    
    # Bigrams
    bigrams = [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    all_tokens = tokens + bigrams
    
    if remove_stopwords:
        all_tokens = [t for t in all_tokens if t not in STOPWORDS]
    return all_tokens


def build_chunk_doc(c):
    vb = c.get("van_ban", "")
    alias = DOC_ALIASES.get(vb, "")
    dieu = f"điều {c.get('dieu', '')}"
    dieu_ten = c.get("dieu_ten", "")
    khoan = f"khoản {c.get('khoan', '')}" if c.get("khoan") else ""
    noi_dung = c.get("noi_dung", "")
    nhan = c.get("nhan", "")
    return f"{alias} {dieu} {dieu_ten} {khoan} {nhan} {noi_dung}"


class BM25Retriever:
    def __init__(self, chunks, k1=1.5, b=0.35):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.n = len(chunks)
        self.docs = [tokenize(build_chunk_doc(c), remove_stopwords=True) for c in chunks]
        self.doc_lens = [len(d) for d in self.docs]
        self.avg_dl = sum(self.doc_lens) / (self.n or 1)
        
        # Build inverted index
        self.inverted_index = {}
        for idx, doc in enumerate(self.docs):
            tf = Counter(doc)
            for term, count in tf.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((idx, count))
        
        # IDF
        self.idf = {}
        for term, postings in self.inverted_index.items():
            df = len(postings)
            self.idf[term] = math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def retrieve(self, question, k=8, expand_article=True):
        q_tokens = tokenize(question, remove_stopwords=True)
        if not q_tokens:
            return []
        
        scores = [0.0] * self.n
        for term in set(q_tokens):
            if term not in self.inverted_index:
                continue
            term_idf = self.idf[term]
            for doc_idx, count in self.inverted_index[term]:
                dl = self.doc_lens[doc_idx]
                tf_weight = (count * (self.k1 + 1)) / (count + self.k1 * (1 - self.b + self.b * dl / self.avg_dl))
                scores[doc_idx] += term_idf * tf_weight
        
        scored = [(scores[i], i, self.chunks[i]) for i in range(self.n) if scores[i] > 0]
        scored.sort(key=lambda x: -x[0])
        
        if not scored:
            return []
        
        top_chunks = [c for s, i, c in scored[:k]]
        
        if not expand_article:
            return top_chunks
            
        # Context expansion: Nếu trong top chunks có Điều nào match rất mạnh, bổ sung các Khoản cùng Điều
        seen_keys = set()
        result = []
        # Lấy các điều hàng đầu
        top_articles = set()
        for s, i, c in scored[:min(4, len(scored))]:
            top_articles.add((c["van_ban"], c["dieu"]))
            
        # Thêm các chunks theo thứ tự xếp hạng
        for s, i, c in scored[:k]:
            key = c["nhan"]
            if key not in seen_keys:
                seen_keys.add(key)
                result.append(c)
                
        # Bổ sung các khoản thuộc top articles nếu chưa có
        for c in self.chunks:
            if (c["van_ban"], c["dieu"]) in top_articles:
                key = c["nhan"]
                if key not in seen_keys and len(result) < k + 4:
                    seen_keys.add(key)
                    result.append(c)
                    
        return result


def main():
    with open(r"data\chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
        
    retriever = BM25Retriever(chunks)
    
    with open(r"evaluation\evaluation\Bo_15_cau_hoi_kiem_thu.json", encoding="utf-8") as f:
        data = json.load(f)
        questions = data.get("questions", [])
        
    print(f"Tổng số câu hỏi: {len(questions)}")
    full_hits = 0
    partial_hits = 0
    zero_hits = 0
    refusal_correct = 0
    
    for q in questions:
        qid = q["id"]
        qtext = q["question"]
        expected = q.get("citations", [])
        retrieved = retriever.retrieve(qtext, k=8)
        retrieved_labels = [c["nhan"] for c in retrieved]
        
        if not expected:
            # Câu ngoài phạm vi hoặc từ chối
            print(f"[{qid}] Refusal/No citation expected: '{qtext[:50]}...' -> Retrieved {len(retrieved)} chunks")
            refusal_correct += 1
            continue
            
        found_expected = [exp for exp in expected if exp in retrieved_labels]
        if set(expected).issubset(set(retrieved_labels)):
            full_hits += 1
            status = "FULL MATCH (100%)"
        elif found_expected:
            partial_hits += 1
            status = f"PARTIAL ({len(found_expected)}/{len(expected)})"
        else:
            zero_hits += 1
            status = "MISSED (0%)"
            
        print(f"[{qid}] {status} | '{qtext[:50]}...'")
        print(f"   Expected: {expected}")
        print(f"   Found:    {found_expected}")
        if not set(expected).issubset(set(retrieved_labels)):
            print(f"   Missing:  {set(expected) - set(retrieved_labels)}")
            print(f"   Top 3 ret: {retrieved_labels[:3]}")

    print("\n" + "="*50)
    print(f"Full hits (toàn bộ citations nằm trong retrieved): {full_hits}")
    print(f"Partial hits: {partial_hits}")
    print(f"Zero hits: {zero_hits}")
    print(f"Refusal questions: {refusal_correct}")


if __name__ == "__main__":
    main()

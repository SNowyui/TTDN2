"""Unit tests chuyên sâu cho Nhiệm vụ 4 (BM25) và Nhiệm vụ 5 (Citations Verification)."""
import os
import unittest
from pathlib import Path
import sys

# Thêm thư mục gốc vào path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["QA_MOCK"] = "1"

from qa import bm25, citations, core

CHUNKS = core.load_chunks()


class TestTask5Citations(unittest.TestCase):
    """Kiểm thử toàn diện Nhiệm vụ 5: Kiểm tra và xác thực trích dẫn."""

    def test_exact_citation_exists(self):
        text = "Căn cứ theo [TT148/2018 | Điều 4 | Khoản 1] công dân từ đủ 18 đến 25 tuổi."
        res = citations.check_citations(text, CHUNKS)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["label"], "TT148/2018 | Điều 4 | Khoản 1")
        self.assertTrue(res[0]["exists"])

    def test_nonexistent_citation_flagged(self):
        text = "Quy định tại [TT148/2018 | Điều 99 | Khoản 1] và [LUAT_NVQS/2015 | Điều 88]."
        res = citations.check_citations(text, CHUNKS)
        self.assertEqual(len(res), 2)
        self.assertFalse(res[0]["exists"])
        self.assertFalse(res[1]["exists"])

    def test_case_insensitive_and_whitespace_normalization(self):
        text = "Xem tại [tt148/2018 | điều 4 | khoản 1] và [  LUAT_NVQS/2015  |  Điều 30  ]."
        res = citations.check_citations(text, CHUNKS)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["label"], "TT148/2018 | Điều 4 | Khoản 1")
        self.assertTrue(res[0]["exists"])
        self.assertEqual(res[1]["label"], "LUAT_NVQS/2015 | Điều 30")
        self.assertTrue(res[1]["exists"])

    def test_deduplication_and_order_preservation(self):
        text = (
            "Đoạn 1 [TT148/2018 | Điều 4 | Khoản 1], đoạn 2 [TT105/2023 | Điều 6 | Khoản 1], "
            "đoạn 3 [TT148/2018 | Điều 4 | Khoản 1] lặp lại."
        )
        res = citations.check_citations(text, CHUNKS)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["label"], "TT148/2018 | Điều 4 | Khoản 1")
        self.assertEqual(res[1]["label"], "TT105/2023 | Điều 6 | Khoản 1")

    def test_helper_functions(self):
        self.assertTrue(citations.is_valid_citation("TT148/2018 | Điều 4 | Khoản 1", CHUNKS))
        self.assertTrue(citations.is_valid_citation("[tt148/2018 | điều 4 | khoản 1]", CHUNKS))
        self.assertFalse(citations.is_valid_citation("TT148/2018 | Điều 999", CHUNKS))
        
        chunk = citations.get_chunk_by_label("TT148/2018 | Điều 4 | Khoản 1", CHUNKS)
        self.assertIsNotNone(chunk)
        self.assertEqual(chunk["dieu"], "4")
        self.assertEqual(chunk["khoan"], "1")


class TestTask4BM25(unittest.TestCase):
    """Kiểm thử toàn diện Nhiệm vụ 4: BM25 Retrieval & QA."""

    def test_tokenizer_numbers_and_bigrams(self):
        tokens = bm25.tokenize("Cận thị lớn hơn 1.5 diop và BMI > 29.9")
        self.assertIn("1.5", tokens)
        self.assertIn("29.9", tokens)
        self.assertIn("cận_thị", tokens)

    def test_retrieval_age_query(self):
        retrieved = bm25.retrieve("độ tuổi gọi nhập ngũ thông thường là bao nhiêu?", CHUNKS)
        labels = [c["nhan"] for c in retrieved]
        self.assertTrue(any("Điều 30" in l or ("Điều 4" in l and "Khoản 1" in l) for l in labels))

    def test_retrieval_article_specific_query(self):
        # Kiểm tra khả năng bắt đúng Điều 41 Khoản 1 khi người dùng nhắc tên Điều cụ thể
        retrieved = bm25.retrieve("Theo Điều 41 Luật Nghĩa vụ quân sự 2015 trường hợp nào được tạm hoãn?", CHUNKS)
        labels = [c["nhan"] for c in retrieved]
        self.assertIn("LUAT_NVQS/2015 | Điều 41 | Khoản 1", labels)

    def test_retrieval_eye_and_bmi(self):
        retrieved = bm25.retrieve("Cận thị bao nhiêu diop và chỉ số BMI thế nào thì không phải nhập ngũ?", CHUNKS)
        labels = [c["nhan"] for c in retrieved]
        self.assertIn("TT148/2018 | Điều 4 | Khoản 3", labels)

    def test_retrieval_off_topic_returns_empty_or_low_score(self):
        retrieved = bm25.retrieve("Thủ đô của nước Pháp là thành phố nào ở châu Âu?", CHUNKS)
        # Các câu ngoài phạm vi phải trả về ít hoặc không có kết quả liên quan
        self.assertTrue(len(retrieved) == 0 or all("thủ đô" not in c["noi_dung"].lower() for c in retrieved))

    def test_bm25_answer_mock(self):
        res = bm25.answer("Độ tuổi gọi nhập ngũ là bao nhiêu?")
        self.assertEqual(res["mode"], "bm25")
        self.assertIn("answer", res)
        self.assertIn("citations", res)
        self.assertIn("retrieved", res)
        self.assertIn("usage", res)
        self.assertIn("seconds", res)
        self.assertIsInstance(res["retrieved"], list)


if __name__ == "__main__":
    unittest.main()

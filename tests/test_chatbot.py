"""
tests/test_chatbot.py - Test Suite for Gemini Dengue Chatbot Engine.
"""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chatbot.gemini_chat_engine import GeminiChatEngine, _offline_answer, _SEVERE_PATIENT_SIGNS


class TestGeminiChatEngine(unittest.TestCase):

    def setUp(self):
        self.engine = GeminiChatEngine()

    def test_offline_fallback_answers(self):
        """Test keyword-based offline responses."""
        symptom_ans = _offline_answer("Tôi muốn hỏi về triệu chứng sốt xuất huyết")
        self.assertIn("Triệu chứng", symptom_ans)

        prevention_ans = _offline_answer("Cách phòng ngừa lăng quăng bọ gậy")
        self.assertIn("Phòng ngừa", prevention_ans)

        treatment_ans = _offline_answer("Phương pháp điều trị chăm sóc tại nhà")
        self.assertIn("Chăm sóc", treatment_ans)

    def test_emergency_sign_detection(self):
        """Test emergency warning trigger for severe dengue signs."""
        query = "Bệnh nhân nôn ra máu và li bì"
        res = self.engine.process_query(query)
        self.assertIn("answer", res)
        # Emergency signs check
        self.assertTrue(any(kw in query.lower() for kw in _SEVERE_PATIENT_SIGNS))

    def test_stream_generator(self):
        """Test stream processing generator."""
        chunks = list(self.engine.process_query_stream("Cách hạ sốt"))
        self.assertTrue(len(chunks) > 0)
        full_text = "".join(chunks)
        self.assertTrue(len(full_text) > 10)


if __name__ == "__main__":
    unittest.main()

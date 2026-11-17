"""
tests/test_chatbot.py - Test Suite for Gemini Dengue Chatbot Engine.
"""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from chatbot.gemini_chat_engine import (
    CONFIRMATION_PROMPT,
    GeminiChatEngine,
    _offline_answer,
    _SEVERE_PATIENT_SIGNS,
    is_confirmation_reply,
)


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

    def test_offtopic_confirmation_guard(self):
        """Test that off-topic queries require confirmation unless confirmed=True."""
        offtopic_q = "Hôm nay thời tiết Hà Nội thế nào?"
        self.assertFalse(self.engine.is_dengue_related(offtopic_q))

        res = self.engine.process_query(offtopic_q)
        self.assertEqual(res["answer"], CONFIRMATION_PROMPT)
        self.assertTrue(res["requires_confirmation"])
        self.assertEqual(res["intent"], "CONFIRMATION_REQUIRED")

        confirmed_res = self.engine.process_query(offtopic_q, confirmed=True)
        self.assertNotEqual(confirmed_res["answer"], CONFIRMATION_PROMPT)
        self.assertFalse(confirmed_res["requires_confirmation"])

    def test_dengue_related_skips_confirmation(self):
        """Test that dengue-related queries do not trigger confirmation."""
        self.assertTrue(self.engine.is_dengue_related("Triệu chứng sốt xuất huyết là gì?"))
        self.assertTrue(self.engine.is_dengue_related("Muỗi vằn truyền bệnh gì?"))

    def test_confirmation_reply_parser(self):
        """Test yes/no confirmation reply parsing."""
        self.assertEqual(is_confirmation_reply("Yes"), "yes")
        self.assertEqual(is_confirmation_reply("Có."), "yes")
        self.assertEqual(is_confirmation_reply("ok"), "yes")
        self.assertEqual(is_confirmation_reply("no"), "no")
        self.assertEqual(is_confirmation_reply("Không!"), "no")
        self.assertIsNone(is_confirmation_reply("Triệu chứng sốt xuất huyết"))


if __name__ == "__main__":
    unittest.main()

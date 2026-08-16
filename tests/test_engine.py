# -*- coding: utf-8 -*-
"""
專案名稱：本機系統快取清理與記憶體優化工具 (System Optimizer Tool)
單元測試模組：核心引擎單元測試 (tests/test_engine.py)
"""

import os
import sys
import unittest
import tempfile
import shutil

# 將專案根目錄納入 Python 搜尋路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.config import CONFIG, format_size_str, load_protected_keywords, save_protected_keywords
from engine.cache_rules import CacheRule, CacheRuleRegistry
from engine.cache_inspector import CacheInspectorEngine
from engine.storage_analyzer import StorageAnalyzerEngine
from engine.uninstaller import UninstallerEngine
from engine.memory import get_system_ram_info


class TestConfigEngine(unittest.TestCase):
    def test_format_size_str(self):
        self.assertEqual(format_size_str(500.0), "500.0 MB")
        self.assertEqual(format_size_str(1024.0), "1.00 GB")
        self.assertEqual(format_size_str(2048.0), "2.00 GB")

    def test_whitelist_keywords(self):
        original = list(CONFIG.PROTECTED_KEYWORDS)
        test_kw = ["unit_test_protect_keyword_xyz"]
        
        saved = save_protected_keywords(test_kw)
        self.assertTrue(saved)
        
        loaded = load_protected_keywords()
        self.assertIn("unit_test_protect_keyword_xyz", loaded)
        
        # 復原白名單
        save_protected_keywords(original)


class TestCacheRulesEngine(unittest.TestCase):
    def test_cache_rule_creation(self):
        rule = CacheRule(
            name="測試快取規則",
            category="測試類別",
            patterns=["C:\\TestPath"],
            risk_level="safe"
        )
        self.assertEqual(rule.name, "測試快取規則")
        self.assertEqual(rule.risk_level, "safe")

    def test_default_rules_registry(self):
        rules = CacheRuleRegistry.get_default_rules()
        self.assertGreater(len(rules), 0)
        
        names = [r.name for r in rules]
        self.assertIn("使用者暫存區 (Temp)", names)

    def test_assess_cache_risk(self):
        risk, category, rec, auto_clean = CacheInspectorEngine.assess_cache_risk(r"C:\Users\test\AppData\Local\Google\Chrome\User Data\Default\Cache")
        self.assertIn("安全", risk)
        self.assertTrue(auto_clean)

        risk_unk, category_unk, rec_unk, auto_clean_unk = CacheInspectorEngine.assess_cache_risk(r"C:\Users\test\AppData\Local\UnknownApp\CustomCache")
        self.assertIn("未知", risk_unk)
        self.assertFalse(auto_clean_unk)


class TestStorageAnalyzerEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_duplicate_finder(self):
        # 建立兩個 100% 相同的大於 1MB 測試檔案
        file1 = os.path.join(self.test_dir, "test_dup1.bin")
        file2 = os.path.join(self.test_dir, "test_dup2.bin")
        dummy_content = b"A" * (1024 * 1024 + 512)  # > 1MB
        
        with open(file1, "wb") as f:
            f.write(dummy_content)
        with open(file2, "wb") as f:
            f.write(dummy_content)

        dup_groups = StorageAnalyzerEngine.analyze_duplicate_files(lambda msg, color=None: None, target_dirs=[self.test_dir])
        self.assertEqual(len(dup_groups), 1)
        self.assertEqual(len(dup_groups[0]["paths"]), 2)


class TestUninstallerEngine(unittest.TestCase):
    def test_leftovers_confidence_score(self):
        candidates = UninstallerEngine.scan_appdata_leftovers_with_confidence("NonExistentApp123456")
        self.assertIsInstance(candidates, list)


class TestMemoryEngine(unittest.TestCase):
    def test_get_system_ram_info(self):
        total, avail, used, load = get_system_ram_info()
        self.assertGreaterEqual(total, 0.0)
        self.assertGreaterEqual(load, 0)
        self.assertLessEqual(load, 100)


if __name__ == "__main__":
    unittest.main()

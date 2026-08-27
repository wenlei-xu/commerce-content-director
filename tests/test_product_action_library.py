import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "query_product_actions.py"


def load_module():
    spec = importlib.util.spec_from_file_location("query_product_actions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class FakeFeishu:
    def __init__(self, records):
        self._records = records

    def records(self, _app_token, _table_id):
        return self._records


class ProductActionLibraryTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.schema = {
            "app_token": "app-test",
            "tables": {
                "product_action_library": {
                    "table_id": "actions",
                    "product_link_field": "产品",
                    "availability_field": "是否可用",
                    "availability_active": "可用",
                    "fields": {
                        "action": "动作",
                        "how_to": "怎么玩",
                        "visual_focus": "画面重点",
                    },
                }
            },
        }
        self.records = [
            {"record_id": "action-1", "fields": {"产品": ["product-durian"], "动作": "拔河", "怎么玩": "轻拉互动", "画面重点": "接触点可见", "是否可用": "可用"}},
            {"record_id": "action-2", "fields": {"产品": ["product-durian"], "动作": "未确认动作", "怎么玩": "待核实", "画面重点": "待核实", "是否可用": "待确认"}},
            {"record_id": "action-3", "fields": {"产品": ["product-pineapple"], "动作": "推动", "怎么玩": "推动探索", "画面重点": "结构可见", "是否可用": "可用"}},
        ]

    def test_returns_only_available_actions_for_product(self):
        result = self.module.query_actions(FakeFeishu(self.records), self.schema, "product-durian")
        self.assertEqual([item["action"] for item in result["actions"]], ["拔河"])

    def test_can_include_unavailable_for_maintenance(self):
        result = self.module.query_actions(FakeFeishu(self.records), self.schema, "product-durian", include_unavailable=True)
        self.assertEqual([item["action"] for item in result["actions"]], ["拔河", "未确认动作"])


if __name__ == "__main__":
    unittest.main()

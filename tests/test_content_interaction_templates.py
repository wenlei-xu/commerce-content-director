import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "query_content_interaction_templates.py"


def load_module():
    spec = importlib.util.spec_from_file_location("query_content_interaction_templates", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class FakeFeishu:
    def __init__(self, records_by_table):
        self._records_by_table = records_by_table

    def records(self, _app_token, table_id):
        return self._records_by_table[table_id]


class ContentInteractionTemplateTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.schema = {
            "app_token": "app-test",
            "tables": {
                "products": {
                    "table_id": "products",
                    "status_field": "状态",
                    "status_active": "可用",
                    "fields": {
                        "interaction_constraints": "交互限制",
                    },
                },
                "content_interaction_templates": {
                    "table_id": "templates",
                    "availability_field": "模板状态",
                    "availability_active": "可用",
                    "fields": {
                        "template_name": "互动模板",
                        "content_function": "内容功能",
                        "behavior_flow": "行为流程",
                        "visual_acceptance": "可视验收点",
                    },
                },
            },
        }
        self.api = FakeFeishu({
            "products": [
                {"record_id": "product-durian", "fields": {"状态": "可用", "交互限制": "只允许轻拉。"}},
                {"record_id": "product-paused", "fields": {"状态": "停用", "交互限制": ""}},
            ],
            "templates": [
                {"record_id": "template-1", "fields": {"互动模板": "引逗够取", "内容功能": ["兴趣", "互动"], "行为流程": "手持引逗后落地", "可视验收点": "狗狗主动够取", "模板状态": "可用"}},
                {"record_id": "template-2", "fields": {"互动模板": "追逐叼回", "内容功能": ["兴趣"], "行为流程": "抛出后叼回", "可视验收点": "狗狗追逐后叼回", "模板状态": "可用"}},
                {"record_id": "template-3", "fields": {"互动模板": "待审核模板", "内容功能": ["兴趣"], "行为流程": "", "可视验收点": "", "模板状态": "待确认"}},
            ],
        })

    def test_returns_all_active_templates_for_product_review(self):
        result = self.module.query_templates(self.api, self.schema, "product-durian")
        self.assertEqual([item["template_name"] for item in result["templates"]], ["引逗够取", "追逐叼回"])

    def test_compatibility_is_reviewed_against_product_facts(self):
        result = self.module.query_templates(self.api, self.schema, "product-durian", include_ineligible=True)
        self.assertEqual(len(result["templates"]), 2)

    def test_rejects_an_unavailable_product(self):
        with self.assertRaisesRegex(ValueError, "not available"):
            self.module.query_templates(self.api, self.schema, "product-paused")

    def test_returns_visual_acceptance(self):
        result = self.module.query_templates(self.api, self.schema, "product-durian")
        self.assertEqual(result["templates"][0]["visual_acceptance"], "狗狗主动够取")


if __name__ == "__main__":
    unittest.main()

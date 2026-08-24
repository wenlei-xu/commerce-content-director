#!/usr/bin/env python3
"""Regression checks for the two reusable knowledge-library validators."""

from __future__ import annotations

import unittest

from validate_sentence_pattern import validate as validate_sentence
from validate_short_video_breakdown import validate as validate_breakdown


class KnowledgeLibraryContractTests(unittest.TestCase):
    @staticmethod
    def reusable_breakdown() -> dict[str, object]:
        return {
            "资产状态": "待审核",
            "目标受众与使用场景": "养宠家庭；家庭互动场景。",
            "叙事视角与表达形式": "主人观察视角；UGC实测。",
            "开头钩子类型": "异常反应＋结果疑问",
            "核心冲突或问题": "宠物是否会主动参与。",
            "钩子兑现时间与方式": "20秒；宠物主动推动产品。",
            "产品首次出现时间": "3秒",
            "核心卖点及出现顺序": "可装零食→宠物互动→即时奖励",
            "证明链条及出现顺序": "闻到→推动→掉粮→吃到",
            "主要说服机制": "宠物自然行为实测",
            "CTA类型": "点击了解",
            "可参考的叙事模板": "适合：宠物参与、结果可视的产品。\n结构：异常疑问→操作证明→行为结果。\n主要证明：主体自然行为证明结果。\n不适合：无法展示即时结果的产品。",
            "字幕表达模板": "类型：重点强调字幕。\n基础样式：底部白字黑描边。\n强调对象：数字、结果词。\n强调方式：黄色放大。\n出现节奏：短语级出现。",
            "叙事节点参考帧": ["S01-钩子-0.2s.jpg"],
            "逐段复刻模板": "| 段落 | 时间 | 叙事任务 | 参考帧 | 原内容 | 保留机制 | 新内容模板 |\n| --- | --- | --- | --- | --- | --- | --- |\n| S01 | 0–3s | 钩子 | S01-钩子-0.2s.jpg | 四只湿猫＋疑问字幕 | 低机位、主体占比、异常视觉＋结果疑问 | [主体]盯着[产品]＋[倒计时问题] |",
        }

    def test_approved_sentence_pattern_requires_one_slot_and_valid_metadata(self) -> None:
        report = validate_sentence({
            "句式名称": "结果先问型钩子",
            "句式用途": "钩子",
            "语言": "语义模板",
            "原句示例": "它真的会去碰吗？",
            "模板句式": "[主体]真的会对[产品]做出[动作]吗？",
            "使用说明": "用于异常结果前的提问。",
            "审核状态": "可用",
        })
        self.assertTrue(report["ok"], report)

    def test_sentence_pattern_without_slot_is_blocked(self) -> None:
        report = validate_sentence({
            "句式名称": "坏样例", "句式用途": "钩子", "语言": "中文",
            "原句示例": "试试看", "模板句式": "试试看", "使用说明": "无", "审核状态": "待审核",
        })
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "MISSING_SLOT")

    def test_breakdown_requires_summary_and_segment_start_frame_mapping(self) -> None:
        report = validate_breakdown(self.reusable_breakdown())
        self.assertTrue(report["ok"], report)

    def test_breakdown_rejects_unattached_reference_frame(self) -> None:
        record = self.reusable_breakdown()
        record["字幕表达模板"] = "类型：无字幕。"
        record["逐段复刻模板"] = "| 段落 | 时间 | 叙事任务 | 参考帧 | 原内容 | 保留机制 | 新内容模板 |\n| --- | --- | --- | --- | --- | --- | --- |\n| S01 | 0–3s | 钩子 | missing.jpg | 原内容 | 原构图 | [主体]使用[产品] |"
        report = validate_breakdown(record)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "REFERENCE_FRAME_NOT_ATTACHED")

    def test_breakdown_rejects_incomplete_emphasis_caption_template(self) -> None:
        record = self.reusable_breakdown()
        record["字幕表达模板"] = "类型：重点强调字幕。\n强调方式：黄色放大。"
        report = validate_breakdown(record)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "CAPTION_LABEL_MISSING")

    def test_breakdown_rejects_missing_commercial_field(self) -> None:
        record = self.reusable_breakdown()
        del record["主要说服机制"]
        report = validate_breakdown(record)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "MISSING_COMMERCIAL_FIELD")

    def test_breakdown_rejects_retired_fields(self) -> None:
        record = self.reusable_breakdown()
        record["高光帧"] = [{"name": "highlight.jpg"}]
        report = validate_breakdown(record)
        self.assertFalse(report["ok"])
        self.assertEqual(report["errors"][0]["code"], "RETIRED_FIELD_PRESENT")

    def test_archive_only_breakdown_does_not_require_replication_assets(self) -> None:
        report = validate_breakdown({"资产状态": "仅留档", "ASR原文": "证据"})
        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()

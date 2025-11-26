import pytest
import json
import logging
import re
from unittest.mock import MagicMock 

# 导入被测模块中的所有函数和类
# 假设您的服务文件名为 ai_service.py
from taiga.projects.userstories.services import (
    generate_single_story, 
    AIServiceError, 
    get_default_story, 
    preprocess,
    anonymize,
    clean_text
)

# ----------------------------------------------------------------------
#                         核心服务功能测试 (真实集成测试)
# ----------------------------------------------------------------------

# 注意：此测试将依赖于：
# 1. 您的 .env 文件必须存在且配置正确。
# 2. 您的网络连接和 AI 服务必须可用。

def test_generate_single_story_real_integration():
    """
    【集成测试】测试 generate_single_story 针对真实需求能否成功调用
    AI 服务，并在不使用 Mocking 的情况下返回正确的结构。
    
    此测试会发起实际的外部 API 调用。
    """
    print("\n--------Test generate_single_story(requirement_text: str)-------")
    # 需求文本已改为英文
    requirement = "As a registered user, I want to be able to set my profile picture so that other users can better identify me."
    print("Natural language: ", requirement)
    
    try:
        result = generate_single_story(requirement)
        print("User Story Generated from AI:\n", result)
    except AIServiceError as e:
        # 如果 AI 服务调用失败，我们将视为配置或连接问题，测试失败
        pytest.fail(f"AI Service call failed. Please check your .env configuration (API Key, Base URL) and network connection. Error: {e}")

    # 验证返回结构是否符合目标 JSON 格式
    assert isinstance(result, dict)
    assert "suggestion_subject" in result
    assert "suggestion_description" in result
    assert "suggestion_tags" in result
    
    # 验证描述是否包含用户故事格式的关键部分 (As a / I want / So that)
    assert "as a" in result["suggestion_description"].lower()
    assert "i want" in result["suggestion_description"].lower()
    assert "so that" in result["suggestion_description"].lower()
    
    # 验证标签数量是否在 [3, 5] 范围内
    assert len(result["suggestion_tags"]) >= 3
    assert len(result["suggestion_tags"]) <= 5


# ----------------------------------------------------------------------
#                           预处理辅助函数测试 (纯单元测试，保留)
# ----------------------------------------------------------------------

def test_anonymize_all_patterns():
    """测试 anonymize 函数是否正确替换所有类型的敏感信息。"""
    raw_text = "Email: user@test.com, Phone: 13912345678, ID: 44000019900101123X, Card: 6228123412341234."
    result = anonymize(raw_text)
    expected = "Email: [EMAIL], Phone: [PHONE], ID: [ID], Card: [BANKCARD]."
    print("--------Test anonymize(text: str)-------")
    print("Raw Text: ", raw_text)
    print("Anonymized Text: ", result)
    assert result == expected

def test_clean_text_removal():
    """测试 clean_text 是否移除 HTML 和 URL，并规范化空格。"""
    raw_text = " <p>Check this out: http://example.com/page. </p>   Extra   spaces. "
    result = clean_text(raw_text)
    expected = "Check this out: Extra spaces."
    print("--------Test clean_text(text: str)-------")
    print("Raw Text: ", raw_text)
    print("Cleaned Text: ", result)
    assert result == expected
    
def test_preprocess_pipeline():
    """测试整个预处理流程（匿名化 -> 清洗）的组合效果。"""
    raw_text = "Contact 13912345678 via <a href='http://link.com'>link</a>."
    result = preprocess(raw_text)
    expected = "Contact [PHONE] via link."
    print("--------Test preprocess(text: str)-------")
    print("Raw Text:", raw_text)
    print("Preprocessed Text:", result)
    assert result == expected

import pytest
import json
from unittest.mock import patch
from taiga.projects.issues import services, validators
from .. import factories as f

pytestmark = pytest.mark.django_db

class TestIssueAIAnalysisValidator:
    def test_validator_happy_path(self):
        project = f.ProjectFactory.create()
        issue = f.IssueFactory.create(project=project)
        
        data = {
            "project_id": project.id,
            "issue_ids": [issue.id],
            "issues": [{"id": issue.id, "subject": "Test Issue"}]
        }
        
        validator = validators.IssueAIAnalysisValidator(data=data)
        assert validator.is_valid(), validator.errors

    def test_validator_issues_length_mismatch(self):
        project = f.ProjectFactory.create()
        
        data = {
            "project_id": project.id,
            "issue_ids": [1, 2], # 2 IDs
            "issues": [{"id": 1}] # 1 Issue object
        }
        
        validator = validators.IssueAIAnalysisValidator(data=data)
        assert validator.is_valid() is False
        assert "non_field_errors" in validator.errors
        # 验证错误信息包含长度不一致的提示
        assert "must have the same length" in validator.errors["non_field_errors"][0]

    def test_validator_issue_not_in_project(self):
        project1 = f.ProjectFactory.create()
        project2 = f.ProjectFactory.create()
        issue_in_p2 = f.IssueFactory.create(project=project2)
        
        data = {
            "project_id": project1.id, # 指向项目 1
            "issue_ids": [issue_in_p2.id], # Issue 属于项目 2
            "issues": [{"id": issue_in_p2.id}]
        }
        
        validator = validators.IssueAIAnalysisValidator(data=data)
        assert validator.is_valid() is False
        assert "non_field_errors" in validator.errors
        assert "don't belong to this project" in validator.errors["non_field_errors"][0]

    def test_validator_max_issues_limit(self):
        project = f.ProjectFactory.create()
        # 构造 51 个 ID
        ids = list(range(51))
        
        data = {
            "project_id": project.id,
            "issue_ids": ids,
            "issues": [{"id": i} for i in ids]
        }
        
        validator = validators.IssueAIAnalysisValidator(data=data)
        assert validator.is_valid() is False
        assert "issue_ids" in validator.errors
        assert "Synchronous mode supports max 50 issues." in validator.errors["issue_ids"][0]


class TestAIService:
    def test_analyze_issues_success(self):
        """测试 Service 正确调用底层 AI 并解析 JSON"""
        issues_data = [
            {"id": 1, "ref": 10, "subject": "Login bug", "description": "Cannot login"}
        ]
        
        # 模拟 AI 返回的 JSON 字符串
        mock_ai_response = json.dumps({
            "priority": "High",
            "priority_reason": "Critical bug",
            "type": "Bug",
            "severity": "Critical",
            "description": "Analysis...",
            "related_modules": ["Auth"],
            "solutions": ["Fix auth"],
            "confidence": 0.9
        })

        # Patch 'ask_once' 因为它是从 taiga.doubai_ai 导入的
        with patch("taiga.projects.issues.services.ask_once", return_value=mock_ai_response) as mock_ask:
            results = services.analyze_issues_with_ai(issues_data)
            
            assert len(results) == 1
            res = results[0]
            assert res["issue_id"] == 1
            assert res["analysis"]["priority"] == "High"
            assert res["analysis"]["confidence"] == 0.9
            
            # 验证 Prompt 构建是否包含 Issue 信息
            call_args = mock_ask.call_args
            assert "Login bug" in call_args[1]['question'] # question is the first arg or kwarg

    def test_analyze_issues_ai_failure_fallback(self):
        """测试当 AI 服务抛出异常时，Service 返回默认值而不是崩溃"""
        issues_data = [{"id": 1, "subject": "Test"}]
        
        with patch("taiga.projects.issues.services.ask_once", side_effect=Exception("AI Down")):
            results = services.analyze_issues_with_ai(issues_data)
            
            assert len(results) == 1
            res = results[0]
            # 应该返回默认分析结果
            assert res["analysis"]["priority"] == "Normal"
            assert "AI service is temporarily unavailable" in res["analysis"]["description"]
            # 应该包含错误信息
            assert "error" in res
            assert str(res["error"]) == "AI Down"

    def test_analyze_issues_invalid_json_response(self):
        """测试 AI 返回了非 JSON 格式的文本"""
        issues_data = [{"id": 1, "subject": "Test"}]
        
        with patch("taiga.projects.issues.services.ask_once", return_value="I am not a JSON object"):
            results = services.analyze_issues_with_ai(issues_data)
            
            assert len(results) == 1
            res = results[0]
            # 解析失败应回退到默认值
            assert res["analysis"]["priority"] == "Normal"
            assert res["analysis"]["confidence"] == 0.0
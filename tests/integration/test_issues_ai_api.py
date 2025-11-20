import json
import pytest
from unittest.mock import patch
from .. import factories as f

pytestmark = pytest.mark.django_db

def url():
    return "/api/v1/issues/ai_analyze"

def test_ai_analyze_api_permission_success(client):
    """
    Test that users with 'view_issues' permission can access the API
    """
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    # 创建角色并赋予 view_issues 权限
    role = f.RoleFactory.create(project=project, permissions=["view_issues"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    
    issue = f.IssueFactory.create(project=project)
    
    client.login(user)
    
    payload = {
        "project_id": project.id,
        "issue_ids": [issue.id],
        "issues": [{"id": issue.id, "subject": issue.subject}]
    }
    
    # Mock Service layer, we only care if API called Service
    with patch("taiga.projects.issues.services.analyze_issues_with_ai") as mock_service:
        mock_service.return_value = [{"issue_id": issue.id, "analysis": "mocked"}]
        
        response = client.post(url(), json.dumps(payload), content_type="application/json")
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_issues"] == 1
    mock_service.assert_called_once()

def test_ai_analyze_api_permission_denied(client):
    """
    Test that users without 'view_issues' permission are denied (403 Forbidden)
    """
    project_owner = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=project_owner)
    issue = f.IssueFactory.create(project=project)
    
    # Create another user who is a member but has no permissions
    user_no_perm = f.UserFactory.create()
    role_no_perm = f.RoleFactory.create(project=project, permissions=[]) # 无权限
    f.MembershipFactory.create(project=project, user=user_no_perm, role=role_no_perm)
    
    client.login(user_no_perm)
    
    payload = {
        "project_id": project.id,
        "issue_ids": [issue.id],
        "issues": [{"id": issue.id, "subject": "test"}]
    }
    
    response = client.post(url(), json.dumps(payload), content_type="application/json")
    
    # 根据 permissions.py: ai_analyze_perms = IsAuthenticated() & HasProjectPerm('view_issues')
    assert response.status_code == 403

def test_ai_analyze_api_validation_error(client):
    """
    测试 API 正确返回 400 错误
    """
    user = f.UserFactory.create()
    client.login(user)
    
    # 缺少 project_id 和 issues
    payload = {}
    
    response = client.post(url(), json.dumps(payload), content_type="application/json")
    
    assert response.status_code == 400
    data = response.json()
    assert "project_id" in data
    assert "issue_ids" in data

def test_ai_analyze_api_project_not_found(client):
    """
    测试项目不存在时返回 400 (由验证器拦截)
    """
    user = f.UserFactory.create()
    client.login(user)
    
    payload = {
        "project_id": 99999, # 不存在的 ID
        "issue_ids": [1],
        "issues": [{"id": 1}]
    }
    
    response = client.post(url(), json.dumps(payload), content_type="application/json")
    
    
    assert response.status_code == 400
    
    # 可选：验证错误信息确实是关于 project_id 的
    data = response.json()
    assert "project_id" in data or "non_field_errors" in data
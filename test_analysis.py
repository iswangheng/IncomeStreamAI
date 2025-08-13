#!/usr/bin/env python3
"""
测试分析功能的单元测试
用于验证AI分析功能的核心流程
"""

import json
import requests
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_analysis_workflow():
    """测试完整的分析工作流程"""
    base_url = "http://localhost:5000"
    
    # 测试数据
    test_form_data = {
        'project_name': '测试项目',
        'project_description': '这是一个测试项目的描述，用于验证AI分析功能是否正常工作。',
        'project_stage': 'planning',
        'person_name[]': ['测试人员A', '测试人员B'],
        'person_role[]': ['测试角色1', '测试角色2'],
        'person_resources[]': ['测试资源1,测试资源2', '测试资源3,测试资源4'],
        'person_needs[]': ['recognition,money', 'learning,networking'],
        'external_resources': ['测试外部资源1', '测试外部资源2']
    }
    
    session = requests.Session()
    
    try:
        logger.info("=== 开始测试分析工作流程 ===")
        
        # 1. 测试主页是否可访问
        logger.info("1. 测试主页访问...")
        response = session.get(f"{base_url}/")
        assert response.status_code == 200, f"主页访问失败: {response.status_code}"
        logger.info("✓ 主页访问成功")
        
        # 2. 提交表单数据
        logger.info("2. 提交测试表单...")
        response = session.post(f"{base_url}/generate", data=test_form_data)
        assert response.status_code == 302, f"表单提交失败: {response.status_code}"
        assert '/thinking' in response.headers.get('Location', ''), "未正确重定向到thinking页面"
        logger.info("✓ 表单提交成功，重定向到thinking页面")
        
        # 3. 访问thinking页面
        logger.info("3. 访问thinking页面...")
        response = session.get(f"{base_url}/thinking")
        assert response.status_code == 200, f"thinking页面访问失败: {response.status_code}"
        logger.info("✓ thinking页面访问成功")
        
        # 4. 轮询分析状态，最多等待60秒
        logger.info("4. 开始轮询分析状态...")
        max_attempts = 30  # 30次尝试，每次间隔2秒
        analysis_completed = False
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"   尝试 {attempt}/{max_attempts}")
            
            response = session.get(f"{base_url}/check_analysis_status")
            assert response.status_code == 200, f"状态检查失败: {response.status_code}"
            
            # 验证返回的是JSON
            try:
                status_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"   响应不是有效的JSON: {response.text[:200]}")
                raise AssertionError(f"状态检查返回无效JSON: {e}")
            
            logger.info(f"   状态: {status_data.get('status', 'unknown')}")
            
            if status_data.get('status') == 'completed':
                redirect_url = status_data.get('redirect_url')
                assert redirect_url == '/results', f"重定向URL不正确: {redirect_url}"
                logger.info("✓ 分析完成，获得正确的重定向URL")
                analysis_completed = True
                break
            elif status_data.get('status') == 'error':
                error_msg = status_data.get('message', '未知错误')
                raise AssertionError(f"分析过程中发生错误: {error_msg}")
            elif status_data.get('status') in ['not_started', 'processing']:
                logger.info(f"   分析进行中，等待2秒后重试...")
                time.sleep(2)
            else:
                raise AssertionError(f"未知的分析状态: {status_data.get('status')}")
        
        if not analysis_completed:
            raise AssertionError(f"分析在{max_attempts * 2}秒内未完成")
        
        # 5. 访问结果页面
        logger.info("5. 访问结果页面...")
        response = session.get(f"{base_url}/results")
        assert response.status_code == 200, f"结果页面访问失败: {response.status_code}"
        
        # 检查页面内容包含预期的关键词
        content = response.text
        assert '路径' in content or 'paths' in content, "结果页面缺少路径内容"
        assert '项目' in content or 'project' in content, "结果页面缺少项目信息"
        logger.info("✓ 结果页面访问成功，包含预期内容")
        
        logger.info("=== 所有测试通过！分析功能工作正常 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        return False

def test_status_endpoint_direct():
    """直接测试状态检查端点的健壮性"""
    base_url = "http://localhost:5000"
    
    try:
        logger.info("=== 测试状态端点健壮性 ===")
        
        session = requests.Session()
        
        # 测试没有session数据时的响应
        response = session.get(f"{base_url}/check_analysis_status")
        assert response.status_code == 200, f"状态检查失败: {response.status_code}"
        
        # 验证返回JSON
        try:
            status_data = response.json()
            logger.info(f"无session时的响应: {status_data}")
            assert status_data.get('status') == 'error', "预期应该返回错误状态"
            assert '没有找到分析数据' in status_data.get('message', ''), "错误消息不正确"
            logger.info("✓ 无session数据时正确返回错误状态")
        except json.JSONDecodeError:
            raise AssertionError("状态端点没有返回有效JSON")
        
        logger.info("=== 状态端点健壮性测试通过 ===")
        return True
        
    except Exception as e:
        logger.error(f"状态端点测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始运行分析功能测试...")
    
    # 测试1: 状态端点健壮性
    if not test_status_endpoint_direct():
        logger.error("状态端点测试失败")
        exit(1)
    
    # 测试2: 完整工作流程
    if not test_analysis_workflow():
        logger.error("完整工作流程测试失败")
        exit(1)
    
    logger.info("🎉 所有测试通过！系统运行正常")
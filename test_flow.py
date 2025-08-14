#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试整个数据流程：从表单数据到AI分析"""

import json
import logging
from app import app, db
from openai_service import AngelaAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_flow():
    """测试完整的数据流程"""
    
    # 1. 模拟表单数据（与首页表单一致的格式）
    form_data = {
        "projectName": "Bonnie英语培训管道",
        "projectDescription": "连接需要英语培训的学生家长与优质英语老师，通过建立标准化培训产品和中介平台，形成稳定的非劳务收入管道",
        "projectStage": "初期阶段",
        "keyPersons": [
            {
                "name": "王老师",
                "role": "英语培训老师",
                "resources": ["英语教学经验", "教学资质", "时间灵活"],
                "make_happy": "带来客户/引流,获得持续收入"
            },
            {
                "name": "李顾问",
                "role": "教育规划师",
                "resources": ["学生家长资源", "升学规划经验"],
                "make_happy": "不冲突现有合作,品牌曝光"
            }
        ],
        "externalResources": ["微信群渠道", "教育类公众号", "家长社群"]
    }
    
    logger.info("=" * 60)
    logger.info("测试数据流程开始")
    logger.info("=" * 60)
    
    # 2. 测试AI服务是否能正确接收和处理数据
    logger.info("\n步骤1: 初始化AI服务")
    angela_ai = AngelaAI()
    
    logger.info("\n步骤2: 准备的表单数据：")
    logger.info(json.dumps(form_data, ensure_ascii=False, indent=2))
    
    # 3. 测试知识库访问
    logger.info("\n步骤3: 测试知识库访问")
    with app.app_context():
        try:
            kb_snippets = angela_ai.get_knowledge_base_snippets(
                form_data['projectDescription'],
                form_data['keyPersons'],
                form_data['externalResources'],
                db.session
            )
            logger.info(f"知识库返回内容长度: {len(kb_snippets)}字符")
            logger.info(f"知识库内容预览: {kb_snippets[:200]}...")
        except Exception as e:
            logger.error(f"知识库访问失败: {e}")
            kb_snippets = angela_ai.get_core_knowledge_fallback()
            logger.info("使用核心知识要点作为备用")
    
    # 4. 测试AI分析生成
    logger.info("\n步骤4: 调用AI生成非劳务收入路径")
    with app.app_context():
        try:
            # 调用AI生成服务
            result = angela_ai.generate_income_paths(form_data, db.session)
            
            if result:
                logger.info("✅ AI分析成功完成！")
                logger.info("\n生成的收入路径概览：")
                
                # 显示概览信息
                if 'overview' in result:
                    overview = result['overview']
                    logger.info(f"- 情况分析: {overview.get('situation', 'N/A')}")
                    logger.info(f"- 收入类型: {overview.get('income_type', 'N/A')}")
                    logger.info(f"- 核心洞察: {overview.get('core_insight', 'N/A')}")
                    
                    if 'gaps' in overview:
                        logger.info(f"- 发现缺口: {len(overview['gaps'])}个")
                        for gap in overview['gaps'][:2]:
                            logger.info(f"  • {gap}")
                
                # 显示生成的路径
                if 'paths' in result:
                    logger.info(f"\n生成了 {len(result['paths'])} 条收入路径：")
                    for i, path in enumerate(result['paths'], 1):
                        logger.info(f"\n路径{i}: {path.get('name', 'N/A')}")
                        logger.info(f"- 收入机制: {path.get('income_mechanism', 'N/A')}")
                        logger.info(f"- 收益触发: {path.get('revenue_trigger', 'N/A')}")
                        logger.info(f"- MVP验证: {path.get('mvp', 'N/A')}")
                        
                        # 显示三方结构
                        if 'three_parties_structure' in path:
                            structure = path['three_parties_structure']
                            logger.info(f"- 三方结构:")
                            logger.info(f"  甲方: {structure.get('party_a', 'N/A')}")
                            logger.info(f"  乙方: {structure.get('party_b', 'N/A')}")
                            logger.info(f"  你的角色: {structure.get('your_role', 'N/A')}")
                
                # 验证结果是否符合预期格式
                logger.info("\n数据验证:")
                logger.info(f"✓ 结果包含overview: {'overview' in result}")
                logger.info(f"✓ 结果包含paths: {'paths' in result}")
                logger.info(f"✓ 路径数量: {len(result.get('paths', []))}")
                
            else:
                logger.error("❌ AI分析返回空结果")
                
        except Exception as e:
            logger.error(f"❌ AI分析失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)

if __name__ == "__main__":
    test_data_flow()
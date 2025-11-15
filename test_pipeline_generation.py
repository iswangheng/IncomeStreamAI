
#!/usr/bin/env python3
"""
测试非劳务收入管道生成功能
模拟真实表单提交,诊断网络/API调用问题
"""
import os
import sys
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pipeline_generation():
    """测试管道生成完整流程"""
    logger.info("=" * 80)
    logger.info("开始测试非劳务收入管道生成")
    logger.info("=" * 80)
    
    # 检查环境变量
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ 未找到 OPENAI_API_KEY 环境变量")
        return False
    
    logger.info(f"✅ API Key 已找到: {api_key[:20]}...")
    
    # 准备测试数据 - 模拟真实表单提交
    test_form_data = {
        "projectName": "测试项目-咨询服务撮合",
        "projectDescription": "我想做一个企业管理咨询的撮合平台,连接有需求的企业和专业咨询师",
        "keyPersons": [
            {
                "name": "张总",
                "role": "enterprise_owner",
                "resources": ["客户资源", "行业人脉", "企业案例"],
                "make_happy": "bring_leads,recurring_income",
                "notes": "有大量中小企业客户资源"
            },
            {
                "name": "李老师",
                "role": "service_provider",
                "resources": ["专业咨询能力", "培训经验", "课程体系"],
                "make_happy": "recognition,money",
                "notes": "资深管理咨询专家"
            }
        ],
        "externalResources": []
    }
    
    logger.info("\n" + "=" * 80)
    logger.info("测试数据:")
    logger.info(json.dumps(test_form_data, ensure_ascii=False, indent=2))
    logger.info("=" * 80 + "\n")
    
    try:
        # 导入 AngelaAI
        logger.info("📦 导入 AngelaAI 服务...")
        from openai_service import AngelaAI
        
        # 创建实例
        angela = AngelaAI()
        logger.info("✅ AngelaAI 实例创建成功")
        
        # 调用生成方法
        logger.info("\n" + "=" * 80)
        logger.info("🚀 开始调用 generate_income_paths()...")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # 这里不传db.session,因为是独立测试
        result = angela.generate_income_paths(test_form_data, None)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info(f"✅ API 调用成功! 耗时: {duration:.2f} 秒")
        logger.info("=" * 80)
        
        # 验证返回结果
        if not result:
            logger.error("❌ 返回结果为空")
            return False
        
        if not isinstance(result, dict):
            logger.error(f"❌ 返回结果类型错误: {type(result)}")
            return False
        
        # 检查是否是备用方案
        overview = result.get('overview', {})
        situation = overview.get('situation', '')
        
        if '设计者作为统筹方' in situation and '基于【意识+能量+能力=结果】公式分析' in situation:
            logger.warning("⚠️  检测到这是备用方案(fallback),不是真实AI生成")
            logger.warning("⚠️  这说明OpenAI API调用可能失败了")
        else:
            logger.info("✅ 确认是真实 OpenAI 生成的内容")
        
        # 打印结果概要
        logger.info("\n" + "=" * 80)
        logger.info("返回结果概要:")
        logger.info("-" * 80)
        logger.info(f"项目洞察: {overview.get('core_insight', 'N/A')[:100]}...")
        
        pipelines = result.get('pipelines', [])
        logger.info(f"\n生成管道数量: {len(pipelines)}")
        
        for i, pipeline in enumerate(pipelines, 1):
            logger.info(f"\n管道 {i}: {pipeline.get('name', 'N/A')}")
            logger.info(f"  收入机制: {pipeline.get('income_mechanism', {}).get('type', 'N/A')}")
            logger.info(f"  参与方数量: {len(pipeline.get('parties_structure', []))}")
        
        logger.info("=" * 80)
        
        # 保存完整结果到文件
        output_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📄 完整结果已保存到: {output_file}")
        
        return True
        
    except ConnectionError as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ 网络连接错误 - 这是卡住的主要原因!")
        logger.error("=" * 80)
        logger.error(f"错误详情: {str(e)}")
        logger.error("\n可能原因:")
        logger.error("  1. laozhang.ai 中转API响应超时")
        logger.error("  2. 网络不稳定导致SSL连接失败")
        logger.error("  3. API Key 配置问题")
        return False
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ 其他错误")
        logger.error("=" * 80)
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误详情: {str(e)}")
        
        import traceback
        logger.error("\n完整堆栈:")
        logger.error(traceback.format_exc())
        
        return False

if __name__ == "__main__":
    print("\n" + "🔍 " * 40)
    print("开始诊断测试...")
    print("🔍 " * 40 + "\n")
    
    success = test_pipeline_generation()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 测试通过! 管道生成功能正常")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ 测试失败! 请查看上面的错误信息")
        print("=" * 80)
        print("\n💡 建议检查:")
        print("  1. 环境变量 OPENAI_API_KEY 是否正确")
        print("  2. 网络连接是否稳定")
        print("  3. laozhang.ai 中转API是否可访问")
        sys.exit(1)

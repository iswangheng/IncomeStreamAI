import os
import json
import logging
from openai import OpenAI
from typing import Dict, List, Any, Optional

# OpenAI客户端初始化
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
import httpx
import time

# 创建带优化连接配置的客户端
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=httpx.Timeout(40.0, connect=15.0),  # 优化超时：连接15秒，读取40秒
    http_client=httpx.Client(
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=httpx.Timeout(40.0, connect=15.0)
    )
)

logger = logging.getLogger(__name__)


class AngelaAI:
    """Angela - 非劳务收入管道设计AI服务"""

    def __init__(self):
        self.default_model = "gpt-4o"  # 默认模型
        self.default_max_tokens = 2500  # 默认token数量

    def get_model_config(self, config_type='main_analysis'):
        """从数据库获取模型配置"""
        try:
            # 延迟导入避免循环导入问题
            import importlib
            models_module = importlib.import_module('models')
            ModelConfig = getattr(models_module, 'ModelConfig')
            config = ModelConfig.get_config(config_type, self.default_model)
            return config
        except Exception as e:
            logger.warning(f"Failed to get model config: {e}, using defaults")
            return {
                'model': self.default_model,
                'temperature': 0.7,
                'max_tokens': self.default_max_tokens,
                'timeout': 45
            }

    def _call_openai_with_retry(self, **kwargs):
        """调用OpenAI API，带强化重试机制"""
        logger.info("=== _call_openai_with_retry方法被调用 ===")
        logger.info(f"传入参数: model={kwargs.get('model')}, timeout={kwargs.get('timeout')}")
        max_retries = 2  # 减少重试次数，避免长时间阻塞
        for attempt in range(max_retries):
            try:
                logger.info(f"正在调用OpenAI API (尝试 {attempt + 1}/{max_retries})...")
                
                # 为每次重试创建新的客户端连接，避免连接复用问题
                if attempt > 0:
                    fresh_client = OpenAI(
                        api_key=os.environ.get("OPENAI_API_KEY"),
                        timeout=httpx.Timeout(45.0, connect=15.0)  # 缩短超时时间
                    )
                    return fresh_client.chat.completions.create(**kwargs)
                else:
                    return client.chat.completions.create(**kwargs)
                    
            except (httpx.TimeoutException, httpx.ConnectError, ConnectionError, 
                    httpx.ReadTimeout, httpx.ConnectTimeout, TimeoutError,
                    OSError, ConnectionResetError, BrokenPipeError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)  # 缩短等待时间: 2s, 4s
                    logger.warning(f"OpenAI API网络超时 (尝试 {attempt + 1}): {str(e)}, {wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"OpenAI API网络连接失败，已重试{max_retries}次: {str(e)}")
                    # 抛出一个明确的网络错误，让调用方知道是网络问题
                    raise ConnectionError(f"网络连接问题，无法访问OpenAI服务")
            except SystemExit as e:
                # 特殊处理Gunicorn worker退出信号
                logger.error(f"Worker进程退出信号: {str(e)}")
                raise ConnectionError("服务重启中，请稍后重试")
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['ssl', 'recv', 'connection', 'broken pipe', 'reset']):
                    logger.error(f"网络连接问题: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        raise ConnectionError("网络连接不稳定")
                else:
                    logger.error(f"OpenAI API调用遇到其他错误: {str(e)}")
                    raise e

    def format_role_to_chinese(self, role_identifier: str) -> str:
        """将英文角色标识符转换为中文显示"""
        role_mapping = {
            # 需求方角色
            'enterprise_owner': '企业主',
            'store_owner': '实体店主', 
            'department_head': '部门负责人',
            'brand_manager': '主理人',
            # 交付方角色
            'product_provider': '产品方',
            'service_provider': '服务方',
            'traffic_provider': '流量方',
            'other_provider': '其他资源方'
        }
        return role_mapping.get(role_identifier, role_identifier)

    def get_role_type_by_identifier(self, role_identifier: str) -> str:
        """根据角色标识符获取角色类型（需求方/交付方等）"""
        demand_roles = ['enterprise_owner', 'store_owner', 'department_head', 'brand_manager']
        delivery_roles = ['product_provider', 'service_provider', 'traffic_provider', 'other_provider']
        
        if role_identifier in demand_roles:
            return '需求方'
        elif role_identifier in delivery_roles:
            return '交付方'
        else:
            return '其他方'

    def format_make_happy(self, make_happy_data) -> str:
        """格式化动机标签数据"""
        if not make_happy_data:
            return "未指定"

        # 如果是字符串，先分割成列表
        if isinstance(make_happy_data, str):
            make_happy_list = make_happy_data.split(',')
        else:
            make_happy_list = make_happy_data

        # 映射值到显示文本（包含新的实际标签）
        label_map = {
            'recognition': '获得认可/名声',
            'learning': '学习新知识/技能',
            'networking': '扩展人脉/社交圈',
            'fun': '娱乐放松/享受过程',
            'helping': '帮助他人/社会价值',
            'money': '获得金钱/经济收益',
            'power': '获得权力/影响力',
            'creation': '创造作品/表达自我',
            'growth': '个人成长/突破挑战',
            # 新增实际使用的标签
            'bring_leads': '带来客户/引流',
            'recurring_income': '获得持续收入',
            'no_conflict_current_partner': '不冲突现有合作',
            'brand_exposure': '品牌曝光',
            'expand_network': '拓展网络/人脉'
        }

        return "、".join([
            label_map.get(item.strip(), item.strip())
            for item in make_happy_list
        ])

    def format_external_resources(self, resources_data: List[str]) -> str:
        """格式化外部资源数据"""
        if not resources_data:
            return "无可用外部资源"

        # 按资源类型分组
        categories = {'资金支持': [], '市场渠道': [], '执行能力': [], '战略合作': []}

        # 根据资源内容分类（简化版）
        for resource in resources_data:
            if any(keyword in resource
                   for keyword in ['资金', '投资', '预算', '赞助']):
                categories['资金支持'].append(resource)
            elif any(keyword in resource
                     for keyword in ['渠道', '平台', '媒体', '社群']):
                categories['市场渠道'].append(resource)
            elif any(keyword in resource
                     for keyword in ['技术', '团队', '设备', '工具']):
                categories['执行能力'].append(resource)
            else:
                categories['战略合作'].append(resource)

        result = []
        for category, items in categories.items():
            if items:
                result.append(f"{category}: {', '.join(items)}")

        return "; ".join(result) if result else "通用外部资源可用"

    def get_knowledge_base_snippets(self, project_description: str,
                                    key_persons: List[Dict],
                                    external_resources: List[str],
                                    db_session) -> str:
        """从知识库中检索相关片段"""
        try:
            import importlib
            models_module = importlib.import_module('models')
            KnowledgeItem = getattr(models_module, 'KnowledgeItem')

            # 获取活跃状态的知识库条目
            knowledge_items = db_session.query(KnowledgeItem).filter(
                KnowledgeItem.status == 'active').all()

            if not knowledge_items:
                return self.get_core_knowledge_fallback()

            # 优先查找非劳务收入相关的知识库内容
            non_labor_income_items = [
                item for item in knowledge_items if item.content_summary and
                ('非劳务收入' in item.content_summary or '管道' in
                 item.content_summary or '租金' in item.content_summary or '股份'
                 in item.content_summary or '版权' in item.content_summary
                 or 'Bonnie' in item.content_summary or 'Angela' in
                 item.content_summary or '楚楚' in item.content_summary or '知了猴'
                 in item.content_summary or '英语培训' in item.content_summary
                 or '商铺' in item.content_summary)
            ]

            relevant_snippets = []

            # 如果找到非劳务收入相关内容，优先使用
            if non_labor_income_items:
                for item in non_labor_income_items[:2]:  # 最多2个核心条目
                    if item.content_summary:
                        # 提取更多有用信息，特别关注核心原理和案例
                        summary = item.content_summary[:800]  # 增加到800字符获取更多信息
                        relevant_snippets.append(f"• {summary}")
                        item.usage_count += 1

            # 补充其他相关条目
            other_items = [
                item for item in knowledge_items
                if item not in non_labor_income_items
            ]
            for item in other_items[:2]:  # 最多再补充2个
                if item.content_summary and len(relevant_snippets) < 4:
                    summary = item.content_summary[:300]
                    relevant_snippets.append(f"• {summary}")
                    item.usage_count += 1

            # 如果没有找到相关内容，返回核心知识要点
            if not relevant_snippets:
                return self.get_core_knowledge_fallback()

            return "\n".join(relevant_snippets)

        except Exception as e:
            logger.error(f"Knowledge base retrieval error: {e}")
            return self.get_core_knowledge_fallback()

    def get_core_knowledge_fallback(self) -> str:
        """当知识库检索失败时的核心知识要点"""
        return """• 非劳务收入核心公式：意识+能量+能力（行动）=结果
• 七大类型：租金（万物皆可租）、利息、股份/红利、版权、专利、企业连锁、团队收益
• 三步法则：盘资源→搭管道→动真格
• 核心原则：让关键环节的关键人物都高兴，严格区分需换取的人物资源vs可直接动用的外部资源
• 成功要素：1)设计共赢机制 2)掌握核心信息+筛选规则 3)前置合作规则
• 成功案例参考：Bonnie英语培训管道（连接规划师+机构，年40万收入）、Angela商铺二房东（1万启动，8年72万收入）、楚楚知了猴管道（7条管道，年70万收入）"""

    def generate_income_paths(self, form_data: Dict[str, Any],
                              db_session) -> Dict[str, Any]:
        """生成非劳务收入路径"""
        logger.info("=== Angela AI generate_income_paths方法开始 ===")
        logger.info(f"输入数据: {json.dumps(form_data, ensure_ascii=False)}")
        try:
            # 提取表单数据
            project_name = form_data.get('projectName', '未命名项目')
            project_description = form_data.get('projectDescription', '')
            key_persons = form_data.get('keyPersons', [])
            external_resources = form_data.get('externalResources', [])

            # 获取知识库片段 - 简化以减少prompt长度
            try:
                kb_snippets = self.get_knowledge_base_snippets(
                    project_description, key_persons, external_resources,
                    db_session)
                # 限制知识库内容长度
                if len(kb_snippets) > 500:
                    kb_snippets = kb_snippets[:500] + "..."
            except Exception as kb_error:
                logger.warning(f"Knowledge base retrieval failed: {kb_error}")
                kb_snippets = self.get_core_knowledge_fallback()

            # 简化系统提示 - 专注于个性化分析  
            system_prompt = """你是Angela，专业的非劳务收入管道设计师。

## 任务
根据用户的具体项目特点，设计个性化的非劳务收入管道方案。

## 核心原则
- 非劳务收入类型：租金、利息、股份、版权、居间、企业连锁、团队收益
- 设计者通过整合资源获得收益，而非依赖持续劳动
- 让所有参与方获益，设计者控制关键环节

## 要求
- 深入分析项目特点，提供针对性建议
- 避免通用模板，体现项目独特性  
- 说明具体的收益机制和第一步行动

## 分析要点
针对这个具体项目，请分析：
1. 项目的独特机会点在哪里？
2. 现有资源如何形成收益闭环？  
3. 设计者可以通过什么方式获得非劳务收入？
4. 第一步应该如何行动？"""

            # 构造用户提示
            user_content = f"""【项目名称】{project_name}
【项目背景】{project_description}

【关键人物】（含角色、资源、动机）"""

            for i, person in enumerate(key_persons):
                name = person.get('name', f'人物{i+1}')
                role = person.get('role', '')  # 修正：使用role而不是roles
                resources = person.get('resources', [])
                make_happy = person.get('make_happy',
                                        '')  # 修正：使用make_happy而不是makeHappy
                notes = person.get('notes', '')

                # 将英文角色标识符转换为中文显示名称
                role_chinese = self.format_role_to_chinese(role) if role else "未指定"
                role_type = self.get_role_type_by_identifier(role) if role else "其他方"

                user_content += f"""
- 人物：{name}｜角色：{role_chinese}（{role_type}）
  资源：{", ".join(resources) if resources else "无"}
  动机标签（如何让TA高兴）：{self.format_make_happy(make_happy)}
  备注：{notes if notes else "无"}"""

            user_content += f"""

【外部资源（可直接使用的资源池）】
{self.format_external_resources(external_resources)}

【知识库要点】（只给要点，避免冗长）
{kb_snippets}"""

            # 构建关键人物列表用于提示
            key_persons_names = ', '.join([
                person.get('name', f'人物{i+1}')
                for i, person in enumerate(key_persons)
            ])

            # 简化assistant prompt - 专注于个性化生成
            assistant_prompt = f"""请根据这个具体项目，生成个性化的非劳务收入管道建议。

要求：
1. 必须体现项目的独特特点
2. 管道名称要反映项目特色，避免通用模板
3. 针对项目的具体痛点和机会
4. 说明如何利用现有资源

请返回JSON格式：
{{
  "overview": {{
    "situation": "项目分析（针对具体项目情况）",
    "income_type": "适用的非劳务收入类型",
    "core_insight": "核心洞察（项目的独特机会）",
    "gaps": ["缺少的关键角色"],
    "suggested_roles_to_hunt": []
  }},
  "pipelines": [
    {{
      "id": "pipeline_1", 
      "name": "针对项目的具体管道名称",
      "income_mechanism": {{
        "type": "收入类型",
        "trigger": "收益触发点",
        "settlement": "结算方式"
      }},
      "parties_structure": [
        {{
          "party": "参与方名称",
          "role_type": "需求方/交付方/资金方/统筹方",
          "role_value": "该参与方的价值",
          "resources": ["资源1", "资源2"],
          "motivation": "参与动机"
        }}
      ],
      "mvp": "针对项目的最小验证方案",
      "first_step": "项目的具体第一步行动",
      "risks_and_plan_b": [
        {{
          "risk": "风险点",
          "plan_b": "应对方案"
        }}
      ]
    }}
  ]
}}"""

            logger.info(f"系统提示长度: {len(system_prompt)} 字符")
            logger.info(f"用户内容长度: {len(user_content)} 字符")  
            logger.info(f"助手提示长度: {len(assistant_prompt)} 字符")

            # OpenAI API调用
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": assistant_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=3000
                )
                
                result_text = response.choices[0].message.content
                logger.info(f"AI原始响应: {result_text[:500]}...")
                
                # 解析JSON
                result = json.loads(result_text)
                logger.info("✅ JSON解析成功")
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始响应: {result_text}")
                return self.get_fallback_response()
                
            except Exception as e:
                logger.error(f"OpenAI API调用失败: {e}")
                return self.get_fallback_response()

        except Exception as e:
            logger.error(f"生成非劳务收入路径时发生错误: {e}")
            return self.get_fallback_response()

    def get_fallback_response(self):
        """返回备用响应"""
        return {
            "overview": {
                "situation": "由于技术问题，暂时无法生成个性化分析",
                "income_type": "居间", 
                "core_insight": "请重试或联系技术支持",
                "gaps": [],
                "suggested_roles_to_hunt": []
            },
            "pipelines": [{
                "id": "pipeline_1",
                "name": "暂时无法生成",
                "income_mechanism": {
                    "type": "居间",
                    "trigger": "暂时无法生成",
                    "settlement": "暂时无法生成"
                },
                "parties_structure": [],
                "mvp": "请重试",
                "first_step": "请重试",
                "risks_and_plan_b": []
            }]
        }
                raise ConnectionError(f"OpenAI API连接失败: {str(api_error)}")

            # 解析响应
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("AI返回内容为空")
            result = json.loads(result_text)

            # 验证结果结构
            if not self._validate_result_structure(result):
                raise ValueError("AI返回结构不完整")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._get_fallback_result(form_data)
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._get_fallback_result(form_data)

    def refine_path(self, pipeline_data: Dict[str, Any],
                    refinement_data: Dict[str,
                                          Any], db_session) -> Dict[str, Any]:
        """细化指定管道（基于最新prompt要求）"""
        try:
            selected_pipeline_id = refinement_data.get(
                'selected_pipeline_id',
                refinement_data.get('selected_path_id'))
            add_personas = refinement_data.get('add_personas', [])
            constraints = refinement_data.get('constraints', '')
            tweaks = refinement_data.get('tweaks', '')

            # 构造完整的系统提示（基于主要prompt的核心原则）
            system_prompt = """你是"Angela"，专精非劳务收入管道设计的高级商业顾问。现在需要细化优化一条现有路径。

【核心原则】
1. 遵循【意识+能量+能力=结果】公式
2. 七大类型：租金/利息/股份/版权/居间/企业连锁/团队收益
3. 设计者必须为"统筹方"，其他人物保持原有role_type
4. 输出框架性方案，不写执行颗粒度
5. 保持所有用户提供的关键人物，名称完全一致

【优化要求】
- 保持路径ID不变
- 完善framework_logic的逻辑链条
- 优化防绕过机制和收益触发点
- 确保MVP更加可行
- 降低劳动量估算"""

            user_content = f"""【当前管道】
{json.dumps(pipeline_data, ensure_ascii=False, indent=2)}

【补充人物】（需要整合到parties_structure中）
{json.dumps(add_personas, ensure_ascii=False, indent=2)}

【约束条件】
{constraints}

【调整要求】
{tweaks}

请严格按照最新JSON结构优化这条管道，重点完善framework_logic、parties_structure、MVP和防绕过机制。保持ID不变，但优化其他所有字段。"""

            # 获取模型配置
            model_config = self.get_model_config('refinement')

            response = self._call_openai_with_retry(
                model=model_config['model'],
                messages=[{
                    "role": "system",
                    "content": system_prompt
                }, {
                    "role": "user",
                    "content": user_content
                }],
                response_format={"type": "json_object"},
                temperature=0.6,
                max_tokens=model_config['max_tokens'],
                timeout=model_config['timeout'])

            # 如果响应为None（网络错误），返回原管道
            if response is None:
                logger.warning("Pipeline refinement API返回None，保持原管道")
                return pipeline_data

            result_text = response.choices[0].message.content
            if not result_text:
                return pipeline_data

            result = json.loads(result_text)

            # 验证细化后的管道结构（简化验证）
            if not result.get('id') or not result.get('name'):
                logger.warning(
                    "Refined pipeline missing basic fields, returning original"
                )
                return pipeline_data

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Pipeline refinement JSON parsing error: {e}")
            return pipeline_data
        except Exception as e:
            logger.error(f"Pipeline refinement error: {e}")
            # 返回原管道作为后备
            return pipeline_data

    def _validate_result_structure(self, result: Dict[str, Any]) -> bool:
        """验证返回结果的结构完整性（基于最新pipelines结构）"""
        # 验证顶级结构
        required_keys = ['overview', 'pipelines']
        if not all(key in result for key in required_keys):
            logger.warning(
                f"Missing top-level keys. Has: {list(result.keys())}, Required: {required_keys}"
            )
            return False

        # 验证overview结构
        overview = result.get('overview', {})
        required_overview_keys = [
            'situation', 'income_type', 'core_insight', 'gaps',
            'suggested_roles_to_hunt'
        ]
        if not all(key in overview for key in required_overview_keys):
            logger.warning(
                f"Overview missing keys. Has: {list(overview.keys())}, Required: {required_overview_keys}"
            )
            return False

        # 验证pipelines结构
        pipelines = result.get('pipelines', [])
        if not pipelines:
            logger.warning("No pipelines found")
            return False

        for i, pipeline in enumerate(pipelines):
            # 验证pipeline的必需字段（基于新的prompt结构）
            required_pipeline_keys = [
                'id', 'name', 'income_mechanism', 'parties_structure',
                'framework_logic', 'mvp', 'weak_link', 'revenue_trigger',
                'risks_and_planB', 'first_step', 'labor_load_estimate'
            ]
            if not all(key in pipeline for key in required_pipeline_keys):
                logger.warning(
                    f"Pipeline {i} missing required keys. Has: {list(pipeline.keys())}, Required: {required_pipeline_keys}"
                )
                return False

            # 验证income_mechanism结构
            income_mechanism = pipeline.get('income_mechanism', {})
            if not all(key in income_mechanism
                       for key in ['type', 'trigger', 'settlement']):
                logger.warning(f"Pipeline {i} income_mechanism incomplete")
                return False

            # 验证parties_structure结构
            parties = pipeline.get('parties_structure', [])
            if not parties:
                logger.warning(f"Pipeline {i} has empty parties_structure")
                return False

            # 验证每个参与方的结构
            for j, party in enumerate(parties):
                required_party_keys = [
                    'party', 'role_type', 'resources', 'role_value',
                    'make_them_happy'
                ]
                if not all(key in party for key in required_party_keys):
                    logger.warning(
                        f"Pipeline {i} party {j} missing keys. Has: {list(party.keys())}, Required: {required_party_keys}"
                    )
                    return False

                # 验证role_type值
                valid_role_types = ['需求方', '交付方', '资金方', '统筹方']
                if party.get('role_type') not in valid_role_types:
                    logger.warning(
                        f"Pipeline {i} party {j} has invalid role_type: {party.get('role_type')}"
                    )
                    return False

            # 验证framework_logic结构
            framework_logic = pipeline.get('framework_logic', {})
            required_framework_keys = [
                'resource_chain', 'motivation_match', 'designer_position',
                'designer_income'
            ]
            if not all(key in framework_logic
                       for key in required_framework_keys):
                logger.warning(f"Pipeline {i} framework_logic incomplete")
                return False

            # 验证labor_load_estimate结构
            labor_load = pipeline.get('labor_load_estimate', {})
            if not all(key in labor_load
                       for key in ['hours_per_week', 'level', 'alternative']):
                logger.warning(f"Pipeline {i} labor_load_estimate incomplete")
                return False

        return True

    def _get_fallback_result(self, form_data: Dict[str,
                                                   Any]) -> Dict[str, Any]:
        """降级返回结果（当AI调用失败时）- 基于最新prompt要求的完整结构"""
        project_name = form_data.get('projectName', '项目')
        project_description = form_data.get('projectDescription', '')
        key_persons = form_data.get('keyPersons', [])

        # 智能判断是否需要补充角色
        needs_additional_roles = len(key_persons) < 2  # 简单规则：少于2个人物时建议补充
        
        # 分析现有人物的角色类型分布
        existing_role_types = set()
        for person in key_persons:
            original_role = person.get('role', '')
            if original_role:
                role_type = self.get_role_type_by_identifier(original_role)
                existing_role_types.add(role_type)
        
        # 检查是否缺少关键角色类型
        required_types = {'需求方', '交付方'}
        missing_types = required_types - existing_role_types
        if missing_types:
            needs_additional_roles = True

        # 构建参与方结构（保留所有用户输入的关键人物）
        parties_structure = [{
            "party":
            "设计者（你）",
            "role_type":
            "统筹方",
            "resources": ["统筹协调能力", "规则制定", "合作伙伴筛选标准", "结算管理"],
            "role_value":
            "作为连接器和规则制定者，确保各方合作顺畅，控制核心环节",
            "make_them_happy":
            "通过撮合服务获得稳定的非劳务收入，建立可持续的商业管道"
        }]

        # 为每个关键人物分配合适的role_type
        role_type_mapping = {
            0: "需求方",  # 第一个人物默认为需求方
            1: "交付方",  # 第二个人物默认为交付方
        }

        for i, person in enumerate(key_persons):
            name = person.get('name', f'关键人物{i+1}')
            resources = person.get('resources', ['专业技能', '客户基础'])
            make_happy = person.get('make_happy', ['获得收益', '扩展业务'])
            
            # 如果有原始role信息，优先使用role类型判断，否则使用索引映射
            original_role = person.get('role', '')
            if original_role:
                role_type = self.get_role_type_by_identifier(original_role)
            else:
                role_type = role_type_mapping.get(i, "交付方")  # 超过2个的默认为交付方

            parties_structure.append({
                "party":
                name,
                "role_type":
                role_type,
                "resources":
                resources if resources else ["专业能力", "客户资源"],
                "role_value":
                f"在闭环中提供{role_type}的核心价值，确保服务质量和客户满意度",
                "make_them_happy":
                self.format_make_happy(make_happy)
            })

        # 添加待补齐角色（如果需要）
        if needs_additional_roles and missing_types:
            for missing_type in missing_types:
                role_name_mapping = {
                    "需求方": "渠道客户源",
                    "交付方": "专业服务方",
                    "资金方": "投资合作方"
                }
                role_name = role_name_mapping.get(missing_type, "合作伙伴")
                
                parties_structure.append({
                    "party": f"【待补齐】{role_name}",
                    "role_type": missing_type,
                    "resources": ["待确定的关键资源", "待匹配的合作能力"],
                    "role_value": f"补齐{missing_type}角色，完善闭环结构，确保管道可持续运行",
                    "make_them_happy": "通过互利共赢的合作模式，实现各方价值最大化"
                })

        return {
            "overview": {
                "situation":
                f"基于【意识+能量+能力=结果】公式分析：{project_name}具备初步资源基础，设计者作为统筹方整合现有关键人物资源，构建撮合型非劳务收入管道。意识来自设计者的规则设计，能量来自关键人物的积极参与，能力借用各方专业资源。",
                "income_type":
                "居间（撮合费/中介费）",
                "core_insight":
                "利用现有关键人物的专业能力和客户基础，设计者作为统筹方制定合作规则和质量标准，通过撮合服务建立持续的非劳务收入管道，关键在于防绕过机制和共管结算。",
                "gaps": ["明确合作细则", "建立防绕过机制"]
                if not needs_additional_roles else ["补充渠道资源方", "建立合作标准"],
                "suggested_roles_to_hunt":
                [] if not needs_additional_roles else [{
                    "role":
                    "渠道资源方",
                    "role_type":
                    "需求方",
                    "why":
                    "需要流量入口和客户获取渠道，确保业务可持续发展",
                    "where_to_find":
                    "行业协会、商会、同城企业家群、相关业务的朋友圈",
                    "outreach_script":
                    "我们有优质的服务团队和成熟的管理经验，正在寻求优质合作伙伴。可以先小规模合作试点，看看是否互利共赢，您觉得如何？"
                }]
            },
            "pipelines": [{
                "id":
                "管道一",
                "name":
                "资源整合撮合管道",
                "income_mechanism": {
                    "type": "居间（撮合费）",
                    "trigger": "成功撮合交易后的佣金分成",
                    "settlement": "按单结算，交易完成确认后收取撮合费"
                },
                "parties_structure":
                parties_structure,
                "framework_logic": {
                    "resource_chain":
                    "设计者统筹规则制定和质量监督，关键人物提供专业服务和客户基础，形成供需匹配的撮合闭环",
                    "motivation_match": "设计者获得撮合费，关键人物获得业务机会和客户扩展，最终客户获得专业服务",
                    "designer_position": "控制合作标准制定和结算管理，通过共管账户和合同条款确保不被绕过",
                    "designer_income": "居间类非劳务收入，通过撮合成功收取佣金，无需持续劳动投入"
                },
                "mvp":
                "连接现有关键人物资源，为1-2个客户提供撮合服务，验证收费模式和防绕过机制的可行性。",
                "weak_link":
                "关键人物的配合度和服务标准统一性，可能影响客户满意度和复购率",
                "revenue_trigger":
                "撮合费（按交易额3-8%收取），属于居间类非劳务收入",
                "risks_and_planB": [{
                    "risk": "关键人物绕过设计者直接合作",
                    "mitigation": "签署分佣协议，控制客户资源入口，建立共管结算机制"
                }, {
                    "risk": "服务质量不稳定影响口碑",
                    "mitigation": "制定服务标准和评价体系，建立客户反馈和改进机制"
                }],
                "first_step":
                "与现有关键人物深度沟通，确定合作模式和收益分配，签署初步合作协议，选择1-2个试点客户开始验证",
                "labor_load_estimate": {
                    "hours_per_week": "4-6小时",
                    "level": "轻度(<5小时)",
                    "alternative": "建立标准化SOP和自助服务平台，将日常协调工作外包给助理或兼职人员"
                }
            }]
        }


# 创建全局实例
angela_ai = AngelaAI()
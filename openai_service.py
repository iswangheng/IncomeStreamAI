import os
import json
import logging
import ssl
import time
from openai import OpenAI
from typing import Dict, List, Any, Optional

# OpenAI客户端初始化
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
import httpx

# 创建带优化连接配置的客户端 - 使用laozhang.ai中转API
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://api.laozhang.ai/v1",  # 使用中转API
    timeout=httpx.Timeout(120.0, connect=30.0),  # 增加超时：连接30秒，读取120秒
    http_client=httpx.Client(limits=httpx.Limits(max_connections=10,
                                                 max_keepalive_connections=5),
                             timeout=httpx.Timeout(120.0, connect=30.0)))

logger = logging.getLogger(__name__)


class AngelaAI:
    """Angela - 非劳务收入管道设计AI服务"""

    def __init__(self):
        self.default_model = "gpt-4o"  # 默认模型
        self.default_max_tokens = 2500  # 默认token数量
        
    def load_prompt_from_file(self, prompt_type: str) -> str:
        """从文件加载prompt"""
        try:
            if prompt_type == 'system':
                file_path = 'prompts/system_prompt.txt'
            elif prompt_type == 'assistant':
                file_path = 'prompts/assistant_prompt.txt'
            else:
                raise ValueError(f"不支持的prompt类型: {prompt_type}")
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            logger.info(f"成功加载{prompt_type} prompt，长度: {len(content)}字符")
            return content
        except Exception as e:
            logger.error(f"加载{prompt_type} prompt失败: {e}")
            # 返回备用prompt
            if prompt_type == 'system':
                return "你是Angela，专业的非劳务收入路径设计师。"
            else:
                return "现在我将为你分析这个项目的非劳务收入设计方案。"

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
        logger.info(
            f"传入参数: model={kwargs.get('model')}, timeout={kwargs.get('timeout')}"
        )
        max_retries = 3  # 增加重试次数提高成功率
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"正在调用OpenAI API (尝试 {attempt + 1}/{max_retries})...")

                # 为每次重试创建新的客户端连接，提升SSL连接稳定性
                if attempt > 0:
                    # 使用更保守的超时设置
                    fresh_client = OpenAI(
                        api_key=os.environ.get("OPENAI_API_KEY"),
                        base_url="https://api.laozhang.ai/v1",  # 使用中转API
                        timeout=httpx.Timeout(150.0, connect=45.0, read=150.0)  # 进一步增加超时时间，提升稳定性
                    )
                    response = fresh_client.chat.completions.create(**kwargs)
                    logger.info("✅ OpenAI API调用成功")
                    return response
                else:
                    response = client.chat.completions.create(**kwargs)
                    logger.info("✅ OpenAI API调用成功")
                    return response

            except (httpx.TimeoutException, httpx.ConnectError,
                    ConnectionError, httpx.ReadTimeout, httpx.ConnectTimeout,
                    TimeoutError, OSError, ConnectionResetError,
                    BrokenPipeError, ssl.SSLError, ssl.SSLEOFError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)  # 缩短等待时间: 2s, 4s
                    logger.warning(
                        f"OpenAI API网络超时 (尝试 {attempt + 1}): {str(e)}, {wait_time}秒后重试..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"OpenAI API网络超时，最终失败: {str(e)}")
                    # 网络连接问题，抛出友好的错误信息
                    raise ConnectionError("OpenAI API网络连接超时，请稍后重试")
            except Exception as e:
                import traceback
                logger.error(f"💥 OpenAI API调用遇到其他错误: {str(e)}")
                logger.error(f"💥 错误类型: {type(e).__name__}")
                logger.error(f"💥 完整堆栈: {traceback.format_exc()}")
                logger.error(f"💥 传入的参数: {kwargs}")
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
        demand_roles = [
            'enterprise_owner', 'store_owner', 'department_head',
            'brand_manager'
        ]
        delivery_roles = [
            'product_provider', 'service_provider', 'traffic_provider',
            'other_provider'
        ]

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

    def get_core_knowledge_fallback(self) -> str:
        """当知识库检索失败时的核心知识要点"""
        return """• 非劳务收入核心公式：意识+能量+能力（行动）=结果
• 七大类型：租金（万物皆可租）、利息、股份/红利、版权、专利、企业连锁、团队收益
• 三步法则：盘资源→搭管道→动真格
• 核心原则：让关键环节的关键人物都高兴，严格区分需换取的人物资源vs可直接动用的外部资源
• 成功要素：1)设计共赢机制 2)掌握核心信息+筛选规则 3)前置合作规则"""

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

            # 从文件加载system prompt和assistant prompt
            system_prompt = self.load_prompt_from_file('system')
            assistant_prompt_prefix = self.load_prompt_from_file('assistant')

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
                role_chinese = self.format_role_to_chinese(
                    role) if role else "未指定"
                role_type = self.get_role_type_by_identifier(
                    role) if role else "其他方"

                user_content += f"""
- 人物：{name}｜角色：{role_chinese}（{role_type}）
  资源：{", ".join(resources) if resources else "无"}
  动机标签（如何让TA高兴）：{self.format_make_happy(make_happy)}
  备注：{notes if notes else "无"}"""

            # 构建关键人物列表用于提示
            key_persons_names = ', '.join([
                person.get('name', f'人物{i+1}')
                for i, person in enumerate(key_persons)
            ])

            # 使用从文件加载的assistant prompt
            assistant_prompt = assistant_prompt_prefix

            # 获取模型配置
            model_config = self.get_model_config('main_analysis')
            logger.info(f"模型配置: {model_config}")

            # 打印prompt长度信息
            total_prompt = system_prompt + user_content + assistant_prompt
            logger.info(f"===== OpenAI API Request Info =====")
            logger.info(f"Model: {model_config['model']}")
            logger.info(f"Max tokens: {model_config['max_tokens']}")
            logger.info(f"System prompt length: {len(system_prompt)} chars")
            logger.info(f"User content length: {len(user_content)} chars")
            logger.info(
                f"Assistant prompt length: {len(assistant_prompt)} chars")
            logger.info(f"Total prompt length: {len(total_prompt)} chars")
            logger.info(f"===== Full Prompt Content =====")
            logger.info(f"System: {system_prompt[:500]}..." if len(
                system_prompt) > 500 else f"System: {system_prompt}")
            logger.info(f"User: {user_content[:500]}..." if len(user_content) >
                        500 else f"User: {user_content}")
            logger.info(f"Assistant: {assistant_prompt[:500]}..." if len(
                assistant_prompt) > 500 else f"Assistant: {assistant_prompt}")
            logger.info(f"================================")

            # 调用OpenAI API，带重试机制和错误处理
            logger.info("=== 即将调用_call_openai_with_retry ===")
            try:
                response = self._call_openai_with_retry(
                    model=model_config['model'],
                    messages=[{
                        "role": "system",
                        "content": system_prompt
                    }, {
                        "role": "user",
                        "content": user_content
                    }, {
                        "role": "assistant",
                        "content": assistant_prompt
                    }],
                    response_format={"type": "json_object"},
                    temperature=model_config['temperature'],
                    max_tokens=model_config['max_tokens'],
                    timeout=model_config['timeout'])

                # 如果响应为None（网络错误），抛出异常而不是返回备用方案
                if response is None:
                    logger.error("💥 OpenAI API返回None，这通常意味着连接失败")
                    raise ConnectionError("OpenAI API连接失败，响应为None")

            except Exception as api_error:
                logger.error(f"OpenAI API调用失败: {str(api_error)}")
                # 抛出连接错误让上层处理
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
            import traceback
            logger.error(f"💥 JSON parsing error: {e}")
            logger.error(f"💥 Full traceback: {traceback.format_exc()}")
            # 尝试记录响应文本
            logger.error("💥 AI response parsing failed - checking for response content")
            return self._get_fallback_result(form_data)
        except Exception as e:
            import traceback
            logger.error(f"💥 AI generation error: {e}")
            logger.error(f"💥 Error type: {type(e).__name__}")
            logger.error(f"💥 Full traceback: {traceback.format_exc()}")
            logger.error(
                f"💥 This error caused fallback result to be used instead of real OpenAI analysis"
            )
            return self._get_fallback_result(form_data)

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
            'situation', 'core_insight', 'gaps',
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
                'mvp', 'weak_link', 'revenue_trigger',
                'anti_bypass_strategies', 'risks_and_planB', 'first_step', 'labor_load_estimate'
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

            # framework_logic is no longer required - removed validation

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
                    "交付方": "专业服务方"
                }
                role_name = role_name_mapping.get(missing_type, "合作伙伴")

                parties_structure.append({
                    "party":
                    f"【待补齐】{role_name}",
                    "role_type":
                    missing_type,
                    "resources": ["待确定的关键资源", "待匹配的合作能力"],
                    "role_value":
                    f"补齐{missing_type}角色，完善闭环结构，确保管道可持续运行",
                    "make_them_happy":
                    "通过互利共赢的合作模式，实现各方价值最大化"
                })

        return {
            "overview": {
                "situation":
                f"基于【意识+能量+能力=结果】公式分析：{project_name}具备初步资源基础，设计者作为统筹方整合现有关键人物资源，构建撮合型非劳务收入管道。意识来自设计者的规则设计，能量来自关键人物的积极参与，能力借用各方专业资源。",
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
                    "我们有优质的服务团队和成熟的管理经验，正在寻求优质合作伙伴扩大业务覆盖，期待与您探讨双赢合作机会"
                }]
            },
            "pipelines": [{
                "id":
                "pipeline_1",
                "name":
                f"{project_name}撮合服务管道",
                "income_mechanism": {
                    "type": "居间（撮合费）",
                    "trigger": "每次成功匹配并完成交易时",
                    "settlement": "按交易金额的百分比收取或固定撮合费"
                },
                "parties_structure":
                parties_structure,
                "framework_logic": {
                    "resource_chain":
                    "通过整合各方资源形成供需匹配闭环：需求方提供客户和需求信息，交付方提供专业服务能力，设计者制定匹配规则和质量标准，确保交易顺利完成",
                    "motivation_match":
                    "需求方获得优质服务解决方案，交付方获得稳定客户来源，设计者通过撮合获得持续收益，形成三方共赢格局",
                    "designer_position":
                    "控制客户筛选标准、服务提供商认证体系、交易流程规范和结算环节，确保所有交易必须通过统筹方完成",
                    "designer_income": "居间收益 - 通过制定规则和控制关键环节获得每笔交易的撮合费用"
                },
                "mvp":
                "建立简单的供需信息收集和匹配机制，先从现有人脉开始小规模撮合，验证商业模式可行性后逐步扩大规模。",
                "weak_link":
                "初期可能面临供需双方信任建立的挑战，需要通过成功案例和口碑积累来强化平台可信度。",
                "revenue_trigger":
                "居间收益：每次成功撮合交易时按比例或固定费用收取撮合费",
                "risks_and_planB": [{
                    "risk": "供需双方绕过平台直接合作",
                    "mitigation": "建立独家合作协议，控制关键客户信息，设计阶梯式奖励机制"
                }, {
                    "risk": "竞争对手进入市场",
                    "mitigation": "建立差异化服务标准，深耕细分领域，提高转换成本"
                }],
                "first_step":
                "从现有人脉中识别2-3个潜在的需求方和交付方，设计初步的合作规则和费用标准，安排试点撮合项目验证模式",
                "labor_load_estimate": {
                    "hours_per_week": "5-8小时",
                    "level": "中度",
                    "alternative":
                    "建立标准化的筛选和匹配流程，培训助手处理日常对接工作，设计自动化的信息收集和初步筛选系统"
                }
            }]
        }

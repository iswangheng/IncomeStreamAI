/**
 * 示例案例处理脚本
 * 处理示例案例的点击、数据填充和自动提交
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // 示例案例数据
    const demoData = {
        'english-training': {
            projectName: 'Bonnie英语培训管道',
            projectDescription: '有一天，一个做升学规划的朋友在饭局上随口吐槽："最近合作的英语机构交付太差，特别不靠谱，你有没有靠谱的老师推荐？"我发现我有这个朋友就有生源，我可以去找老师就有交付，我来做连接不就能搭个闭环？而且机构交付差是因为价格太低只有市场价1/3，我就设计标准化产品配助教，成本降下来。',
            projectStage: 'testing',
            keyPersons: [
                {
                    name: '升学规划师朋友',
                    role: 'channel',
                    resources: ['家长客户资源', '升学规划服务信任度', '教育圈人脉'],
                    make_happy: 'bring_leads,recurring_income,no_conflict_current_partner'
                },
                {
                    name: '英语培训机构',
                    role: 'product,delivery', 
                    resources: ['英语课程产品', '师资助教团队', '线上教学系统'],
                    make_happy: 'bring_leads,brand_exposure,expand_network'
                }
            ],
            externalResources: ['暂无明确外部资源']
        },
        'rental-business': {
            projectName: '商铺租赁管道',
            projectDescription: '通过1万元启动资金，采用二房东模式，寻找位置好但房租便宜的商铺进行转租，利用信息差和包装能力获得租金差价收益，8年内累计实现72万收益。',
            projectStage: 'planning',
            keyPersons: [
                {
                    name: '房东',
                    role: 'product',
                    resources: ['商铺产权', '租赁决策权', '区域房产信息'],
                    make_happy: 'stable_income,reliable_tenant,property_maintenance'
                },
                {
                    name: '承租商户',
                    role: 'buyer',
                    resources: ['经营资金', '客流需求', '商业运营能力'],
                    make_happy: 'good_location,reasonable_rent,flexible_lease'
                }
            ],
            externalResources: ['房产中介平台', '商圈调研数据']
        },
        'cicada-farming': {
            projectName: '知了猴养殖管道',
            projectDescription: '利用1万元启动成本，在农村建立知了猴养殖基地，通过7条不同销售管道（餐厅直供、批发市场、网上销售等），实现年收入70万的农业创业项目。',
            projectStage: 'scaling',
            keyPersons: [
                {
                    name: '农村合作社',
                    role: 'delivery',
                    resources: ['养殖场地', '养殖技术', '农村劳动力'],
                    make_happy: 'employment_opportunities,technical_support,stable_orders'
                },
                {
                    name: '餐厅采购经理',
                    role: 'buyer',
                    resources: ['采购预算', '餐厅客户群', '菜品研发能力'],
                    make_happy: 'quality_supply,competitive_price,reliable_delivery'
                },
                {
                    name: '批发商',
                    role: 'channel',
                    resources: ['批发渠道', '仓储物流', '客户网络'],
                    make_happy: 'consistent_supply,good_margins,market_exclusivity'
                }
            ],
            externalResources: ['农业补贴政策', '电商销售平台', '冷链物流网络']
        }
    };

    // 获取所有示例案例卡片
    const demoCaseCards = document.querySelectorAll('.demo-case-card');
    
    demoCaseCards.forEach(card => {
        card.addEventListener('click', function() {
            const caseType = this.getAttribute('data-case');
            
            // 自定义项目的处理
            if (caseType === 'custom') {
                // 清空表单，让用户自己填写
                clearForm();
                scrollToForm();
                return;
            }
            
            // 获取对应的示例数据
            const caseData = demoData[caseType];
            if (!caseData) {
                console.warn('未找到案例数据:', caseType);
                return;
            }
            
            // 添加视觉反馈
            card.classList.add('selected');
            setTimeout(() => card.classList.remove('selected'), 1000);
            
            // 填充表单数据
            fillFormWithCaseData(caseData);
            
            // 滚动到表单区域
            scrollToForm();
            
            // 显示填充完成提示，但不自动提交
            showFillCompletedNotification();
        });
    });

    /**
     * 填充表单数据
     */
    function fillFormWithCaseData(caseData) {
        // 填充基本项目信息
        const projectNameInput = document.getElementById('project_name');
        const projectDescInput = document.getElementById('project_description');
        const projectStageSelect = document.getElementById('project_stage');
        
        if (projectNameInput) projectNameInput.value = caseData.projectName;
        if (projectDescInput) projectDescInput.value = caseData.projectDescription;
        if (projectStageSelect) projectStageSelect.value = caseData.projectStage;
        
        // 清空现有的人物卡片
        clearPersonCards();
        
        // 添加关键人物
        if (caseData.keyPersons && caseData.keyPersons.length > 0) {
            caseData.keyPersons.forEach((person, index) => {
                setTimeout(() => {
                    addPersonCardWithData(person, false); // false表示不聚焦
                }, index * 200); // 延时添加，避免DOM操作冲突
            });
        }
        
        // 填充外部资源
        setTimeout(() => {
            fillExternalResources(caseData.externalResources);
        }, caseData.keyPersons.length * 200 + 300);
    }

    /**
     * 清空表单
     */
    function clearForm() {
        const projectNameInput = document.getElementById('project_name');
        const projectDescInput = document.getElementById('project_description');
        const projectStageSelect = document.getElementById('project_stage');
        
        if (projectNameInput) projectNameInput.value = '';
        if (projectDescInput) projectDescInput.value = '';
        if (projectStageSelect) projectStageSelect.value = 'ideation';
        
        clearPersonCards();
        clearExternalResources();
    }

    /**
     * 清空人物卡片
     */
    function clearPersonCards() {
        const personsContainer = document.getElementById('personsContainer');
        if (personsContainer) {
            personsContainer.innerHTML = '';
        }
        
        // 重置人物计数器
        if (window.personCounter !== undefined) {
            window.personCounter = 0;
        }
        
        // 显示空状态消息
        const noPersonsMsg = document.getElementById('noPersonsMsg') || document.getElementById('emptyState');
        if (noPersonsMsg) {
            noPersonsMsg.style.display = 'block';
        }
    }

    /**
     * 添加带数据的人物卡片
     */
    function addPersonCardWithData(personData, shouldFocus = false) {
        // 调用模板中的全局addPerson函数
        if (typeof window.addPerson === 'function') {
            window.addPerson();
        } else {
            // 备用：手动创建基础的人物卡片
            createBasicPersonCard(personData);
            return;
        }
        
        // 等待DOM更新后填充数据
        setTimeout(() => {
            const personCards = document.querySelectorAll('.person-card');
            const latestCard = personCards[personCards.length - 1];
            
            if (latestCard) {
                fillPersonCardData(latestCard, personData);
            }
        }, 300);
    }

    /**
     * 创建基础人物卡片（备用方案）
     */
    function createBasicPersonCard(personData) {
        const container = document.getElementById('personsContainer');
        if (!container) return;
        
        const cardHtml = `
            <div class="person-card">
                <div class="person-card-header">
                    <div class="person-number">${container.children.length + 1}</div>
                    <button type="button" class="remove-person-btn" onclick="removePerson(this)">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="form-group">
                    <label class="form-label">人物代号/姓名</label>
                    <input type="text" class="form-control" name="person_name[]" value="${personData.name || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">掌握的资源</label>
                    <textarea class="form-control" name="person_resources[]" placeholder="请描述具体资源">${personData.resources ? personData.resources.join(',') : ''}</textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">动机需求</label>
                    <input type="text" class="form-control" name="person_needs[]" value="${personData.make_happy || ''}">
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', cardHtml);
        
        // 隐藏空状态
        const emptyState = document.getElementById('emptyState');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }

    /**
     * 填充人物卡片数据
     */
    function fillPersonCardData(personCard, personData) {
        try {
            // 填充姓名
            const nameInput = personCard.querySelector('input[name="person_name[]"]');
            if (nameInput && personData.name) {
                nameInput.value = personData.name;
            }
            
            // 填充角色（处理多选）
            if (personData.role) {
                const roles = personData.role.split(',');
                roles.forEach(role => {
                    const roleCheckbox = personCard.querySelector(`input[name="person_role[]"][value="${role.trim()}"]`);
                    if (roleCheckbox) {
                        roleCheckbox.checked = true;
                        // 触发change事件以更新UI
                        roleCheckbox.dispatchEvent(new Event('change'));
                    }
                });
            }
            
            // 填充资源 - 兼容复杂的资源输入系统
            if (personData.resources && personData.resources.length > 0) {
                // 尝试找到资源隐藏字段
                const resourceHiddenField = personCard.querySelector('input[name="person_resources[]"]');
                if (resourceHiddenField) {
                    resourceHiddenField.value = personData.resources.join(',');
                }
                
                // 尝试填充可见的资源区域
                const selectedResourcesContainer = personCard.querySelector('.selected-resources-container');
                if (selectedResourcesContainer) {
                    selectedResourcesContainer.classList.remove('empty');
                    const resourceTags = personData.resources.map(resource => 
                        `<div class="selected-resource-tag">${resource}<button type="button" class="remove-resource-btn">×</button></div>`
                    ).join('');
                    selectedResourcesContainer.innerHTML = resourceTags;
                }
                
                // 更新资源计数
                const countElement = personCard.querySelector('.resource-count');
                if (countElement) {
                    countElement.textContent = personData.resources.length;
                }
            }
            
            // 填充动机需求标签
            if (personData.make_happy) {
                const needs = personData.make_happy.split(',');
                needs.forEach(need => {
                    const needCheckbox = personCard.querySelector(`input[name="person_needs[]"][value="${need.trim()}"]`);
                    if (needCheckbox) {
                        needCheckbox.checked = true;
                    }
                });
            }
            
        } catch (error) {
            console.warn('填充人物数据时出现错误:', error);
            // 使用简单的备用填充方式
            fillPersonCardDataSimple(personCard, personData);
        }
    }

    /**
     * 简单的人物卡片数据填充（备用）
     */
    function fillPersonCardDataSimple(personCard, personData) {
        const nameInput = personCard.querySelector('input[name="person_name[]"]');
        if (nameInput) nameInput.value = personData.name || '';
        
        const resourceInputs = personCard.querySelectorAll('textarea, input[placeholder*="资源"]');
        resourceInputs.forEach(input => {
            if (personData.resources && personData.resources.length > 0) {
                input.value = personData.resources.join(', ');
            }
        });
    }

    /**
     * 填充外部资源
     */
    function fillExternalResources(resources) {
        if (!resources || resources.length === 0) return;
        
        // 清空现有选择
        const resourceCheckboxes = document.querySelectorAll('input[name="external_resources"]');
        resourceCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // 填充匹配的资源
        resources.forEach(resource => {
            const matchingCheckbox = document.querySelector(`input[name="external_resources"][value="${resource}"]`);
            if (matchingCheckbox) {
                matchingCheckbox.checked = true;
            } else if (resource && resource !== '暂无明确外部资源') {
                // 如果没有匹配的选项，填写到"其他资源"
                const otherResourceCheckbox = document.getElementById('other_resource_checkbox');
                const otherResourceText = document.getElementById('other_resource_text');
                
                if (otherResourceCheckbox && otherResourceText) {
                    otherResourceCheckbox.checked = true;
                    otherResourceText.style.display = 'block';
                    otherResourceText.value = resource;
                }
            }
        });
    }

    /**
     * 清空外部资源
     */
    function clearExternalResources() {
        const resourceCheckboxes = document.querySelectorAll('input[name="external_resources"]');
        resourceCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        const otherResourceCheckbox = document.getElementById('other_resource_checkbox');
        const otherResourceText = document.getElementById('other_resource_text');
        
        if (otherResourceCheckbox) otherResourceCheckbox.checked = false;
        if (otherResourceText) {
            otherResourceText.value = '';
            otherResourceText.style.display = 'none';
        }
    }

    /**
     * 滚动到表单区域
     */
    function scrollToForm() {
        const formElement = document.getElementById('mainForm') || document.querySelector('.main-content form');
        if (formElement) {
            formElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    }

    /**
     * 显示填充完成提示（不自动提交）
     */
    function showFillCompletedNotification() {
        const notification = document.createElement('div');
        notification.className = 'fill-completed-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            font-weight: 500;
            animation: slideInFromRight 0.5s ease;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-check-circle" style="color: #fff;"></i>
                <span>示例数据已填充完成！请检查并修改后点击"开始AI智能分析"</span>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: none; 
                    border: none; 
                    color: white; 
                    font-size: 18px; 
                    cursor: pointer;
                    margin-left: 10px;
                    padding: 0;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // 6秒后自动移除提示
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.remove();
            }
        }, 6000);
        
        // 高亮分析按钮提醒用户
        const analyzeButton = document.querySelector('button[type="submit"]');
        if (analyzeButton) {
            analyzeButton.style.animation = 'pulse 2s infinite';
            analyzeButton.style.boxShadow = '0 0 0 4px rgba(0, 122, 255, 0.3)';
            
            // 3秒后移除高亮效果
            setTimeout(() => {
                analyzeButton.style.animation = '';
                analyzeButton.style.boxShadow = '';
            }, 3000);
        }
    }

    // 添加CSS样式
    if (!document.getElementById('demo-case-styles')) {
        const style = document.createElement('style');
        style.id = 'demo-case-styles';
        style.textContent = `
            .demo-case-card {
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .demo-case-card:hover {
                transform: translateY(-4px) scale(1.02);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
            }
            
            .demo-case-card.selected {
                transform: translateY(-6px) scale(1.05);
                box-shadow: 0 12px 35px rgba(102, 126, 234, 0.25);
                border: 2px solid #667eea;
            }
            
            .demo-case-card.selected::after {
                content: '✓';
                position: absolute;
                top: -5px;
                right: -5px;
                width: 25px;
                height: 25px;
                background: #28a745;
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: bold;
                animation: checkmark-bounce 0.5s ease;
            }
            
            @keyframes checkmark-bounce {
                0% { transform: scale(0); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
            
            .fill-completed-notification {
                animation: slideInFromRight 0.5s ease;
            }
            
            @keyframes slideInFromRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
});
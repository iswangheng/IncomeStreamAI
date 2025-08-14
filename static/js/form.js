document.addEventListener('DOMContentLoaded', function() {
    const addPersonBtn = document.getElementById('addPersonBtn');
    const personsContainer = document.getElementById('personsContainer');
    const noPersonsMsg = document.getElementById('noPersonsMsg');
    const personCardTemplate = document.getElementById('personCardTemplate');
    
    let personCounter = 0;
    
    // 性能优化: 缓存DOM查询结果
    const domCache = new Map();
    
    // 性能优化: 防抖函数
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Add person card functionality
    addPersonBtn.addEventListener('click', function() {
        addPersonCard();
    });

    // 优化的展开/收起功能
    function setupExpandToggle(personCard) {
        const toggleBtn = personCard.querySelector('.expand-toggle-btn');
        const expandableSection = personCard.querySelector('.needs-expandable-section');
        const toggleIcon = toggleBtn.querySelector('i');
        
        if (!toggleBtn || !expandableSection) return;
        
        // 使用CSS类而不是内联样式来提高性能
        toggleBtn.addEventListener('click', function() {
            const isExpanded = expandableSection.classList.contains('expanded');
            
            if (isExpanded) {
                // 收起 - 使用CSS类切换
                expandableSection.classList.remove('expanded');
                expandableSection.classList.add('collapsing');
                
                toggleIcon.className = 'fas fa-angle-down me-1';
                toggleBtn.innerHTML = '<i class="fas fa-angle-down me-1"></i>展开更多选项';
                
                // 动画结束后隐藏元素
                setTimeout(() => {
                    expandableSection.classList.remove('collapsing');
                    expandableSection.classList.add('collapsed');
                }, 300);
                
            } else {
                // 展开 - 使用CSS类切换
                expandableSection.classList.remove('collapsed');
                expandableSection.classList.add('expanding');
                
                toggleIcon.className = 'fas fa-angle-up me-1';
                toggleBtn.innerHTML = '<i class="fas fa-angle-up me-1"></i>收起选项';
                
                // 动画结束后设置为展开状态
                setTimeout(() => {
                    expandableSection.classList.remove('expanding');
                    expandableSection.classList.add('expanded');
                }, 300);
            }
        });
    }

    function addPersonCard(shouldFocus = true) {
        // 性能优化: 批量DOM操作
        const fragment = document.createDocumentFragment();
        
        // Hide the "no persons" message
        noPersonsMsg.style.display = 'none';
        
        // Clone the template
        const template = personCardTemplate.content.cloneNode(true);
        const personCard = template.querySelector('.person-card');
        
        // Add unique identifier
        personCounter++;
        const personId = personCounter;
        personCard.setAttribute('data-person-id', personId);
        
        // 性能优化: 一次性处理所有DOM操作
        requestAnimationFrame(() => {
            // 替换模板中的 ${personId} 占位符，为每个复选框创建唯一ID
            const needsContainer = personCard.querySelector('.needs-selection-container');
            if (needsContainer) {
                needsContainer.innerHTML = needsContainer.innerHTML.replace(/\$\{personId\}/g, personId);
            }
            
            // 添加展开/收起功能
            setupExpandToggle(personCard);
            
            // Add remove functionality
            const removeBtn = personCard.querySelector('.remove-person-btn');
            removeBtn.addEventListener('click', function() {
                removePersonCard(personCard);
            });
            
            // 使用CSS类来处理动画而不是内联样式
            personCard.classList.add('person-card-entering');
            
            // Add the card to the container
            personsContainer.appendChild(personCard);
            
            // 触发入场动画
            setTimeout(() => {
                personCard.classList.remove('person-card-entering');
                personCard.classList.add('person-card-entered');
            }, 50);
            
            // 有条件的聚焦逻辑 - 用户点击添加时聚焦，自动添加时不聚焦
            if (shouldFocus) {
                const firstInput = personCard.querySelector('input[name="person_name[]"]');
                if (firstInput) {
                    // 延迟聚焦避免影响动画
                    setTimeout(() => firstInput.focus(), 350);
                }
            }
        });
    }

    function removePersonCard(personCard) {
        // 使用CSS类处理退场动画
        personCard.classList.add('person-card-leaving');
        
        setTimeout(() => {
            personCard.remove();
            
            // Show "no persons" message if no cards left
            const remainingCards = personsContainer.querySelectorAll('.person-card');
            if (remainingCards.length === 0) {
                noPersonsMsg.style.display = 'block';
            }
        }, 300);
    }

    // Form validation
    const mainForm = document.getElementById('mainForm');
    mainForm.addEventListener('submit', function(e) {
        const projectName = document.getElementById('project_name').value.trim();
        const projectDescription = document.getElementById('project_description').value.trim();
        
        if (!projectName || !projectDescription) {
            e.preventDefault();
            alert('请填写项目名称和项目背景描述');
            return false;
        }
        
        // Check if at least one person is added
        const personCards = personsContainer.querySelectorAll('.person-card');
        if (personCards.length === 0) {
            const result = confirm('您尚未添加任何关键人物，这可能影响分析结果的准确性。是否继续提交？');
            if (!result) {
                e.preventDefault();
                return false;
            }
        }
        
        // Validate person cards
        let hasInvalidPerson = false;
        personCards.forEach(function(card) {
            const personName = card.querySelector('input[name="person_name[]"]').value.trim();
            if (!personName) {
                hasInvalidPerson = true;
            }
        });
        
        if (hasInvalidPerson) {
            e.preventDefault();
            alert('请为所有关键人物填写姓名/代号');
            return false;
        }
        
        // Show loading state
        const submitBtn = mainForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>正在生成方案...';
        submitBtn.disabled = true;
        
        // Re-enable button after a delay in case of error
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 10000);
    });

    // Auto-resize textareas with debouncing for performance
    const autoResizeTextarea = debounce(function(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }, 100);
    
    document.querySelectorAll('textarea').forEach(function(textarea) {
        // 使用防抖来减少频繁的DOM操作
        textarea.addEventListener('input', function() {
            autoResizeTextarea(this);
        });
        
        // 监听动态添加的textarea
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        const textareas = node.querySelectorAll ? node.querySelectorAll('textarea') : [];
                        textareas.forEach(function(textarea) {
                            textarea.addEventListener('input', function() {
                                autoResizeTextarea(this);
                            });
                        });
                    }
                });
            });
        });
        
        observer.observe(personsContainer, {
            childList: true,
            subtree: true
        });
    });

    // 默认添加一个人物卡片但不聚焦 - 改善用户体验
    setTimeout(() => {
        addPersonCard(false);
    }, 100);

    // 处理其他资源输入框的显示隐藏
    const otherResourceCheckbox = document.getElementById('resource8');
    const otherResourceInput = document.getElementById('otherResourceInput');
    const otherResourceText = document.getElementById('other_resource_text');

    if (otherResourceCheckbox && otherResourceInput) {
        otherResourceCheckbox.addEventListener('change', function() {
            if (this.checked) {
                otherResourceInput.style.display = 'block';
                otherResourceText.focus();
            } else {
                otherResourceInput.style.display = 'none';
                otherResourceText.value = '';
            }
        });
    }
});

// 示例案例加载函数 - 放在DOMContentLoaded外部，使其成为全局函数
function loadExample(caseType) {
    // 清空现有表单
    document.getElementById('project_name').value = '';
    document.getElementById('project_description').value = '';
    document.getElementById('project_stage').value = '';
    
    // 清空所有关键人物卡片
    const personsContainer = document.getElementById('personsContainer');
    personsContainer.innerHTML = '';
    
    // 清空外部资源选择
    document.querySelectorAll('input[name="external_resources"]').forEach(cb => cb.checked = false);
    
    // 根据案例类型填充数据
    switch(caseType) {
        case 'bonnie':
            // 填充Bonnie案例数据
            document.getElementById('project_name').value = 'Bonnie英语培训管道';
            document.getElementById('project_description').value = '连接需要英语培训的学生家长与优质英语老师，通过建立标准化培训产品和中介平台，形成稳定的非劳务收入管道。目标是创建一个不需要自己亲自教学就能持续获得收益的系统。';
            document.getElementById('project_stage').value = '资源具备，等待设计整合';
            
            // 添加关键人物
            setTimeout(() => {
                // 添加第一个人物 - 英语老师
                addPersonCardWithData({
                    name: '王老师',
                    role: '英语培训老师',
                    resources: '英语教学经验, 教学资质, 时间灵活',
                    needs: ['带来客户/引流', '获得持续收入']
                });
                
                // 添加第二个人物 - 教育规划师
                setTimeout(() => {
                    addPersonCardWithData({
                        name: '李顾问',
                        role: '教育规划师',
                        resources: '学生家长资源, 升学规划经验',
                        needs: ['不冲突现有合作', '品牌曝光']
                    });
                }, 200);
            }, 300);
            
            // 选择外部资源
            const resource1 = document.getElementById('resource1');
            const resource3 = document.getElementById('resource3');
            if (resource1) resource1.checked = true; // 自媒体资源
            if (resource3) resource3.checked = true; // 渠道入口
            break;
            
        case 'angela':
            // 填充Angela案例数据
            document.getElementById('project_name').value = 'Angela商铺二房东项目';
            document.getElementById('project_description').value = '通过市场调研发现商铺租赁市场供需不匹配，计划整租大面积商铺后分割转租，通过租金差价和增值服务获得稳定收益。已有初步市场调研数据和潜在房东资源。';
            document.getElementById('project_stage').value = '初步接触';
            
            // 添加关键人物
            setTimeout(() => {
                // 添加房东
                addPersonCardWithData({
                    name: '张房东',
                    role: '商铺业主',
                    resources: '多个商铺资源, 灵活租赁条件',
                    needs: ['稳定租金收入', '省心管理']
                });
                
                // 添加商户
                setTimeout(() => {
                    addPersonCardWithData({
                        name: '小商户群体',
                        role: '承租方',
                        resources: '租赁需求, 现金流',
                        needs: ['低成本租赁', '灵活租期']
                    });
                }, 200);
            }, 300);
            
            // 选择外部资源
            const resource2 = document.getElementById('resource2');
            const resource4 = document.getElementById('resource4');
            if (resource2) resource2.checked = true; // 合作方产品
            if (resource4) resource4.checked = true; // 顾问背书
            break;
            
        case 'chuchu':
            // 填充楚楚案例数据
            document.getElementById('project_name').value = '楚楚知了猴养殖管道';
            document.getElementById('project_description').value = '知了猴（金蝉）养殖项目，整合销路、林地、人力、技术四方资源，形成完整的养殖和销售管道。通过掌握核心销售渠道和技术标准，确保各方合作稳定。';
            document.getElementById('project_stage').value = '项目已启动部分内容';
            
            // 添加关键人物
            setTimeout(() => {
                // 添加销售渠道
                addPersonCardWithData({
                    name: '餐饮批发商',
                    role: '销售渠道',
                    resources: '稳定采购需求, 批量订单',
                    needs: ['稳定供货', '质量保证']
                });
                
                // 添加林地主
                setTimeout(() => {
                    addPersonCardWithData({
                        name: '林地承包人',
                        role: '场地提供方',
                        resources: '大面积林地, 适合养殖环境',
                        needs: ['额外收入', '不影响林木']
                    });
                }, 200);
                
                // 添加技术员
                setTimeout(() => {
                    addPersonCardWithData({
                        name: '养殖技术员',
                        role: '技术支持',
                        resources: '养殖技术, 病虫害防治经验',
                        needs: ['技术服务费', '长期合作']
                    });
                }, 400);
            }, 300);
            
            // 选择外部资源
            const resource5 = document.getElementById('resource5');
            if (resource5) resource5.checked = true; // 内容产能
            break;
    }
    
    // 平滑滚动到项目基础信息区域
    setTimeout(() => {
        const projectSection = document.querySelector('.card');
        projectSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
        
        // 添加闪烁效果提示用户
        projectSection.classList.add('highlight-flash');
        setTimeout(() => {
            projectSection.classList.remove('highlight-flash');
        }, 2000);
    }, 100);
}

// 辅助函数：添加带数据的人物卡片
function addPersonCardWithData(data) {
    const personsContainer = document.getElementById('personsContainer');
    const noPersonsMsg = document.getElementById('noPersonsMsg');
    const personCardTemplate = document.getElementById('personCardTemplate');
    
    // Hide no persons message
    noPersonsMsg.style.display = 'none';
    
    // Clone template
    const template = personCardTemplate.content.cloneNode(true);
    const personCard = template.querySelector('.person-card');
    
    // 添加唯一标识
    const personId = Date.now() + Math.random();
    personCard.setAttribute('data-person-id', personId);
    
    // 填充数据
    const nameInput = personCard.querySelector('input[name="person_name[]"]');
    const roleSelect = personCard.querySelector('select[name="person_role[]"]');
    const resourcesTextarea = personCard.querySelector('textarea[name="person_resources[]"]');
    
    if (nameInput) nameInput.value = data.name || '';
    if (roleSelect && data.role) {
        // 尝试匹配角色选项
        const options = roleSelect.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].text.includes(data.role) || data.role.includes(options[i].text)) {
                roleSelect.value = options[i].value;
                break;
            }
        }
    }
    if (resourcesTextarea) resourcesTextarea.value = data.resources || '';
    
    // 处理需求复选框
    if (data.needs && data.needs.length > 0) {
        const needsContainer = personCard.querySelector('.needs-selection-container');
        if (needsContainer) {
            // 替换模板中的占位符
            needsContainer.innerHTML = needsContainer.innerHTML.replace(/\$\{personId\}/g, personId);
            
            // 勾选对应的需求
            data.needs.forEach(need => {
                const checkboxes = needsContainer.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    if (cb.nextElementSibling && cb.nextElementSibling.textContent.includes(need)) {
                        cb.checked = true;
                    }
                });
            });
        }
    }
    
    // 添加展开/收起功能
    const toggleBtn = personCard.querySelector('.expand-toggle-btn');
    const expandableSection = personCard.querySelector('.needs-expandable-section');
    if (toggleBtn && expandableSection) {
        toggleBtn.addEventListener('click', function() {
            const isExpanded = expandableSection.classList.contains('expanded');
            if (isExpanded) {
                expandableSection.classList.remove('expanded');
                expandableSection.classList.add('collapsed');
                toggleBtn.innerHTML = '<i class="fas fa-angle-down me-1"></i>展开更多选项';
            } else {
                expandableSection.classList.remove('collapsed');
                expandableSection.classList.add('expanded');
                toggleBtn.innerHTML = '<i class="fas fa-angle-up me-1"></i>收起选项';
            }
        });
    }
    
    // 添加删除功能
    const removeBtn = personCard.querySelector('.remove-person-btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', function() {
            personCard.classList.add('person-card-leaving');
            setTimeout(() => {
                personCard.remove();
                const remainingCards = personsContainer.querySelectorAll('.person-card');
                if (remainingCards.length === 0) {
                    noPersonsMsg.style.display = 'block';
                }
            }, 300);
        });
    }
    
    // 添加到容器
    personsContainer.appendChild(personCard);
    
    // 触发入场动画
    personCard.classList.add('person-card-entering');
    setTimeout(() => {
        personCard.classList.remove('person-card-entering');
        personCard.classList.add('person-card-entered');
    }, 50);
}

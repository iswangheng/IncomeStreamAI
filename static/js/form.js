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
            showElegantConfirm('请填写项目名称和项目背景描述', () => {});
            return false;
        }
        
        // Check if at least one person is added
        const personCards = personsContainer.querySelectorAll('.person-card');
        if (personCards.length === 0) {
            showElegantConfirm('您尚未添加任何关键人物，这可能影响分析结果的准确性。是否继续提交？', () => {
                // 用户确认继续，表单将自动提交
            }, () => {
                e.preventDefault();
                return false;
            });
        }
        
        // Validate person cards
        let hasInvalidPerson = false;
        let hasRoleValidationError = false;
        let roleErrorMessage = '';
        
        personCards.forEach(function(card, index) {
            const personName = card.querySelector('input[name="person_name[]"]').value.trim();
            if (!personName) {
                hasInvalidPerson = true;
            }
            
            // 角色验证逻辑
            const roleCheckboxes = card.querySelectorAll('input[name="person_role[]"]:checked');
            if (roleCheckboxes.length === 0) {
                hasRoleValidationError = true;
                roleErrorMessage = `第${index + 1}个关键人物必须选择至少一个身份角色`;
                return;
            }
            
            // 检查是否在需求方和交付方中各选择了至少一个
            const selectedRoles = Array.from(roleCheckboxes).map(cb => cb.value);
            const demandRoles = ['enterprise_owner', 'store_owner', 'department_head', 'brand_manager'];
            const deliveryRoles = ['product_provider', 'service_provider', 'traffic_provider', 'other_provider'];
            
            const hasDemandRole = selectedRoles.some(role => demandRoles.includes(role));
            const hasDeliveryRole = selectedRoles.some(role => deliveryRoles.includes(role));
            
            if (!hasDemandRole && !hasDeliveryRole) {
                hasRoleValidationError = true;
                roleErrorMessage = `第${index + 1}个关键人物需要在需求方和交付方中各选择至少一个角色`;
                return;
            }
        });
        
        if (hasInvalidPerson) {
            e.preventDefault();
            showElegantConfirm('请为所有关键人物填写姓名/代号', () => {});
            return false;
        }
        
        if (hasRoleValidationError) {
            e.preventDefault();
            showElegantConfirm(roleErrorMessage, () => {});
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


});

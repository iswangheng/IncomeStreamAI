document.addEventListener('DOMContentLoaded', function() {
    const addPersonBtn = document.getElementById('addPersonBtn');
    const personsContainer = document.getElementById('personsContainer');
    const noPersonsMsg = document.getElementById('noPersonsMsg');
    const personCardTemplate = document.getElementById('personCardTemplate');
    
    let personCounter = 0;

    // Add person card functionality
    addPersonBtn.addEventListener('click', function() {
        addPersonCard();
    });

    // 展开/收起功能
    function setupExpandToggle(personCard) {
        const toggleBtn = personCard.querySelector('.expand-toggle-btn');
        const expandableSection = personCard.querySelector('.needs-expandable-section');
        const toggleIcon = toggleBtn.querySelector('i');
        
        if (!toggleBtn || !expandableSection) return;
        
        toggleBtn.addEventListener('click', function() {
            const isExpanded = expandableSection.style.display !== 'none';
            
            if (isExpanded) {
                // 收起
                expandableSection.style.transition = 'all 0.3s ease';
                expandableSection.style.maxHeight = expandableSection.scrollHeight + 'px';
                setTimeout(() => {
                    expandableSection.style.maxHeight = '0';
                    expandableSection.style.opacity = '0';
                }, 10);
                setTimeout(() => {
                    expandableSection.style.display = 'none';
                }, 300);
                
                toggleIcon.className = 'fas fa-angle-down me-1';
                toggleBtn.innerHTML = '<i class="fas fa-angle-down me-1"></i>展开更多选项';
            } else {
                // 展开
                expandableSection.style.display = 'block';
                expandableSection.style.maxHeight = '0';
                expandableSection.style.opacity = '0';
                expandableSection.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    expandableSection.style.maxHeight = expandableSection.scrollHeight + 'px';
                    expandableSection.style.opacity = '1';
                }, 10);
                
                toggleIcon.className = 'fas fa-angle-up me-1';
                toggleBtn.innerHTML = '<i class="fas fa-angle-up me-1"></i>收起选项';
            }
        });
    }

    function addPersonCard(shouldFocus = true) {
        // Hide the "no persons" message
        noPersonsMsg.style.display = 'none';
        
        // Clone the template
        const template = personCardTemplate.content.cloneNode(true);
        const personCard = template.querySelector('.person-card');
        
        // Add unique identifier
        personCounter++;
        const personId = personCounter;
        personCard.setAttribute('data-person-id', personId);
        
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
        
        // Add the card to the container
        personsContainer.appendChild(personCard);
        
        // 有条件的聚焦逻辑 - 用户点击添加时聚焦，自动添加时不聚焦
        if (shouldFocus) {
            const firstInput = personCard.querySelector('input[name="person_name[]"]');
            if (firstInput) {
                firstInput.focus();
            }
        }
        
        // Add animation
        personCard.style.opacity = '0';
        personCard.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            personCard.style.transition = 'all 0.3s ease';
            personCard.style.opacity = '1';
            personCard.style.transform = 'translateY(0)';
        }, 10);
    }

    function removePersonCard(personCard) {
        // Add fade out animation
        personCard.style.transition = 'all 0.3s ease';
        personCard.style.opacity = '0';
        personCard.style.transform = 'translateY(-20px)';
        
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

    // Auto-resize textareas
    document.querySelectorAll('textarea').forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
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

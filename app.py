import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")

@app.route('/')
def index():
    """Main form page for user input"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Process form data and generate AI suggestions"""
    try:
        # Get form data
        project_name = request.form.get('project_name', '').strip()
        project_description = request.form.get('project_description', '').strip()
        project_stage = request.form.get('project_stage', '')
        
        # Validate required fields
        if not project_name or not project_description:
            flash('项目名称和背景描述不能为空', 'error')
            return redirect(url_for('index'))
        
        # Process key persons data
        key_persons = []
        person_names = request.form.getlist('person_name[]')
        person_roles = request.form.getlist('person_role[]')
        person_resources = request.form.getlist('person_resources[]')
        person_needs = request.form.getlist('person_needs[]')
        
        for i in range(len(person_names)):
            if person_names[i].strip():  # Only add if name is not empty
                key_persons.append({
                    "name": person_names[i].strip(),
                    "role": person_roles[i].strip() if i < len(person_roles) else "",
                    "resources": [r.strip() for r in person_resources[i].split(',') if r.strip()] if i < len(person_resources) else [],
                    "make_happy": person_needs[i].strip() if i < len(person_needs) else ""
                })
        
        # Process external resources
        external_resources = request.form.getlist('external_resources')
        
        # Handle other resource input
        other_resource_text = request.form.get('other_resource_text', '').strip()
        if other_resource_text and request.form.get('other_resource_checkbox'):
            external_resources.append(other_resource_text)
        
        external_resources = request.form.getlist('external_resources')
        
        # Create JSON structure as per PRD
        form_data = {
            "project_name": project_name,
            "project_description": project_description,
            "project_stage": project_stage,
            "key_persons": key_persons,
            "external_resources": external_resources
        }
        
        # Log the received data
        app.logger.info(f"Received form data: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        
        # Generate AI suggestions (simulated for demo)
        suggestions = generate_ai_suggestions(form_data)
        
        return render_template('result.html', 
                             form_data=form_data, 
                             suggestions=suggestions)
    
    except Exception as e:
        app.logger.error(f"Error processing form: {str(e)}")
        flash('处理表单时发生错误，请重试', 'error')
        return redirect(url_for('index'))

def generate_ai_suggestions(form_data):
    """Generate AI suggestions based on form data"""
    # This is where you would integrate with an actual LLM API
    # For now, we'll return realistic suggestions based on the input
    
    project_name = form_data.get('project_name', '')
    key_persons = form_data.get('key_persons', [])
    
    suggestions = []
    
    # Suggestion 1: Revenue Sharing Model
    suggestion1 = {
        "title": "收益分成模式",
        "description": f"基于{project_name}项目，建立多方收益分成机制",
        "details": [
            "与品牌方建立产品销售分成关系，获得销售额的10-15%分成",
            "整合渠道资源，为品牌方提供精准流量导入",
            "建立长期合作关系，确保持续收益流"
        ],
        "key_roles": [person["name"] for person in key_persons[:2]],
        "revenue_potential": "中等-稳定",
        "implementation_difficulty": "中等"
    }
    
    # Suggestion 2: Platform Integration Model
    suggestion2 = {
        "title": "平台整合变现模式",
        "description": "通过整合多方资源，搭建收益分发平台",
        "details": [
            "建立资源整合平台，连接品牌方、渠道方和内容方",
            "收取平台服务费和交易佣金",
            "提供增值服务，如数据分析、营销策划等"
        ],
        "key_roles": [person["name"] for person in key_persons],
        "revenue_potential": "高-可扩展",
        "implementation_difficulty": "较高"
    }
    
    # Suggestion 3: Consulting & Advisory Model
    suggestion3 = {
        "title": "顾问咨询收费模式",
        "description": "基于项目经验，提供专业咨询服务",
        "details": [
            "为类似项目提供策划和执行咨询服务",
            "建立行业专家网络，收取介绍费和咨询费",
            "开发标准化解决方案，实现规模化收费"
        ],
        "key_roles": ["项目负责人", "行业专家"],
        "revenue_potential": "中等-专业化",
        "implementation_difficulty": "较低"
    }
    
    suggestions = [suggestion1, suggestion2, suggestion3]
    
    return suggestions

@app.route('/result')
def result():
    """Results page (in case of direct access)"""
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

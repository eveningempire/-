#!/usr/bin/env python
"""
楠岃瘉妯℃澘淇鏄惁鎴愬姛
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

def check_template_syntax():
    """妫€鏌ユā鏉胯娉曟槸鍚︽纭?""
    print("馃攳 妫€鏌ユā鏉胯娉?)
    print("=" * 50)
    
    template_path = 'rule_detection/templates/rule_detection/rule-edit.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 妫€鏌ユ槸鍚﹁繕鏈夐敊璇殑涓夊厓杩愮畻绗﹁娉?
        problematic_patterns = [
            "{{ isSaving ? '",
            "{{ isSaving ? \"",
            "{{ isSaving ? `",
            "{{ formatTime(",
            "{{ saveError }}"
        ]
        
        found_issues = []
        for pattern in problematic_patterns:
            if pattern in content:
                found_issues.append(pattern)
        
        if found_issues:
            print("鉂?鍙戠幇妯℃澘璇硶闂:")
            for issue in found_issues:
                print(f"   - {issue}")
            return False
        else:
            print("鉁?妯℃澘璇硶妫€鏌ラ€氳繃")
            
            # 妫€鏌ヤ慨澶嶅悗鐨勮娉?
            if "{% verbatim %}{{ formatTime(lastSaveTime) }}{% endverbatim %}" in content:
                print("鉁?Vue.js 鍑芥暟璋冪敤宸叉纭寘瑁?)
            else:
                print("鈿狅笍  Vue.js 鍑芥暟璋冪敤鍖呰鍙兘鏈夐棶棰?)
                
            if "{% verbatim %}{{ saveError }}{% endverbatim %}" in content:
                print("鉁?Vue.js 鍙橀噺鏄剧ず宸叉纭寘瑁?)
            else:
                print("鈿狅笍  Vue.js 鍙橀噺鏄剧ず鍖呰鍙兘鏈夐棶棰?)
                
            return True
            
    except Exception as e:
        print(f"鉂?妯℃澘璇硶妫€鏌ュ紓甯? {e}")
        return False

def test_template_rendering():
    """娴嬭瘯妯℃澘娓叉煋"""
    print(f"\n馃И 娴嬭瘯妯℃澘娓叉煋")
    print("=" * 50)
    
    try:
        from django.template.loader import render_to_string
        from django.test import RequestFactory
        
        # 鍒涘缓璇锋眰宸ュ巶
        factory = RequestFactory()
        request = factory.get('/api/v1/rules/editor/editor/')
        
        # 娴嬭瘯妯℃澘娓叉煋
        context = {
            'request': request,
            'title': '瑙勫垯缂栬緫鍣?
        }
        
        # 灏濊瘯娓叉煋妯℃澘
        rendered = render_to_string('rule_detection/rule-edit.html', context)
        
        if rendered:
            print("鉁?妯℃澘娓叉煋鎴愬姛")
            print(f"   娓叉煋鍐呭闀垮害: {len(rendered)} 瀛楃")
            
            # 妫€鏌ュ叧閿唴瀹?
            if '瑙勫垯缂栬緫鍣? in rendered:
                print("鉁?椤甸潰鏍囬姝ｇ‘")
            if 'isSaving' in rendered:
                print("鉁?Vue.js 鏁版嵁缁戝畾姝ｇ‘")
            if '淇濆瓨涓? in rendered:
                print("鉁?淇濆瓨鐘舵€佹枃鏈纭?)
            if 'v-if="isSaving"' in rendered:
                print("鉁?Vue.js 鏉′欢娓叉煋璇硶姝ｇ‘")
            if '{% verbatim %}' in rendered:
                print("鉁?Django verbatim 鏍囩姝ｇ‘")
                
            return True
        else:
            print("鉂?妯℃澘娓叉煋澶辫触锛氳繑鍥炵┖鍐呭")
            return False
            
    except Exception as e:
        print(f"鉂?妯℃澘娓叉煋寮傚父: {e}")
        return False

if __name__ == "__main__":
    print("馃殌 楠岃瘉妯℃澘淇")
    print("=" * 50)
    
    # 鎵ц楠岃瘉
    success1 = check_template_syntax()
    success2 = test_template_rendering()
    
    print(f"\n" + "=" * 50)
    if all([success1, success2]):
        print("馃帀 妯℃澘淇楠岃瘉鎴愬姛锛?)
        print("鉁?鎵€鏈夎娉曢敊璇凡淇")
        print("鉁?妯℃澘鍙互姝ｅ父娓叉煋")
        print("鉁?Vue.js 鍜?Django 妯℃澘璇硶鍏煎")
    else:
        print("鉂?妯℃澘淇楠岃瘉澶辫触锛岃妫€鏌ヤ慨澶嶇粨鏋?)
    
    print("=" * 50)


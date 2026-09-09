# MSFG澶氫俊鍙锋祦鍥炬ā鍧楀叧閿棶棰樺垎鏋愪笌淇鏂规

## 馃毃 鍙戠幇鐨勫叧閿棶棰?

### 1. 娴嬬偣璇勫垎閫昏緫闂 鉂?

**闂鎻忚堪锛?*
鍦?`data_management/batch_processing.py` 鐨?`_run_msfg_detection` 鏂规硶涓細

```python
# 褰撳墠鐨勯敊璇€昏緫
for i, test_node in enumerate(test_nodes):
    if i < len(numeric_params):
        param_key, param_value = numeric_params[i]
        # 闂锛氱畝鍗曟寜绱㈠紩鏄犲皠锛屾病鏈夎€冭檻娴嬬偣瑙勫垯
        score = max(0.0, min(1.0, abs(param_value) / (abs(param_value) + 1.0)))
        test_scores[test_node.name] = [score]
```

**闂鍒嗘瀽锛?*
- 娌℃湁浣跨敤閰嶇疆鐨勬祴鐐硅鍒欙紙TestPointRule锛?
- 绠€鍗曟寜绱㈠紩鏄犲皠鏁版嵁鍙傛暟鍒版祴璇曠偣锛岀己涔忚涔夊叧鑱?
- 璇勫垎绠楁硶杩囦簬绠€鍖栵紝娌℃湁鑰冭檻瀹為檯鐨勬晠闅滄娴嬮€昏緫

### 2. 娴嬬偣瑙勫垯鏈浣跨敤 鉂?

**闂鎻忚堪锛?*
绯荤粺涓湁瀹屾暣鐨?`TestPointRule` 妯″瀷鍜岀鐞嗙晫闈紝浣嗗湪瀹為檯鍒嗘瀽杩囩▼涓畬鍏ㄦ病鏈変娇鐢細

```python
# TestPointRule 妯″瀷瀛樺湪浣嗘湭琚皟鐢?
class TestPointRule(models.Model):
    rule_expression = models.TextField(help_text="瑙勫垯琛ㄨ揪寮忥紙鍗曠偣琛ㄨ揪寮忥級")
    weight = models.FloatField(default=1.0, help_text="鏉冮噸锛?..10锛?)
    # ... 浣嗗湪鎵归噺澶勭悊涓粠鏈娇鐢?
```

### 3. 閮ㄤ欢鏄犲皠閫昏緫娣蜂贡 鉂?

**闂鎻忚堪锛?*
鍦?`_run_msfg_detection` 涓殑閮ㄤ欢鏄犲皠閫昏緫鏈変弗閲嶉敊璇細

```python
# 閿欒鐨勬槧灏勯€昏緫
component_mappings = {}
for mapping in mappings:
    component_name = mapping.component_name
    if component_name not in component_mappings:
        component_mappings[component_name] = []
    # 馃毃 涓ラ噸閿欒锛氬拷鐣ヤ簡瀹為檯鐨勬祴璇曠偣鏄犲皠鍏崇郴
    component_mappings[component_name] = [fault_node.name for fault_node in fault_nodes]
```

### 4. 楂樼骇铻嶅悎绠楁硶鏈纭泦鎴?鉂?

**闂鎻忚堪锛?*
铏界劧鏈?`AdvancedMSFGFusion` 绫伙紝浣嗗湪鎵归噺澶勭悊涓殑璋冪敤鏂瑰紡鏈夐棶棰橈細

```python
# 褰撳墠璋冪敤
analysis_result = fusion_algorithm.run_advanced_analysis(
    test_scores=test_scores,  # 鏍煎紡锛歿test_name: [score]}
    test_nodes=test_nodes,
    fault_nodes=fault_nodes,
    edges=edges,
    component_mappings=component_mappings  # 杩欎釜鏄犲皠鏄敊璇殑
)
```

### 5. 鏁版嵁搴撳瓧娈典笉鍖归厤 鉂?

**闂鎻忚堪锛?*
`MSFGAnalysisResult` 妯″瀷瀛楁涓庡疄闄呮暟鎹粨鏋勪笉鍖归厤锛?

```python
# 妯″瀷瀛楁
component_results = models.JSONField(default=dict, help_text="閮ㄤ欢绾у埆鍒嗘瀽缁撴灉")

# 浣嗗疄闄呭瓨鍌ㄧ殑鏁版嵁缁撴瀯涓嶄竴鑷?
```

## 馃敡 淇鏂规

### 淇1锛氶噸鍐欐祴鐐硅瘎鍒嗛€昏緫

闇€瑕佸垱寤轰竴涓笓闂ㄧ殑娴嬬偣璇勫垎鏈嶅姟锛屾纭娇鐢═estPointRule锛?

```python
class TestPointScoringService:
    def calculate_test_scores(self, data_point: PHMData, msfg_definition: MSFGDefinition) -> Dict[str, float]:
        """鍩轰簬娴嬬偣瑙勫垯璁＄畻娴嬬偣鍒嗘暟"""
        # 1. 鑾峰彇璇SFG鐨勬墍鏈夋祴鐐硅鍒?
        # 2. 鎵ц瑙勫垯琛ㄨ揪寮?
        # 3. 搴旂敤鏉冮噸
        # 4. 杩斿洖鏍囧噯鍖栧垎鏁?
```

### 淇2锛氫慨澶嶉儴浠舵槧灏勯€昏緫

闇€瑕佹纭娇鐢?`TestPointComponentMapping`锛?

```python
def build_component_mappings(msfg_definition: MSFGDefinition) -> Dict[str, List[str]]:
    """鏋勫缓姝ｇ‘鐨勯儴浠舵槧灏勫叧绯?""
    # 鍩轰簬TestPointComponentMapping鍜孧SFG鍥剧粨鏋?
    # 鏋勫缓 component_name -> [fault_names] 鐨勬槧灏?
```

### 淇3锛氬畬鍠勬暟鎹簱瀛樺偍

闇€瑕佺‘淇濇暟鎹粨鏋勪竴鑷存€у拰瀹屾暣鎬с€?

### 淇4锛氱鍒扮娴嬭瘯

闇€瑕佸垱寤哄畬鏁寸殑娴嬭瘯鐢ㄤ緥楠岃瘉鏁翠釜娴佺▼銆?

## 馃搵 璇︾粏淇璁″垝

### 闃舵1锛氫慨澶嶆牳蹇冭瘎鍒嗛€昏緫 馃敟 楂樹紭鍏堢骇
- 鍒涘缓 TestPointScoringService
- 淇 batch_processing.py 涓殑 _run_msfg_detection 鏂规硶
- 纭繚娴嬬偣瑙勫垯琚纭娇鐢?

### 闃舵2锛氫慨澶嶉儴浠舵槧灏?馃敟 楂樹紭鍏堢骇  
- 淇 component_mappings 鏋勫缓閫昏緫
- 纭繚 TestPointComponentMapping 琚纭娇鐢?
- 楠岃瘉閮ㄤ欢鍋ュ悍搴﹁绠?

### 闃舵3锛氫慨澶嶆暟鎹簱瀛樺偍 馃敟 楂樹紭鍏堢骇
- 妫€鏌?MSFGAnalysisResult 瀛楁瀹氫箟
- 淇鏁版嵁淇濆瓨閫昏緫
- 纭繚鏁版嵁缁撴瀯涓€鑷存€?

### 闃舵4锛氱鍒扮楠岃瘉 馃敟 楂樹紭鍏堢骇
- 鍒涘缓娴嬭瘯鏁版嵁
- 楠岃瘉瀹屾暣娴佺▼
- 纭繚缁撴灉鍑嗙‘鎬?

## 馃幆 棰勬湡鏁堟灉

淇鍚庣殑MSFG妯″潡灏嗚兘澶燂細

1. **姝ｇ‘浣跨敤娴嬬偣瑙勫垯**锛氭牴鎹厤缃殑瑙勫垯琛ㄨ揪寮忚绠楁祴鐐瑰垎鏁?
2. **鍑嗙‘鐨勯儴浠舵槧灏?*锛氬熀浜嶵estPointComponentMapping杩涜姝ｇ‘鐨勯儴浠跺仴搴峰害鎺ㄦ柇
3. **鍙潬鐨勬暟鎹瓨鍌?*锛氱‘淇濆垎鏋愮粨鏋滆兘姝ｇ‘淇濆瓨鍒版暟鎹簱
4. **绔埌绔竴鑷存€?*锛氫粠鏁版嵁杈撳叆鍒扮粨鏋滆緭鍑虹殑瀹屾暣娴佺▼閮借兘姝ｅ父宸ヤ綔

## 鈿狅笍 椋庨櫓璇勪及

- **楂橀闄?*锛氬綋鍓嶇殑璇勫垎閫昏緫瀹屽叏閿欒锛屽彲鑳藉鑷磋鍒?
- **涓闄?*锛氭暟鎹簱瀛樺偍闂鍙兘瀵艰嚧缁撴灉涓㈠け
- **浣庨闄?*锛氱晫闈㈡樉绀哄彲鑳介渶瑕佺浉搴旇皟鏁?

杩欎簺闂闇€瑕佺珛鍗充慨澶嶏紝鍥犱负瀹冧滑褰卞搷浜嗘暣涓狹SFG妯″潡鐨勬牳蹇冨姛鑳姐€?


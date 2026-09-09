# 瑙勫垯淇濆瓨BUG淇璇存槑

## 闂鎻忚堪

鍦–MG鍋ュ悍妫€娴嬪钩鍙扮殑瑙勫垯妫€娴嬬粍浠朵腑锛屽綋鐢ㄦ埛鏂板缓瑙勫垯鎴栫紪杈戣鍒欏悗鐐瑰嚮"淇濆瓨"鎸夐挳锛岃鍒欏苟娌℃湁鐪熸淇濆瓨鍒板悗绔暟鎹簱銆傚埛鏂伴〉闈㈠悗锛岃鍒欎細鍙樺洖鍘熸潵鐨勭姸鎬併€傚鎬殑鏄紝鍒犻櫎瑙勫垯鍔熻兘鏄甯稿伐浣滅殑銆?

## 闂鍒嗘瀽

### 鏍规湰鍘熷洜

缁忚繃娣卞叆鍒嗘瀽锛屽彂鐜伴棶棰樼殑鏍规湰鍘熷洜鏄細

1. **鍓嶇淇濆瓨閫昏緫缂洪櫡**锛氬湪 `rule_detection/templates/rule_detection/rule-edit.html` 涓紝`saveRule()` 鏂规硶鍙槸鍦ㄥ墠绔唴瀛樹腑鏇存柊浜?`tableData`锛屼絾娌℃湁璋冪敤鍚庣鐨勪繚瀛樻帴鍙ｃ€?

2. **鏁版嵁鎸佷箙鍖栫己澶?*锛氭柊寤烘垨缂栬緫瑙勫垯鍚庯紝鏁版嵁鍙繚瀛樺湪鍓嶇鍐呭瓨涓紝娌℃湁鍚屾鍒板悗绔暟鎹簱銆?

3. **鐢ㄦ埛鎿嶄綔娴佺▼闂**锛氱敤鎴烽渶瑕佹墜鍔ㄧ偣鍑?閰嶇疆瑙勫垯"鎸夐挳鎵嶈兘淇濆瓨鏁版嵁锛屼絾杩欎釜姝ラ寰堝鏄撹蹇界暐銆?

### 鍏蜂綋闂浠ｇ爜

**淇鍓嶇殑 `saveRule()` 鏂规硶锛?*
```javascript
saveRule() {
  if (this.currentIndex === -1) {
    // 鏂板
    this.tableData.push({ ...this.currentRule });
  } else {
    // 缂栬緫
    this.$set(this.tableData, this.currentIndex, { ...this.currentRule });
  }
  this.totalItems = this.tableData.length;
  this.dialogVisible = false;
  this.$message.success('淇濆瓨鎴愬姛');
}
```

杩欎釜鏂规硶鍙槸鍦ㄥ墠绔唴瀛樹腑鏇存柊鏁版嵁锛屾病鏈夎皟鐢?`configRule()` 鏂规硶鏉ユ寔涔呭寲鍒板悗绔€?

## 瑙ｅ喅鏂规

### 淇鍐呭

1. **淇敼鍓嶇 `saveRule()` 鏂规硶**锛?
   - 灏嗘柟娉曟敼涓哄紓姝ユ柟娉?(`async`)
   - 鍦ㄤ繚瀛樺埌鍓嶇鍐呭瓨鍚庯紝鑷姩璋冪敤 `configRule()` 鏂规硶
   - 娣诲姞鏇村ソ鐨勯敊璇鐞嗗拰鐢ㄦ埛鍙嶉

2. **浼樺寲 `configRule()` 鏂规硶**锛?
   - 鏀硅繘閿欒澶勭悊閫昏緫
   - 纭繚姝ｇ‘杩斿洖Promise
   - 鎻愪緵鏇磋缁嗙殑閿欒淇℃伅

### 淇鍚庣殑浠ｇ爜

**淇鍚庣殑 `saveRule()` 鏂规硶锛?*
```javascript
async saveRule() {
  if (this.currentIndex === -1) {
    // 鏂板
    this.tableData.push({ ...this.currentRule });
  } else {
    // 缂栬緫
    this.$set(this.tableData, this.currentIndex, { ...this.currentRule });
  }
  this.totalItems = this.tableData.length;
  this.dialogVisible = false;
  this.$message.success('瑙勫垯宸蹭繚瀛樺埌鏈湴');
  
  // 鑷姩淇濆瓨鍒板悗绔?
  try {
    await this.configRule();
    this.$message.success('瑙勫垯宸叉垚鍔熶繚瀛樺埌鏈嶅姟鍣?);
  } catch (error) {
    this.$message.error('瑙勫垯淇濆瓨鍒版湇鍔″櫒澶辫触锛岃鎵嬪姩鐐瑰嚮"閰嶇疆瑙勫垯"鎸夐挳閲嶈瘯');
    console.error('鑷姩淇濆瓨澶辫触:', error);
  }
}
```

**浼樺寲鍚庣殑 `configRule()` 鏂规硶锛?*
```javascript
async configRule() {
  if (!this.selectedCmgModel) {
    this.$message.warning('璇峰厛閫夋嫨PHM妯″瀷');
    throw new Error('鏈€夋嫨PHM妯″瀷');
  }
  
  try {
    const response = await axios.post('/api/v1/rules/editor/config-rule/', {
      cmg_model_id: this.selectedCmgModel,
      tableData: JSON.stringify(this.tableData)
    }, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    
    if (response.data && response.data.status === 'success') {
      this.$message.success('瑙勫垯閰嶇疆淇濆瓨鎴愬姛');
      return response.data;
    } else {
      throw new Error('鏈嶅姟鍣ㄨ繑鍥為敊璇姸鎬?);
    }
  } catch (error) {
    console.error('淇濆瓨瑙勫垯澶辫触:', error);
    this.$message.error('淇濆瓨瑙勫垯澶辫触: ' + (error.response?.data?.error || error.message));
    throw error;
  }
}
```

## 淇鏁堟灉

### 淇鍓嶇殑闂
- 鏂板缓鎴栫紪杈戣鍒欏悗锛屾暟鎹彧淇濆瓨鍦ㄥ墠绔唴瀛?
- 鍒锋柊椤甸潰鍚庤鍒欎涪澶?
- 鐢ㄦ埛闇€瑕佹墜鍔ㄧ偣鍑?閰嶇疆瑙勫垯"鎸夐挳鎵嶈兘淇濆瓨
- 鐢ㄦ埛浣撻獙宸紝瀹规槗涓㈠け鏁版嵁

### 淇鍚庣殑鏀硅繘
- 鏂板缓鎴栫紪杈戣鍒欏悗鑷姩淇濆瓨鍒板悗绔暟鎹簱
- 鍒锋柊椤甸潰鍚庤鍒欎繚鎸佷笉鍙?
- 鎻愪緵娓呮櫚鐨勪繚瀛樼姸鎬佸弽棣?
- 鑷姩閿欒澶勭悊鍜岄噸璇曟彁绀?
- 鐢ㄦ埛浣撻獙鏄捐憲鏀瑰杽

## 娴嬭瘯楠岃瘉

### 娴嬭瘯姝ラ
1. 鍚姩PHM骞冲彴
2. 杩涘叆瑙勫垯妫€娴嬬粍浠?
3. 閫夋嫨PHM妯″瀷
4. 鏂板缓涓€涓鍒?
5. 鐐瑰嚮淇濆瓨鎸夐挳
6. 鍒锋柊椤甸潰楠岃瘉瑙勫垯鏄惁淇濇寔

### 娴嬭瘯鑴氭湰
杩愯 `test_rule_save_fix.py` 鑴氭湰鍙互鑷姩娴嬭瘯淇鏁堟灉锛?
```bash
python test_rule_save_fix.py
```

## 鎶€鏈粏鑺?

### 鍚庣淇濆瓨閫昏緫
鍚庣 `config_rule` 鏂规硶浣跨敤浜嬪姟纭繚鏁版嵁涓€鑷存€э細
1. 鍒犻櫎鐜版湁瑙勫垯锛堥伩鍏嶅敮涓€绾︽潫鍐茬獊锛?
2. 瑙ｆ瀽瑙勫垯琛ㄨ揪寮忥紝鎻愬彇鐩稿叧鍙傛暟
3. 鍒涘缓鎴栨洿鏂版晠闅滃畾涔?
4. 鍒涘缓瑙勫垯瀹氫箟
5. 鑷姩鎺ㄦ柇缁勪欢锛堝鏋滄湭鎸囧畾锛?

### 鏁版嵁娴佺▼
1. 鍓嶇鐢ㄦ埛鎿嶄綔 鈫?鏇存柊鍓嶇鍐呭瓨鏁版嵁
2. 鑷姩璋冪敤 `configRule()` 鈫?鍙戦€佹暟鎹埌鍚庣
3. 鍚庣澶勭悊 鈫?淇濆瓨鍒版暟鎹簱
4. 杩斿洖缁撴灉 鈫?鍓嶇鏄剧ず鎴愬姛/澶辫触娑堟伅

## 娉ㄦ剰浜嬮」

1. **鍚戝悗鍏煎**锛氫慨澶嶄笉褰卞搷鐜版湁鍔熻兘锛屽彧鏄敼杩涗簡淇濆瓨娴佺▼
2. **閿欒澶勭悊**锛氬鏋滆嚜鍔ㄤ繚瀛樺け璐ワ紝鐢ㄦ埛浠嶅彲鎵嬪姩鐐瑰嚮"閰嶇疆瑙勫垯"鎸夐挳
3. **鎬ц兘褰卞搷**锛氭瘡娆′繚瀛橀兘浼氳皟鐢ㄥ悗绔疉PI锛屼絾杩欐槸蹇呰鐨勬寔涔呭寲鎿嶄綔
4. **鐢ㄦ埛浣撻獙**锛氭彁渚涙竻鏅扮殑鐘舵€佸弽棣堬紝閬垮厤鐢ㄦ埛鍥版儜

## 鎬荤粨

杩欎釜淇瑙ｅ喅浜嗚鍒欎繚瀛樼殑鏍稿績闂锛岄€氳繃鑷姩鍖栫殑鏁版嵁鎸佷箙鍖栨祦绋嬶紝纭繚浜嗙敤鎴锋搷浣滅殑鍙潬鎬с€備慨澶嶅悗鐨勭郴缁熸彁渚涗簡鏇村ソ鐨勭敤鎴蜂綋楠岋紝閬垮厤浜嗘暟鎹涪澶辩殑椋庨櫓銆?


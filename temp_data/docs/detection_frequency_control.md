# 妫€娴嬮鐜囨帶鍒跺姛鑳借鏄?

## 鍔熻兘姒傝堪

妫€娴嬮鐜囨帶鍒跺姛鑳芥棬鍦ㄤ紭鍖栧ぇ閲忔暟鎹鍏ユ椂鐨勬娴嬫€ц兘锛岄€氳繃鎺у埗妫€娴嬮鐜囧噺灏戞娴嬮噺锛屼粠鑰屾樉钁楁彁鍗囧鐞嗛€熷害銆?

## 问题背景

### 原始问题
- **閫愬抚妫€娴?*锛氭瘡涓暟鎹抚閮戒細杩涜IMS妫€娴?
- **鎬ц兘鐡堕**锛氬ぇ閲忔暟鎹椂妫€娴嬮噺杩囧ぇ锛屽鐞嗛€熷害鎱?
- **鐢ㄦ埛浣撻獙宸?*锛氱敤鎴烽渶瑕佺瓑寰呭緢闀挎椂闂存墠鑳界湅鍒版娴嬬粨鏋?

### 瑙ｅ喅鏂规
閫氳繃妫€娴嬮鐜囨帶鍒讹紝瀹炵幇浠ヤ笅浼樺寲锛?
- **鏅鸿兘甯ч€夋嫨**锛氭牴鎹椂闂撮棿闅旈€夋嫨浠ｈ〃鎬у抚杩涜妫€娴?
- **妫€娴嬮噺鍑忓皯**锛氬ぇ骞呭噺灏戦渶瑕佹娴嬬殑甯ф暟
- **鎬ц兘鎻愬崌**锛氭樉钁楁彁鍗囧鐞嗛€熷害
- **绾ц仈浼樺寲**锛氬噺灏戝悗缁鍒欐娴嬪拰MSFG妫€娴嬬殑宸ヤ綔閲?

## 妫€娴嬫ā寮?

### 1. 楂橀妯″紡 (high_frequency)
- **闂撮殧**锛?绉?
- **閫傜敤鍦烘櫙**锛氬皬鏁版嵁闆嗭紝闇€瑕侀珮绮惧害妫€娴?
- **妫€娴嬫瘮渚?*锛氱害100%锛堟椂闂磋寖鍥村皬浜?绉掓椂锛?

### 2. 涓妯″紡 (medium_frequency)
- **闂撮殧**锛?0绉?
- **适用场景**：中等数据集，平衡精度和性能
- **妫€娴嬫瘮渚?*锛氱害3-5%

### 3. 浣庨妯″紡 (low_frequency)
- **闂撮殧**锛?0绉?
- **閫傜敤鍦烘櫙**锛氬ぇ鏁版嵁闆嗭紝浼樺厛鑰冭檻鎬ц兘
- **妫€娴嬫瘮渚?*锛氱害1-2%

### 4. 鑷€傚簲妯″紡 (adaptive)
- **鏅鸿兘璋冩暣**锛氭牴鎹暟鎹噺鑷姩閫夋嫨鏈€浣抽棿闅?
- **闃堝€奸厤缃?*锛?
  - 灏忔暟鎹泦锛堚墹1000甯э級锛?绉掗棿闅?
  - 涓暟鎹泦锛堚墹5000甯э級锛?0绉掗棿闅?
  - 澶ф暟鎹泦锛堚墹10000甯э級锛?0绉掗棿闅?
  - 瓒呭ぇ鏁版嵁闆嗭紙>10000甯э級锛?0绉掗棿闅?

### 5. 绂佺敤妯″紡 (disabled)
- **琛屼负**锛氶€愬抚妫€娴嬶紙鍘熷閫昏緫锛?
- **閫傜敤鍦烘櫙**锛氶渶瑕佹渶楂樼簿搴︽娴?

## 配置说明

### 绯荤粺閰嶇疆鏂囦欢
浣嶇疆锛歚config/system_config.json`

```json
{
  "detection_frequency": {
    "enabled": true,
    "mode": "adaptive",
    "high_frequency": {
      "interval_seconds": 1,
      "frames_per_interval": 1
    },
    "medium_frequency": {
      "interval_seconds": 30,
      "frames_per_interval": 1
    },
    "low_frequency": {
      "interval_seconds": 60,
      "frames_per_interval": 1
    },
    "adaptive": {
      "small_dataset_threshold": 1000,
      "medium_dataset_threshold": 5000,
      "large_dataset_threshold": 10000,
      "small_dataset_interval": 1,
      "medium_dataset_interval": 30,
      "large_dataset_interval": 60
    }
  }
}
```

### 配置参数说明

| 鍙傛暟 | 绫诲瀷 | 榛樿鍊?| 璇存槑 |
|------|------|--------|------|
| enabled | boolean | true | 鏄惁鍚敤妫€娴嬮鐜囨帶鍒?|
| mode | string | adaptive | 妫€娴嬫ā寮?|
| interval_seconds | int | 1/30/60 | 妫€娴嬮棿闅旓紙绉掞級 |
| frames_per_interval | int | 1 | 姣忎釜闂撮殧妫€娴嬬殑甯ф暟 |
| small_dataset_threshold | int | 1000 | 灏忔暟鎹泦闃堝€?|
| medium_dataset_threshold | int | 5000 | 涓暟鎹泦闃堝€?|
| large_dataset_threshold | int | 10000 | 澶ф暟鎹泦闃堝€?|

## 浣跨敤鏂规硶

### 1. 鏌ョ湅褰撳墠閰嶇疆
```bash
python manage.py update_detection_frequency --show
```

### 2. 鏇存柊妫€娴嬫ā寮?
```bash
# 璁剧疆涓洪珮棰戞ā寮?
python manage.py update_detection_frequency --mode high_frequency

# 璁剧疆涓轰腑棰戞ā寮?
python manage.py update_detection_frequency --mode medium_frequency

# 璁剧疆涓轰綆棰戞ā寮?
python manage.py update_detection_frequency --mode low_frequency

# 璁剧疆涓鸿嚜閫傚簲妯″紡
python manage.py update_detection_frequency --mode adaptive

# 绂佺敤棰戠巼鎺у埗
python manage.py update_detection_frequency --mode disabled
```

### 3. 鏇存柊妫€娴嬮棿闅?
```bash
# 鏇存柊楂橀闂撮殧涓?绉?
python manage.py update_detection_frequency --high-interval 2

# 鏇存柊涓闂撮殧涓?5绉?
python manage.py update_detection_frequency --medium-interval 45

# 鏇存柊浣庨闂撮殧涓?20绉?
python manage.py update_detection_frequency --low-interval 120
```

### 4. 鏇存柊鑷€傚簲闃堝€?
```bash
# 鏇存柊灏忔暟鎹泦闃堝€?
python manage.py update_detection_frequency --small-threshold 500

# 鏇存柊涓暟鎹泦闃堝€?
python manage.py update_detection_frequency --medium-threshold 3000

# 鏇存柊澶ф暟鎹泦闃堝€?
python manage.py update_detection_frequency --large-threshold 8000
```

### 5. 测试功能
```bash
# 娴嬭瘯鎸囧畾PHM鐨勬娴嬮鐜囨帶鍒?
python manage.py test_detection_frequency --cmg-id PHM001 --mode adaptive --hours 24
```

## 性能优化效果

### 鐞嗚鎬ц兘鎻愬崌
- **灏忔暟鎹泦锛?000甯э級**锛氭娴嬫瘮渚?00%锛屾棤鎬ц兘鎻愬崌
- **涓暟鎹泦锛?000甯э級**锛氭娴嬫瘮渚?-5%锛屾€ц兘鎻愬崌95-97%
- **澶ф暟鎹泦锛?0000甯э級**锛氭娴嬫瘮渚?-2%锛屾€ц兘鎻愬崌98-99%
- **瓒呭ぇ鏁版嵁闆嗭紙50000甯э級**锛氭娴嬫瘮渚?.5-1%锛屾€ц兘鎻愬崌99-99.5%

### 实际测试数据
鍩轰簬16000甯ф暟鎹殑娴嬭瘯缁撴灉锛?

| 妯″紡 | 妫€娴嬪抚鏁?| 妫€娴嬫瘮渚?| 澶勭悊鏃堕棿 | 鎬ц兘鎻愬崌 |
|------|----------|----------|----------|----------|
| 绂佺敤 | 16000 | 100% | 111绉?| 0% |
| 楂橀 | 16000 | 100% | 111绉?| 0% |
| 涓 | 533 | 3.3% | 4绉?| 96.4% |
| 浣庨 | 267 | 1.7% | 2绉?| 98.2% |
| 鑷€傚簲 | 533 | 3.3% | 4绉?| 96.4% |

## 鎶€鏈疄鐜?

### 鏍稿績缁勪欢

1. **DetectionFrequencyController**
   - 浣嶇疆锛歚health_management/detection_frequency_controller.py`
   - 功能：检测频率控制的核心逻辑

2. **闆嗘垚鐐?*
   - 鎵归噺澶勭悊锛歚data_management/batch_processing.py`
   - 娴佸紡澶勭悊锛歚data_management/batch_processing.py`

### 甯ч€夋嫨绠楁硶

1. **时间窗口划分**：根据配置的间隔将时间范围划分为多个窗口
2. **鏈€杩戝抚閫夋嫨**锛氬湪姣忎釜鏃堕棿绐楀彛涓€夋嫨鏈€鎺ヨ繎鐩爣鏃堕棿鐨勫抚
3. **杈圭晫甯т繚璇?*锛氱‘淇濋€夋嫨绗竴甯у拰鏈€鍚庝竴甯?
4. **鍘婚噸鎺掑簭**锛氬幓闄ら噸澶嶅抚骞舵帓搴?

### 结果映射

- **妫€娴嬬粨鏋?*锛氬彧瀵归€変腑鐨勫抚杩涜妫€娴?
- **缁撴灉鏄犲皠**锛氬皢妫€娴嬬粨鏋滄槧灏勫洖鍘熷璁板綍绱㈠紩
- **鏈娴嬪抚**锛氭爣璁颁负None锛岃〃绀烘湭杩涜妫€娴?

## 娉ㄦ剰浜嬮」

### 1. 绮惧害鏉冭　
- 妫€娴嬮鐜囪秺浣庯紝鍙兘閬楁紡鐨勫紓甯歌秺澶?
- 寤鸿鏍规嵁瀹為檯闇€姹傞€夋嫨鍚堥€傜殑妯″紡

### 2. 鏃堕棿绮惧害
- 甯ч€夋嫨鍩轰簬鏃堕棿鎴筹紝纭繚鏁版嵁鏃堕棿绮惧害
- 支持毫秒级时间戳

### 3. 閰嶇疆鎸佷箙鍖?
- 閰嶇疆鏇存敼浼氱珛鍗崇敓鏁?
- 閲嶅惎鏈嶅姟鍚庨厤缃繚鎸佷笉鍙?

### 4. 鍏煎鎬?
- 鍚戝悗鍏煎锛屽彲浠ラ殢鏃剁鐢ㄩ鐜囨帶鍒?
- 涓嶅奖鍝嶇幇鏈夌殑妫€娴嬮€昏緫

## 鏁呴殰鎺掗櫎

### 1. 閰嶇疆涓嶇敓鏁?
- 妫€鏌ラ厤缃枃浠舵牸寮忔槸鍚︽纭?
- 确认配置更新命令执行成功

### 2. 妫€娴嬫瘮渚嬪紓甯?
- 妫€鏌ユ暟鎹椂闂存埑鏄惁姝ｇ‘
- 纭鏃堕棿鑼冨洿璁剧疆鍚堢悊

### 3. 鎬ц兘鎻愬崌涓嶆槑鏄?
- 妫€鏌ユ暟鎹噺鏄惁杈惧埌闃堝€?
- 纭妫€娴嬫ā寮忚缃纭?

## 鏈潵鎵╁睍

### 1. 鍔ㄦ€佽皟鏁?
- 鏍规嵁绯荤粺璐熻浇鍔ㄦ€佽皟鏁存娴嬮鐜?
- 鏀寔瀹炴椂閰嶇疆鏇存柊

### 2. 鏅鸿兘浼樺寲
- 鍩轰簬鍘嗗彶鏁版嵁浼樺寲甯ч€夋嫨绛栫暐
- 鏀寔鏈哄櫒瀛︿範浼樺寲妫€娴嬮棿闅?

### 3. 鍙鍖栭厤缃?
- 鎻愪緵Web鐣岄潰杩涜閰嶇疆绠＄悊
- 鏀寔瀹炴椂鎬ц兘鐩戞帶


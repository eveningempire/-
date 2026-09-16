# 鏁版嵁搴撴€ц兘浼樺寲寤鸿

## 绱㈠紩浼樺寲

涓轰簡鎻愬崌鏌ヨ鎬ц兘锛屽缓璁负浠ヤ笅瀛楁娣诲姞鏁版嵁搴撶储寮曪細

### PHMData琛ㄧ储寮?

```sql
-- 澶嶅悎绱㈠紩锛欳MG ID + 鏃堕棿鎴筹紙鏈€閲嶈锛?
CREATE INDEX idx_cmgdata_cmg_timestamp ON data_management_cmgdata(cmg_id, timestamp);

-- 鏃堕棿鎴崇储寮曪紙鐢ㄤ簬鏃堕棿鑼冨洿鏌ヨ锛?
CREATE INDEX idx_cmgdata_timestamp ON data_management_cmgdata(timestamp);

-- PHM ID绱㈠紩锛堢敤浜庢寜PHM杩囨护锛?
CREATE INDEX idx_cmgdata_cmg_id ON data_management_cmgdata(cmg_id);
```

### PHM琛ㄧ储寮?

```sql
-- PHM ID绱㈠紩锛堢敤浜庡揩閫熸煡鎵撅級
CREATE UNIQUE INDEX idx_cmg_cmg_id ON data_management_cmg(cmg_id);
```

### 瑙勫垯妫€娴嬬粨鏋滆〃绱㈠紩

```sql
-- 澶嶅悎绱㈠紩锛欳MG + 鏃堕棿鎴?
CREATE INDEX idx_rule_results_cmg_timestamp ON rule_detection_ruleresult(cmg_id, created_at);

-- 鏁呴殰绾у埆绱㈠紩锛堢敤浜庢寜涓ラ噸绋嬪害杩囨护锛?
CREATE INDEX idx_rule_results_fault_level ON rule_detection_ruleresult(fault_level);
```

### IMS妫€娴嬬粨鏋滆〃绱㈠紩

```sql
-- 澶嶅悎绱㈠紩锛欳MG + 鏃堕棿鎴?
CREATE INDEX idx_ims_results_cmg_timestamp ON health_management_imsdetectionresult(cmg_data_id, created_at);

-- 寮傚父鏍囪绱㈠紩
CREATE INDEX idx_ims_results_anomaly ON health_management_imsdetectionresult(is_anomaly);
```

## 鏌ヨ浼樺寲绛栫暐

### 1. 鍒嗛〉鏌ヨ浼樺寲
- 浣跨敤鍩轰簬娓告爣鐨勫垎椤佃€岄潪OFFSET/LIMIT
- 闄愬埗鍗曟鏌ヨ杩斿洖鐨勬暟鎹噺锛堥粯璁?000鏉★級

### 2. 鏃堕棿鑼冨洿鏌ヨ浼樺寲
- 浣跨敤澶嶅悎绱㈠紩(cmg_id, timestamp)
- 閬垮厤鍦╓HERE瀛愬彞涓娇鐢ㄥ嚱鏁?

### 3. 鏁版嵁缂撳瓨绛栫暐
- Redis缂撳瓨鐑偣鏁版嵁锛堟渶杩?0鍒嗛挓锛?
- 鏌ヨ缁撴灉缂撳瓨锛?-5鍒嗛挓TTL锛?
- 瀹炴椂鏁版嵁浼樺厛浠庣紦瀛樿幏鍙?

## 鏁版嵁搴撹繛鎺ヤ紭鍖?

### 杩炴帴姹犻厤缃?
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'isolation_level': 'read committed',
        },
        'CONN_MAX_AGE': 3600,  # 杩炴帴澶嶇敤1灏忔椂
        'CONN_HEALTH_CHECKS': True,
    }
}
```

### MySQL閰嶇疆浼樺寲
```ini
[mysqld]
# 缂撳啿姹犲ぇ灏忥紙寤鸿涓虹郴缁熷唴瀛樼殑70-80%锛?
innodb_buffer_pool_size = 2G

# 鏃ュ織鏂囦欢澶у皬
innodb_log_file_size = 256M

# 鏌ヨ缂撳瓨
query_cache_type = 1
query_cache_size = 128M

# 杩炴帴鏁?
max_connections = 200
max_user_connections = 180

# 鎱㈡煡璇㈡棩蹇?
slow_query_log = 1
long_query_time = 2
```

## 鏁版嵁娓呯悊绛栫暐

### 瀹氭湡娓呯悊鍘嗗彶鏁版嵁
```python
# 淇濈暀鏈€杩?涓湀鐨勮缁嗘暟鎹?
# 3-12涓湀鐨勬暟鎹繘琛岃仛鍚堝瓨鍌?
# 12个月以上的数据归档或删除

# 绀轰緥娓呯悊鑴氭湰
from datetime import datetime, timedelta
from django.db import transaction

def cleanup_old_data():
    cutoff_date = datetime.now() - timedelta(days=90)
    
    with transaction.atomic():
        # 鍒犻櫎90澶╁墠鐨勮缁嗘暟鎹?
        old_count = PHMData.objects.filter(
            timestamp__lt=cutoff_date
        ).count()
        
        if old_count > 0:
            PHMData.objects.filter(
                timestamp__lt=cutoff_date
            ).delete()
            
        print(f"Cleaned up {old_count} old records")
```

## 鐩戞帶鍜岀淮鎶?

### 鎬ц兘鐩戞帶鎸囨爣
- 鏌ヨ鍝嶅簲鏃堕棿
- 鏁版嵁搴撹繛鎺ユ暟
- 缂撳瓨鍛戒腑鐜?
- Redis鍐呭瓨浣跨敤鐜?

### 定期维护任务
- 重建索引统计信息
- 娓呯悊鏌ヨ缂撳瓨
- 妫€鏌ユ參鏌ヨ鏃ュ織
- 鐩戞帶鏁版嵁搴撶┖闂翠娇鐢?

## 瀹炴柦姝ラ

1. **绔嬪嵆瀹炴柦**
   - 娣诲姞鍏抽敭绱㈠紩
   - 鍚敤Redis缂撳瓨
   - 閰嶇疆杩炴帴姹?

2. **鐭湡浼樺寲锛?-2鍛級**
   - 瀹炴柦鏁版嵁娓呯悊绛栫暐
   - 浼樺寲鎱㈡煡璇?
   - 璋冩暣缂撳瓨绛栫暐

3. **闀挎湡浼樺寲锛?涓湀鍚庯級**
   - 鑰冭檻璇诲啓鍒嗙
   - 鏁版嵁鍒嗙墖绛栫暐
   - 鍘嗗彶鏁版嵁褰掓。

閫氳繃浠ヤ笂浼樺寲鎺柦锛岄鏈熷彲浠ュ皢鏁版嵁搴撴煡璇㈡€ц兘鎻愬崌50-80%锛屾樉钁楁敼鍠勭敤鎴蜂綋楠屻€?


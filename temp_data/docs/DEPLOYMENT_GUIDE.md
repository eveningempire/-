# PHM骞冲彴浼樺寲閮ㄧ讲鎸囧崡

## 馃殌 浼樺寲鍔熻兘姒傝堪

鏈浼樺寲涓篊MG鍋ュ悍绠＄悊骞冲彴寮曞叆浜嗕互涓嬮噸瑕佸姛鑳斤細

### 鉁?鏍稿績浼樺寲
1. **Redis缂撳瓨灞?* - 鏄捐憲鎻愬崌鏁版嵁鏌ヨ鎬ц兘
2. **WebSocket瀹炴椂閫氫俊** - 鐪熸鐨勫疄鏃舵暟鎹帹閫?
3. **鏁版嵁搴撴煡璇紭鍖?* - 鍑忚交鏁版嵁搴撳帇鍔?
4. **绯荤粺鐘舵€佺洃鎺?* - 瀹炴椂鐩戞帶绯荤粺鍋ュ悍鐘舵€?

## 馃搵 閮ㄧ讲鍓嶅噯澶?

### 1. 鐜瑕佹眰
- Python 3.10+
- Redis Server 5.0+
- MySQL 5.7+ 鎴?8.0+
- Node.js 16+ (鍓嶇寮€鍙?

### 2. 瀹夎Redis
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Windows (浣跨敤WSL鎴栦笅杞絎indows鐗堟湰)
# 鎴栦娇鐢―ocker
docker run -d --name redis -p 6379:6379 redis:latest

# 鍚姩Redis鏈嶅姟
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 楠岃瘉Redis杩愯
redis-cli ping
```

## 馃敡 鍚庣閮ㄧ讲

### 1. 瀹夎鏂颁緷璧?
```bash
# 婵€娲昏櫄鎷熺幆澧?
source .venv/bin/activate  # Linux/Mac
# 鎴?
.venv\Scripts\activate     # Windows

# 瀹夎鏂颁緷璧?
pip install -r requirements.txt
```

### 2. 鐜鍙橀噺閰嶇疆
鍒涘缓 `.env` 鏂囦欢鎴栬缃幆澧冨彉閲忥細
```bash
# Redis閰嶇疆
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # 濡傛灉Redis璁剧疆浜嗗瘑鐮?

# MySQL閰嶇疆锛堢幇鏈夛級
MYSQL_DATABASE=cmg_db
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

### 3. 鏁版嵁搴撲紭鍖?
```bash
# 鍒涘缓鎬ц兘浼樺寲绱㈠紩
python manage.py create_indexes

# 濡傛灉闇€瑕佸己鍒堕噸寤虹储寮?
python manage.py create_indexes --force
```

### 4. 鍚姩鏈嶅姟
```bash
# 浣跨敤ASGI鏈嶅姟鍣ㄦ敮鎸乄ebSocket锛堟帹鑽愮敓浜х幆澧冿級
pip install daphne
daphne -b 0.0.0.0 -p 8000 phm_backend.asgi:application

# 鎴栦娇鐢―jango寮€鍙戞湇鍔″櫒锛堝紑鍙戠幆澧冿級
python manage.py runserver
```

## 馃帹 鍓嶇閮ㄧ讲

### 1. 瀹夎渚濊禆
```bash
cd frontend
npm install
```

### 2. 寮€鍙戞ā寮?
```bash
npm run dev
```

### 3. 鐢熶骇鏋勫缓
```bash
npm run build
```

## 馃攳 楠岃瘉閮ㄧ讲

### 1. 妫€鏌edis杩炴帴
```bash
# 杩涘叆Django Shell
python manage.py shell

# 娴嬭瘯Redis杩炴帴
from data_management.redis_service import redis_service
print(redis_service.ping())  # 搴旇杩斿洖True
```

### 2. 妫€鏌ebSocket
- 璁块棶鍓嶇椤甸潰
- 杩涘叆"绯荤粺绠＄悊 -> 绯荤粺鐘舵€?
- 鏌ョ湅WebSocket杩炴帴鐘舵€?
- 娴嬭瘯瀹炴椂鏁版嵁鍔熻兘

### 3. 鎬ц兘娴嬭瘯
```bash
# 鏌ョ湅缂撳瓨鐘舵€?
curl http://localhost:8000/api/v1/data/data/cache-stats/

# 娴嬭瘯瀹炴椂鏁版嵁API
curl http://localhost:8000/api/v1/data/data/realtime/?cmg_id=PHM_001&limit=100
```

## 馃搳 鎬ц兘鐩戞帶

### 1. 绯荤粺鐘舵€侀〉闈?
璁块棶 `http://localhost:3000/system-status` 鏌ョ湅锛?
- Redis杩炴帴鐘舵€?
- 缂撳瓨浣跨敤鎯呭喌
- WebSocket杩炴帴鐘舵€?
- 鍐呭瓨缂撳瓨缁熻

### 2. 鎬ц兘鎸囨爣
浼樺寲鍚庨鏈熸敼鍠勶細
- **鏁版嵁鏌ヨ閫熷害**: 鎻愬崌50-80%
- **瀹炴椂鎬?*: 浠庤疆璇㈡敼涓烘帹閫侊紝寤惰繜鍑忓皯90%
- **鏁版嵁搴撳帇鍔?*: 鍑忓皯70%浠ヤ笂
- **鐢ㄦ埛浣撻獙**: 鏄捐憲鎻愬崌

## 馃敡 甯歌闂瑙ｅ喅

### 1. Redis杩炴帴澶辫触
```bash
# 妫€鏌edis鏈嶅姟鐘舵€?
sudo systemctl status redis-server

# 妫€鏌ョ鍙ｅ崰鐢?
netstat -tlnp | grep 6379

# 娴嬭瘯杩炴帴
redis-cli -h localhost -p 6379 ping
```

### 2. WebSocket杩炴帴闂
- 纭繚浣跨敤ASGI鏈嶅姟鍣?(daphne)
- 妫€鏌ラ槻鐏璁剧疆
- 楠岃瘉鍓嶇浠ｇ悊閰嶇疆

### 3. 鏁版嵁搴撴€ц兘闂
```bash
# 妫€鏌ョ储寮曞垱寤烘儏鍐?
python manage.py shell
from django.db import connection
cursor = connection.cursor()
cursor.execute("SHOW INDEX FROM data_management_cmgdata;")
print(cursor.fetchall())
```

## 馃殌 鐢熶骇鐜寤鸿

### 1. Redis閰嶇疆浼樺寲
```ini
# /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 2. Nginx閰嶇疆锛圵ebSocket鏀寔锛?
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 绯荤粺鐩戞帶
- 璁剧疆Redis鍐呭瓨鐩戞帶
- 鐩戞帶WebSocket杩炴帴鏁?
- 瀹氭湡妫€鏌ユ暟鎹簱鎬ц兘
- 閰嶇疆鏃ュ織杞浆

## 馃搱 鍚庣画浼樺寲寤鸿

1. **鏁版嵁鍒嗙墖**: 褰撴暟鎹噺澧為暱鏃惰€冭檻鍒嗗簱鍒嗚〃
2. **璇诲啓鍒嗙**: 閰嶇疆MySQL涓讳粠澶嶅埗
3. **缂撳瓨棰勭儹**: 瀹炵幇鐑偣鏁版嵁棰勫姞杞?
4. **娑堟伅闃熷垪**: 寮曞叆Celery澶勭悊寮傛浠诲姟

## 馃啒 鏀寔涓庣淮鎶?

濡傞亣鍒伴棶棰橈紝璇锋鏌ワ細
1. 鏃ュ織鏂囦欢涓殑閿欒淇℃伅
2. Redis鍜屾暟鎹簱杩炴帴鐘舵€?
3. 绯荤粺璧勬簮浣跨敤鎯呭喌
4. 缃戠粶杩炴帴閰嶇疆

閫氳繃绯荤粺鐘舵€侀〉闈㈠彲浠ュ疄鏃剁洃鎺у悇缁勪欢鐘舵€侊紝渚夸簬蹇€熷畾浣嶉棶棰樸€?


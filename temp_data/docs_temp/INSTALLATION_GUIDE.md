# PHM鍋ュ悍绠＄悊骞冲彴 - 瀹夎鎸囧崡

## 姒傝堪

PHM鍋ュ悍绠＄悊骞冲彴鏄竴涓熀浜嶥jango + Vue.js鐨勭幇浠ｅ寲鑸ぉ鍣ㄦ帶鍒跺姏鐭╅檧铻哄仴搴风洃娴嬩笌鏁呴殰璇婃柇绯荤粺銆傛湰鎸囧崡灏嗗府鍔╂偍鍦ㄦ柊璁＄畻鏈轰笂姝ｇ‘瀹夎鍜岄厤缃郴缁熴€?
## 绯荤粺瑕佹眰

### 纭欢瑕佹眰
- **鍐呭瓨**: 8GB+ (鎺ㄨ崘16GB)
- **瀛樺偍绌洪棿**: 50GB+ 鍙敤绌洪棿
- **澶勭悊鍣?*: 鏀寔64浣嶆灦鏋?
### 杞欢瑕佹眰
- **鎿嶄綔绯荤粺**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: 3.8+ 
- **Node.js**: 16+
- **MySQL**: 8.0+
- **Redis**: 6.0+

## 蹇€熷畨瑁呮鏌?
### Windows鐢ㄦ埛
```bash
# 鍙屽嚮杩愯
install_check.bat
```

### Linux/Mac鐢ㄦ埛
```bash
# 缁欒剼鏈墽琛屾潈闄?chmod +x install_check.sh

# 杩愯妫€鏌ヨ剼鏈?./install_check.sh
```

### 閫氱敤Python鑴氭湰
```bash
python install_check.py
```

## 璇︾粏瀹夎姝ラ

### 1. 瀹夎Python 3.8+

#### Windows
1. 璁块棶 [Python瀹樼綉](https://www.python.org/downloads/)
2. 下载Python 3.8+版本
3. 杩愯瀹夎绋嬪簭锛?*纭繚鍕鹃€?Add Python to PATH"**
4. 楠岃瘉瀹夎锛?   ```bash
   python --version
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### macOS
```bash
# 浣跨敤Homebrew
brew install python3

# 鎴栦粠瀹樼綉涓嬭浇瀹夎鍖?```

### 2. 瀹夎Node.js 16+

#### Windows
1. 璁块棶 [Node.js瀹樼綉](https://nodejs.org/)
2. 下载LTS版本
3. 运行安装程序
4. 楠岃瘉瀹夎锛?   ```bash
   node --version
   npm --version
   ```

#### Linux (Ubuntu/Debian)
```bash
# 浣跨敤NodeSource浠撳簱
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### macOS
```bash
# 浣跨敤Homebrew
brew install node

# 鎴栦娇鐢╪vm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### 3. 瀹夎MySQL 8.0+

#### Windows
1. 璁块棶 [MySQL瀹樼綉](https://dev.mysql.com/downloads/mysql/)
2. 下载MySQL 8.0+版本
3. 运行安装程序，设置root密码
4. 鍚姩MySQL鏈嶅姟

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

#### macOS
```bash
# 浣跨敤Homebrew
brew install mysql
brew services start mysql
```

### 4. 瀹夎Redis 6.0+

#### Windows
1. 涓嬭浇 [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
2. 瑙ｅ帇鍒版寚瀹氱洰褰?3. 杩愯 `redis-server.exe`

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### macOS
```bash
# 浣跨敤Homebrew
brew install redis
brew services start redis
```

### 5. 閰嶇疆铏氭嫙鐜

#### 鏂规硶涓€锛氬鍒剁幇鏈夎櫄鎷熺幆澧冿紙鎺ㄨ崘锛?```bash
# 灏?venv鏂囦欢澶瑰鍒跺埌椤圭洰鏍圭洰褰?# 婵€娲昏櫄鎷熺幆澧?
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 鏂规硶浜岋細鍒涘缓鏂扮殑铏氭嫙鐜
```bash
# 鍒涘缓铏氭嫙鐜
python -m venv .venv

# 婵€娲昏櫄鎷熺幆澧?# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 瀹夎Python渚濊禆
pip install -r requirements.txt
```

### 6. 瀹夎鍓嶇渚濊禆

```bash
# 杩涘叆鍓嶇鐩綍
cd frontend

# 瀹夎npm鍖?npm install

# 杩斿洖鏍圭洰褰?cd ..
```

### 7. 閰嶇疆鐜鍙橀噺

鍒涘缓 `.env` 鏂囦欢锛堝鏋滀笉瀛樺湪锛夛細

```bash
# 鏁版嵁搴撻厤缃?MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=cmg_db

# Redis閰嶇疆
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Django閰嶇疆
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### 8. 鏁版嵁搴撳垵濮嬪寲

```bash
# 鍒涘缓鏁版嵁搴擄紙濡傛灉涓嶅瓨鍦級
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS cmg_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 杩愯鏁版嵁搴撹縼绉?python manage.py migrate

# 鍒涘缓瓒呯骇鐢ㄦ埛锛堝彲閫夛級
python manage.py createsuperuser
```

### 9. 鍚姩绯荤粺

#### 寮€鍙戞ā寮?```bash
# 鍚姩Django鍚庣
python manage.py runserver

# 新终端窗口启动前端开发服务器
cd frontend
npm run dev
```

#### 鐢熶骇妯″紡
```bash
# 鏋勫缓鍓嶇
cd frontend
npm run build

# 鏀堕泦闈欐€佹枃浠?python manage.py collectstatic

# 鍚姩鐢熶骇鏈嶅姟鍣?python manage.py runserver 0.0.0.0:8000
```

## 楠岃瘉瀹夎

1. 璁块棶 http://localhost:8000 鏌ョ湅鍚庣API
2. 璁块棶 http://localhost:3000 鏌ョ湅鍓嶇鐣岄潰
3. 妫€鏌ョ郴缁熺姸鎬侀〉闈㈢‘璁ゆ墍鏈夋湇鍔℃甯歌繍琛?
## 常见问题

### Q: Python鍖呭畨瑁呭け璐?**A**: 纭繚浣跨敤铏氭嫙鐜锛屽苟灏濊瘯鍗囩骇pip锛?```bash
pip install --upgrade pip
```

### Q: MySQL杩炴帴澶辫触
**A**: 妫€鏌ySQL鏈嶅姟鏄惁鍚姩锛岀‘璁ょ敤鎴峰悕瀵嗙爜姝ｇ‘锛?```bash
# Windows
net start mysql

# Linux
sudo systemctl status mysql
```

### Q: Redis杩炴帴澶辫触
**A**: 妫€鏌edis鏈嶅姟鏄惁鍚姩锛?```bash
# Windows
redis-server

# Linux
sudo systemctl status redis
```

### Q: 鍓嶇渚濊禆瀹夎澶辫触
**A**: 娓呴櫎npm缂撳瓨骞堕噸鏂板畨瑁咃細
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Q: 绔彛琚崰鐢?**A**: 妫€鏌ョ鍙ｅ崰鐢ㄦ儏鍐靛苟鍏抽棴鍐茬獊鏈嶅姟锛?```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

## 鎶€鏈敮鎸?
濡傛灉閬囧埌瀹夎闂锛岃锛?
1. 杩愯 `install_check.py` 鑴氭湰妫€鏌ョ幆澧?2. 鏌ョ湅閿欒鏃ュ織鍜岀郴缁熻緭鍑?3. 鍙傝€冨父瑙侀棶棰樿В鍐虫柟妗?4. 鑱旂郴鎶€鏈敮鎸佸洟闃?
## 更新日志

- **v1.0.0**: 鍒濆鐗堟湰锛屾敮鎸佸熀鏈殑鍋ュ悍鐩戞祴鍜屾晠闅滆瘖鏂姛鑳?- 鏇村鏇存柊淇℃伅璇锋煡鐪?[CHANGELOG.md](CHANGELOG.md)

---

**娉ㄦ剰**: 鏈郴缁熶粎渚涘唴閮ㄤ娇鐢紝璇峰嬁鍦ㄥ叕缃戠幆澧冮儴缃层€?

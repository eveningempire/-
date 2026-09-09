# PHM 绂荤嚎杩佺Щ鍖?
杩欐槸浠庡師椤圭洰澶嶅埗鍑虹殑鐙珛杩佺Щ鍓湰銆傚師椤圭洰鐩綍涓嶄細琚湰鍖呯殑鑴氭湰淇敼銆?
## 鍦ㄦ柊鐢佃剳涓婂畨瑁?
1. 灏嗘暣涓?`cmg_migration_package` 鐩綍澶嶅埗鍒版柊鐢佃剳銆?2. 瀹夎 Python 3.10锛堝繀椤讳笌绂荤嚎 wheel 鐨勭増鏈尮閰嶏級銆丯ode.js 18+锛堝彧闇€瀹夎杩愯鏃讹紝涓嶉渶瑕佽仈缃戯級銆?3. 纭 `offline/python` 宸插寘鍚?Python wheel锛岀劧鍚庤繍琛?`setup_migration.ps1`銆?4. 鍙屽嚮 `start_migration.bat`锛岃闂?`http://localhost:5173`銆?
棣栨鍒濆鍖栦細鍦ㄥ寘鏍圭洰褰曞垱寤?`db.sqlite3` 骞舵墽琛?Django migrations銆備互鍚庤縼绉绘暟鎹彧闇€澶嶅埗杩欎釜鏂囦欢锛屽悓鏃跺鍒?`media` 鐩綍涓殑涓婁紶鏂囦欢銆?
## 鏋勫缓绂荤嚎渚濊禆

鍦ㄤ竴鍙板彲鑱旂綉銆佷笖 Python 鐗堟湰涓庣洰鏍囨満涓€鑷寸殑鐢佃剳涓婅繍琛岋細

```powershell
.\build_offline_bundle.ps1
```

鑴氭湰灏嗘墍鏈?Python 渚濊禆涓嬭浇鍒?`offline/python`銆傚墠绔緷璧栭殢鍖呮彁渚涚殑 `frontend/node_modules` 宸插鍒讹紱鑻ラ渶閲嶈锛屼娇鐢?`npm ci --offline`锛屽墠鎻愭槸鐩爣鏈?npm 缂撳瓨涓凡鏈夐攣鏂囦欢瀵瑰簲鐨勫寘銆?
## 閰嶇疆

榛樿浣跨敤 SQLite銆傚彲澶嶅埗 `.env.example` 涓?`.env` 浣滀负閰嶇疆鍙傝€冦€傝嫢蹇呴』杩炴帴 MySQL锛岃缃?`USE_SQLITE=false` 骞舵彁渚?`MYSQL_*` 鐜鍙橀噺銆?
Redis 浠嶇敤浜庣紦瀛樸€乀CP瀹炴椂鎺ュ叆鍜?WebSocket锛涘寘鍐呮彁渚?Windows Redis锛屽彲鐢卞惎鍔ㄨ剼鏈嚜鍔ㄥ惎鍔ㄣ€?

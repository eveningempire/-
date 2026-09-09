# 鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁熷悗鍙?
鏈粨搴撴彁渚涗簡涓€涓熀浜?Django 鐨勫悗鍙板疄鐜帮紝鐢ㄤ簬鏀拺鍩轰簬妯″瀷鐨勫鍛介娴嬬郴缁熴€傚悗绔垝鍒嗕负涓変釜鏍稿績妯″潡锛氭暟鎹鐞嗐€佸仴搴风鐞嗗拰鐢ㄦ埛绠＄悊銆傚叾涓紝鏁版嵁绠＄悊鐢ㄤ簬鎺ユ敹鏉ヨ嚜 TCP 娴佹垨鑰呮枃浠剁殑閬ユ祴鏁版嵁骞朵繚瀛樺埌 MySQL 鏁版嵁搴擄紱鍋ュ悍绠＄悊璐熻矗璋冪敤绠楁硶妯″潡杩涜寮傚父妫€娴嬨€佽鍒欏垽鍒€佹晠闅滆瘖鏂€佸仴搴疯瘎浼板拰瀵垮懡棰勬祴锛涚敤鎴风鐞嗘彁渚涘瑙掕壊鐨勮处鎴蜂綋绯诲拰绠€鍗曠殑娉ㄥ唽銆佺櫥褰曟帴鍙ｃ€?
## 鐩綍缁撴瀯

```
phm_backend/
鈹溾攢鈹€ manage.py               # Django 绠＄悊鑴氭湰
鈹溾攢鈹€ phm_backend/            # 椤圭洰閰嶇疆
鈹?  鈹溾攢鈹€ settings.py         # 椤圭洰閰嶇疆锛堟暟鎹簱銆佸簲鐢ㄣ€丷EST 璁剧疆锛?鈹?  鈹溾攢鈹€ urls.py             # 璺敱閰嶇疆
鈹?  鈹溾攢鈹€ wsgi.py / asgi.py    # 閮ㄧ讲鍏ュ彛
鈹溾攢鈹€ data_management/        # 鏁版嵁绠＄悊搴旂敤
鈹?  鈹溾攢鈹€ models.py           # PHM銆佹暟鎹鍏ヤ細璇濆拰璁板綍妯″瀷
鈹?  鈹溾攢鈹€ views.py            # PHM CRUD銆佹暟鎹鍏ャ€佸疄鏃舵暟鎹帴鍙?鈹?  鈹溾攢鈹€ serializers.py      # 搴忓垪鍖栫被
鈹?  鈹斺攢鈹€ urls.py            # 璺敱閰嶇疆
鈹溾攢鈹€ health_management/      # 鍋ュ悍绠＄悊搴旂敤
鈹?  鈹溾攢鈹€ models.py           # 寮傚父妫€娴嬨€佽鍒欍€佽瘖鏂€佸仴搴疯瘎浼版ā鍨?鈹?  鈹溾攢鈹€ algorithms/         # 绠楁硶瀛樻牴鐩綍
鈹?  鈹?  鈹溾攢鈹€ ims.py          # IMS 寮傚父妫€娴嬪瓨鏍?鈹?  鈹?  鈹溾攢鈹€ rules.py        # 瑙勫垯鍒ゅ埆瀛樻牴
鈹?  鈹?  鈹溾攢鈹€ multi_signal.py # 澶氫俊鍙锋祦鍥捐瘖鏂瓨鏍?鈹?  鈹?  鈹斺攢鈹€ health.py       # 鍋ュ悍铻嶅悎涓庡鍛介娴嬪瓨鏍?鈹?  鈹溾攢鈹€ services.py         # 璋冪敤绠楁硶骞朵繚瀛樼粨鏋滅殑鏈嶅姟灞?鈹?  鈹溾攢鈹€ views.py            # 瑙勫垯銆佽瘖鏂浘绛夋帴鍙?鈹?  鈹斺攢鈹€ urls.py            # 璺敱閰嶇疆
鈹溾攢鈹€ users/                  # 鐢ㄦ埛绠＄悊搴旂敤
鈹?  鈹溾攢鈹€ models.py           # 鑷畾涔夌敤鎴锋ā鍨?鈹?  鈹溾攢鈹€ serializers.py      # 鐢ㄦ埛搴忓垪鍖栫被
鈹?  鈹溾攢鈹€ views.py            # 鐢ㄦ埛鎺ュ彛
鈹?  鈹斺攢鈹€ urls.py            # 璺敱閰嶇疆
鈹斺攢鈹€ requirements.txt        # 渚濊禆鍒楄〃
```

## 浣跨敤璇存槑

1. **鍑嗗鐜**锛氱‘淇濆畨瑁呬簡 Python 3.10+锛屽苟瀹夎渚濊禆锛?
```bash
pip install -r requirements.txt
```

2. **鏁版嵁搴撻厤缃?*锛氶」鐩粯璁や娇鐢?MySQL锛屾暟鎹簱鍚嶇О銆佺敤鎴峰悕銆佸瘑鐮佺瓑鍙湪 `phm_backend/settings.py` 涓€氳繃鐜鍙橀噺瑕嗙洊锛?
```bash
export MYSQL_DATABASE=cmg_db
export MYSQL_USER=cmg_user
export MYSQL_PASSWORD=secret
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
```

3. **鍒濆鍖栨暟鎹簱**锛?
```bash
python manage.py migrate
```

4. **鍒涘缓绠＄悊鍛樿处鎴?*锛?
```bash
python manage.py createsuperuser
```

5. **杩愯寮€鍙戞湇鍔″櫒**锛?
```bash
python manage.py runserver
```

璁块棶 [http://localhost:8000/admin/](http://localhost:8000/admin/) 鍙互浣跨敤 Django 鍚庡彴绠＄悊鏁版嵁搴撹〃锛涙墍鏈?REST API 浣嶄簬 `/api/v1/` 涓嬶紝渚嬪锛?
- `POST /api/v1/data/imports/` 涓婁紶鏂囦欢瀵煎叆鏁版嵁
- `GET /api/v1/data/records/?cmg_id=cmg1&start=2023-01-01T00:00:00&end=2023-01-02T00:00:00` 鏌ヨ鎸囧畾鏃堕棿娈电殑鏁版嵁
- `POST /api/v1/data/records/real-time/` 瀹炴椂鎺ㄩ€佹暟鎹?- `POST /api/v1/health/rules/` 鍒涘缓瑙勫垯
- `POST /api/v1/health/diagnosis-graphs/` 鍒涘缓澶氫俊鍙锋祦鍥?- `POST /api/v1/health/evaluations/recompute/` 閲嶆柊璁＄畻鎸囧畾 PHM 鐨勫仴搴峰垎鏁?
## 绠楁硶鎺ュ彛

绠楁硶鍥㈤槦宸茬粡瀹屾垚 IMS 绠楁硶銆佸淇″彿娴佸浘绛夊疄鐜帮紝鏈」鐩湪 `health_management/algorithms/` 涓嬫彁渚涗簡瀛樻牴瀹炵幇锛屼緵鍓嶅悗绔仈璋冧娇鐢ㄣ€備笂绾挎椂璇风敤鐪熷疄绠楁硶浠ｇ爜鏇挎崲杩欎簺瀛樻牴銆傛湇鍔″眰鍦?`health_management/services.py` 涓礋璐ｈ皟鐢ㄧ畻娉曞苟瀛樺偍缁撴灉銆?
## 鏉冮檺涓庤璇?
鏈」鐩娇鐢?Django 鐨?Session 璁よ瘉鍜屽熀鏈璇併€傛敞鍐屾帴鍙ｅ厑璁稿尶鍚嶈闂紱鍏朵粬鎺ュ彛榛樿瑕佹眰鐧诲綍銆傚彲鏍规嵁闇€瑕佸湪 `REST_FRAMEWORK` 閰嶇疆鍜屽悇瑙嗗浘涓婅皟鏁存潈闄愮瓥鐣ャ€

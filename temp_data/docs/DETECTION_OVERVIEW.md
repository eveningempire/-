## PHM 妫€娴嬫祦绋嬩笌鍒嗘暟璇存槑锛堢郴缁熸€昏锛?

鏈鏄庢枃妗ｆ杩版暣濂椻€滈仴娴嬫暟鎹?鈫?寮傚父妫€娴嬶紙IMS锛夆啋 瑙勫垯妫€娴?鈫?澶氫俊鍙锋祦鍥撅紙MSFG锛夊垎鏋愨€濈殑绔埌绔祦绋嬶紝浠ュ強鍓嶅悗绔暟鎹帴鍙ｃ€佸悇绫诲垎鏁扮殑鏉ユ簮涓庢剰涔夈€佸墠绔睍绀虹瓥鐣ヤ笌鍒よ寤鸿銆?

### 1. 鏁版嵁娴佹€昏

- 鏁版嵁鏉ユ簮涓庡叆搴擄紙data_management锛?
  - 鏂囦欢瀵煎叆锛氶€氳繃瀵煎叆浼氳瘽 `ImportSession` 灏嗗巻鍙叉暟鎹啓鍏?`PHMData`锛堟敮鎸?CSV/Excel/NDJSON锛夈€?
  - 瀹炴椂鎺ュ叆锛歍CP 鏈嶅姟鎺ュ叆鍚庣敱寮傛澶勭悊鍐欏叆 `PHMData`锛屽悓鏃跺啓鍏ュ唴瀛樼紦瀛?Redis 瀹炴椂缂撳瓨銆?
  - 缂撳瓨锛?
    - 鍐呭瓨缂撳瓨 `realtime_cache` 鐢ㄤ簬蹇€熸椂搴忓閲忥紱
    - Redis 缂撳瓨 `redis_service` 鐢ㄤ簬璺ㄨ繘绋嬪叡浜€乄ebSocket 鎺ㄩ€侀€氱煡銆?
  - 鍚庡彴璺緞锛堜妇渚嬶級锛歚data_management/views.py::PHMDataViewSet`銆乣get_realtime_data`銆乣redis_service`銆乣realtime_cache`銆?

- 鍓嶇鏁版嵁鑾峰彇锛坒rontend锛?
  - 鍘嗗彶鏁版嵁锛歚GET /api/v1/data/data/`锛堝彲鎼哄甫 `cmg_id銆乻tart銆乪nd銆乻ince銆乴imit`锛夈€?
  - 瀹炴椂鏁版嵁锛歚GET /api/v1/data/data/realtime/`锛坄cmg_id銆乻ince_ms銆乴imit`锛夛紱涔熷彲缁?WebSocket 澧為噺鎺ユ敹銆?
  - IMS 缁撴灉锛歚GET /api/v1/health/ims-results/anomaly-data/`锛坄cmg_id銆乻tart_time銆乪nd_time銆乴imit銆乤nomaly_only`锛夈€?
  - 瑙勫垯缁撴灉锛歚GET /api/v1/rules/results/`锛坄cmg_id銆乻tart_time銆乪nd_time銆乴imit`锛夈€?
  - MSFG 缁撴灉锛歚GET /api/v1/msfg/results/`锛坄cmg_id銆乻tart_time銆乪nd_time銆乴imit銆乷rdering`锛夈€?

### 2. 妫€娴嬩笌鍒嗘瀽妯″潡

#### 2.1 IMS 寮傚父妫€娴嬶紙health_management锛?
- 瑙﹀彂锛?
  - 鍘嗗彶瀵煎叆瀹屾垚鍚庯紙绂荤嚎澶勭悊锛夛紝鎴栧疄鏃舵暟鎹埌杈撅紙鍦ㄧ嚎澶勭悊锛夈€?
  - 鍙傝€冿細`health_management/services.py`銆乣ims_service.get_anomaly_data_with_ims`銆乣IMSDetectionResultViewSet`銆?
- 涓昏杈撳嚭锛?
  - `anomaly_score`锛?~1锛夛細寮傚父绋嬪害鍒嗘暟锛堣秺澶ц秺寮傚父锛夈€?
  - `parameter_scores`锛氬悇鍙傛暟鐨勫紓甯稿垎瀛楀吀锛岀敤浜庡畾浣嶈础鐚渶澶х殑鍙傛暟銆?
  - `is_anomaly`锛氭槸鍚﹀垽瀹氫负寮傚父銆?
- 鍓嶇鍛堢幇锛?
  - 鏃堕棿杞存寜 `timestamp` 鎺掑垪锛屾樉绀?`anomaly_score` 涓庢渶鍙枒鍙傛暟锛坄parameter_scores` 鏈€澶ч」锛夈€?

#### 2.2 瑙勫垯妫€娴嬶紙rule_detection锛?
- 瑙﹀彂锛氬悓 IMS锛堢绾垮鍏ャ€佸疄鏃舵祦鍧囧彲锛夈€?
- 涓昏杈撳嚭锛坄RuleDetectionResult`锛夛細
  - `is_triggered`锛氭槸鍚﹁Е鍙戣鍒欍€?
  - `confidence_score`锛?~1锛夛細瑙﹀彂缃俊搴︼紙瓒婂ぇ瓒婂彲淇★級銆?
  - `detection_details.component_health_score`锛?~1锛夛細缁勪欢鍋ュ悍搴︼紙1 = 鍋ュ悍锛? = 瀹屽叏寮傚父锛夈€?
  - 鍏宠仈锛歚rule_definition`锛堣鍒?ID銆佽〃杈惧紡锛夈€乣fault_definition`锛堟晠闅滃悕绉般€侀儴浠躲€佺瓑绾э級銆?
- 鍓嶇鍛堢幇锛?
  - 鎸夊悓涓€鏃堕棿鎴宠仛鍚堟垚鈥滆鍒欏抚鈥濓紝骞舵寜鏄惁鏈夊紓甯歌鍒欐爣璁扳€滃紓甯稿抚/姝ｅ父甯р€濄€?
  - 甯у唴鎸夎鍒欏垪琛ㄥ睍绀哄叧閿俊鎭紝骞惰绠椻€滄寜閮ㄤ欢鑱氬悎鍚庣殑鍋ュ悍搴︾粺璁♀€濄€?

#### 2.3 澶氫俊鍙锋祦鍥?MSFG 鍒嗘瀽锛坢sfg_analysis锛?
- 杈撳叆锛氭祴璇曠偣鍒嗘暟銆佽鍒欑粨鏋滅瓑锛涚粨鍚?MSFG 鎷撴墤杩涜铻嶅悎锛坄algorithms/msfg/fusion.py`锛夈€?
- 涓昏杈撳嚭缁撴瀯锛坄MSFGAnalysisResult`锛?
  - `test_results`锛氭祴璇曠偣 鈫?鍒嗘暟锛?~1锛夈€?
  - `fault_results`锛氭晠闅?鈫?鍒嗘暟锛?~1锛夈€?
  - `system_results`锛堢郴缁熸瑙堬級锛?
    - `overall_health`锛氱郴缁熷仴搴峰害锛?~1锛?=鍋ュ悍锛?=寮傚父锛涚患鍚堟渶涓ラ噸鏁呴殰涓庢晠闅滄暟閲忥級銆?
    - `fault_count`锛氳Е鍙戠殑鏁呴殰鏁伴噺锛堟寜闃堝€肩粺璁★級銆?
    - `critical_faults`锛氬叧閿晠闅滃垪琛紙鍒嗘暟 > 闃堝€硷級銆?
    - `worst_fault_score`锛氬崟涓渶涓ラ噸鐨勬晠闅滃垎鏁般€?
    - `average_fault_score`锛氬叏閮ㄦ晠闅滃垎鏁扮殑骞冲潎鍊硷紙鈥滅患鍚堟晠闅滃垎锛堝钩鍧囷級鈥濓級銆?
  - `component_results`锛堥儴浠舵瑙堬級锛?
    - `health_score`锛氶儴浠跺仴搴峰害锛?~1锛?=鍋ュ悍銆佽秺浣庨闄╄秺楂橈級銆?
    - `active_fault_count`锛氳閮ㄤ欢娑夊強鐨勬椿璺冩晠闅滄暟閲忋€?
    - `max_fault_score` / `avg_fault_score`锛氳閮ㄤ欢娑夊強鏁呴殰鐨勬渶澶?骞冲潎鍒嗘暟銆?
    - `active_faults`锛氳閮ㄤ欢娑夊強鐨勫叧閿晠闅滃垪琛ㄣ€?
  - `overall_health_score`锛氬嚭浜庡悜鍚庡吋瀹逛繚鐣欑殑绯荤粺鍋ュ悍鍒嗗瓧娈碉紙涓?`overall_health` 瀵瑰簲锛夈€?
- 璁＄畻瑕佺偣锛?
  - `summarize_system()` 涓鍋ュ悍搴︾患鍚堣€冭檻鈥滄渶涓ラ噸鏁呴殰锛坵orst锛夆€濅笌鈥滄晠闅滄暟閲忥紙quantity锛夆€濄€?
  - 閮ㄤ欢鍋ュ悍搴︼細浼樺厛浣跨敤鈥滄祴璇曠偣-閮ㄤ欢鏄犲皠鈥濈殑鍔犳潈绛栫暐锛涜嫢涓嶅彲鐢紝鍥為€€鍒扳€滄晠闅?閮ㄤ欢鍏崇郴鈥濈殑鎺ㄦ柇绛栫暐銆?

### 3. 分数的来源与意义（判读指南）

- IMS 妯″潡
  - `anomaly_score`锛?~1锛岃秺澶ц秺寮傚父锛涘彲缁撳悎 `parameter_scores` 瀹氫綅褰卞搷鏈€澶у弬鏁般€?
  - 寤鸿闃堝€硷細0.5 闄勮繎浣滀负棰勮绾匡紝>0.8 浣滀负鏄捐憲寮傚父锛堝彲鎸夊疄闄呮暟鎹啀璋冧紭锛夈€?

- 瑙勫垯妫€娴嬫ā鍧?
  - `confidence_score`锛?~1锛岃秺澶ц秺鍙俊锛涗富瑕佺敤浜庢帓搴忎笌楂樹寒寮傚父瑙勫垯銆?
  - `component_health_score`锛?~1锛?=鍋ュ悍锛?=寮傚父锛涘彲鐢ㄤ簬閮ㄤ欢绾у仴搴锋眹鎬伙紙鍙栧悓涓€閮ㄤ欢鐨勬渶灏忓€煎仛淇濆畧浼拌锛夈€?

- MSFG 妯″潡
  - `average_fault_score`锛堢郴缁燂級锛氣€滅患鍚堟晠闅滃垎锛堝钩鍧囷級鈥濓紝0~1锛岃秺澶ч棶棰樿秺涓ラ噸銆傚墠绔湪缁撴灉鍒楄〃涓娇鐢ㄦ鍊肩敤浜庢椂闂磋酱鍜屾€昏澶ц〃鏍笺€?
  - `worst_fault_score`锛堢郴缁燂級锛氭渶涓ラ噸鏁呴殰寮哄害锛屼究浜庡揩閫熻瘑鍒€滄渶鍧忕偣鈥濄€?
  - `overall_health` / `overall_health_score`锛堢郴缁熷仴搴峰垎锛夛細0~1锛岃秺澶ц秺鍋ュ悍銆傚畠涓庘€滅患鍚堟晠闅滃垎鈥濆憟璐熺浉鍏筹紝浣嗗寘鍚暟閲忔晥搴斾笌绛栫暐鏉冮噸锛岄€傚悎鍋氭暣浣撴€佸娍璇勪及銆?
  - `component_results.health_score`锛堥儴浠跺仴搴峰垎锛夛細0~1锛岃秺浣庨闄╄秺楂橈紱鐢ㄤ簬鈥滄晠闅?TOP3锛堥儴浠讹級鈥濈殑鎺掑簭锛堥€夋嫨鍋ュ悍搴︽渶浣庣殑鍓嶄笁涓儴浠讹級銆?

### 4. 鍓嶇灞曠ず绛栫暐锛堝叧閿〉闈級

- PHM 璇︽儏锛坄CmgDetail.vue`锛?
  - 閬ユ祴瓒嬪娍锛氭寜閫変腑鍙傛暟缁樺浘锛沋 杞村彲缂╂斁锛涙敮鎸佸疄鏃?鍘嗗彶妯″紡锛涘姣斿垎鏋愬脊绐楁敮鎸佸 PHM 鎴栧鍙傛暟瀵规瘮銆?
  - IMS 鏃堕棿杞达細灞曠ず `anomaly_score` 涓庣枒浼煎弬鏁般€?
  - 瑙勫垯鏃堕棿杞达細鎸夆€滆鍒欏抚鈥濆睍绀哄紓甯?姝ｅ父锛屽抚鍐呯粰鍑鸿鍒欐槑缁嗕笌鈥滄寜閮ㄤ欢鑱氬悎鐨勫仴搴峰害鈥濄€?
  - MSFG 鏃堕棿杞达細鎸?`created_at` 灞曠ず姣忔潯缁撴灉锛屾樉绀衡€滃钩鍧囨晠闅滃垎鈥濓紙鏁板€艰秺澶ц秺鍗遍櫓锛変笌鈥滄渶鍙兘鐨勪竴涓晠闅滈儴浠垛€濄€?

- 澶氫俊鍙锋祦鍥剧粨鏋滈〉锛坄MSFGResults.vue`锛?
  - 澶ц〃鏍煎垪锛?
    - 鏃堕棿銆丆MG銆侀厤缃紱
    - 骞冲潎鏁呴殰鍒嗭紙鏉ヨ嚜 `system_results.average_fault_score`锛夛紱
    - 鏁呴殰 TOP3锛堥儴浠讹級锛氫粠 `component_results` 涓€夊仴搴峰害鏈€浣庣殑 3 涓儴浠讹紱
    - 鎿嶄綔锛堣鎯咃級銆?
  - 璇︽儏鎶藉眽锛?
    - 绯荤粺姒傝锛堟晠闅滄暟銆佹渶涓ラ噸鏁呴殰鍒嗐€佸钩鍧囨晠闅滃垎銆佸叧閿晠闅滃垪琛級锛?
    - 娴嬭瘯鐐瑰垎鏁般€佹晠闅滃垎鏁帮紱
    - 閮ㄤ欢鍋ュ悍鍒嗘瀽璇︽儏锛堜繚鐣欌€滃仴搴峰垎鏁般€佹椿璺冩晠闅滄暟鈥濈瓑鏍稿績椤癸紱宸茬Щ闄ゆ剰涔変笉寮烘垨绌哄垪锛夈€?

### 5. 瀹炴椂/鍘嗗彶涓庢€ц兘瑕佺偣

- 瀹炴椂妯″紡锛?
  - 首次进入实时时，从当前时间起始接收增量（`since_ms`）；
  - WebSocket 鍙帹閫佹渶鏂版暟鎹紱鑻ヤ笉鍙敤鍒欓檷绾т负杞锛?
  - 鍓嶇浼氶檺鍒跺唴瀛樹腑鐨勭偣鏁板苟鍘婚噸鍚堝苟锛岄伩鍏嶅ぇ鏁版嵁瀵艰嚧鍗￠】銆?

- 鍘嗗彶妯″紡锛?
  - 渚濇嵁 `start銆乪nd` 涓ユ牸绛涢€夛紱
  - 褰撲笉鎸囧畾鏃堕棿鑼冨洿鏃讹紝鍚庣榛樿杩斿洖鏈€杩?`N` 鏉★紙姝ｅ簭锛夛紱
  - 鍓嶇閽堝涓嶅悓 API 鍏煎鏁扮粍涓庡垎椤佃繑鍥炵粨鏋勶紙`results`锛夈€?

### 6. 甯歌闂涓庢帓鏌ュ缓璁?

- “健康分全是 0”的原因与处理：
  - 鏃╂湡椤甸潰浣跨敤浜嗕笉鍚堥€傜殑瀛楁鎴栨暟鎹┖缂猴紱鐩墠宸茬粺涓€灞曠ず `average_fault_score` 浣滀负鎬昏鍒嗭紝鏁板€肩ǔ瀹氫笖鏄撲簬瑙ｉ噴銆?
  - 鑻ヤ粛涓?0锛屾鏌ヨ鏃堕棿娈垫槸鍚﹀瓨鍦ㄦ湁鏁堟晠闅滃垎銆佹垨娲昏穬鏁呴殰闃堝€兼槸鍚﹁繃楂樸€?

- 缁勪欢鍗歌浇鏃舵姤閿欙紙vnode/DOM 涓虹┖锛夛細
  - 鐜板凡鍔犲叆 `isActive` 瀹堝崼涓庤姹傚彇娑堬紙AbortController锛夛紝骞朵粎鍦ㄥ脊绐楁墦寮€涓?DOM 灏辩华鏃跺垵濮嬪寲鍥捐〃锛岄棶棰樺凡瑙ｅ喅銆?

### 7. 接口与字段对照表（简表）

- `/api/v1/data/data/` 鈫?鍘嗗彶閬ユ祴锛坄timestamp, data{...}`锛夈€?
- `/api/v1/data/data/realtime/` 鈫?瀹炴椂閬ユ祴锛堝閲忥級銆?
- `/api/v1/health/ims-results/anomaly-data/` 鈫?IMS锛坄timestamp, anomaly_score, parameter_scores...`锛夈€?
- `/api/v1/rules/results/` 鈫?瑙勫垯缁撴灉锛坄is_triggered, confidence_score, detection_details.component_health_score...`锛夈€?
- `/api/v1/msfg/results/` 鈫?MSFG 缁撴灉锛坄test_results, fault_results, system_results(overall_health, average_fault_score...) , component_results(...)`锛夈€?

### 8. 术语说明

- 寮傚父鍒嗭紙Anomaly Score锛夛細寮傚父寮哄害锛岃秺澶ц秺寮傚父銆?
- 缃俊搴︼紙Confidence Score锛夛細瑙勫垯瑙﹀彂鍙俊搴︼紝瓒婂ぇ瓒婂彲淇°€?
- 绯荤粺鍋ュ悍鍒嗭紙Overall Health锛夛細鏁翠綋鍋ュ悍搴︼紝瓒婂ぇ瓒婂仴搴凤紱涓庢晠闅滃垎杩戜技璐熺浉鍏炽€?
- 缁煎悎鏁呴殰鍒嗭紙骞冲潎锛夛紙Average Fault Score锛夛細鎵€鏈夋晠闅滃垎鐨勫钩鍧囧€硷紝瓒婂ぇ璇存槑鏁翠綋鈥滄晠闅滃己搴︹€濇洿楂樸€?
- 鏈€涓ラ噸鏁呴殰鍒嗭紙Worst Fault Score锛夛細鍗曚釜鏁呴殰鐨勫嘲鍊煎垎鏁帮紝鍒╀簬瀹氫綅鈥滄渶鍧忕偣鈥濄€?
- 閮ㄤ欢鍋ュ悍搴︼紙Component Health Score锛夛細瓒婁綆瓒婂嵄闄╋紝鐢ㄤ簬纭畾鈥滄晠闅?TOP3锛堥儴浠讹級鈥濄€?

---

濡傞渶杩涗竴姝ュ畾鍒讹紙渚嬪璋冩暣寮傚父/鏁呴殰闃堝€笺€佷慨鏀?TOP3 鎺掑簭閫昏緫銆佸紩鍏ユ柊鐨勫仴搴峰害鑱氬悎绛栫暐锛夛紝璇峰湪姝ゆ枃妗ｅ熀纭€涓婅ˉ鍏呬綘鐨勪笟鍔＄害鏉熶笌闃堝€艰瀹氾紝鎴戜滑鍙互灏嗗叾鍥哄寲涓洪厤缃」骞跺湪鍓嶅悗绔粺涓€浣跨敤銆?




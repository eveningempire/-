# PHM Platform 2024

#### 浠嬬粛
鍒濆鐗堟湰鏄?0241205楠屾敹鐗堟湰

#### 杞欢鏋舵瀯
软件架构说明

## 鐜瀹夎

### MATLAB Engine for Python

浠跨湡鍔熻兘闇€瑕佸畨瑁匨ATLAB Engine for Python锛岃鎸変互涓嬫楠ゆ搷浣滐細

1. 首先确保您已安装MATLAB，并且Python版本与MATLAB兼容
2. 浣跨敤鍔╂墜鑴氭湰鑷姩瀹夎:
   ```
   python matlab_setup.py
   ```
3. 如果自动安装失败，请手动安装:
   ```
   cd "<MATLAB瀹夎鐩綍>\extern\engines\python"
   python setup.py install
   ```
4. 测试安装是否成功:
   ```python
   import matlab.engine
   eng = matlab.engine.start_matlab()
   ```

### 鍏跺畠渚濊禆

```
pip install -r requirements.txt
```

## 鍚姩鏈嶅姟

```
python manage.py
```

#### 瀹夎鏁欑▼

1.  xxxx
2.  xxxx
3.  xxxx

## 使用说明

1. 璁块棶 http://localhost:8005/ 杩涘叆绯荤粺
2. 浠跨湡鍔熻兘浣嶄簬 http://localhost:8005/sim-model

#### 鍙備笌璐＄尞

1.  Fork 鏈粨搴?2.  鏂板缓 Feat_xxx 鍒嗘敮
3.  鎻愪氦浠ｇ爜
4.  鏂板缓 Pull Request


#### 鐗规妧

1.  浣跨敤 Readme\_XXX.md 鏉ユ敮鎸佷笉鍚岀殑璇█锛屼緥濡?Readme\_en.md, Readme\_zh.md
2.  Gitee 瀹樻柟鍗氬 [blog.gitee.com](https://blog.gitee.com)
3.  浣犲彲浠?[https://gitee.com/explore](https://gitee.com/explore) 杩欎釜鍦板潃鏉ヤ簡瑙?Gitee 涓婄殑浼樼寮€婧愰」鐩?4.  [GVP](https://gitee.com/gvp) 鍏ㄧО鏄?Gitee 鏈€鏈変环鍊煎紑婧愰」鐩紝鏄患鍚堣瘎瀹氬嚭鐨勪紭绉€寮€婧愰」鐩?5.  Gitee 瀹樻柟鎻愪緵鐨勪娇鐢ㄦ墜鍐?[https://gitee.com/help](https://gitee.com/help)
6.  Gitee 灏侀潰浜虹墿鏄竴妗ｇ敤鏉ュ睍绀?Gitee 浼氬憳椋庨噰鐨勬爮鐩?[https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)


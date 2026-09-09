1. 在year1.py中get_predict_result函数里添加了读取隐参数mu, nu并返回的逻辑（只提供了这一组隐参数，Bm和Kt没有）

2. table10.py的get_limited_sensing_res函数(调用了上面这个函数)的返回数据结构中新增了一个键"hps"，从get_limited_sensing_res返回结果中对应地取数就行：
```python
def get_limited_sensing_res(group: int = 1):
    ...
    
    res_limited_sensing = {
        ...,
        "hps": {  # 只提供mu和nu这一组隐参数
            "mu": mu,
            "nu": nu,
        },
    }

    return json_serialize_with_ndarray(res_limited_sensing)
```
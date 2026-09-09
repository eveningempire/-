import numpy as np
from typing import Iterable

_eps = 0.001
_alias = {
        "+": "_plus", 
        "-": "_minus", 
        "*": "_mul", 
        "/": "_div", 
        "//": "_intdiv", 
        "%": "_mod", 
        "**": "_pow", 
        "&": "_bitand", 
        "|": "_bitor", 
        "^": "_bitxor", 
        "~": "_bitnot", 
        "int": "_int", 
        "log": "_log", 
        "exp": "_exp", 
        "abs": "_abs",
        "sin": "_sin",
        "cos": "_cos",
        "tan": "_tan",
        "asin": "_asin",
        "acos": "_acos",
        "atan": "_atan",
        "atan2": "_atan2"
    }

class FuncBase:
    @staticmethod
    def Mean(a, n=1):
        n = int(n)
        res = np.zeros([n, *a.shape], dtype="float32")
        ref = np.zeros([n, *a.shape], dtype="float32")
        for i in range(n):
            res[i, i:] = a[:-i] if i != 0 else a[:]
            ref[i, i:] = np.where(~np.isnan(a[:-i] if i != 0 else a[:]), 1, 0)
        res = np.mean(res, axis=0)
        ref = np.mean(ref, axis=0)
        if np.any(ref == 0):
            res[ref == 0] = float("nan")
        if np.any(ref != 0):
            res[ref != 0] /= ref[ref != 0]
        return res
    
    @staticmethod
    def Max(a, n=1):
        n = int(n)
        res = np.array(a, dtype="float32")
        for i in range(n-1):
            res[i:] = np.maximum(
                np.where(~np.isnan(a[:-i] if i != 0 else a[:]), a[:-i] if i != 0 else a[:], -float("inf")), 
                np.where(~np.isnan(a[i:] if i != 0 else a[:]), a[i:] if i != 0 else a[:], -float("inf")))
        return np.where(~np.isinf(res), res, float("nan"))
    
    @staticmethod
    def Min(a, n=1):
        n = int(n)
        res = np.array(a, dtype="float32")
        for i in range(n-1):
            res[i:] = np.minimum(
                np.where(~np.isnan(a[:-i] if i != 0 else a[:]), a[:-i] if i != 0 else a[:], -float("inf")), 
                np.where(~np.isnan(a[i:] if i != 0 else a[:]), a[i:] if i != 0 else a[:], -float("inf")))
        return np.where(~np.isinf(res), res, float("nan"))

    @staticmethod
    def _plus(*args):
        result = args[0]
        for arg in args[1:]:
            result += arg
        return result

    @staticmethod
    def _minus(*args):
        result = args[0]
        for arg in args[1:]:
            result -= arg
        return result

    @staticmethod
    def _mul(*args):
        result = args[0]
        for arg in args[1:]:
            result *= arg
        return result

    @staticmethod
    def _inner_div(a,b):
        if isinstance(b, float) or isinstance(b, int):
            if b == 0 or np.isnan(b):
                if isinstance(a, float) or isinstance(a, int):
                    return np.nan
                else:
                    return np.nan*np.ones(a.shape)
            else:
                return a/b
        else:
            result = np.nan*np.ones(b.shape)
            if isinstance(a, float) or isinstance(a, int):
                result[(b!=0)&(~np.isnan(b))] = a/b[(b!=0)&(~np.isnan(b))]
            else:
                result[(b!=0)&(~np.isnan(b))] = a[(b!=0)&(~np.isnan(b))]/b[(b!=0)&(~np.isnan(b))]
            return result

    @staticmethod
    def _div(*args):
        result = args[0]
        for arg in args[1:]:
            result = FuncBase._inner_div(result, arg)
        return result

    @staticmethod
    def _intdiv(a,b):
        if isinstance(b, float) or isinstance(b, int):
            if b == 0 or np.isnan(b):
                if isinstance(a, float) or isinstance(a, int):
                    return np.nan
                else:
                    return np.nan*np.ones(a.shape)
            else:
                return a//b
        else:
            result = np.nan*np.ones(b.shape)
            if isinstance(a, float) or isinstance(a, int):
                result[(b!=0)&(~np.isnan(b))] = a//b[(b!=0)&(~np.isnan(b))]
            else:
                result[(b!=0)&(~np.isnan(b))] = a[(b!=0)&(~np.isnan(b))]//b[(b!=0)&(~np.isnan(b))]
            return result

    @staticmethod
    def _mod(a,b):
        if isinstance(b, float) or isinstance(b, int):
            if b == 0 or np.isnan(b):
                if isinstance(a, float) or isinstance(a, int):
                    return np.nan
                else:
                    return np.nan*np.ones(a.shape)
            else:
                return a%b
        else:
            result = np.nan*np.ones(b.shape)
            if isinstance(a, float) or isinstance(a, int):
                result[(b!=0)&(~np.isnan(b))] = a%b[(b!=0)&(~np.isnan(b))]
            else:
                result[(b!=0)&(~np.isnan(b))] = a[(b!=0)&(~np.isnan(b))]%b[(b!=0)&(~np.isnan(b))]
            return result

    @staticmethod
    def _pow(a,b):
        return a**b

    @staticmethod
    def _bitand(a,b):
        if isinstance(b, float) or isinstance(b, int):
            if np.isnan(b) or np.isinf(b):
                if isinstance(a, float) or isinstance(a, int):
                    return np.nan
                else:
                    return np.nan*np.ones(a.shape)
            else:
                if isinstance(a, float) or isinstance(a, int):
                    if np.isnan(a) or np.isinf(a):
                        return np.nan
                    else:
                        return int(a)&int(b)
                else:
                    result = np.nan*np.ones(a.shape)
                    result[(~np.isnan(a))&(~np.isinf(a))] = a[(~np.isnan(a))&(~np.isinf(a))]&int(b)
                    return result
        else:
            result = np.nan*np.ones(b.shape)
            if isinstance(a, float) or isinstance(a, int):
                if (not np.isnan(a)) and (not np.isinf(a)):
                    result[(~np.isnan(b))&(~np.isinf(b))] = int(a)&b[(~np.isnan(b))&(~np.isinf(b))].astype(np.int)
            else:
                noNanIndex = (~np.isnan(a*b))&(~np.isinf(a*b))
                result[noNanIndex] = a[noNanIndex].astype(np.int)&b[noNanIndex].astype(np.int)
            return result

    @staticmethod
    def _bitor(a,b):
        if isinstance(b, float) or isinstance(b, int):
            if np.isnan(b) or np.isinf(b):
                if isinstance(a, float) or isinstance(a, int):
                    return np.nan
                else:
                    return np.nan*np.ones(a.shape)
            else:
                if isinstance(a, float) or isinstance(a, int):
                    if np.isnan(a) or np.isinf(a):
                        return np.nan
                    else:
                        return int(a)|int(b)
                else:
                    result = np.nan*np.ones(a.shape)
                    result[(~np.isnan(a))&(~np.isinf(a))] = a[(~np.isnan(a))&(~np.isinf(a))]|int(b)
                    return result
        else:
            result = np.nan*np.ones(b.shape)
            if isinstance(a, float) or isinstance(a, int):
                if (not np.isnan(a)) and (not np.isinf(a)):
                    result[(~np.isnan(b))&(~np.isinf(b))] = int(a)|b[(~np.isnan(b))&(~np.isinf(b))].astype(np.int)
            else:
                noNanIndex = (~np.isnan(a*b))&(~np.isinf(a*b))
                result[noNanIndex] = a[noNanIndex].astype(np.int)|b[noNanIndex].astype(np.int)
            return result

    @staticmethod
    def _bitxor(a,b):
        if isinstance(b, float) or isinstance(b, int):
            if np.isnan(b) or np.isinf(b):
                if isinstance(a, float) or isinstance(a, int):
                    return np.nan
                else:
                    return np.nan*np.ones(a.shape)
            else:
                if isinstance(a, float) or isinstance(a, int):
                    if np.isnan(a) or np.isinf(a):
                        return np.nan
                    else:
                        return int(a)^int(b)
                else:
                    result = np.nan*np.ones(a.shape)
                    result[(~np.isnan(a))&(~np.isinf(a))] = a[(~np.isnan(a))&(~np.isinf(a))]^int(b)
                    return result
        else:
            result = np.nan*np.ones(b.shape)
            if isinstance(a, float) or isinstance(a, int):
                if (not np.isnan(a)) and (not np.isinf(a)):
                    result[(~np.isnan(b))&(~np.isinf(b))] = int(a)^b[(~np.isnan(b))&(~np.isinf(b))].astype(np.int)
            else:
                noNanIndex = (~np.isnan(a*b))&(~np.isinf(a*b))
                result[noNanIndex] = a[noNanIndex].astype(np.int)^b[noNanIndex].astype(np.int)
            return result

    @staticmethod
    def _bitnot(a):
        if isinstance(a, float) or isinstance(a, int):
            if np.isnan(a) or np.isinf(a):
                return np.nan
            else:
                return ~int(a)
        else:
            result = np.nan*np.ones(a.shape)
            result[(~np.isnan(a))&(~np.isinf(a))] = ~a[(~np.isnan(a))&(~np.isinf(a))].astype(np.int)
            return result
                
    @staticmethod
    def _log(a):
        if isinstance(a, float) or isinstance(a, int):
            if a<= 0:
                return np.nan
            else:
                return np.log(a)
        else:
            result = np.nan*np.ones(a.shape)
            result[a>0] = np.log(a[a>0])
            return result

    @staticmethod
    def _exp(a):
        return np.exp(a)

    @staticmethod
    def _sin(a):
        return np.sin(a)
    
    @staticmethod
    def _cos(a):
        return np.cos(a)

    @staticmethod
    def _tan(a):
        return np.tan(a)

    @staticmethod
    def _asin(a):
        if isinstance(a, float) or isinstance(a, int):
            if -1 <= a<= 1:
                return np.arcsin(a)
            else:
                return np.nan
        else:
            result = np.nan*np.ones(a.shape)
            result[(a>=-1)&(a<=1)] = np.arcsin(a[(a>=-1)&(a<=1)])
            return result

    @staticmethod
    def _acos(a):
        if isinstance(a, float) or isinstance(a, int):
            if -1 <= a<= 1:
                return np.arccos(a)
            else:
                return np.nan
        else:
            result = np.nan*np.ones(a.shape)
            result[(a>=-1)&(a<=1)] = np.arccos(a[(a>=-1)&(a<=1)])
            return result

    @staticmethod
    def _atan(a):
        return np.arctan(a)
    
    @staticmethod
    def _atan2(a,b):
        return np.arctan2(a,b)

    @staticmethod
    def _abs(a):
        return np.abs(a)
    
    
def _inner_getResult(data, args):
    if isinstance(args, list):
        if len(args) == 1:
            return _getResult(data, args[0])
        data = np.array(data, dtype="float32")
        funcname_ = _alias.get(args[0]) or args[0]
        if funcname_ in dir(FuncBase):
            func_ = getattr(FuncBase, funcname_)
        elif funcname_ in dir(np):
            func_ = getattr(np, funcname_)
        elif funcname_ in dir(np.linalg):
            func_ = getattr(np.linalg, funcname_)
        elif funcname_[0] == "P":
            try:
                v = data[..., int(funcname_[1:])]
                res = np.ones(v.shape)*float("nan")
                res[:-abs(int(args[1])), ...] = v[abs(int(args[1])):, ...]
                return res
            except Exception as e:
                print("[Error]:", e)
                raise Exception(f"Uncomprehensive method {funcname_}")
                
        return func_(*(_getResult(data, arg) for arg in args[1:]))
    elif isinstance(args, str):
        return data[..., int(args[1:])]
    else:
        return args

def _getResult(data, args):
    res_inner = _inner_getResult(data, args)
    if isinstance(res_inner, Iterable) and not isinstance(res_inner, str):
        res = np.ones([len(data)]+list(np.shape(res_inner))[1:], dtype="float32")*float("nan")
        res[-len(res_inner):, ...] = res_inner
    else:
        res = res_inner
    return res


def _evalPureopExpress(data, args):
    if args:
        return _getResult(data, args).astype("float32")
    else:
        return np.nan*np.ones(data.shape[0])

def evalOp(data, opExpress_args):
    opExpress = _evalPureopExpress(data, opExpress_args)
    return list(map(float, opExpress))

def list2opExpress(opExpress, inner=False):
    if isinstance(opExpress, list):
        if inner:
            return f"({opExpress[0].join([list2opExpress(preC, inner=True) for prePos, preC in enumerate(opExpress[1:])])})"
        else:
            return opExpress[0].join([list2opExpress(preC, inner=True) for prePos, preC in enumerate(opExpress[1:])])
    else:
        return str(opExpress)

if __name__ == "__main__":
    res = _getResult(np.random.uniform(0,1,[55,5]), ["round", "P1",2])
    print(res)

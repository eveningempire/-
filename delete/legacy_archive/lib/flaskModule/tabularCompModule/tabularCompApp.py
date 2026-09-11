import json
import pandas as pd
from io import BytesIO
from flask import request, jsonify, send_file

def check_data_file(data, colConfig=None):
    return True, [{"warn":0, "error": 0, "info": []} for itm in data]

def get_key_from_dict(d, value):
    for k, v in d.items():
        if v == value:
            return k
    return value

class tabularEngine:
    def __init__(self, dir_url="ate-tabular-comp"):
        self._dir_url = dir_url
        self._check_func = check_data_file

    def configCheck(self, func):
        if callable(func):
            self._check_func = func

    @property
    def upload_data_file(self):
        def _inner_upload():
            dataInfo = []
            colConfig = json.loads(request.form.get("colConfig"))
            dataFile = pd.read_excel(request.files.get("tableDataFile"), header=0).T.fillna("").to_dict().values()
            for dataId, dataItem in enumerate(dataFile):
                dataLine = {}
                for colItem in colConfig:
                    inputType = colItem.get("inputType", "input")
                    if inputType == "switch":
                        switchMap = [colItem.get("falseLabel", "不勾选"), colItem.get("trueLabel", "勾选")]
                        val = dataItem.get(colItem["name"], switchMap[1 if colItem.get("default", False) else 0])
                        dataLine[colItem["key"]] = (val==switchMap[1])
                    elif inputType == "input-number":
                        vstr = str(dataItem.get(colItem["name"], colItem.get("default", "")).replace(" ",""))
                        vstr = vstr[1:] if vstr[:1] in ["+", "-"] else vstr
                        if vstr.split(".") == 1:
                            dataLine[colItem["key"]] = int(vstr)
                        elif vstr.split(".") == 2 and vstr.replace(".","").isnumeric():
                            dataLine[colItem["key"]] = float(vstr)
                        else:
                            dataLine[colItem["key"]] = ""
                    elif inputType == "input":
                        dataLine[colItem["key"]] = dataItem.get(colItem["name"], colItem.get("default", ""))
                    elif inputType == "select":
                        if isinstance(colItem["options"], dict):
                            colOptionsDict = {v: k for v, k in colItem["options"].items()}
                        else:
                            colOptionsDict = {v: v for v in colItem["options"]}
                        if colItem.get("multiple", False):
                            dataLine[colItem["key"]] = [colOptionsDict.get(itm, itm) \
                                                        for itm in dataItem.get(colItem["name"], ";".join(colItem.get("default", []))).split(";")]
                        else:
                            itm = dataItem.get(colItem["name"], colItem.get("default", ""))
                            dataLine[colItem["key"]] = get_key_from_dict(colOptionsDict, itm)
                dataInfo.append(dataLine)
            checkPass, dataInfoLog = self._check_func(dataInfo, colConfig)[:2]
            return jsonify({"checkPass":checkPass, "data": [{
                "_tabular_comp_private_log": dataInfo[itmId],
                **itm,
                **{
                    "editable": dataInfo[itmId].get("error")!=0,
                    }
                } for itmId, itm in enumerate(dataInfo)]})
        _inner_upload.__name__ = f"{self._dir_url}_inner_upload".replace("/","_").replace(".", "")
        return _inner_upload

    @property
    def check_data_file(self):
        def _inner_check():
            tableData = json.loads(request.form.get("tableData"))
            colConfig = json.loads(request.form.get("colConfig"))
            result = self._check_func(tableData, colConfig)
            checkPass, dataInfo = result[:2]
            if len(result) == 3:
                dataAll = result[2]
            else:
                dataAll = None
            if dataAll is None:
                return jsonify({"checkPass":checkPass, "data": [{**itm, **{"_tabular_comp_private_log": dataInfo[itmId], "editable": dataInfo[itmId].get("error")!=0}} for itmId, itm in enumerate(dataInfo)]})
            else:
                return jsonify({"checkPass":checkPass, "data": [{**dataAllItm, **{"_tabular_comp_private_log": dataInfoItm}} for dataInfoItm, dataAllItm in zip(dataInfo, dataAll)]})

        _inner_check.__name__ = f"{self._dir_url}_inner_check".replace("/","_").replace(".", "")
        return _inner_check

    @property
    def download_data_file(self):
        def _inner_download():
            filename = request.form.get("filename")
            if filename and str(filename).lower() not in ["undefined", "null"]:
                if not str(filename).endswith(".xlsx"):
                    filename = str(filename).replace(".", "_") + ".xlsx"
            else:
                filename = "表格数据.xlsx"
            colConfig = json.loads(request.form.get("colConfig"))
            dataInfoItems = []
            for dataId, dataInfo in enumerate(json.loads(request.form.get("tableData", "[]"))):
                dataLine = {}
                for colItem in colConfig:
                    inputType = colItem.get("inputType", "input")
                    if inputType == "switch":
                        val = dataInfo.get(colItem["key"], colItem.get("default", False))
                        dataLine[colItem["name"]] = colItem.get("trueLabel", "勾选") if val else colItem.get("falseLabel", "不勾选")
                    elif inputType == "input-number":
                        dataLine[colItem["name"]] = dataInfo.get(colItem["key"], colItem.get("default", "")).replace(" ","")
                    elif inputType == "input":
                        dataLine[colItem["name"]] = dataInfo.get(colItem["key"], colItem.get("default", ""))
                    elif inputType == "select":
                        if colItem.get("multiple", False):
                            dataLine[colItem["name"]] = ";".join([str(colItem["options"].get(itm, itm)) for itm in dataInfo.get(colItem["key"], colItem.get("default", []))])
                        else:
                            itm = dataInfo.get(colItem["key"], colItem.get("default", ""))
                            dataLine[colItem["name"]] = colItem["options"].get(itm, itm)
                dataInfoItems.append(dataLine)
            dataInfo = pd.DataFrame(dataInfoItems).fillna("")
            io_out = BytesIO()
            writer = pd.ExcelWriter(io_out, engine="xlsxwriter")
            dataInfo.to_excel(writer, sheet_name=filename, index=False)
            writer.close()
            io_out.seek(0)
            return send_file(io_out, as_attachment=True, download_name=filename)
        _inner_download.__name__ = f"{self._dir_url}_inner_download".replace("/","_").replace(".", "")
        return _inner_download


    def tabular_app(self, app):
        app.route(f"/{self._dir_url}/import-data-file-default",methods=['POST'])(self.upload_data_file)
        app.route(f"/{self._dir_url}/export-data-file-default",methods=['POST'])(self.download_data_file)
        app.route(f"/{self._dir_url}/check-all-data-default",methods=['POST'])(self.check_data_file)

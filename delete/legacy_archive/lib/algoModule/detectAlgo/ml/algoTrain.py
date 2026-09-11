from multiprocessing import Process, Queue
from pprint import pprint
from threading import Thread

import os, time, uuid
import pandas as pd

from .algoChoose import Model as mlModel

def simpleTrain(model_name, model_uuid, model_algo, relatParas, dataFile, res_queque,
                model_rl=False, model_comp="unknown"):
    model = mlModel(index=model_uuid, name=model_name, algoname=model_algo, component=model_comp,pnames=relatParas)
    if model_rl:
        try:
            model.load_model(model_uuid)
        except Exception as e:
            model.trained = False 
    data = []
    if isinstance(dataFile, str):
        dataFile = [dataFile]
    for dataFile_ in dataFile:
        data_ = pd.read_csv(dataFile_, index_col=0, header=0, encoding="gbk").fillna(method="ffill", limit=5).dropna(how="any", axis=0)
        try:
            data_ = data_.loc[:, relatParas].values.astype("float32")
        except:
            continue
        data.append(data_)
    if len(data) != 0:
        model.fit(data, model_rl=model_rl, save=True)
    res_queque.put([model_uuid, model.algoname])

class taskTrainWorker:
    def __init__(self, worker_num=5, obj="Unknown", time_resample=0.005):
        self.obj = obj
        self.time_resample = time_resample
        self.worker_num = worker_num

    def create_process(self, model_name, model_uuid, model_algo, model_relatPara,
                       model_file, res_queque, model_rl=False, model_comp="@"):
        return Process(target=simpleTrain, args=(model_name, model_uuid, model_algo, model_relatPara,
                                                 model_file, res_queque, model_rl, model_comp))
                
    def main_process(self, toDoList, paranames):
        workers_on = 0
        Workers = [None for _ in range(self.worker_num)]
        dataFile = set()

        result_queue = Queue()
        result = {}
            
        try:
            while len(toDoList)!= 0 or workers_on != 0:
                if not toDoList:
                    time.sleep(1)
                for w in range(self.worker_num):
                    if Workers[w] is None:
                        if toDoList:
                            model_name, model_uuid, model_algo, model_relatPara, model_file, model_rl, model_comp = toDoList.pop(0)
                            model_relatPara = [paranames[pid] for pid in model_relatPara]
                            dataFile.add(model_file)
                            Workers[w] = self.create_process(model_name, model_uuid, model_algo,
                                                             model_relatPara, model_file, result_queue, model_rl, model_comp)
                            if Workers[w]:
                                print(f">>> {w}-START: {model_name}@{model_algo}({model_relatPara})")
                                Workers[w].start()
                                workers_on += 1

                    elif not Workers[w].is_alive():
                        print(f">>> {w}-END")
                        if toDoList:
                            model_name, model_uuid, model_relatPara, model_file, model_rl, model_comp  = toDoList.pop(0)
                            model_relatPara = [paranames[pid] for pid in model_relatPara]
                            dataFile.add(model_file)
                            Workers[w] = self.create_process(model_name, model_uuid, model_algo,
                                                             model_relatPara, model_file, result_queue, model_rl, model_comp)
                            if Workers[w]:
                                print(f">>> {w}-START: {model_name}@{model_algo}({model_relatPara})")
                                Workers[w].start()
                                workers_on -= 1

                        else:
                            Workers[w].join()
                            print(f">>> {w}-END")
                            Workers[w] = None
                            workers_on -= 1

                while not result_queue.empty():
                    uuid_, res = result_queue.get_nowait()
                    result[uuid_] = res

                time.sleep(0.1)

        except Exception as e:
            print(e)
            print("Error")
        finally:
            while not result_queue.empty():
                uuid_, res = result_queue.get_nowait()
                result[uuid_] = res
            result_queue.close()

        for dataFilePath in dataFile:
            try:
                os.remove(dataFilePath)
            except:
                print(f"[WARN] Fail to delete the roaming file: {dataFilePath}")
                
        return result

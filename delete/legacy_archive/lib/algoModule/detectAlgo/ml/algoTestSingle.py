from multiprocessing import Process, Queue
from threading import Thread

import os, time, uuid
import pandas as pd

from .algoChoose import Model as mlModel

def simpleTest(model_name, model_uuid, model_algo, relatParas, dataFile, res_queque, obj="unknown", nlimit=20):
    data = pd.read_csv(dataFile, index_col=0, header=0, encoding="gbk").fillna(method="ffill", limit=nlimit).dropna(how="any", axis=0)
    data = data.loc[:, relatParas].values.astype("float32")
    #time_ = data.index.values
    model = mlModel(index=model_uuid, name=model_name, algoname=model_algo, pnames=relatParas)
    try:
        model.load_model(model_uuid)
    except Exception as e:
        model.trained = False
    _, scores, supp = model.validate(data)
    ruleCriterion = model.rule_induce(data)
    result = {"scores": scores, "suppValues": supp[0], "suppLabel": supp[1], "ruleCriterion": ruleCriterion}
    res_queque.put([model_uuid, result])
    return 
    
class taskTestWorker:
    def __init__(self, worker_num=5, obj="Unknown", time_resample=0.005):
        self.obj = obj
        self.time_resample = time_resample
        self.worker_num = worker_num

    def create_process(self, model_name, model_uuid, model_algo, model_relatPara, model_file, queue):
        return Process(target=simpleTest, args=(model_name, model_uuid, model_algo, model_relatPara, model_file, queue))
                
    def valid_rule(self, toDoList, paranames):
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
                            model_name, model_uuid, model_algo, model_relatPara, model_file = toDoList.pop(0)
                            model_relatPara = [paranames[pid] for pid in model_relatPara]
                            dataFile.add(model_file)
                            Workers[w] = self.create_process(model_name, model_uuid, model_algo, model_relatPara, model_file, result_queue)
                            if Workers[w]:
                                print(f">>> {w}-START: {model_name}@{model_algo}({model_relatPara})")
                                Workers[w].start()
                                workers_on += 1

                    elif not Workers[w].is_alive():
                        print(f">>> {w}-END")
                        if toDoList:
                            model_name, model_uuid, model_algo, model_relatPara, model_file  = toDoList.pop(0)
                            model_relatPara = [paranames[pid] for pid in model_relatPara]
                            dataFile.add(model_file)
                            Workers[w] = self.create_process(model_name, model_uuid, model_algo, model_relatPara, model_file, result_queue)
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
            print("[Error]",e)
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

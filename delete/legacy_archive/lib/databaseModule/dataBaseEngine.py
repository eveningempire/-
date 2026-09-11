import os
import pandas as pd

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, text, Column, INTEGER, TEXT, TIMESTAMP, BLOB, DECIMAL
from sqlalchemy.orm import sessionmaker

import sys
DATABASE = "ate_phm_db_2024"
if __name__ == "__main__":
    DATAPATH = os.path.join(r"..", r"..", "static", "database", f"{DATABASE}.db")
else:
    DATAPATH = os.path.join(r".", "static", "database", f"{DATABASE}.db")
BaseClass = declarative_base()

try:
    print(f"[INFO] Try to connect database on \'sqlite:///{DATAPATH}\'")
    ENGINE = create_engine(f'sqlite:///{DATAPATH}')
    print(f"[INFO] Seemingly succeed to connecting database on \'sqlite:///{DATAPATH}\'")
except Exception as e:
    raise Exception("[Error] Please go to \"platform\" or \"platform.\\lib\" to run this file!")
Session = sessionmaker(bind=ENGINE)

class dataInfoBase(BaseClass):
    __tablename__ = "datainfobase"
    data_name = Column(TEXT(50), nullable=False)
    data_descript =  Column(TEXT(50), nullable=True)
    source =    Column(TEXT(50), nullable=True)
    data_uuid = Column(TEXT(50), primary_key=True)
     
class dataBase(BaseClass):
    __tablename__ = "database"
    data_uuid = Column(TEXT(50), primary_key=True)
    data = Column(BLOB, nullable=False)

    


class msfgBase(BaseClass):
    __tablename__ = "msfgbase"

    msfg_id = Column(INTEGER, primary_key=True, autoincrement=True)
    obj = Column(TEXT(50), nullable=False)
    msfg_raw_params = Column(BLOB, autoincrement=True)
    msfg_params = Column(BLOB, autoincrement=True)
    creator_uuid = Column(TEXT(50), nullable=True)
    editor_uuid = Column(TEXT(250), nullable=True)
    create_time = Column(TIMESTAMP(True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

class ruleBase(BaseClass):
    __tablename__ = "rulebase"

    rule_id = Column(INTEGER, primary_key=True, autoincrement=True)
    obj = Column(TEXT(50), nullable=False)
    create_time = Column(TIMESTAMP(True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    rule_express = Column(TEXT(50), nullable=False)
    fault_name_uuid = Column(TEXT(300), nullable=False)
    plan_descript = Column(TEXT(50), nullable=False)
    creator_uuid = Column(TEXT(50), nullable=True)
    editor_uuid = Column(TEXT(250), nullable=True)
    online_state = Column(INTEGER, nullable=False)


if __name__ == "__main__":
    import argparse, uuid, time
    parser = argparse.ArgumentParser(description="[数据库操作]")
    parser.add_argument("-ib", "--incre-build", type=str, default=False, help="若.db文件或内部表格缺失，请置为True")
    parser.add_argument("-rb", "--re-build", type=str, default=False, help="若需要删除重建.db文件，请置为True")
    parser.add_argument("-u", "--usrname", type=str, default=False, help="新增用户名")
    parser.add_argument("-p", "--password", type=str, default=False, help="新增用户密码")
    parser.add_argument("-ad", "--admin", type=str, default="user", help="新增用户权限")
    args = parser.parse_args()
    
    def get_uuid(kw=""):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kw}#%.7f"%time.time()))
    
    if args.incre_build and args.incre_build[:1].lower() != "f":
        session = Session()
        BaseClass.metadata.create_all(ENGINE)
        session.commit()
        print(f"[INFO] 数据库补录成功")
        session.close()
    
    elif args.re_build and args.re_build[:1].lower() != "f":
        if os.path.exists(DATAPATH):
            os.remove(DATAPATH)
        session = Session()
        BaseClass.metadata.create_all(ENGINE)
        session.commit()
        print(f"[INFO] 数据库重构成功")
        session.close()


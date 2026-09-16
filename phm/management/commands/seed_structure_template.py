from django.core.management.base import BaseCommand
from django.db import transaction

from phm.models import StructureNode


TEMPLATE = [
    ("vehicle", "RLV", "重复使用运载器", "vehicle", None),
    ("sys-propulsion", "RLV-01", "推进分系统", "system", "vehicle"),
    ("sub-engine", "RLV-01-01", "发动机子系统", "subsystem", "sys-propulsion"),
    ("prod-lox-pump", "RLV-01-01-01", "液氧泵", "product", "sub-engine"),
    ("prod-oxygen-turbine", "RLV-01-01-02", "氧涡轮", "product", "sub-engine"),
    ("prod-kerosene-pipeline", "RLV-01-01-03", "煤油管路", "product", "sub-engine"),
    ("prod-kerosene-valve", "RLV-01-01-04", "煤油阀门", "product", "sub-engine"),
    ("prod-gas-generator", "RLV-01-01-05", "燃气发生器", "product", "sub-engine"),
    ("prod-combustion-chamber", "RLV-01-01-06", "燃烧室", "product", "sub-engine"),
    ("prod-nozzle", "RLV-01-01-07", "喷管", "product", "sub-engine"),
    ("sub-propellant", "RLV-01-02", "推进剂供应子系统", "subsystem", "sys-propulsion"),
    ("prod-lox-tank", "RLV-01-02-01", "液氧贮箱", "product", "sub-propellant"),
    ("prod-fuel-tank", "RLV-01-02-02", "燃料贮箱", "product", "sub-propellant"),
    ("sys-guidance", "RLV-02", "制导导航与控制分系统", "system", "vehicle"),
    ("sub-guidance", "RLV-02-01", "制导导航子系统", "subsystem", "sys-guidance"),
    ("prod-imu", "RLV-02-01-01", "惯性测量组合", "product", "sub-guidance"),
    ("prod-computer", "RLV-02-01-02", "飞行控制计算机", "product", "sub-guidance"),
    ("sub-attitude", "RLV-02-02", "姿态控制子系统", "subsystem", "sys-guidance"),
    ("prod-actuator", "RLV-02-02-01", "伺服执行机构", "product", "sub-attitude"),
    ("sys-power", "RLV-03", "电源分系统", "system", "vehicle"),
    ("sub-power-supply", "RLV-03-01", "供配电子系统", "subsystem", "sys-power"),
    ("prod-battery", "RLV-03-01-01", "蓄电池组", "product", "sub-power-supply"),
    ("prod-pdu", "RLV-03-01-02", "配电单元", "product", "sub-power-supply"),
    ("sys-measurement", "RLV-04", "测控分系统", "system", "vehicle"),
    ("sub-telemetry", "RLV-04-01", "遥测子系统", "subsystem", "sys-measurement"),
    ("prod-telemetry-unit", "RLV-04-01-01", "遥测采编单元", "product", "sub-telemetry"),
    ("sys-thermal", "RLV-05", "热控分系统", "system", "vehicle"),
    ("sub-active-thermal", "RLV-05-01", "主动热控子系统", "subsystem", "sys-thermal"),
    ("prod-thermal-controller", "RLV-05-01-01", "热控控制器", "product", "sub-active-thermal"),
    ("sys-data", "RLV-06", "数据管理分系统", "system", "vehicle"),
    ("sub-data", "RLV-06-01", "数据处理子系统", "subsystem", "sys-data"),
    ("prod-data-unit", "RLV-06-01-01", "综合数据处理单元", "product", "sub-data"),
]


class Command(BaseCommand):
    help = "Create the editable four-level reusable-launch-vehicle PBS template."

    @transaction.atomic
    def handle(self, *args, **options):
        nodes = {}
        for key, pbs, name, node_type, parent_key in TEMPLATE:
            node, _ = StructureNode.objects.update_or_create(
                node_key=key,
                defaults={"pbs_code": pbs, "name": name, "node_type": node_type,
                          "parent": nodes.get(parent_key), "properties": {"template": True}},
            )
            nodes[key] = node
        self.stdout.write(self.style.SUCCESS(f"结构树模板已就绪：{len(nodes)} 个节点"))

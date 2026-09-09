import { createRouter, createWebHistory } from 'vue-router';
import PhmLayout from '../components/PhmLayout.vue';
import PhmOverview from '../views/PhmOverview.vue';
import CapabilityPlaceholder from '../views/CapabilityPlaceholder.vue';
import FmecaKnowledge from '../views/FmecaKnowledge.vue';
import ComponentLibrary from '../views/ComponentLibrary.vue';
import IntegrationAssets from '../views/IntegrationAssets.vue';
import SimulationDataset from '../views/SimulationDataset.vue';

const page = (path, title, description, features) => ({ path, component: CapabilityPlaceholder, meta: { title, description, features } });

const routes = [{ path: '/', component: PhmLayout, children: [
  { path: '', name: 'Overview', component: PhmOverview },
  page('telemetry','遥测数据监测','接入飞行与地面试验遥测，展示参数趋势和工况。',['实时/历史遥测查询','参数阈值与趋势监视','数据刷新延迟监控']),
  page('alarms','异常告警管理','汇总异常事件并跟踪确认、处置与闭环。',['分级告警','告警确认与处置','历史告警检索']),
  page('fault-diagnosis','故障诊断分析','承载规则、模型与数据驱动的故障诊断结果。',['至少两类分系统诊断','至少两种诊断方法适配','故障定位与隔离']),
  page('msfg-editor','结构/MSFG模型','维护航天器层级结构和故障传播关系。',['节点增删改','连接关系编辑','MSFG模型导入导出']),
  page('fault-injection','故障注入配置','配置典型故障模式和仿真验证任务。',['分系统故障注入','多故障模式配置','验证任务管理']),
  { path:'fmeca', component:FmecaKnowledge },
  page('fta','FTA故障树','建立顶事件、中间事件与底事件的逻辑关系。',['故障树浏览','逻辑门编辑','最小割集分析接口']),
  page('health-assessment','部件健康指数','展示部件级健康指标及演化趋势。',['多种健康指标算法适配','健康指数HI融合','历史状态对比']),
  page('system-health','系统健康状态','依据系统结构聚合部件健康状态。',['系统级健康评估','分系统健康排名','健康状态追溯']),
  page('lifetime-prediction','剩余寿命预测','展示RUL预测值、置信区间和退化趋势。',['预测任务配置','RUL与不确定性区间','预测结果对比']),
  page('model-management','预测模型管理','统一管理诊断、评估和预测模型版本。',['模型注册与版本','启停和发布','运行记录']),
  page('data-management','数据管理','管理遥测、试验、仿真和分析结果数据。',['预处理与存储','历史数据比对','数据表格导入导出']),
  { path:'vehicle-structure', component:ComponentLibrary },
  page('maintenance-decision','维修辅助决策','根据诊断、健康度与寿命结果形成维修建议。',['维修策略生成','备件与资源约束','决策依据追溯']),
  { path:'integration-assets', component:IntegrationAssets },
  { path:'simulation-dataset', component:SimulationDataset },
  page('users','用户与权限','通过角色控制数据和功能访问权限。',['角色权限','用户管理','访问审计'])
] }];

export default createRouter({ history: createWebHistory(), routes });

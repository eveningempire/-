<template>
  <div class="modeling-overview">
    <SectionCard class="intro-card">
      <template #header>
        <div class="header-with-icon">
          <el-icon class="header-icon"><DataAnalysis /></el-icon>
          <div>
            <h1>CMG寿命预测建模</h1>
            <p class="subtitle">基于多算法融合的剩余使用寿命智能预测技术</p>
          </div>
        </div>
      </template>

      <div class="intro-content">
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            <strong>系统概述</strong>
          </template>
          <p style="margin-top: 8px; line-height: 1.6;">
            本系统采用四种先进的机器学习算法对CMG（控制力矩陀螺）进行剩余寿命预测（RUL - Remaining Useful Life）。
            通过SVD特征提取、深度学习模型推理、健康指数计算和智能平滑处理，实现高精度的寿命预测。
            四种算法各有特点，可根据实际应用场景灵活选择。
          </p>
        </el-alert>

        <!-- 预测流程图 -->
        <div class="pipeline-section">
          <h3>
            <el-icon><TrendCharts /></el-icon>
            完整预测流程
          </h3>
          <div class="image-container">
            <img 
              src="/images/modeling/rul_prediction_pipeline_1766314166495.png" 
              alt="RUL预测流程"
              class="pipeline-image"
            />
          </div>
          <div class="pipeline-steps">
            <el-steps :active="7" finish-status="success" align-center>
              <el-step title="原始数据" description="CMG遥测数据"></el-step>
              <el-step title="数据预处理" description="滑动窗口分割"></el-step>
              <el-step title="特征提取" description="SVD奇异值分解"></el-step>
              <el-step title="模型推理" description="四种算法并行"></el-step>
              <el-step title="健康指数" description="HI计算"></el-step>
              <el-step title="平滑处理" description="EMA+卡尔曼滤波"></el-step>
              <el-step title="RUL预测" description="剩余寿命输出"></el-step>
            </el-steps>
          </div>
        </div>
      </div>
    </SectionCard>

    <!-- 四个算法介绍 -->
    <el-row :gutter="24">
      <!-- Algorithm 1: AutoEncoder -->
      <el-col :xs="24" :sm="12" :lg="12">
        <SectionCard class="algorithm-card">
          <template #header>
            <div class="algorithm-header">
              <el-tag type="primary" size="large" effect="dark">算法 1</el-tag>
              <h2>AutoEncoder 自编码器</h2>
            </div>
          </template>

          <div class="algorithm-content">
            <!-- 架构图 -->
            <div class="architecture-image">
              <img 
                src="/images/modeling/autoencoder_architecture_1766314064078.png" 
                alt="AutoEncoder架构"
              />
            </div>

            <!-- 原理说明 -->
            <div class="principle-section">
              <h4><el-icon><Reading /></el-icon> 算法原理</h4>
              <p class="principle-text">
                自编码器是一种无监督学习的神经网络，通过压缩-重建的方式学习数据的潜在表示。
                正常数据可以很好地重建（误差小），而退化数据重建误差大，表明健康状态下降。
              </p>
            </div>

            <!-- 网络结构 -->
            <div class="structure-section">
              <h4><el-icon><Connection /></el-icon> 网络结构</h4>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="编码器">
                  <el-tag size="small">输入(8维)</el-tag>
                  <el-icon><Right /></el-icon>
                  <el-tag size="small" type="success">隐藏层(32)</el-tag>
                  <el-icon><Right /></el-icon>
                  <el-tag size="small" type="warning">潜在空间(8)</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="解码器">
                  <el-tag size="small" type="warning">潜在空间(8)</el-tag>
                  <el-icon><Right /></el-icon>
                  <el-tag size="small" type="success">隐藏层(32)</el-tag>
                  <el-icon><Right /></el-icon>
                  <el-tag size="small">输出(8维)</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="激活函数">ReLU</el-descriptions-item>
                <el-descriptions-item label="损失函数">MSE (均方误差)</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 优势与应用 -->
            <div class="features-section">
              <h4><el-icon><Star /></el-icon> 核心优势</h4>
              <ul class="feature-list">
                <li><el-icon color="#409EFF"><Check /></el-icon> 平衡性好，易于解释</li>
                <li><el-icon color="#409EFF"><Check /></el-icon> 训练稳定，收敛快速</li>
                <li><el-icon color="#409EFF"><Check /></el-icon> 适合生产环境部署</li>
                <li><el-icon color="#409EFF"><Check /></el-icon> GPU加速支持，推理高效</li>
              </ul>
            </div>

            <!-- 适用场景 -->
            <el-alert type="success" :closable="false" show-icon>
              <template #title><strong>推荐场景</strong></template>
              <p style="margin-top: 4px;">通用场景，适合作为主策略部署在生产环境中</p>
            </el-alert>
          </div>
        </SectionCard>
      </el-col>

      <!-- Algorithm 2: VAE -->
      <el-col :xs="24" :sm="12" :lg="12">
        <SectionCard class="algorithm-card">
          <template #header>
            <div class="algorithm-header">
              <el-tag type="success" size="large" effect="dark">算法 2</el-tag>
              <h2>VAE 变分自编码器</h2>
            </div>
          </template>

          <div class="algorithm-content">
            <!-- 架构图 -->
            <div class="architecture-image">
              <img 
                src="/images/modeling/vae_architecture_1766314085559.png" 
                alt="VAE架构"
              />
            </div>

            <!-- 原理说明 -->
            <div class="principle-section">
              <h4><el-icon><Reading /></el-icon> 算法原理</h4>
              <p class="principle-text">
                VAE是AutoEncoder的概率化改进版本，编码器输出均值μ和方差σ²，通过重参数化技巧采样潜在变量。
                引入KL散度正则化，使潜在空间更规整，对噪声数据具有更好的鲁棒性。
              </p>
            </div>

            <!-- 数学公式 -->
            <div class="formula-section">
              <h4><el-icon><Document /></el-icon> 核心公式</h4>
              <div class="formula-box">
                <div class="formula-item">
                  <span class="formula-label">重参数化:</span>
                  <code>z = μ + σ · ε, ε ~ N(0, 1)</code>
                </div>
                <div class="formula-item">
                  <span class="formula-label">损失函数:</span>
                  <code>Loss = MSE + KL散度</code>
                </div>
                <div class="formula-item">
                  <span class="formula-label">KL散度:</span>
                  <code>-0.5 × Σ(1 + log(σ²) - μ² - σ²)</code>
                </div>
              </div>
            </div>

            <!-- 优势与应用 -->
            <div class="features-section">
              <h4><el-icon><Star /></el-icon> 核心优势</h4>
              <ul class="feature-list">
                <li><el-icon color="#67C23A"><Check /></el-icon> 概率解释性强</li>
                <li><el-icon color="#67C23A"><Check /></el-icon> 潜在空间规整</li>
                <li><el-icon color="#67C23A"><Check /></el-icon> 对噪声鲁棒性好</li>
                <li><el-icon color="#67C23A"><Check /></el-icon> 可生成健康状态样本</li>
              </ul>
            </div>

            <!-- 适用场景 -->
            <el-alert type="success" :closable="false" show-icon>
              <template #title><strong>推荐场景</strong></template>
              <p style="margin-top: 4px;">噪声数据较多的场景，需要概率建模的应用</p>
            </el-alert>
          </div>
        </SectionCard>
      </el-col>

      <!-- Algorithm 3: Isolation Forest -->
      <el-col :xs="24" :sm="12" :lg="12">
        <SectionCard class="algorithm-card">
          <template #header>
            <div class="algorithm-header">
              <el-tag type="warning" size="large" effect="dark">算法 3</el-tag>
              <h2>Isolation Forest 孤立森林</h2>
            </div>
          </template>

          <div class="algorithm-content">
            <!-- 架构图 -->
            <div class="architecture-image">
              <img 
                src="/images/modeling/isolation_forest_concept_1766314107379.png" 
                alt="Isolation Forest概念"
              />
            </div>

            <!-- 原理说明 -->
            <div class="principle-section">
              <h4><el-icon><Reading /></el-icon> 算法原理</h4>
              <p class="principle-text">
                基于集成学习的异常检测算法。核心思想是：异常点更容易被隔离，需要更少的随机切分。
                通过构建多棵隔离树（Isolation Tree），计算样本的平均路径长度作为异常分数。
              </p>
            </div>

            <!-- 算法特点 -->
            <div class="structure-section">
              <h4><el-icon><DataAnalysis /></el-icon> 算法特点</h4>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="训练方式">无监督学习</el-descriptions-item>
                <el-descriptions-item label="树的数量">100棵（默认）</el-descriptions-item>
                <el-descriptions-item label="异常判定">路径长度 < 阈值</el-descriptions-item>
                <el-descriptions-item label="分数归一化">
                  <code>score = (depth - min) / (max - min)</code>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 优势与应用 -->
            <div class="features-section">
              <h4><el-icon><Star /></el-icon> 核心优势</h4>
              <ul class="feature-list">
                <li><el-icon color="#E6A23C"><Check /></el-icon> 无需GPU，计算效率高</li>
                <li><el-icon color="#E6A23C"><Check /></el-icon> 对高维数据敏感</li>
                <li><el-icon color="#E6A23C"><Check /></el-icon> 无需假设数据分布</li>
                <li><el-icon color="#E6A23C"><Check /></el-icon> 适合实时在线预测</li>
              </ul>
            </div>

            <!-- 适用场景 -->
            <el-alert type="warning" :closable="false" show-icon>
              <template #title><strong>推荐场景</strong></template>
              <p style="margin-top: 4px;">实时性要求高、计算资源受限的场景</p>
            </el-alert>
          </div>
        </SectionCard>
      </el-col>

      <!-- Algorithm 4: SOM -->
      <el-col :xs="24" :sm="12" :lg="12">
        <SectionCard class="algorithm-card">
          <template #header>
            <div class="algorithm-header">
              <el-tag type="danger" size="large" effect="dark">算法 4</el-tag>
              <h2>SOM 自组织映射网络</h2>
            </div>
          </template>

          <div class="algorithm-content">
            <!-- 架构图 -->
            <div class="architecture-image">
              <img 
                src="/images/modeling/som_architecture_1766314129819.png" 
                alt="SOM架构"
              />
            </div>

            <!-- 原理说明 -->
            <div class="principle-section">
              <h4><el-icon><Reading /></el-icon> 算法原理</h4>
              <p class="principle-text">
                自组织映射是一种无监督学习的神经网络，将高维数据映射到低维（通常是2D）网格。
                通过竞争学习和邻域更新，保持数据的拓扑结构。使用马氏距离计算样本到神经元的距离，实现异常检测。
              </p>
            </div>

            <!-- 训练过程 -->
            <div class="structure-section">
              <h4><el-icon><Operation /></el-icon> 训练过程</h4>
              <el-timeline>
                <el-timeline-item timestamp="Step 1" placement="top">
                  找到最佳匹配单元（BMU）- 距离输入最近的神经元
                </el-timeline-item>
                <el-timeline-item timestamp="Step 2" placement="top">
                  计算邻域函数：exp(-d²/2σ²)
                </el-timeline-item>
                <el-timeline-item timestamp="Step 3" placement="top">
                  更新BMU及其邻域神经元权重
                </el-timeline-item>
                <el-timeline-item timestamp="Step 4" placement="top">
                  学习率和邻域半径随迭代衰减
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- 异常检测方法 -->
            <div class="formula-section">
              <h4><el-icon><Document /></el-icon> 异常检测</h4>
              <div class="formula-box">
                <div class="formula-item">
                  <span class="formula-label">马氏距离:</span>
                  <code>d = √((x-μ)ᵀ Σ⁻¹ (x-μ))</code>
                </div>
                <div class="formula-item">
                  <span class="formula-label">判定规则:</span>
                  <code>d > d_max → 异常</code>
                </div>
                <div class="formula-item">
                  <span class="formula-label">健康指数:</span>
                  <code>HI = 1 - 异常点比例</code>
                </div>
              </div>
            </div>

            <!-- 优势与应用 -->
            <div class="features-section">
              <h4><el-icon><Star /></el-icon> 核心优势</h4>
              <ul class="feature-list">
                <li><el-icon color="#F56C6C"><Check /></el-icon> 可视化能力强</li>
                <li><el-icon color="#F56C6C"><Check /></el-icon> 发现数据拓扑结构</li>
                <li><el-icon color="#F56C6C"><Check /></el-icon> 聚类+异常检测一体化</li>
                <li><el-icon color="#F56C6C"><Check /></el-icon> 易于解释和分析</li>
              </ul>
            </div>

            <!-- 适用场景 -->
            <el-alert type="error" :closable="false" show-icon>
              <template #title><strong>推荐场景</strong></template>
              <p style="margin-top: 4px;">需要可视化分析退化模式、探索数据结构的场景</p>
            </el-alert>
          </div>
        </SectionCard>
      </el-col>
    </el-row>

    <!-- 辅助算法：维纳过程 -->
    <SectionCard class="auxiliary-card">
      <template #header>
        <div class="header-with-icon">
          <el-icon class="header-icon"><Timer /></el-icon>
          <div>
            <h2>辅助算法：单阶段维纳过程模型</h2>
            <p class="subtitle">用于RUL预测的随机过程模型</p>
          </div>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :xs="24" :md="12">
          <div class="wiener-section">
            <h4><el-icon><Reading /></el-icon> 模型概述</h4>
            <p>
              维纳过程是一种连续时间随机过程，用于建模CMG的退化轨迹。
              通过在线更新漂移系数μ和扩散系数σ，实时跟踪退化趋势。
            </p>

            <div class="formula-section" style="margin-top: 16px;">
              <h4><el-icon><Document /></el-icon> 数学模型</h4>
              <div class="formula-box">
                <div class="formula-item">
                  <span class="formula-label">维纳过程:</span>
                  <code>dX(t) = μ·dt + σ·dW(t)</code>
                </div>
                <div class="formula-item">
                  <span class="formula-label">参数估计:</span>
                  <code>μ = mean(ΔX/Δt), σ = √(var(ΔX)/Δt)</code>
                </div>
                <div class="formula-item">
                  <span class="formula-label">RUL预测:</span>
                  <code>蒙特卡洛模拟至阈值</code>
                </div>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :xs="24" :md="12">
          <div class="wiener-features">
            <h4><el-icon><Star /></el-icon> 关键特性</h4>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="在线更新">
                滑动窗口估计参数（默认100个数据点）
              </el-descriptions-item>
              <el-descriptions-item label="数据补齐">
                数据不足时用健康状态值(1)补齐
              </el-descriptions-item>
              <el-descriptions-item label="预测方法">
                向量化蒙特卡洛模拟（支持GPU加速）
              </el-descriptions-item>
              <el-descriptions-item label="加速选项">
                支持线性增长的漂移系数 μ(t) = μ + α|μ|t
              </el-descriptions-item>
            </el-descriptions>

            <el-alert 
              type="info" 
              :closable="false" 
              show-icon 
              style="margin-top: 16px;"
            >
              <template #title><strong>应用说明</strong></template>
              <p style="margin-top: 4px;">
                维纳过程模型用于计算动态边界阈值，配合健康指数HI进行RUL预测。
                通过加权平均理论退化速度和实际退化速度，得到最终的剩余寿命估计。
              </p>
            </el-alert>
          </div>
        </el-col>
      </el-row>
    </SectionCard>

    <!-- 算法对比表 -->
    <SectionCard class="comparison-card">
      <template #header>
        <div class="header-with-icon">
          <el-icon class="header-icon"><Histogram /></el-icon>
          <h2>算法性能对比</h2>
        </div>
      </template>

      <el-table 
        :data="comparisonData" 
        stripe 
        border
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', fontWeight: 'bold' }"
      >
        <el-table-column prop="metric" label="指标" width="150" fixed />
        <el-table-column label="AutoEncoder" align="center">
          <el-table-column prop="ae_pros" label="优势" />
          <el-table-column prop="ae_score" label="评分" width="80" align="center">
            <template #default="scope">
              <el-rate v-model="scope.row.ae_score" disabled show-score text-color="#ff9900" />
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="VAE" align="center">
          <el-table-column prop="vae_pros" label="优势" />
          <el-table-column prop="vae_score" label="评分" width="80" align="center">
            <template #default="scope">
              <el-rate v-model="scope.row.vae_score" disabled show-score text-color="#ff9900" />
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="Isolation Forest" align="center">
          <el-table-column prop="if_pros" label="优势" />
          <el-table-column prop="if_score" label="评分" width="80" align="center">
            <template #default="scope">
              <el-rate v-model="scope.row.if_score" disabled show-score text-color="#ff9900" />
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="SOM" align="center">
          <el-table-column prop="som_pros" label="优势" />
          <el-table-column prop="som_score" label="评分" width="80" align="center">
            <template #default="scope">
              <el-rate v-model="scope.row.som_score" disabled show-score text-color="#ff9900" />
            </template>
          </el-table-column>
        </el-table-column>
      </el-table>

      <div style="margin-top: 24px;">
        <el-alert type="info" :closable="false" show-icon>
          <template #title><strong>选择建议</strong></template>
          <ul style="margin-top: 8px; line-height: 1.8;">
            <li><strong>AutoEncoder</strong>: 推荐作为主策略，平衡性好，适合生产环境</li>
            <li><strong>VAE</strong>: 噪声环境下首选，概率建模能力强</li>
            <li><strong>Isolation Forest</strong>: 实时性要求高、资源受限场景</li>
            <li><strong>SOM</strong>: 需要可视化分析和模式探索时使用</li>
          </ul>
        </el-alert>
      </div>
    </SectionCard>

    <!-- 技术路线总结 -->
    <SectionCard class="summary-card">
      <template #header>
        <div class="header-with-icon">
          <el-icon class="header-icon"><Memo /></el-icon>
          <h2>技术路线总结</h2>
        </div>
      </template>

      <el-row :gutter="24">
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="summary-item">
            <template #header>
              <div class="summary-header">
                <el-icon color="#409EFF"><Tools /></el-icon>
                <span>特征工程</span>
              </div>
            </template>
            <ul class="summary-list">
              <li>滑动窗口分割（window=64, step自适应）</li>
              <li>SVD奇异值分解提取本质特征</li>
              <li>标准化归一化处理</li>
              <li>低速电流有效值计算（三相合成）</li>
            </ul>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="summary-item">
            <template #header>
              <div class="summary-header">
                <el-icon color="#67C23A"><Cpu /></el-icon>
                <span>模型推理</span>
              </div>
            </template>
            <ul class="summary-list">
              <li>预训练模型加载（pkl格式）</li>
              <li>重建误差/异常分数计算</li>
              <li>GPU加速支持（PyTorch）</li>
              <li>批量并行处理提升效率</li>
            </ul>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="summary-item">
            <template #header>
              <div class="summary-header">
                <el-icon color="#E6A23C"><TrendCharts /></el-icon>
                <span>后处理</span>
              </div>
            </template>
            <ul class="summary-list">
              <li>EMA指数移动平均平滑</li>
              <li>斜率修正去除异常波动</li>
              <li>自适应卡尔曼滤波</li>
              <li>加权退化速度RUL计算</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>

      <div style="margin-top: 24px;">
        <el-divider content-position="center">
          <el-icon><StarFilled /></el-icon>
        </el-divider>
        <p style="text-align: center; color: #606266; font-size: 14px;">
          四种算法各有特点，可根据实际应用场景灵活选择。系统设计完善，结合了多种机器学习和统计方法，形成了鲁棒的寿命预测框架。
        </p>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import {
  DataAnalysis, TrendCharts, Reading, Connection, Right, Star, Check,
  Document, Operation, Timer, Histogram, Memo, Tools, Cpu, StarFilled
} from '@element-plus/icons-vue';

// 算法对比数据
const comparisonData = ref([
  {
    metric: '训练速度',
    ae_pros: '快速收敛',
    ae_score: 4,
    vae_pros: '中等速度',
    vae_score: 3,
    if_pros: '极快',
    if_score: 5,
    som_pros: '较慢',
    som_score: 2
  },
  {
    metric: '推理效率',
    ae_pros: 'GPU加速',
    ae_score: 4,
    vae_pros: 'GPU加速',
    vae_score: 4,
    if_pros: 'CPU高效',
    if_score: 5,
    som_pros: '中等',
    som_score: 3
  },
  {
    metric: '鲁棒性',
    ae_pros: '良好',
    ae_score: 4,
    vae_pros: '优秀',
    vae_score: 5,
    if_pros: '良好',
    if_score: 4,
    som_pros: '中等',
    som_score: 3
  },
  {
    metric: '可解释性',
    ae_pros: '中等',
    ae_score: 3,
    vae_pros: '概率解释',
    vae_score: 4,
    if_pros: '路径长度',
    if_score: 4,
    som_pros: '可视化强',
    som_score: 5
  },
  {
    metric: '适用场景',
    ae_pros: '生产环境',
    ae_score: 5,
    vae_pros: '噪声数据',
    vae_score: 4,
    if_pros: '实时预测',
    if_score: 5,
    som_pros: '模式探索',
    som_score: 4
  }
]);
</script>

<style scoped>
.modeling-overview {
  padding: 0;
}

/* 头部样式 */
.header-with-icon {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 32px;
  color: var(--cmg-aerospace-primary);
}

.subtitle {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: var(--cmg-text-secondary);
  font-weight: normal;
}

/* 介绍卡片 */
.intro-card {
  margin-bottom: 24px;
}

.intro-content {
  padding: 0;
}

/* 流程图部分 */
.pipeline-section {
  margin-top: 32px;
  padding: 24px;
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-lg);
}

.pipeline-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px 0;
  font-size: 18px;
  color: var(--cmg-text-primary);
}

.image-container {
  text-align: center;
  margin: 24px 0;
  padding: 16px;
  background: white;
  border-radius: var(--cmg-radius-base);
  box-shadow: var(--cmg-shadow-sm);
}

.pipeline-image {
  max-width: 100%;
  height: auto;
  border-radius: var(--cmg-radius-base);
}

.pipeline-steps {
  margin-top: 24px;
}

/* 算法卡片 */
.algorithm-card {
  margin-bottom: 24px;
  height: 100%;
}

.algorithm-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.algorithm-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--cmg-text-primary);
}

.algorithm-content {
  padding: 0;
}

.architecture-image {
  text-align: center;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-base);
}

.architecture-image img {
  max-width: 100%;
  height: auto;
  border-radius: var(--cmg-radius-base);
}

/* 原理说明 */
.principle-section,
.structure-section,
.features-section,
.formula-section {
  margin-bottom: 20px;
}

.principle-section h4,
.structure-section h4,
.features-section h4,
.formula-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--cmg-text-primary);
  font-weight: 600;
}

.principle-text {
  margin: 0;
  line-height: 1.8;
  color: var(--cmg-text-secondary);
  text-align: justify;
}

/* 公式框 */
.formula-box {
  padding: 16px;
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-base);
  border-left: 4px solid var(--cmg-aerospace-primary);
}

.formula-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.formula-item:last-child {
  margin-bottom: 0;
}

.formula-label {
  font-weight: 600;
  color: var(--cmg-text-primary);
  min-width: 100px;
}

.formula-item code {
  flex: 1;
  padding: 6px 12px;
  background: white;
  border-radius: var(--cmg-radius-sm);
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: var(--cmg-aerospace-primary);
}

/* 特性列表 */
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: var(--cmg-text-secondary);
}

/* 辅助算法卡片 */
.auxiliary-card {
  margin-bottom: 24px;
}

.wiener-section,
.wiener-features {
  padding: 16px;
}

/* 对比表卡片 */
.comparison-card {
  margin-bottom: 24px;
}

/* 总结卡片 */
.summary-card {
  margin-bottom: 24px;
}

.summary-item {
  height: 100%;
  border-radius: var(--cmg-radius-lg);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.summary-list li {
  padding: 8px 0;
  color: var(--cmg-text-secondary);
  border-bottom: 1px dashed var(--cmg-border-light);
}

.summary-list li:last-child {
  border-bottom: none;
}

.summary-list li::before {
  content: '▹';
  color: var(--cmg-aerospace-primary);
  margin-right: 8px;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-icon {
    font-size: 24px;
  }

  .algorithm-header h2 {
    font-size: 18px;
  }

  .pipeline-section {
    padding: 16px;
  }
}
</style>

export const isSimulinkDerived = dataset =>
  dataset?.source === 'simulation' && dataset?.component === '派生参数'

const isDerivedParameterDataset = dataset =>
  dataset?.component === '派生参数' || /p_values|派生参数/i.test(dataset?.name || '')

export const diagnosisDataRequirements = {
  hier14:
    '原始状态量 scope CSV（含时间列与 Hier14 模型测点），不要使用「派生参数 / P_values」数据集。',
  msfg_teams_rt:
    'P_values /「派生参数」CSV（含 P1–P17），或已登记同名「任务名-派生参数」的 scope 数据集（将自动解析派生文件）。',
  pca_iforest:
    '含多路数值测点的时序 CSV（至少 8 行），建议使用 scope 状态量，而非派生 P 参数。',
}

export function isMsfgCompatible(dataset, allDatasets) {
  if (!dataset) return false
  if (isDerivedParameterDataset(dataset)) return true
  const siblingName = `${dataset.name}-派生参数`
  if (allDatasets.some(d => d.id !== dataset.id && d.name === siblingName && d.source === dataset.source)) {
    return true
  }
  const prefix = (dataset.name || '').split('-')[0]
  if (
    prefix &&
    allDatasets.some(
      d =>
        d.id !== dataset.id &&
        d.component === '派生参数' &&
        d.source === dataset.source &&
        (d.name === siblingName || d.name.startsWith(prefix)),
    )
  ) {
    return true
  }
  return false
}

export function isHier14Compatible(dataset) {
  if (!dataset) return false
  return !isSimulinkDerived(dataset) && dataset.component !== '派生参数'
}

export function isPcaCompatible(dataset) {
  if (!dataset) return false
  return dataset.component !== '派生参数' && !/p_values/i.test(dataset.name || '')
}

export function datasetsForDiagnosisAlgorithm(algorithm, datasets, pluginRecord) {
  const all = datasets || []
  if (pluginRecord?.source === 'plugin') return all
  if (algorithm === 'hier14') return all.filter(isHier14Compatible)
  if (algorithm === 'msfg_teams_rt') return all.filter(d => isMsfgCompatible(d, all))
  if (algorithm === 'pca_iforest') return all.filter(isPcaCompatible)
  return all
}

export function diagnosisDataRequirementText(algorithm, pluginRecord) {
  if (pluginRecord?.data_requirement) return pluginRecord.data_requirement
  if (pluginRecord?.source === 'plugin') {
    const minRows = pluginRecord.min_rows
    return minRows && minRows > 1
      ? `CSV 数据集，建议不少于 ${minRows} 行。`
      : '平台登记的 CSV 数据集。'
  }
  return diagnosisDataRequirements[algorithm] || 'CSV 数据集。'
}

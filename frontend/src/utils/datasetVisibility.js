export const isSimulinkDerived = dataset =>
  String(dataset?.component || '').trim() === '派生参数' ||
  ['derived_parameter', 'derived_parameters'].includes(dataset?.data_type) ||
  /(?:^|[-\s])派生参数$/.test(String(dataset?.name || ''))

// Keep paired preprocessing files in storage, hide them from file selectors.
export const isSelectableDataset = dataset => !isSimulinkDerived(dataset)

export const isSimulinkDerived = dataset =>
  dataset?.source === 'simulation' && dataset?.component === '派生参数'

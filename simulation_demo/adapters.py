from .views import _series
class SimulationAdapter:
    name='demo'
    def run(self,params): return _series(params.get('fault') or params)
class MatlabEngineAdapter(SimulationAdapter): name='matlab-engine'
class PortForwardAdapter(SimulationAdapter): name='port-forward'
def get_adapter(): return SimulationAdapter()

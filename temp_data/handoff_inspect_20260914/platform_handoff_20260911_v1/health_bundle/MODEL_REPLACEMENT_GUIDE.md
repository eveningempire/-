# MODEL REPLACEMENT GUIDE (no Schema/core/caller changes - ever)

## Contract
A model is pluggable iff it ships (1) an artifact file under models/, (2) one
model_registry.json entry under a (head, component) key with sha256,
qualification and fallback_head. The Schema (schemas.py), the orchestration
(core.py) and every caller stay untouched.

## Steps (example: new component_hi model for gas_generator)
1. Drop the artifact: models/component_hi_gas_generator_<NEW>.joblib
2. Edit model_registry.json - replace the component_hi/gas_generator entry:
   {"head": "component_hi", "component_id": "gas_generator",
    "model_name": "<your-model>", "model_version": "<semver>",
    "artifact": "models/component_hi_gas_generator_<NEW>.joblib",
    "sha256": "<file sha256>", "qualification": "qualified",
    "fallback_head": "component_hi_frozen_cdPCA"}
3. Add an adapter class for <your-model> in platform_adapter/adapters.py and
   one branch in AdapterFactory.build (the ONLY code edit, additive only).
4. Run: python -m platform_adapter.cli --bundle . --replace-drill
   The drill re-runs the same client input through the new model, proves the
   schema/output shape is unchanged, and proves a corrupted sha256 refuses the
   artifact and engages the registered fallback.

## Qualification honesty
Only set qualification="qualified" when strict outer-OOF evidence (fold-fit
models, frozen thresholds, bootstrap gates) supports it. Anything else must be
fallback / development_only_not_registered / abstain. The platform never
silently outputs a healthy value for a head that abstains.

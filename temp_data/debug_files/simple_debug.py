import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
import django
django.setup()

print("Django setup complete")

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
print("Models imported")

msfgs = MSFGDefinition.objects.all()
print(f"MSFG count: {msfgs.count()}")

mappings = TestPointComponentMapping.objects.all()
print(f"Mapping count: {mappings.count()}")

if msfgs.exists():
    msfg = msfgs.first()
    print(f"First MSFG: {msfg.name}")
    print(f"Test names: {msfg.test_names}")
    print(f"Component names: {msfg.component_names}")


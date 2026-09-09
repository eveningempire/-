import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel, PHM

print("Current PHM Models:")
for model in PHMModel.objects.all():
    print(f"  - {model.model_name}")

print("\nCurrent PHMs:")
for cmg in PHM.objects.all():
    print(f"  - {cmg.cmg_id}: {cmg.name}")


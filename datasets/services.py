import csv
from .models import Dataset
def path_for(dataset_id): return Dataset.objects.get(pk=dataset_id).file.path
def read_rows(dataset_id):
 with open(path_for(dataset_id),encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

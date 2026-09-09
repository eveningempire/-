from __future__ import annotations

import os
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError

from data_management.models import PHMModel
from health_management.models import IMSModel
from health_management.algorithms.IMS.legacy_trainer import train_legacy_ims_from_csv


class Command(BaseCommand):
    help = "Train legacy IMS (KMeans radius) model from CSVs and register IMSModel with type=kmeans_ims."

    def add_arguments(self, parser):
        parser.add_argument("--cmg-model-id", type=int, required=True, help="Target PHMModel ID")
        parser.add_argument("--data-dir", type=str, default=os.path.join("delete", "IMS", "Health"), help="CSV directory (recursive)")
        parser.add_argument("--columns", type=str, default=None, help="Comma-separated column names to use (optional)")
        parser.add_argument("--name", type=str, default=None, help="IMS model name (optional)")
        parser.add_argument("--threshold", type=float, default=0.5, help="Anomaly threshold (0..1)")
        parser.add_argument("--n-clusters", type=int, default=None, help="Number of clusters (optional)")
        parser.add_argument("--shrink-ratio", type=float, default=0.05, help="Radius shrink ratio")
        parser.add_argument("--calib-percentile", type=float, default=95.0, help="Calibration percentile for distances")
        parser.add_argument("--deactivate-others", action="store_true", help="Deactivate other IMS models for this PHMModel")

    def handle(self, *args, **options):
        cmg_model_id: int = options["cmg_model_id"]
        data_dir: str = options["data_dir"]
        columns_str: Optional[str] = options["columns"]
        name: Optional[str] = options["name"]
        threshold: float = options["threshold"]
        n_clusters: Optional[int] = options["n_clusters"]
        shrink_ratio: float = options["shrink_ratio"]
        calib_percentile: float = options["calib_percentile"]
        deactivate_others: bool = options["deactivate_others"]

        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            raise CommandError(f"PHMModel {cmg_model_id} not found")

        cols: Optional[List[str]] = [c.strip() for c in columns_str.split(",")] if columns_str else None

        # Train via shared trainer
        try:
            model_bytes, final_cols = train_legacy_ims_from_csv(
                data_dir=data_dir,
                columns=cols,
                n_clusters=n_clusters,
                shrink_ratio=shrink_ratio,
                calib_percentile=calib_percentile,
            )
        except FileNotFoundError as e:
            raise CommandError(str(e))

        # Create IMSModel row
        params = final_cols

        if deactivate_others:
            IMSModel.objects.filter(cmg_model=cmg_model, is_active=True).update(is_active=False)

        ims = IMSModel.objects.create(
            cmg_model=cmg_model,
            name=name or f"LegacyIMS_{cmg_model.model_name}",
            parameters=params,
            model_config={
                "type": "kmeans_ims",
                "n_clusters": n_clusters,
                "shrink_ratio": shrink_ratio,
                "calib_percentile": calib_percentile,
            },
            model_data=model_bytes,
            threshold=float(threshold),
            is_active=True,
        )

        self.stdout.write(self.style.SUCCESS(f"Legacy IMS model created: ID={ims.id}, name={ims.name}, params={len(params)}"))




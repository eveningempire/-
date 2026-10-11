import hashlib
import json
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import Client, TestCase, override_settings

from datasets.models import Dataset
from .fault_replay import _ensure_asset_events
from .models import FaultEvent, StructureNode, TelemetrySample, TelemetrySession


class StructureApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def post(self, payload):
        return self.client.post("/api/v1/phm/acceptance/structure/", json.dumps(payload), content_type="application/json")

    def test_create_update_move_and_tree_response(self):
        root = self.post({"node_key": "vehicle", "pbs_code": "V", "name": "运载器", "node_type": "vehicle"}).json()["node"]
        propulsion = self.post({"node_key": "propulsion", "pbs_code": "V-01", "name": "动力系统", "node_type": "system", "parent_id": root["id"]}).json()["node"]
        subsystem = self.post({"node_key": "engine", "pbs_code": "V-01-01", "name": "发动机", "node_type": "subsystem", "parent_id": propulsion["id"]}).json()["node"]
        sensor = self.post({"node_key": "sensor", "pbs_code": "V-01-01-01", "name": "压力传感器", "node_type": "product", "parent_id": subsystem["id"]}).json()["node"]
        other_subsystem = self.post({"node_key": "supply", "pbs_code": "V-01-02", "name": "供应系统", "node_type": "subsystem", "parent_id": propulsion["id"]}).json()["node"]
        response = self.client.patch(
            f"/api/v1/phm/acceptance/structure/{sensor['id']}/",
            json.dumps({"name": "压力传感器A", "parent_id": other_subsystem["id"]}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["node"]["parent_id"], other_subsystem["id"])
        tree = response.json()["tree"]
        self.assertEqual(tree[0]["node_key"], "vehicle")
        self.assertEqual(tree[0]["children"][0]["node_key"], "propulsion")

    def test_move_rejects_parent_cycle(self):
        root = self.post({"node_key": "root", "pbs_code": "R", "name": "根", "node_type": "vehicle"}).json()["node"]
        child = self.post({"node_key": "child", "pbs_code": "R-01", "name": "子", "node_type": "system", "parent_id": root["id"]}).json()["node"]
        response = self.client.patch(
            f"/api/v1/phm/acceptance/structure/{root['id']}/",
            json.dumps({"parent_id": child["id"]}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(StructureNode.objects.get(pk=root["id"]).parent_id)


class FaultReplayApiTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="replay-user")
        self.session = TelemetrySession.objects.create(
            name="replay", created_by=user, token_hash=hashlib.sha256(b"token").hexdigest(),
            columns=["time", "pressure", "temperature"],
        )
        for timestamp in range(11):
            TelemetrySample.objects.create(
                session=self.session,
                values={"time": timestamp, "pressure": 1 - timestamp * 0.04, "temperature": 0.4},
            )
        self.event = FaultEvent.objects.create(
            session=self.session, name="推进剂泄漏", severity="critical",
            isolation_target="推进剂供给与压力链路", start_time=4, end_time=10,
        )
        self.client = Client()

    def test_replay_supports_window_speed_pause_and_curve(self):
        created = self.client.post(
            f"/api/v1/phm/fault-events/{self.event.id}/replays/",
            json.dumps({"start": 3, "end": 8, "speed": 2}), content_type="application/json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        payload = created.json()
        self.assertEqual(payload["curve"]["count"], 6)
        self.assertIn("pressure", payload["curve"]["series"])
        replay_id = payload["replay"]["id"]
        self.client.post(f"/api/v1/phm/fault-replays/{replay_id}/", json.dumps({"action": "play"}), content_type="application/json")
        ticked = self.client.post(
            f"/api/v1/phm/fault-replays/{replay_id}/",
            json.dumps({"action": "tick", "elapsed": 1}), content_type="application/json",
        ).json()
        self.assertEqual(ticked["replay"]["current_time"], 5)
        self.assertEqual(ticked["curve"]["count"], 3)
        paused = self.client.post(
            f"/api/v1/phm/fault-replays/{replay_id}/",
            json.dumps({"action": "pause"}), content_type="application/json",
        ).json()
        self.assertEqual(paused["replay"]["state"], "paused")

    def test_bundled_simulation_assets_remain_readable_but_are_hidden_from_project_sources(self):
        FaultEvent.objects.all().delete()
        self.assertEqual(_ensure_asset_events(), 9)
        self.assertEqual(_ensure_asset_events(), 0)
        imported = FaultEvent.objects.get(diagnosis__asset_code="m1")
        detail = self.client.get(f"/api/v1/phm/fault-events/{imported.id}/").json()
        self.assertEqual(detail["curve"]["count"], 500)
        self.assertIn("current", detail["curve"]["series"])
        response = self.client.get("/api/v1/phm/fault-events/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["count"], 0)

    def test_events_exclude_derived_datasets_including_existing_events(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            raw = Dataset.objects.create(name="原始数据", component="原始状态量")
            raw.file.save("scope.csv", ContentFile(b"Time,pressure,FaultFlag\n0,1,0\n1,.5,1\n"))
            derived = Dataset.objects.create(name="派生数据", component="派生参数")
            derived.file.save("P_values.csv", ContentFile(b"Time,P1,FaultFlag\n0,1,0\n1,.5,1\n"))
            FaultEvent.objects.create(session=self.session, name=derived.name, start_time=0, end_time=1,
                                      diagnosis={"dataset_id": derived.pk, "source_key": f"dataset:{derived.pk}"})
            response = self.client.get("/api/v1/phm/fault-events/")
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual([event["dataset_id"] for event in response.json()["results"]], [raw.pk])
            self.assertEqual(FaultEvent.objects.filter(diagnosis__dataset_id=derived.pk).count(), 1)

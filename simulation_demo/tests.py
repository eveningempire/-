import json

from django.test import Client, TestCase


class FaultWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_realtime_fault_workflow_triggers_full_chain(self):
        response = self.client.post(
            "/api/v1/simulation-demo/workflows/",
            data=json.dumps({"mode": "realtime", "subsystem": "动力", "fault_mode": "泄漏", "severity": 0.8, "injection_time": 2}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        task_id = response.json()["task"]["id"]
        for timestamp in range(3):
            response = self.client.post(
                f"/api/v1/simulation-demo/workflows/{task_id}/samples/",
                data=json.dumps({"timestamp": timestamp, "values": {"pressure": 1.0, "temperature": 0.4}}),
                content_type="application/json",
            )
        result = response.json()["event"]["result"]
        self.assertTrue(result["injected"])
        self.assertTrue(result["alarm"]["triggered"])
        self.assertEqual(result["diagnosis"]["fault"], "泄漏")
        self.assertEqual(result["isolation"]["status"], "isolated")
        self.assertIsNotNone(result["rul"]["value"])
        self.assertTrue(result["notification"]["published"])

    def test_offline_workflow_generates_dataset(self):
        created = self.client.post(
            "/api/v1/simulation-demo/workflows/",
            data=json.dumps({"mode": "offline", "subsystem": "控制", "fault_mode": "传感器偏置", "injection_time": 20}),
            content_type="application/json",
        ).json()
        response = self.client.post(f"/api/v1/simulation-demo/workflows/{created['task']['id']}/generate/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNotNone(response.json()["dataset_id"])

    def test_power_fault_and_clearance(self):
        created = self.client.post("/api/v1/simulation-demo/workflows/", data=json.dumps({"mode":"realtime","subsystem":"电源","fault_mode":"母线欠压","severity":.8,"injection_time":0}), content_type="application/json").json()
        url = f"/api/v1/simulation-demo/workflows/{created['task']['id']}/samples/"
        injected = self.client.post(url, data=json.dumps({"timestamp":1,"values":{"bus_voltage":1}}), content_type="application/json").json()
        self.assertTrue(injected["event"]["result"]["alarm"]["triggered"])
        cleared = self.client.post(url, data=json.dumps({"timestamp":2,"clear_fault":True}), content_type="application/json").json()
        self.assertEqual(cleared["event"]["stage"], "cleared")
        self.assertTrue(cleared["event"]["result"]["clearance"]["restored"])

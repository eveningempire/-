from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AlarmRule, FaultEvent, RealtimeAlarm, TelemetrySample, TelemetrySession
from .realtime_detection import detect_sample


class RealtimeAlarmTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alarm-test", password="pass")
        self.session = TelemetrySession.objects.create(name="live", created_by=self.user, token_hash="x")

    def test_disabled_session_does_not_generate_alarm(self):
        sample = TelemetrySample.objects.create(session=self.session, values={"time": 1, "pressure": 0.5})
        self.assertEqual(detect_sample(self.session, sample), [])
        self.assertEqual(RealtimeAlarm.objects.count(), 0)

    def test_enabled_session_generates_realtime_alarm(self):
        self.session.monitoring_enabled = True
        self.session.save(update_fields=["monitoring_enabled"])
        sample = TelemetrySample.objects.create(session=self.session, values={"time": 1, "pressure": 0.5})
        alarms = detect_sample(self.session, sample)
        self.assertEqual(len(alarms), 1)
        self.assertEqual(alarms[0].fault_name, "推进剂泄漏")
        self.assertEqual(alarms[0].isolation_target, "推进剂供给与压力链路")
        event = FaultEvent.objects.get(alarm=alarms[0])
        self.assertEqual(event.start_time, 1)
        self.assertEqual(event.name, "推进剂泄漏")

    def test_custom_rule_does_not_replace_platform_rule_for_same_signal(self):
        AlarmRule.objects.create(
            name="pressure high",
            signal="pressure",
            operator="gt",
            threshold=10.0,
        )
        self.session.monitoring_enabled = True
        self.session.save(update_fields=["monitoring_enabled"])
        sample = TelemetrySample.objects.create(
            session=self.session,
            values={"time": 1, "pressure": 0.65},
        )

        alarms = detect_sample(self.session, sample)

        self.assertEqual(len(alarms), 1)
        self.assertEqual(alarms[0].fault_name, "推进剂泄漏")
        self.assertEqual(alarms[0].threshold, 0.88)

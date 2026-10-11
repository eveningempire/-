from unittest.mock import Mock
from django.test import SimpleTestCase
from .service import DiagnosisService
from .views import _standardize_result


class DiagnosisServiceTests(SimpleTestCase):
    def test_bad_input_does_not_replace_trained_predictor(self):
        service = object.__new__(DiagnosisService)
        service.predictor_path = 'predictor.py'
        service.predictor = Mock()
        service.predictor.predict_scope_csv.side_effect = [ValueError('missing raw columns'),
            {'pred_name': '正常', 'aggregate_pred_name': '泵气蚀',
             'class_probs': [{'name': '正常', 'prob': .8}],
             'aggregate_class_probs': [{'name': '泵气蚀', 'prob': .7}]}]
        service.error = None
        with self.assertRaisesRegex(ValueError, 'missing raw columns'):
            service.predict('derived.csv')
        self.assertTrue(service.available)
        self.assertIsNone(service.error)
        result = service.predict('raw.csv')
        self.assertEqual(result['model_mode'], 'trained-hier14')
        self.assertEqual(result['confidence'], .7)
        self.assertEqual(result['latest_confidence'], .8)

    def test_window_events_are_preserved_when_aggregate_is_normal(self):
        keys = ('row_count', 'columns', 'numeric_columns', 'parameter_columns', 'numeric_parameter_columns', 'time_column', 'fault_flag_column', 'column_roles', 'time_summary', 'fault_label_summary', 'missing_value_count', 'invalid_value_count', 'quality_status', 'quality_message')
        quality = dict.fromkeys(keys)
        windows = [{'pred_name':'正常','confidence':.9,'time_start':0,'time_end':10},
                   {'pred_name':'泵气蚀','confidence':.9,'time_start':10,'time_end':20},
                   {'pred_name':'泵气蚀','confidence':.8,'time_start':15,'time_end':25},
                   {'pred_name':'正常','confidence':.9,'time_start':25,'time_end':35}]
        result = _standardize_result({'aggregate_pred_name':'正常','confidence':.8,'window_series':windows}, quality)
        self.assertEqual(result['event_summary']['event_count'], 1)
        self.assertEqual(result['detected_events'][0]['fault'], '泵气蚀')
        self.assertEqual(result['detected_events'][0]['window_count'], 2)
        self.assertEqual(result['detected_events'][0]['time_start'], 10)
        self.assertEqual(result['detected_events'][0]['time_end'], 25)

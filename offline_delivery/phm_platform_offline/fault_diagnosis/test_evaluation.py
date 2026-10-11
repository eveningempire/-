import pandas as pd
from django.test import SimpleTestCase
from .evaluation import score_windows


class EvaluationTests(SimpleTestCase):
    def test_truth_windows_and_transitions_are_scored_separately(self):
        frame = pd.DataFrame({'Time': [0,1,2,3,4,5], 'FaultFlag': [0,0,1,1,0,0]})
        result = {'window_series': [{'time_start':0, 'time_end':1, 'pred_name':'正常'},
                                   {'time_start':1, 'time_end':2, 'pred_name':'泵气蚀'},
                                   {'time_start':2, 'time_end':3, 'pred_name':'泵气蚀'},
                                   {'time_start':4, 'time_end':5, 'pred_name':'异常'}]}
        scores = score_windows(frame, result, '泵气蚀')
        self.assertEqual([row['truth'] for row in scores], ['正常','transition','泵气蚀','正常'])
        self.assertEqual([row['class_correct'] for row in scores], [True,None,True,False])

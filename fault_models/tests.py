from django.test import TestCase


class FaultTreeGraphTests(TestCase):
 def test_persists_nodes_edges_and_logic_gates(self):
  graph={'nodes':[{'id':'top','name':'动力系统失效','type':'top'},{'id':'or1','name':'任一事件','type':'OR'},{'id':'e1','name':'泵失效','type':'basic'}],'edges':[{'source':'top','target':'or1'},{'source':'or1','target':'e1'}]}
  response=self.client.post('/api/v1/knowledge/fault-trees/',data={'name':'动力FTA','graph':graph},content_type='application/json')
  self.assertEqual(response.status_code,201,response.content); self.assertEqual(len(response.json()['graph']['edges']),2)
  list_response=self.client.get('/api/v1/knowledge/fault-trees/')
  self.assertEqual(list_response.status_code,200)
  self.assertEqual(list_response.json()[0]['name'],'动力FTA')

 def test_rejects_cycle(self):
  graph={'nodes':[{'id':'a','type':'event'},{'id':'b','type':'OR'}],'edges':[{'source':'a','target':'b'},{'source':'b','target':'a'}]}
  response=self.client.post('/api/v1/knowledge/fault-trees/',data={'name':'非法FTA','graph':graph},content_type='application/json')
  self.assertEqual(response.status_code,400)

 def test_fmeca_is_updated_as_latest_record(self):
  first=self.client.post('/api/v1/knowledge/fmeca/',data={'data':[{'component':'蓄电池组','mode':'容量衰减','cause':'循环老化','level':'中'}]},content_type='application/json')
  self.assertEqual(first.status_code,201)
  record_id=first.json()['id']
  second=self.client.put(f'/api/v1/knowledge/fmeca/{record_id}/',data={'data':[{'component':'配电单元','mode':'母线欠压','cause':'接触电阻增大','level':'高'}]},content_type='application/json')
  self.assertEqual(second.status_code,200)
  listing=self.client.get('/api/v1/knowledge/fmeca/')
  self.assertEqual(listing.status_code,200)
  self.assertEqual(len(listing.json()),1)
  self.assertEqual(listing.json()[0]['data'][0]['component'],'配电单元')

 def test_fmeca_list(self):
  create_response=self.client.post('/api/v1/knowledge/fmeca/',data={'data':{'mode':'阀门卡滞'}},content_type='application/json')
  self.assertEqual(create_response.status_code,201)
  list_response=self.client.get('/api/v1/knowledge/fmeca/')
  self.assertEqual(list_response.status_code,200)
  self.assertEqual(list_response.json()[0]['data']['mode'],'阀门卡滞')

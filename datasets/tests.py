import tempfile
from pathlib import Path
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from .models import Dataset
from phm.models import StructureNode


class DatasetPermissionsTests(TestCase):
    def test_roles_and_file_cleanup(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            admin = get_user_model().objects.create_user('dataset_admin', is_staff=True)
            viewer = get_user_model().objects.create_user('dataset_viewer')
            client = APIClient()
            self.assertEqual(client.get('/api/v1/datasets/').status_code, 403)
            client.force_authenticate(admin)
            response = client.post('/api/v1/datasets/', {
                'name': 'permission-test', 'source': 'offline',
                'file': SimpleUploadedFile('test.csv', b'time,HI\n0,1\n1,0.9\n')}, format='multipart')
            self.assertEqual(response.status_code, 201)
            dataset = Dataset.objects.get(pk=response.data['id'])
            file_path = Path(dataset.file.path)
            url = f'/api/v1/datasets/{dataset.pk}/'
            client.force_authenticate(viewer)
            self.assertEqual(client.get('/api/v1/datasets/').status_code, 200)
            download = client.get(url + 'download/')
            self.assertEqual(download.status_code, 200)
            download.close()
            self.assertEqual(client.post('/api/v1/datasets/', {}, format='multipart').status_code, 403)
            self.assertEqual(client.delete(url).status_code, 403)
            self.assertTrue(file_path.exists())
            client.force_authenticate(admin)
            self.assertEqual(client.delete(url).status_code, 204)
            self.assertFalse(file_path.exists())
            self.assertFalse(Dataset.objects.filter(pk=dataset.pk).exists())

    def test_admin_can_link_dataset_to_pbs_product(self):
        root = StructureNode.objects.create(node_key='test-vehicle', name='运载器', node_type='vehicle', pbs_code='TV')
        system = StructureNode.objects.create(node_key='test-system', name='推进系统', node_type='system', pbs_code='TV-01', parent=root)
        subsystem = StructureNode.objects.create(node_key='test-subsystem', name='发动机', node_type='subsystem', pbs_code='TV-01-01', parent=system)
        product = StructureNode.objects.create(node_key='test-pump', name='液氧泵', node_type='product', pbs_code='TV-01-01-01', parent=subsystem)
        admin = get_user_model().objects.create_user('pbs-admin', is_staff=True)
        viewer = get_user_model().objects.create_user('pbs-viewer')
        client = APIClient()
        client.force_authenticate(admin)
        response = client.post('/api/v1/datasets/', {'name': 'pump-data', 'source': 'offline', 'structure_node_id': product.pk, 'file': SimpleUploadedFile('pump.csv', b'time,HI\n0,1\n')}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['structure_node_key'], 'test-pump')
        dataset_id = response.data['id']
        self.assertEqual(client.patch(f'/api/v1/datasets/{dataset_id}/', {'structure_node_id': system.pk}, format='json').status_code, 400)
        self.assertEqual(client.patch(f'/api/v1/datasets/{dataset_id}/', {'structure_node_id': None}, format='json').status_code, 200)
        self.assertEqual(client.patch(f'/api/v1/datasets/{dataset_id}/', {'structure_node_id': product.pk}, format='json').status_code, 200)
        client.force_authenticate(viewer)
        self.assertEqual(client.patch(f'/api/v1/datasets/{dataset_id}/', {'structure_node_id': None}, format='json').status_code, 403)

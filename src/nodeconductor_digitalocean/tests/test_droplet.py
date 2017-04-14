import mock
from rest_framework import status, test

from nodeconductor.structure.models import CustomerRole
from nodeconductor.structure.tests import factories as structure_factories

from .. import models
from . import factories, fixtures


class DropletResizeTest(test.APITransactionTestCase):
    def setUp(self):
        self.user = structure_factories.UserFactory()
        self.customer = structure_factories.CustomerFactory()
        self.project = structure_factories.ProjectFactory(customer=self.customer)
        self.service = factories.DigitalOceanServiceFactory(customer=self.customer)
        self.customer.add_user(self.user, CustomerRole.OWNER)
        self.spl = factories.DigitalOceanServiceProjectLinkFactory(service=self.service, project=self.project)

    def test_user_can_not_resize_provisioning_droplet(self):
        self.client.force_authenticate(user=self.user)

        self.droplet = factories.DropletFactory(service_project_link=self.spl,
                                                cores=2, ram=2 * 1024, disk=10 * 1024,
                                                state=models.Droplet.States.UPDATING)
        new_size = factories.SizeFactory(cores=3, ram=3 * 1024, disk=20 * 1024)

        response = self.client.post(factories.DropletFactory.get_url(self.droplet, 'resize'), {
            'size': factories.SizeFactory.get_url(new_size),
            'disk': True
        })
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_user_can_resize_droplet_to_bigger_size(self):
        self.client.force_authenticate(user=self.user)

        self.droplet = factories.DropletFactory(service_project_link=self.spl,
                                                cores=2, ram=2 * 1024, disk=10 * 1024,
                                                state=models.Droplet.States.OK,
                                                runtime_state=models.Droplet.RuntimeStates.OFFLINE)
        new_size = factories.SizeFactory(cores=3, ram=3 * 1024, disk=20 * 1024)

        response = self.client.post(factories.DropletFactory.get_url(self.droplet, 'resize'), {
            'size': factories.SizeFactory.get_url(new_size),
            'disk': True
        })
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_user_can_resize_droplet_to_smaller_cpu(self):
        self.client.force_authenticate(user=self.user)

        self.droplet = factories.DropletFactory(service_project_link=self.spl, cores=3, disk=20 * 1024,
                                                state=models.Droplet.States.OK,
                                                runtime_state=models.Droplet.RuntimeStates.OFFLINE)
        new_size = factories.SizeFactory(cores=2, disk=20 * 1024)

        response = self.client.post(factories.DropletFactory.get_url(self.droplet, 'resize'), {
            'size': factories.SizeFactory.get_url(new_size),
            'disk': False
        })
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_user_can_not_resize_droplet_to_smaller_disk(self):
        self.client.force_authenticate(user=self.user)

        self.droplet = factories.DropletFactory(service_project_link=self.spl, disk=20 * 1024,
                                                state=models.Droplet.States.OK,
                                                runtime_state=models.Droplet.RuntimeStates.OFFLINE)
        new_size = factories.SizeFactory(disk=10 * 1024)

        response = self.client.post(factories.DropletFactory.get_url(self.droplet, 'resize'), {
            'size': factories.SizeFactory.get_url(new_size),
            'disk': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)


class DropletCreateTest(test.APITransactionTestCase):

    def setUp(self):
        self.fixture = fixtures.DigitalOceanFixture()
        self.url = factories.DropletFactory.get_list_url()

    def test_droplet_is_created(self):
        self.client.force_authenticate(self.fixture.owner)
        payload = self._get_valid_payload()

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_spl_quotas_usage_are_increased_on_droplet_creation(self):
        self.client.force_authenticate(self.fixture.owner)
        payload = self._get_valid_payload()

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        droplet = models.Droplet.objects.get(uuid=response.data['uuid'])
        spl = droplet.service_project_link
        actual_storage_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.storage).usage
        actual_ram_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.ram).usage
        actual_vcpu_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.vcpu).usage
        self.assertEqual(self.fixture.size.disk, actual_storage_usage)
        self.assertEqual(self.fixture.size.ram, actual_ram_usage)
        self.assertEqual(self.fixture.size.cores, actual_vcpu_usage)

    def _get_valid_payload(self):
        return {
            'name': 'droplet-name',
            'service_project_link': factories.DigitalOceanServiceProjectLinkFactory.get_url(self.fixture.spl),
            'image': factories.ImageFactory.get_url(self.fixture.image),
            'size': factories.SizeFactory.get_url(self.fixture.size),
            'region': factories.RegionFactory.get_url(self.fixture.region),
        }


class DropletDeleteTest(test.APITransactionTestCase):

    def setUp(self):
        self.fixture = fixtures.DigitalOceanFixture()

    @mock.patch('nodeconductor_digitalocean.executors.DropletDeleteExecutor.execute')
    def test_spl_quotas_are_decreased_on_droplet_deletion(self, delete_exectutor_mock):
        self.client.force_authenticate(self.fixture.owner)
        droplet = self.fixture.droplet
        # emulate creation.
        droplet.increase_backend_quotas_usage()

        def mock_droplet_deletion(droplet, *args, **kwargs):
            droplet.decrease_backend_quotas_usage()

        delete_exectutor_mock.side_effect = mock_droplet_deletion

        response = self.client.delete(factories.DropletFactory.get_url(droplet))

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        delete_exectutor_mock.assert_called_once()
        spl = self.fixture.spl
        actual_storage_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.storage).usage
        actual_ram_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.ram).usage
        actual_vcpu_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.vcpu).usage
        self.assertEqual(0, actual_storage_usage)
        self.assertEqual(0, actual_ram_usage)
        self.assertEqual(0, actual_vcpu_usage)


class DropletResizeTest(test.APITransactionTestCase):

    def setUp(self):
        self.fixture = fixtures.DigitalOceanFixture()

    @mock.patch('nodeconductor_digitalocean.executors.DropletResizeExecutor.execute')
    def test_droplet_resize_increases_quotas(self, executor):
        self.client.force_authenticate(self.fixture.owner)
        droplet = self.fixture.droplet
        droplet.runtime_state = droplet.RuntimeStates.OFFLINE
        droplet.save()
        droplet.increase_backend_quotas_usage()
        size = factories.SizeFactory(cores=droplet.cores+2, disk=droplet.disk+2048, ram=droplet.ram+1024)
        payload = {
            'size': factories.SizeFactory.get_url(size),
            'disk': True,
        }

        response = self.client.post(factories.DropletFactory.get_url(droplet, 'resize'), payload)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.data)
        spl = self.fixture.spl
        actual_storage_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.storage).usage
        actual_ram_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.ram).usage
        actual_vcpu_usage = spl.quotas.get(name=models.DigitalOceanServiceProjectLink.Quotas.vcpu).usage
        self.assertEqual(size.disk, actual_storage_usage)
        self.assertEqual(size.ram, actual_ram_usage)
        self.assertEqual(size.cores, actual_vcpu_usage)


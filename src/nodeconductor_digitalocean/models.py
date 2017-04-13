from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from nodeconductor.quotas.fields import CounterQuotaField
from nodeconductor.quotas.models import QuotaModelMixin
from nodeconductor.structure import models as structure_models


from .log import alert_logger


class DigitalOceanService(structure_models.Service):
    projects = models.ManyToManyField(
        structure_models.Project, related_name='digitalocean_services', through='DigitalOceanServiceProjectLink')

    class Meta(structure_models.Service.Meta):
        verbose_name = 'DigitalOcean provider'
        verbose_name_plural = 'DigitalOcean providers'

    class Quotas(QuotaModelMixin.Quotas):
        droplet_count = CounterQuotaField(
            default_limit=50,
            target_models=lambda: [Droplet],
            path_to_scope='service_project_link.service'
        )

    def raise_readonly_token_alert(self):
        """ Raise alert if provided token is read-only """
        alert_logger.digital_ocean.warning(
            'DigitalOcean token for {settings_name} is read-only.',
            scope=self.settings,
            alert_type='token_is_read_only',
            alert_context={'settings': self.settings})

    def close_readonly_token_alert(self):
        alert_logger.digital_ocean.close(scope=self.settings, alert_type='token_is_read_only')

    @classmethod
    def get_url_name(cls):
        return 'digitalocean'


class DigitalOceanServiceProjectLink(structure_models.CloudServiceProjectLink):
    service = models.ForeignKey(DigitalOceanService)

    class Meta(structure_models.CloudServiceProjectLink.Meta):
        verbose_name = 'DigitalOcean provider project link'
        verbose_name_plural = 'DigitalOcean provider project links'

    @classmethod
    def get_url_name(cls):
        return 'digitalocean-spl'


class Region(structure_models.GeneralServiceProperty):
    @classmethod
    def get_url_name(cls):
        return 'digitalocean-region'


@python_2_unicode_compatible
class Image(structure_models.GeneralServiceProperty):
    regions = models.ManyToManyField(Region)
    distribution = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    is_official = models.BooleanField(default=False, help_text='Is image provided by DigitalOcean')
    min_disk_size = models.PositiveIntegerField(
        null=True, help_text='Minimum disk required for a size to use this image')
    created_at = models.DateTimeField(null=True)

    @property
    def is_ssh_key_mandatory(self):
        MANDATORY = 'Ubuntu', 'FreeBSD', 'CoreOS'
        return self.distribution in MANDATORY

    def __str__(self):
        return '{} {} ({})'.format(self.name, self.distribution, self.type)

    @classmethod
    def get_url_name(cls):
        return 'digitalocean-image'

    @classmethod
    def get_backend_fields(cls):
        return super(Image, cls).get_backend_fields() + ('type', 'distribution', 'is_official', 'min_disk_size', 'created_at')


class Size(structure_models.GeneralServiceProperty):
    regions = models.ManyToManyField(Region)

    cores = models.PositiveSmallIntegerField(help_text='Number of cores in a VM')
    ram = models.PositiveIntegerField(help_text='Memory size in MiB')
    disk = models.PositiveIntegerField(help_text='Disk size in MiB')
    transfer = models.PositiveIntegerField(help_text='Amount of transfer bandwidth in MiB')
    price = models.DecimalField('Hourly price rate', default=0, max_digits=11, decimal_places=5)

    @classmethod
    def get_url_name(cls):
        return 'digitalocean-size'

    @classmethod
    def get_backend_fields(cls):
        return super(Size, cls).get_backend_fields() + ('cores', 'ram', 'disk', 'transfer', 'price')


class Droplet(structure_models.VirtualMachine):
    service_project_link = models.ForeignKey(
        DigitalOceanServiceProjectLink, related_name='droplets', on_delete=models.PROTECT)
    transfer = models.PositiveIntegerField(default=0, help_text='Amount of transfer bandwidth in MiB')
    ip_address = models.GenericIPAddressField(null=True, protocol='IPv4', blank=True)
    region_name = models.CharField(max_length=150, blank=True)
    size_name = models.CharField(max_length=150, blank=True)

    def increase_backend_quotas_usage(self, validate=True):
        self.service_project_link.add_quota_usage(self.service_project_link.Quotas.storage, self.disk)
        self.service_project_link.add_quota_usage(self.service_project_link.Quotas.ram, self.ram)
        self.service_project_link.add_quota_usage(self.service_project_link.Quotas.vcpu, self.cores)

    def decrease_backend_quotas_usage(self):
        self.service_project_link.add_quota_usage(self.service_project_link.Quotas.storage, -self.disk)
        self.service_project_link.add_quota_usage(self.service_project_link.Quotas.ram, -self.ram)
        self.service_project_link.add_quota_usage(self.service_project_link.Quotas.vcpu, -self.cores)

    @property
    def external_ips(self):
        return [self.ip_address]

    @property
    def internal_ips(self):
        return []

    @classmethod
    def get_url_name(cls):
        return 'digitalocean-droplet'

    @classmethod
    def get_backend_fields(cls):
        return super(Droplet, cls).get_backend_fields() + ('state', 'runtime_state', 'image_name')

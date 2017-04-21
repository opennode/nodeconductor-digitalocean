from __future__ import unicode_literals

from rest_framework import decorators, response, status, serializers as rf_serializers

from nodeconductor.core import executors as core_executors, validators as core_validators
from nodeconductor.structure import views as structure_views

from . import models, serializers, log, filters, executors


class DigitalOceanServiceViewSet(structure_views.BaseServiceViewSet):
    queryset = models.DigitalOceanService.objects.all()
    serializer_class = serializers.ServiceSerializer
    import_serializer_class = serializers.DropletImportSerializer


class DigitalOceanServiceProjectLinkViewSet(structure_views.BaseServiceProjectLinkViewSet):
    queryset = models.DigitalOceanServiceProjectLink.objects.all()
    serializer_class = serializers.ServiceProjectLinkSerializer


class ImageViewSet(structure_views.BaseServicePropertyViewSet):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer
    filter_class = filters.ImageFilter
    lookup_field = 'uuid'


class RegionViewSet(structure_views.BaseServicePropertyViewSet):
    queryset = models.Region.objects.all()
    serializer_class = serializers.RegionSerializer
    filter_class = filters.RegionFilter
    lookup_field = 'uuid'

    def get_queryset(self):
        return models.Region.objects.order_by('name')


class SizeViewSet(structure_views.BaseServicePropertyViewSet):
    queryset = models.Size.objects.all()
    serializer_class = serializers.SizeSerializer
    filter_class = filters.SizeFilter
    lookup_field = 'uuid'


class DropletViewSet(structure_views.ResourceViewSet):
    queryset = models.Droplet.objects.all()
    serializer_class = serializers.DropletSerializer

    create_executor = executors.DropletCreateExecutor
    update_executor = core_executors.EmptyExecutor
    delete_executor = executors.DropletDeleteExecutor
<<<<<<< HEAD
    destroy_validators = [core_validators.StateValidator(models.Droplet.States.OK, models.Droplet.States.ERRED)]
=======
    resize_executor = executors.DropletResizeExecutor
    runtime_state_executor = executors.DropletStateChangeExecutor
    runtime_acceptable_states = dict(
        resize=models.Droplet.RuntimeStates.OFFLINE,
        **structure_views.VirtualMachineViewSet.runtime_acceptable_states
    )

    def get_serializer_class(self):
        if self.action == 'resize':
            return serializers.DropletResizeSerializer
        return super(DropletViewSet, self).get_serializer_class()
>>>>>>> bef93c3c67fea7ddb59746fb496dc80af0bac6fc

    def perform_create(self, serializer):
        region = serializer.validated_data['region']
        image = serializer.validated_data['image']
        size = serializer.validated_data['size']
        ssh_key = serializer.validated_data.get('ssh_public_key')

        droplet = serializer.save(
            cores=size.cores,
            ram=size.ram,
            disk=size.disk,
            transfer=size.transfer)

        # XXX: We do not operate with backend_id`s in views.
        #      View should pass objects to executor.
        self.create_executor.execute(
            droplet,
            async=self.async_executor,
            backend_region_id=region.backend_id,
            backend_image_id=image.backend_id,
            backend_size_id=size.backend_id,
            ssh_key_uuid=ssh_key.uuid.hex if ssh_key else None)

    @decorators.detail_route(methods=['post'])
    def start(self, request, uuid=None):
        instance = self.get_object()
        executors.DropletStartExecutor().execute(instance)
        return response.Response({'status': 'start was scheduled'}, status=status.HTTP_202_ACCEPTED)

    start_validators = [core_validators.StateValidator(models.Droplet.States.OK),
                        core_validators.RuntimeStateValidator(models.Droplet.RuntimeStates.OFFLINE)]
    start_serializer_class = rf_serializers.Serializer

    @decorators.detail_route(methods=['post'])
    def stop(self, request, uuid=None):
        instance = self.get_object()
        executors.DropletStopExecutor().execute(instance)
        return response.Response({'status': 'stop was scheduled'}, status=status.HTTP_202_ACCEPTED)

    stop_validators = [core_validators.StateValidator(models.Droplet.States.OK),
                       core_validators.RuntimeStateValidator(models.Droplet.RuntimeStates.ONLINE)]
    stop_serializer_class = rf_serializers.Serializer

    @decorators.detail_route(methods=['post'])
    def restart(self, request, uuid=None):
        instance = self.get_object()
        executors.DropletRestartExecutor().execute(instance)
        return response.Response({'status': 'restart was scheduled'}, status=status.HTTP_202_ACCEPTED)

    restart_validators = [core_validators.StateValidator(models.Droplet.States.OK),
                          core_validators.RuntimeStateValidator(models.Droplet.RuntimeStates.ONLINE)]
    restart_serializer_class = rf_serializers.Serializer

    @decorators.detail_route(methods=['post'])
    def resize(self, request, uuid=None):
        """
        To resize droplet, submit a **POST** request to the instance URL, specifying URI of a target size.

        Pass {'disk': true} along with target size in order to perform permanent resizing,
        which allows you to resize your disk space as well as CPU and RAM.
        After increasing the disk size, you will not be able to decrease it.

        Pass {'disk': false} along with target size in order to perform flexible resizing,
        which only upgrades your CPU and RAM. This option is reversible.

        Note that instance must be OFFLINE. Example of a valid request:

        .. code-block:: http

            POST /api/digitalocean-droplets/6c9b01c251c24174a6691a1f894fae31/resize/ HTTP/1.1
            Content-Type: application/json
            Accept: application/json
            Authorization: Token c84d653b9ec92c6cbac41c706593e66f567a7fa4
            Host: example.com

            {
                "size": "http://example.com/api/digitalocean-sizes/1ee385bc043249498cfeb8c7e3e079f0/"
            }
        """
        droplet = self.get_object()
        serializer = self.get_serializer(droplet, data=request.data)
        serializer.is_valid(raise_exception=True)

        size = serializer.validated_data['size']
        disk = serializer.validated_data['disk']

        self.resize_executor.execute(
            droplet,
            disk=disk,
            size=size,
            updated_fields=None,
            async=self.async_executor)

        message = 'Droplet {droplet_name} has been scheduled to %s resize.' % \
                  (disk and 'permanent' or 'flexible')
        log.event_logger.droplet_resize.info(
            message,
            event_type='droplet_resize_scheduled',
            event_context={'droplet': droplet, 'size': size}
        )

        cores_increment = size.cores - droplet.cores
        ram_increment = size.ram - droplet.ram
        disk_increment = None

        droplet.cores = size.cores
        droplet.ram = size.ram

        if disk:
            disk_increment = size.disk - droplet.disk
            droplet.disk = size.disk

        droplet.save()

        spl = droplet.service_project_link

        if disk_increment:
            spl.add_quota_usage(spl.Quotas.storage, disk_increment, validate=True)
        spl.add_quota_usage(spl.Quotas.ram, ram_increment, validate=True)
        spl.add_quota_usage(spl.Quotas.vcpu, cores_increment, validate=True)

        return response.Response({'detail': 'resizing was scheduled'}, status=status.HTTP_202_ACCEPTED)

    resize_serializer_class = serializers.DropletResizeSerializer

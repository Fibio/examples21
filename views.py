from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, views, viewsets, exceptions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from acidatabase import models as aci_models
from acidatabase import serializers
from acidatabase.mixins import DataTableViewSetMixin


User = get_user_model()


class IncidentViewSet(DataTableViewSetMixin, viewsets.ModelViewSet):
    queryset = aci_models.Incident.objects.active()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.IncidentSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # Separate list view
    def get_serializer_class(self):
        if self.is_list:
            return serializers.IncidentListSerializer
        return serializers.IncidentSerializer

    def transform_ordering(self, ordering):
        ordering_str = ordering
        ordering = ordering.split(',')
        if 'long_id' in ordering_str:
            ordering = self.set_id_ordering(ordering)
        for name in ('status', 'origin'):
            if name in ordering_str:
                ordering = self.set_priority_ordering(ordering, name)
        return [name.strip() for name in ordering]

    def set_id_ordering(self, ordering, prefix=''):
        name = prefix + 'long_id'
        if name in ordering:
            index = ordering.index(name)
            ordering[index] = prefix + 'id_prefix'
            ordering.insert(index + 1, prefix + 'dj_id')
            return ordering
        return self.set_id_ordering(ordering, prefix='-')

    def set_priority_ordering(self, ordering, name, prefix=''):
        full_name = prefix + name
        if full_name in ordering:
            index = ordering.index(full_name)
            ordering[index] = "{}{}_priority".format(prefix, name)
            return ordering
        return self.set_priority_ordering(ordering, name, prefix='-')

    @detail_route(methods=['put', 'get'], url_path='finish-merge/(?P<pk2>[0-9]+)')
    def finish_merge(self, *args, **kwargs):
        """ Remove secondary case after merging """
        primary_case = self.get_object()
        secondary_case = self.get_queryset().filter(pk=kwargs['pk2']).first()
        if not secondary_case:
            return Response(status=status.HTTP_204_NO_CONTENT)

        with transaction.atomic():
            secondary_case.keyactivity_set.update(incident=primary_case)
            secondary_case.keydocument_set.update(incident=primary_case)
            primary_case.related_cases.add(*secondary_case.related_cases.all())
            secondary_case.delete()
        return Response({'finished': True})


class RelatedIncidentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = aci_models.Incident.objects.active().select_related(
        'primary_reporter', 'primary_incident_type', 'primary_involvement', 'resolution', 'status')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.RelatedIncidentSerializer


class IncidentMergeView(views.APIView):
    queryset = aci_models.Incident.objects.active().select_related(
        'primary_reporter', 'primary_incident_type', 'primary_involvement', 'resolution', 'status')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.IncidentSerializer

    def get(self, *args, **kwargs):
        main_case = self.validate_incident(int(kwargs.get('pk1')))
        secondary_case = self.validate_incident(int(kwargs.get('pk2')))
        main_case = self.serializer_class(main_case).data
        secondary_case = self.serializer_class(secondary_case).data

        for field in ('related_cases', 'suspects', 'reporters', 'animals', 'incident_type', 'involvement'):
            main_case[field] = self.merge_lists(main_case[field], secondary_case[field])
        for field in ('author', 'is_highlighted', 'primary_suspect', 'primary_reporter', 'status',
                      'resolution', 'primary_incident_type', 'primary_involvement', 'origin'):
            main_case[field] = self.merge_simple_value(main_case[field], secondary_case[field])

        self.merge_location(main_case, secondary_case)
        self.set_dates(main_case, secondary_case, 'created')

        main_case['notes'] = '{} {}'.format(main_case['notes'], secondary_case['notes']).strip() or ''
        return Response(main_case)

    def validate_incident(self, pk):
        incident = self.queryset.filter(pk=pk).first()
        if not incident:
            raise exceptions.NotFound('Incident with id=%s does not exist' % str(pk))
        return incident

    def merge_simple_value(self, main_value, secondary_value):
        # return first not null
        return main_value or secondary_value

    def merge_lists(self, main_values, secondary_values):
        ids = [el.get('id') for el in main_values]
        for value in secondary_values:
            if value['id'] not in ids:
                main_values.append(value)
        return main_values

    def merge_location(self, main_case, secondary_case):
        location_fields = ('location_desc', 'street', 'city', 'state', 'zip_code', 'county', 'jurisdictional_agency')
        location_exists = [main_case[field] for field in location_fields if main_case[field]]
        if not location_exists:
            for field in location_fields:
                if secondary_case[field]:
                    main_case[field] = secondary_case[field]
        return main_case

    def set_dates(self, main_case, secondary_case, field):
        main_date = parse(main_case[field])
        secondary_date = parse(secondary_case[field])
        if secondary_date < main_date:
            main_case[field] = secondary_case[field]
        return main_case

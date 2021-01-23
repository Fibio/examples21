import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete, pre_delete, m2m_changed
from django.dispatch import receiver

import myproject.search_indexes as idx

from .models import Incident, Suspect, Reporter, IncidentType, Involvement
from .utils import get_all_fks


log = logging.getLogger(__name__)

User = get_user_model()

INCIDENT_FK_MODELS = get_all_fks(Incident)
SUSPECT_FK_MODELS = get_all_fks(Suspect)


RELATED_MAPPING = {
    "suspect": ("primary_suspect", "suspects", "primary_suspect"),
    "reporter": ("primary_reporter", "reporters", "primary_reporter"),
    "incidenttype": ("primary_incident_type", "incident_type", "primary_incident_type"),
    "involvement": ("incidents", "involvement", "primary_involvement"),
}


def is_important_change(**kwargs):
    """ To skip last_login changes in usermodel
    """
    update_fields = kwargs.get('update_fields')
    if not update_fields:
        return False

    user_fields = set(['first_name', 'last_name', 'email', 'username'])
    if user_fields.intersection(update_fields):
        return True
    return False


@receiver(post_delete, sender=Incident)
@receiver(post_delete, sender=Suspect)
def index_related_instance_removed(sender, **kwargs):
    instance = kwargs['instance']
    cls_name = instance.__class__.__name__
    index_id = instance.get_index_id()
    idx.remove_index(getattr(idx, '{}TableIndex'.format(cls_name)), index_id)


@receiver(pre_delete, sender=Reporter)
@receiver(pre_delete, sender=Suspect)
@receiver(pre_delete, sender=IncidentType)
@receiver(pre_delete, sender=Involvement)
def update_related_incident(sender, **kwargs):
    instance = kwargs['instance']
    cls_name = instance.__class__.__name__.lower()
    related_name, qs_name, primary_name = RELATED_MAPPING.get(cls_name)
    for incident in getattr(instance, related_name).all():
        qs = getattr(incident, qs_name)
        if qs.count() > 1:
            setattr(incident, primary_name, qs.exclude(id=instance.id).first())
            incident.save(update_fields=[primary_name])


@receiver(post_save)
def index_related_instance_changed(sender, **kwargs):
    instance = kwargs['instance']
    if sender in (Incident, Suspect):
        cls_name = sender.__name__
        idx.update_index(getattr(idx, '{}TableIndex'.format(cls_name)), instance)
    elif sender in INCIDENT_FK_MODELS and (isinstance(sender, User) and is_important_change(**kwargs)):
        qs = instance.incident_set.search_index()
        idx.bulk_update_index(idx.IncidentTableIndex, qs)
    elif sender in SUSPECT_FK_MODELS:
        qs = instance.suspect_set.all()
        idx.bulk_update_index(idx.SuspectTableIndex, qs)


@receiver(m2m_changed, sender=Incident.reporters.through)
@receiver(m2m_changed, sender=Incident.suspects.through)
@receiver(m2m_changed, sender=Incident.incident_type.through)
@receiver(m2m_changed, sender=Incident.involvement.through)
def index_m2m_changed(sender, **kwargs):
    instance = kwargs['instance']
    idx.update_index(idx.IncidentTableIndex, instance)

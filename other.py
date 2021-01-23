# Just some code parts with no imports:


class EventFormView(PermissionRequiredMixin, PassOrgToFormViewMixin, UpdateView):
    pk_url_kwarg = 'slug'
    template_name = "events/event_form.html"
    permission_required = 'events.change_event'
    model = Event
    form_class = EventForm

    def form_valid(self, form):  # noqa
        context = self.get_context_data()
        event_formset = context['event_dates_formset']
        form.data = form.data.copy()

        # If the form and the formset are valid then proceed.
        if form.is_valid() and event_formset.is_valid():
            event = form.save()
            if form.cleaned_data.get('type') != Event.ONDEMAND:
                for formset in event_formset:
                    if formset.cleaned_data.get('DELETE'):
                        EventDates.objects.get(id=formset.cleaned_data['id'].id).delete()
                    else:
                        eventdates = formset.cleaned_data.get('date')
                        event_start = form.cleaned_data['event_start']
                        event_end = form.cleaned_data['event_end']
                        if event_start.date() <= eventdates <= event_end.date():
                            eventdates = formset.save(commit=False)
                            eventdates.event = event
                            eventdates.save()
                        else:
                            form.add_error(
                                None,
                                f"Date: {eventdates} - should not be bigger than "
                                f"Event Date/Time or Smaller than Event Start Date/Time")
                            return self.form_invalid(form)
                self.check_dates(event)
            if form.cleaned_data.get('sync_in_gc'):
                self.process_google_event(event)
            return super().form_valid(form)

        form.add_error(None, "There is something wrong!")
        return self.form_invalid(form)

    def form_invalid(self, form):
        render_form_errors(self.request, form)
        return super().form_invalid(form)

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.pk_url_kwarg)
        if slug is None:
            self.created = True
            return None
        self.created = False
        queryset = queryset or self.get_queryset()
        return get_object_or_404(queryset, slug=slug)



# decorators:

def organization_ownership(cls):
    """Limit response queryset per user.organization."""
    original = getattr(cls, 'get_queryset', None)
    if original:

        @wraps(cls.get_queryset, assigned=available_attrs(cls.get_queryset))
        def get_queryset_per_org(self):
            if is_banzai_admin(self.request.user):
                return original(self)
            return filter_by_org(original(self), self.request.user.userprofile.organization_id)

        cls.get_queryset = get_queryset_per_org
    else:
        raise ValueError('{} does not support get_queryset method'.format(cls.__name__))
    return cls


class RisksReport:
    risks_mapper = cfg.RISKS_MAPPER
    risks_text_mapper = cfg.RISKS_TEXT_MAPPER
    max_column_height = 290 - 40  # Max column height for risks graph - indicator box height in px

    def __init__(self, bmi):
        self.bmi = bmi
        self.is_risky = bmi > 23
        values = []
        for key, options in self.risks_mapper.items():
            value = options.get('func')(bmi)
            max_val = options.get('max')
            max_height = self.max_column_height

            values.append({
                "title": options.get("title"),
                "value": value,
                "bottom": (max_height * value) / max_val,
                **self.get_text(round(value / (max_val / 3) + 0.3), key)
            })
        self.values = values

    def __iter__(self):
        for value in self.values:
            yield value

    def get_text(self, value, name):
        for key in sorted(self.risks_text_mapper.keys()):
            if value > key:
                continue
            return self.risks_text_mapper.get(key)
        else:
            key = list(self.risks_text_mapper.keys())[-1]
            return self.risks_text_mapper.get(key)


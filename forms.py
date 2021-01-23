from django.core.exceptions import ValidationError
from django import forms


class OptionalChoiceWidget(forms.MultiWidget):
    template_name = 'common/widgets/optional_choice.html'

    def decompress(self, value):
        if value:
            if value in [x[0] for x in self.widgets[0].choices]:
                return [value, ""]
            return ["", value]
        return ["", ""]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        return context


class OptionalChoiceField(forms.MultiValueField):

    def __init__(self, choices, max_length=80, *args, **kwargs):
        choices = list(enumerate(choices, start=1))
        fields = (forms.ChoiceField(choices=choices, required=False),
                  forms.CharField(required=False))
        super(OptionalChoiceField, self).__init__(required=False, fields=fields)
        self.widget = OptionalChoiceWidget(widgets=[f.widget for f in fields])

    def compress(self, data_list):
        if not data_list:
            raise ValidationError('Need to select choice or enter text for this field')
        return data_list[0] or data_list[1]


class MultivalueChoiceField(forms.TypedMultipleChoiceField):

    def __init__(self, choices, *args, **kwargs):
        choices = list(enumerate(choices, start=1))
        choices.append(('', 'Other'))
        kwargs['choices'] = choices
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if value:
            choices = dict(self.choices)
            new_value = []
            for val in value:
                try:
                    choice = choices.get(int(val))
                except ValueError:
                    choice = val
                new_value.append(choice)
            return new_value
        return self.empty_value

    def prepare_value(self, value):
        if not value:
            return value

        choices = {val[1]: val[0] for val in self.choices}
        new_value = []
        for val in value:
            choice = choices.get(val)
            if not choice:
                self.choices[-1] = (val, 'Other')
                choice = val
            new_value.append(choice)
        return new_value


class Select2ModelChoiceField(forms.ChoiceField):

    def __init__(self, model, prepare_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.prepare_func = prepare_func

    def validate(self, value):
        """Validate that the input is in self.choices."""
        if value:
            value = self.model.objects.filter(pk=value).first()
            if value:
                return value
        raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice', params={'value': value})

    def clean(self, value):
        value = self.to_python(value)
        value = self.validate(value)
        self.run_validators(value)
        return value

    def prepare_value(self, value):
        if self.prepare_func:
            value = self.prepare_func(value)
            if value:
                self.choices = [value]
        return value

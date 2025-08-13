from django import forms
from .models import Application

class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None):
        final_attrs = {'style': 'width: 200px;'}
        if attrs:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)

class ApplicationAdminForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = '__all__'
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date'}),
            'to_date': forms.DateInput(attrs={'type': 'date'}),
            'total_days': forms.NumberInput(attrs={
                'readonly': 'readonly',  # makes field uneditable
                'style': 'background-color: #eee;'  # optional: style to indicate it's not editable
            }),
        }

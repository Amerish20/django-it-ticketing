from django import forms
from django.utils.safestring import mark_safe
from .models import Application

class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, attrs=None):
        final_attrs = {'style': 'width: 200px;'}
        if attrs:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)


class ApplicationAdminForm(forms.ModelForm):
    application_id_rejoin = forms.ChoiceField(required=False, label=mark_safe("Application ID Rejoin"))
    class Meta:
        model = Application
        fields = '__all__'
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date'}),
            'to_date': forms.DateInput(attrs={'type': 'date'}),
            'rejoin_date': forms.DateInput(attrs={'type': 'date'}),
            'total_days': forms.NumberInput(attrs={
                'readonly': 'readonly',  # makes field uneditable
                'style': 'background-color: #eee;'  # optional: style to indicate it's not editable
            }),
            'delayed_days': forms.NumberInput(attrs={
                'readonly': 'readonly',  # makes field uneditable
                'style': 'background-color: #eee;'  # optional: style to indicate it's not editable
            }),
            'total_days_after_rejoin': forms.NumberInput(attrs={
                'readonly': 'readonly',  # makes field uneditable
                'style': 'background-color: #eee;'  # optional: style to indicate it's not editable
            }),
            
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate dropdown safely — only if model is fully loaded
        try:
            approved_apps = Application.objects.filter(
                status='Approved',
                delete_status=False,
                request_form_id=1
            ).order_by('-id')

            choices = [('', '---------')]
            for app in approved_apps:
                label = f"ID {app.id} — {app.user} ({app.from_date} → {app.to_date})"
                choices.append((str(app.id), label))

            self.fields['application_id_rejoin'].choices = choices
        except Exception as e:
            print("Error loading approved applications:", e)

        
    

from django import forms
from .models import PlayerMetric, PlayerProfile
from allauth.account.forms import SignupForm

class PlayerMetricForm(forms.ModelForm):
    class Meta:
        model = PlayerMetric
        fields = ['metricType', 'metric', 'ageCaptured', 'dateCaptured', 'notes']
        widgets = {
            'metricType': forms.Select(attrs={'class': 'form-control'}),
            'metric': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter metric value (e.g., 85.5)',
                'step': '0.01',
                'min': '0',
                'oninput': 'validateNumeric(this)'
            }),
            'ageCaptured': forms.Select(attrs={'class': 'form-control'}),
            'dateCaptured': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this metric...',
                'maxlength': '500'
            }),
        }


class CaptureForm(forms.Form):
    """Form for capturing multiple metrics at once"""
    
    # Common fields for all metrics
    ageCaptured = forms.IntegerField(
        widget=forms.Select(choices=[(i, str(i)) for i in range(12, 21)], attrs={'class': 'form-control'}),
        label='Age Captured',
        help_text='Select your age (12-20)'
    )
    dateCaptured = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date Captured',
        required=True,
        help_text='When were these metrics recorded?'
    )
    capturedBy = forms.ChoiceField(
        choices=[
            ('perfect_game', 'Perfect Game'),
            ('player_metrix', 'Player Metrix'),
            ('prep_baseball', 'Prep Baseball'),
            ('self_captured', 'Self Captured'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Captured By',
        required=False,
        help_text='Who captured these metrics?'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes about these metrics...', 'maxlength': '500'}),
        label='Notes',
        required=False,
        max_length=500,
        help_text='Optional notes about these metrics'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add metric fields for each metric type
        for metric_type, display_name in PlayerMetric.METRIC_TYPE_CHOICES:
            field_name = f'metric_{metric_type}'
            self.fields[field_name] = forms.DecimalField(
                widget=forms.TextInput(attrs={
                    'class': 'form-control metric-input',
                    'placeholder': f'Enter {display_name.lower()}',
                    'pattern': r'^\d+(\.\d{1,2})?$',
                    'title': 'Enter a number with up to 2 decimal places'
                }),
                label=display_name,
                required=False,
                max_digits=8,
                decimal_places=2
            )


class PlayerSignupForm(SignupForm):
    position = forms.CharField(max_length=50, required=False)
    graduation_year = forms.IntegerField(required=False)
    
    def save(self, request):
        user = super().save(request)
        user.player_profile.position = self.cleaned_data.get('position')
        user.player_profile.graduation_year = self.cleaned_data.get('graduation_year')
        user.player_profile.save()
        return user


class PlayerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    # Allow image upload in the form; will be saved to the model ImageField
    picture = forms.ImageField(required=False)

    class Meta:
        model = PlayerProfile
        fields = ['first_name', 'last_name', 'position', 'team', 'school', 'graduation_year', 'height_inches', 'weight_lbs', 'city', 'state', 'throws', 'hits', 'picture', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'team': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'height_inches': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight_lbs': forms.NumberInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'throws': forms.Select(attrs={'class': 'form-control'}),
            'hits': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'height_inches': 'Height (inches)',
            'weight_lbs': 'Weight (lbs)',
            'graduation_year': 'Graduation Year'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.user:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.save()
        if commit:
            profile.save()
        return profile

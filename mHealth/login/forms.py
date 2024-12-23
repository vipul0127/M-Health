from django import forms
from .models import ExcelFile
from django import forms
from django.contrib.auth.models import User
from django.core.validators import EmailValidator

from django import forms
from django.core.exceptions import ValidationError
from .models import User  # Assuming you're using a custom User model

class ExcelFileForm(forms.ModelForm):
    class Meta:
        model = ExcelFile
        fields = ['name', 'file']

# forms.py
from django import forms
from .models import Contact



class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your Message'}),
        }


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    # Additional health-related fields
    age = forms.IntegerField(label="Age", required=True)
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = forms.ChoiceField(choices=gender_choices, required=True)

    height = forms.FloatField(label="Height (in cm)", required=True)
    weight = forms.FloatField(label="Weight (in kg)", required=True)

    # Cardiovascular health
    cardiovascular_conditions_choices = [
        ('Hypertension', 'Hypertension (High Blood Pressure)'),
        ('Hypotension', 'Hypotension (Low Blood Pressure)'),
        ('Arrhythmia', 'Arrhythmia (Irregular Heartbeat)'),
        ('None', 'No cardiovascular conditions'),
        ('Other', 'Other'),
    ]
    cardiovascular_conditions = forms.MultipleChoiceField(
        choices=cardiovascular_conditions_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    cardiovascular_other = forms.CharField(max_length=100, required=False, label="Other cardiovascular conditions")

    cardiovascular_symptoms_choices = [
        ('Chest Pain', 'Chest Pain'),
        ('Shortness of Breath', 'Shortness of Breath'),
        ('Palpitations', 'Palpitations'),
        ('Dizziness', 'Dizziness'),
        ('None', 'No symptoms'),
        ('Other', 'Other'),
    ]
    cardiovascular_symptoms = forms.MultipleChoiceField(
        choices=cardiovascular_symptoms_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    cardiovascular_symptoms_other = forms.CharField(max_length=100, required=False, label="Other cardiovascular symptoms")

    # Metabolic health
    metabolic_conditions_choices = [
        ('Type 1 Diabetes', 'Type 1 Diabetes'),
        ('Type 2 Diabetes', 'Type 2 Diabetes'),
        ('Prediabetes', 'Prediabetes'),
        ('None', 'No metabolic conditions'),
        ('Other', 'Other'),
    ]
    metabolic_conditions = forms.MultipleChoiceField(
        choices=metabolic_conditions_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    metabolic_other = forms.CharField(max_length=100, required=False, label="Other metabolic conditions")

    # Mental and emotional health
    mental_health_conditions_choices = [
        ('Anxiety', 'Anxiety Disorder'),
        ('Depression', 'Depression'),
        ('Panic', 'Panic Disorder'),
        ('None', 'No mental health conditions'),
        ('Other', 'Other'),
    ]
    mental_health_conditions = forms.MultipleChoiceField(
        choices=mental_health_conditions_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    mental_health_other = forms.CharField(max_length=100, required=False, label="Other mental health conditions")

    stress_level_choices = [
        ('Never', 'Never'),
        ('Rarely', 'Rarely'),
        ('Occasionally', 'Occasionally'),
        ('Frequently', 'Frequently'),
        ('Always', 'Always'),
    ]
    stress_level = forms.ChoiceField(choices=stress_level_choices, required=True, label="How often do you experience high levels of stress?")

    # Lifestyle factors
    lifestyle_factors_choices = [
        ('Smoker', 'Current or past smoker'),
        ('Alcohol', 'Regular alcohol consumption'),
        ('Sedentary', 'Sedentary lifestyle (little to no physical activity)'),
        ('Active', 'Regular physical activity (at least 3 times per week)'),
        ('None', 'No significant lifestyle factors'),
        ('Other', 'Other'),
    ]
    lifestyle_factors = forms.MultipleChoiceField(
        choices=lifestyle_factors_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    lifestyle_other = forms.CharField(max_length=100, required=False, label="Other lifestyle factors")

    # Sleep patterns
    sleep_hours_choices = [
        ('Less than 5 hours', 'Less than 5 hours'),
        ('5-6 hours', '5-6 hours'),
        ('7-9 hours', '7-9 hours'),
        ('More than 10 hours', 'More than 10 hours'),
    ]
    sleep_hours = forms.ChoiceField(choices=sleep_hours_choices, required=True, label="How many hours of sleep do you typically get per night?")

    sleep_disorders_choices = [
        ('Insomnia', 'Insomnia'),
        ('Sleep Apnea', 'Sleep Apnea'),
        ('None', 'No sleep disorders'),
        ('Other', 'Other'),
    ]
    sleep_disorders = forms.MultipleChoiceField(
        choices=sleep_disorders_choices, widget=forms.CheckboxSelectMultiple(), required=False
    )
    sleep_disorders_other = forms.CharField(max_length=100, required=False, label="Other sleep disorders")

    # Recent medical history
    last_medical_checkup_choices = [
        ('Within the last year', 'Within the last year'),
        ('1-2 years ago', '1-2 years ago'),
        ('More than 2 years ago', 'More than 2 years ago'),
    ]
    last_medical_checkup = forms.ChoiceField(choices=last_medical_checkup_choices, required=True, label="When was your last full medical check-up?")
    health_concerns = forms.CharField(max_length=100, required=False, label="Health concerns identified during the last check-up")

    class Meta:
        model = User  # Use your custom User model here
        fields = ['username', 'email', 'password1', 'password2', 'age', 'gender', 'height', 'weight']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data






# forms.py

from django import forms
from .models import ParticipantConsent

class ConsentForm(forms.ModelForm):
    class Meta:
        model = ParticipantConsent
        fields = [
            'age', 'gender', 'height', 'weight',
            'respiratory_conditions', 'cardiovascular_conditions',
            'cardiovascular_symptoms', 'metabolic_conditions',
            'mental_health_conditions', 'stress_level', 'lifestyle_factors',
            'sleep_hours', 'sleep_disorders', 'last_medical_checkup', 'health_concerns'
        ]
        widgets = {
            'respiratory_conditions': forms.CheckboxSelectMultiple(),
            'cardiovascular_conditions': forms.CheckboxSelectMultiple(),
            'cardiovascular_symptoms': forms.CheckboxSelectMultiple(),
            'metabolic_conditions': forms.CheckboxSelectMultiple(),
            'mental_health_conditions': forms.CheckboxSelectMultiple(),
            'lifestyle_factors': forms.CheckboxSelectMultiple(),
            'sleep_disorders': forms.CheckboxSelectMultiple(),
        }



from django import forms

from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(
        label="Title",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter title for your Google Sheet'
        }),
        help_text='Enter a title for your Google Sheet (Eg. Patient_Name)'
    )
    google_sheet_url = forms.URLField(
        label="Google Sheet URL",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Google Sheet URL'
        }),
        help_text='Enter a valid Google Sheet URL (e.g., https://docs.google.com/spreadsheets/d/...)'
    )

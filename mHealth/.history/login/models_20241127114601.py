from django.db import models

class ExcelFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


from django.db import models
from django.contrib.auth.models import User
import random

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        otp = str(random.randint(100000, 999999))
        self.otp_code = otp
        self.save()
        return otp


from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} at {self.timestamp}"



# models.py

from django.db import models

class ParticipantConsent(models.Model):
    unique_id = models.AutoField(primary_key=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    height = models.FloatField()
    weight = models.FloatField()
    
    respiratory_conditions = models.CharField(max_length=255, blank=True, null=True)
    cardiovascular_conditions = models.CharField(max_length=255, blank=True, null=True)
    cardiovascular_symptoms = models.CharField(max_length=255, blank=True, null=True)
    metabolic_conditions = models.CharField(max_length=255, blank=True, null=True)
    mental_health_conditions = models.CharField(max_length=255, blank=True, null=True)
    stress_level = models.CharField(max_length=50)
    
    lifestyle_factors = models.CharField(max_length=255, blank=True, null=True)
    sleep_hours = models.CharField(max_length=50)
    sleep_disorders = models.CharField(max_length=255, blank=True, null=True)
    
    last_medical_checkup = models.CharField(max_length=50)
    health_concerns = models.CharField(max_length=255, blank=True, null=True)

    date_submitted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Participant {self.unique_id}"
        
from django.db import models
from django.contrib.auth.models import User  # Import User model

from django.db import models
from django.contrib.auth.models import User

class GoogleSheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to User model
    sheet_url = models.URLField()
    title = models.CharField(max_length=255,default=)  # New title attribute
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.sheet_url}"


# models.py
from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"







from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    form_submitted = models.BooleanField(default=False)

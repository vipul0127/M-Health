
from django.contrib.auth.models import User
from django.core.validators import EmailValidator, ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
from django.http import HttpResponse
import csv
from django.http import HttpResponse
import io
import requests
from .models import ExcelFile
from django.http import HttpResponse

# views.py

from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.urls import reverse_lazy

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

def test_session(request):
    if 'visited' in request.session:
        request.session['visited'] += 1
    else:
        request.session['visited'] = 1
    return HttpResponse(f"Number of visits: {request.session['visited']}")

def generate_hl7(request):
    # URL of the file in the GitHub repository
    file_url = 'https://raw.githubusercontent.com/sakethwithanh/mHealth-frontend/main/AHLSAM018434.csv'

    try:
        # Download the file and save it as a string
        csv_file_content = requests.get(file_url).text

        # Read data from CSV content directly
        csv_reader = csv.DictReader(csv_file_content.splitlines())
        dataset = list(csv_reader)

        # Create an HL7 message template (MSH segment)
        hl7_message = (
            "MSH|^~\\&|YourApp|YourFacility|HL7Server|HL7Server|20230908170000||ORU^R01|123456|P|2.5|||\n"
        )

        # Iterate through the dataset and create an HL7 message for each record
        for record in dataset:
            # Create a new HL7 message for each record
            hl7_message += f"PID|1||{record['Time']}||{record['Sleep']}|||\n"

            # OBX segment for GSR
            obx_gsr = (
                f"OBX|1|NM|GSR^Galvanic Skin Response^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['GSR']}\n"
            )
            hl7_message += obx_gsr

            # OBX segment for CBT
            obx_cbt = (
                f"OBX|2|NM|CBT^Core Body Temperature^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['CBT(degC)']}\n"
            )
            hl7_message += obx_cbt

            # OBX segment for PPG
            obx_ppg = (
                f"OBX|3|NM|PPG^Photoplethysmogram^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['PPG']}\n"
            )
            hl7_message += obx_ppg

            # OBX segment for ECG
            obx_ecg = (
                f"OBX|4|NM|ECG^Electrocardiogram^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['ECG']}\n"
            )
            hl7_message += obx_ecg

        # Set the proper content type for plain text
        response = HttpResponse(hl7_message, content_type='text/plain')
        
        # Set the Content-Disposition header to inline
        response['Content-Disposition'] = 'inline; filename="hl7_messages.hl7"'
        
        return response

    except requests.exceptions.RequestException as e:
        # Handle the exception (print/log the error, return an appropriate response, etc.)
        print(f"Error fetching data from GitHub: {e}")
        return HttpResponse("Internal Server Error", status=500)
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from .models import GoogleSheet  # Assuming you have a GoogleSheet model
import csv

def view_hl7(request, file_id):
    # Fetch the GoogleSheet object
    google_sheet = get_object_or_404(GoogleSheet, id=file_id)

    # Set up Google Sheets API credentials
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/krishbhoruka/Downloads/mHealth/credentials.json', scope)  # Replace with your credentials file path
    client = gspread.authorize(creds)

    # Open the Google Sheet by URL
    try:
        sheet = client.open_by_url(google_sheet.sheet_url).sheet1  # Open the first sheet
        rows = sheet.get_all_records()  # Fetch all rows as dictionaries
    except Exception as e:
        return HttpResponse(f"Error accessing Google Sheet: {e}", status=500)

    # Initialize HL7 message template (MSH segment)
    hl7_message = (
        "MSH|^~\\&|YourApp|YourFacility|HL7Server|HL7Server|20230908170000||ORU^R01|123456|P|2.5|||\n"
    )

    # Process the Google Sheets data
    for row in rows:
        if 'Time' in row and 'PPG' in row and 'ECG' in row and 'CBT(degC)' in row and 'GSR' in row:
            time = row['Time']
            sleep = row.get('Sleep', '')  # Use .get() to handle missing values
            ppg = row['PPG']
            ecg = row['ECG']
            gsr = row['GSR']
            cbt = row['CBT(degC)']

            # Create HL7 segments for the extracted data
            hl7_message += f"PID|1||{time}||{sleep}|||\n"
            hl7_message += f"OBX|1|NM|GSR^Galvanic Skin Response^HL7|||{time}|||||AmplitudeData^{time}^Units|{gsr}\n"
            hl7_message += f"OBX|2|NM|CBT^Core Body Temperature^HL7|||{time}|||||AmplitudeData^{time}^Units|{cbt}\n"
            hl7_message += f"OBX|3|NM|PPG^Photoplethysmogram^HL7|||{time}|||||AmplitudeData^{time}^Units|{ppg}\n"
            hl7_message += f"OBX|4|NM|ECG^Electrocardiogram^HL7|||{time}|||||AmplitudeData^{time}^Units|{ecg}\n"

    # Return the HL7 data as plain text in the browser
    context = {'hl7_message': hl7_message}
    return render(request, 'hl7_display.html', context)


def download_hl7(request):
    # URL of the file in the GitHub repository
    file_url = 'https://raw.githubusercontent.com/sakethwithanh/mHealth-frontend/main/AHLSAM018434.csv'

    try:
        # Download the file and save it as a string
        csv_file_content = requests.get(file_url).text

        # Read data from CSV content directly
        csv_reader = csv.DictReader(csv_file_content.splitlines())
        dataset = list(csv_reader)

        # Create an HL7 message template (MSH segment)
        hl7_message = (
            "MSH|^~\\&|YourApp|YourFacility|HL7Server|HL7Server|20230908170000||ORU^R01|123456|P|2.5|||\n"
        )

        # Iterate through the dataset and create an HL7 message for each record
        for record in dataset:
            # Create a new HL7 message for each record
            hl7_message += f"PID|1||{record['Time']}||{record['Sleep']}|||\n"

            # OBX segment for GSR
            obx_gsr = (
                f"OBX|1|NM|GSR^Galvanic Skin Response^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['GSR']}\n"
            )
            hl7_message += obx_gsr

            # OBX segment for CBT
            obx_cbt = (
                f"OBX|2|NM|CBT^Core Body Temperature^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['CBT(degC)']}\n"
            )
            hl7_message += obx_cbt

            # OBX segment for PPG
            obx_ppg = (
                f"OBX|3|NM|PPG^Photoplethysmogram^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['PPG']}\n"
            )
            hl7_message += obx_ppg

            # OBX segment for ECG
            obx_ecg = (
                f"OBX|4|NM|ECG^Electrocardiogram^HL7|||{record['Time']}|||||AmplitudeData^{record['Time']}^Units|{record['ECG']}\n"
            )
            hl7_message += obx_ecg

        # Set the proper content type for plain text
        response = HttpResponse(hl7_message, content_type='text/plain')
        
        # Set the Content-Disposition header to trigger download
        response['Content-Disposition'] = 'attachment; filename="hl7_messages.hl7"'
        
        return response

    except requests.exceptions.RequestException as e:
        # Handle the exception (print/log the error, return an appropriate response, etc.)
        print(f"Error fetching data from GitHub: {e}")
        return HttpResponse("Internal Server Error", status=500)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pandas as pd

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import gspread
from oauth2client.service_account import ServiceAccountCredentials




from django.shortcuts import render, redirect
from .forms import ExcelFileForm

from django.shortcuts import render, redirect


from django.shortcuts import render, redirect
from .forms import ExcelFileForm

def upload_success(request):
    return render(request, 'upload_success.html')
from django.shortcuts import render
from .models import ExcelFile

# views.py
from django.shortcuts import render, get_object_or_404
from .models import ExcelFile

def SheetPage(request, id):
    file = get_object_or_404(ExcelFile, id=id)
    # Pass the file to the template or perform other logic
    return render(request, 'sheet.html', {'file': file})

from django.shortcuts import render
from .models import ExcelFile

import pandas as pd
from django.shortcuts import render
from .models import ExcelFile
from .forms import UploadFileForm

from django.shortcuts import render
from .models import ExcelFile

def home_view(request):
    # Retrieve all ExcelFile objects
    excel_files = ExcelFile.objects.all()

    # Pass the data to the template
    context = {
        'excel_files': excel_files,
    }
    return render(request, 'home.html', context)

# views.py
from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import ExcelFile
import re
from .models import GoogleSheet
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Utility function to extract Google Sheet ID from URL
def extract_sheet_id(sheet_url):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if match:
        return match.group(1)
    return None



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
import random
import json
import random
import json
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import EmailValidator
from django.http import JsonResponse

from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import OTP
from django.contrib import messages
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .models import User, OTP

from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import User, OTP

from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages


from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from login.models import ParticipantConsent  # Adjust this import based on your app structure
import random

from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import random
import json
import os
import random
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.http import JsonResponse
from .models import UserProfile  # Import UserProfile model

def signup(request):
    if request.method == 'POST':
        # Basic signup fields
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Check if all required fields are filled
        if not all([username, email, password1, password2]):
            messages.error(request, "All required fields must be filled.")
            return render(request, 'signup.html')

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email address.")
            return render(request, 'signup.html')

        # Check if the username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'signup.html')

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        try:
            # Store user details in the session for OTP verification
            request.session['username'] = username
            request.session['email'] = email
            request.session['password1'] = password1

            # Generate and send OTP
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp

            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                'vipulkhosya00007@gmail.com',  # Replace with your sending email
                [email],
                fail_silently=False,
            )

            return redirect('verify_otp')  # Redirect to OTP verification
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return render(request, 'signup.html')

    return render(request, 'signup.html')

# views.py - Updated to redirect to login page

def verify_otp(request):
    if request.method == 'POST':
        # Get data from form or JSON request
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            entered_otp = data.get('otp')
            username = data.get('username')
            email = data.get('email')
            password = data.get('password1')
        else:
            entered_otp = request.POST.get('otp')
            username = request.session.get('username')
            email = request.session.get('email')
            password = request.session.get('password1')
        
        # Get OTP from session
        session_otp = request.session.get('otp')
        
        # Check if OTP matches
        if not session_otp:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'OTP session expired. Please request a new OTP'})
            messages.error(request, "OTP session expired. Please request a new OTP")
            return render(request, 'verify_otp.html')
        
        # Convert both to strings for comparison and check equality
        if str(entered_otp) == str(session_otp):
            try:
                # Check if user already exists (additional security check)
                if User.objects.filter(username=username).exists():
                    if request.headers.get('Content-Type') == 'application/json':
                        return JsonResponse({'success': False, 'message': 'Username already exists'})
                    messages.error(request, "Username already exists.")
                    return render(request, 'verify_otp.html')
                
                if User.objects.filter(email=email).exists():
                    if request.headers.get('Content-Type') == 'application/json':
                        return JsonResponse({'success': False, 'message': 'Email already exists'})
                    messages.error(request, "Email already exists.")
                    return render(request, 'verify_otp.html')
                
                # Create the user ONLY after successful OTP verification
                user = User.objects.create_user(username=username, email=email, password=password)
                
                # Create a user-specific folder
                base_user_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
                user_folder = os.path.join(base_user_dir, username)
                
                if not os.path.exists(user_folder):
                    os.makedirs(user_folder)
                
                # Clear session data after successful signup
                request.session.pop('otp', None)
                request.session.pop('username', None)
                request.session.pop('email', None)
                request.session.pop('password1', None)
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': True, 'message': 'Account created successfully', 'redirect': '/login/'})
                
                messages.success(request, "Account created successfully! Please login with your credentials.")
                return redirect('login')  # Redirect to login page instead of dashboard
                
            except Exception as e:
                print(f"Error creating user: {str(e)}")  # Add server-side logging
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'message': f'Error during user creation: {str(e)}'})
                messages.error(request, f"Error during user creation: {str(e)}")
                return render(request, 'verify_otp.html')
        else:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'verify_otp.html')
    
    return render(request, 'verify_otp.html')
def send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            username = data.get('username')

            # Validate email format
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'message': 'Invalid email address'})

            # Check if the email or username is already registered
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email is already registered'})

            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username is already taken'})

            # Generate and save OTP
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            request.session['email'] = email
            request.session['username'] = username

            # Send OTP via email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                'vipulkhosya00007@gmail.com',  # Replace with your sending email
                [email],
                fail_silently=False,
            )

            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request format'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home if login is successful
        else:



            
            messages.error(request, 'Invalid username or password')  # Show error message on invalid login
    
    return render(request, 'login.html')  # Render the login template

def LogoutPage(request):
    logout(request)
    return redirect('welcome')



def SheetPage(request):
    return render(request, 'sheets.html')

# views.py

def download_csv_data(request):
    # Replace this with your logic to fetch data from the Google Sheet
    # For example, you can use gspread library or any other method to get the data
    sheet_data = [
        ["Header1", "Header2", "Header3"],
        ["Data1", "Data2", "Data3"],
        # Add more rows as needed
    ]

    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="google_sheet_data.csv"'

    # Create a CSV writer and write the data to the response
    csv_writer = csv.writer(response)
    for row in sheet_data:
        csv_writer.writerow(row)

    return response



from django.shortcuts import render, get_object_or_404
from .models import ExcelFile

from django.contrib.auth.decorators import login_required
from .models import GoogleSheet

@login_required
def view_files(request):
    # Debugging line to verify if user is superuser
    print(f"User: {request.user.username}, Superuser: {request.user.is_superuser}")

    if request.user.is_superuser:
        # Superuser can see all Google Sheets along with the uploader's name
        google_sheets = GoogleSheet.objects.select_related('user').all()
    else:
        # Regular users see only their own files
        google_sheets = GoogleSheet.objects.filter(user=request.user)

    return render(request, 'view_files.html', {'google_sheets': google_sheets})







import pandas as pd
from django.shortcuts import render, get_object_or_404
from .models import ExcelFile
import pandas as pd
from django.shortcuts import render, get_object_or_404
from .models import ExcelFile

import pandas as pd
from django.shortcuts import render
from .models import ExcelFile

def view_ppg(request, file_id):
    
        # Retrieve the ExcelFile object
    excel_file = ExcelFile.objects.get(id=file_id)
        
        # Read the CSV file
    df = pd.read_csv(excel_file.file.path)
        
        # Convert the DataFrame to a dictionary for easier use in the template
    data = df.to_dict(orient='records')
        
        # Pass the data to the template
    context = {
        'data': data,
    }
    return render(request, 'view_ppg.html', context)
        
   




import matplotlib.pyplot as plt
from django.http import HttpResponse
import pandas as pd
from .models import ExcelFile

import pandas as pd
import matplotlib.pyplot as plt
import io
from django.http import HttpResponse
from .models import ExcelFile
from django.shortcuts import get_object_or_404
# views.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.shortcuts import render
import pandas as pd
import plotly.express as px
from django.http import JsonResponse
import csv
from django.shortcuts import render
from django.http import HttpResponse
from .models import ExcelFile

import csv
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.http import HttpResponse
from .models import ExcelFile
import io
import urllib, base64

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from plotly.offline import plot
import plotly.graph_objs as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta
from .models import GoogleSheet

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from plotly.offline import plot
import plotly.graph_objs as go
import statistics
from datetime import timedelta
import time

from .models import GoogleSheet  # Assuming GoogleSheet is a Django model in your app

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
from plotly.offline import plot
from datetime import timedelta
import statistics



from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from plotly.offline import plot
import statistics
from datetime import timedelta
from datetime import datetime, time, timedelta

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime, timedelta, time
import statistics
import plotly.graph_objects as go
from plotly.offline import plot
from scipy.signal import find_peaks
import numpy as np
from .models import GoogleSheet

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
from datetime import datetime
import logging


def access_excel(request):
    # Google Sheets API setup
    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)  # Update with your credentials file path
    client = gspread.authorize(creds)

    # Access the Google Sheet
    sheet = client.open_by_key('2PACX-1vRaQsqTs4elSrtWoSdwsfSTUm_-zF2kWFtmoFGtvEK5ftqnRxKgbRMB07TUyF3oKv7rwpOvdaDS1LDj')  # Replace with your Google Sheet ID
    worksheet = sheet.worksheet('graph')  # Update with the sheet name if different

    # Fetch data from specific columns
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    # Ensure the columns exist
    if 'PPG' in df.columns and 'Time' in df.columns:
        # Create a Plotly line chart
        fig = px.line(df, x='Time', y='PPG', title='PPG vs Time')

        # Convert plot to JSON for frontend rendering
        graph_json = fig.to_json()

        return render(request, 'access_excel.html', {'graph_json': graph_json})
    else:
        return render(request, 'access_excel.html', {'error': 'Required columns PPG and Time not found in the sheet.'})

def time_to_seconds(time_str):

    try:
        if not time_str or not isinstance(time_str, str):
            return None
        
        # Split into hours, minutes, and seconds (with potential milliseconds)
        time_parts = time_str.split(':')
        if len(time_parts) != 3:  # Must have exactly HH:MM:SS format
            return None
            
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        
        # Handle seconds and milliseconds
        if '.' in time_parts[2]:  # Has milliseconds
            seconds_str, millis_str = time_parts[2].split('.')
            # Ensure milliseconds are properly padded to 3 digits
            millis_str = millis_str.ljust(3, '0')[:3]  # Pad with zeros and take first 3 digits
            seconds = int(seconds_str)
            milliseconds = int(millis_str)
        else:  # No milliseconds
            seconds = int(time_parts[2])
            milliseconds = 0
            
        # Validate ranges
        if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 
                0 <= seconds <= 59 and 0 <= milliseconds <= 999):
            return None
            
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        
    except (ValueError, IndexError, AttributeError):
        return None

def format_time_with_ms(seconds):
    try:
        if seconds is None or seconds < 0:
            return None
            
        # Extract hours, minutes, seconds, and milliseconds
        total_seconds = int(seconds)
        milliseconds = int((seconds % 1) * 1000)  # Get milliseconds with proper rounding
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        # Ensure hours don't exceed 24
        if hours >= 24:
            hours = hours % 24
            
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
        
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return None

import plotly.graph_objects as go
from plotly.offline import plot
from datetime import datetime, time

def create_graph(time_data, ppg_data, day_number):
    """Create a Plotly graph with independent axis zooming control for time series PPG data."""
    if not time_data or not ppg_data:
        return "<div>No data available for the selected time range.</div>"

    fig = go.Figure()
    
    # Convert string times to datetime objects
    x_times = []
    y_values = []
    
    for t, v in zip(time_data, ppg_data):
        try:
            if '.' in t:
                time_parts, ms = t.split('.')
                h, m, s = map(int, time_parts.split(':'))
                ms = int(ms)
                x_times.append(datetime.combine(
                    datetime.today().date(),
                    time(h, m, s, ms * 1000)  # Convert ms to microseconds
                ))
                y_values.append(v)
            else:
                time_parts = t.split(':')
                if len(time_parts) == 3:
                    h, m, s = map(int, time_parts)
                    x_times.append(datetime.combine(
                        datetime.today().date(),
                        time(h, m, s)
                    ))
                    y_values.append(v)
        except Exception:
            continue

    fig.add_trace(go.Scatter(
        x=x_times,
        y=y_values,
        mode='lines',
        name=f'Day {day_number} PPG Data',
        line=dict(color='#007bff', width=1),
        hovertemplate='Time: %{x|%H:%M:%S.%L}<br>PPG: %{y:.2f}<extra></extra>'
    ))

    # Calculate y-axis range with padding to avoid extreme zooming issues
    if y_values:
        y_min = min(y_values)
        y_max = max(y_values)
        y_range = y_max - y_min
        y_padding = y_range * 0.1  # 10% padding
        y_min_display = y_min - y_padding
        y_max_display = y_max + y_padding
    else:
        y_min_display = 0
        y_max_display = 1

    # Create range selector buttons for x-axis
    x_rangeselector = dict(
        buttons=list([
            dict(count=15, label="15m", step="minute", stepmode="backward"),
            dict(count=30, label="30m", step="minute", stepmode="backward"),
            dict(count=1, label="1h", step="hour", stepmode="backward"),
            dict(count=3, label="3h", step="hour", stepmode="backward"),
            dict(count=6, label="6h", step="hour", stepmode="backward"),
            dict(step="all", label="All")
        ]),
        font=dict(size=10),
        bgcolor="rgba(150, 200, 250, 0.4)",
        activecolor="rgba(0, 123, 255, 0.9)",
        x=0.01,
        y=1.1,
    )

    # Dynamic tick formatting for different zoom levels
    tickformatstops = [
        dict(dtickrange=[None, 1000], value="%H:%M:%S.%L"),  # Milliseconds when zoomed in
        dict(dtickrange=[1000, 60000], value="%H:%M:%S"),     # Seconds when zoomed out a bit
        dict(dtickrange=[60000, 3600000], value="%H:%M"),     # Minutes when zoomed further
        dict(dtickrange=[3600000, None], value="%H:%M")       # Hours when fully zoomed out
    ]

    # Create Y-axis adjustment buttons
    y_buttons = [
        # Show full range
        dict(
            args=[{'yaxis.range': [y_min_display, y_max_display]}],
            label="Full Y Range",
            method="relayout"
        ),
        # Different percentage views of the range
        dict(
            args=[{'yaxis.range': [y_min + y_range*0.25, y_max - y_range*0.25]}],
            label="50% Range",
            method="relayout"
        ),
        dict(
            args=[{'yaxis.range': [y_min + y_range*0.4, y_max - y_range*0.4]}],
            label="20% Range",
            method="relayout"
        )
    ]

    # Update layout configuration
    fig.update_layout(
        title=dict(
            text=f'PPG vs Time for Day {day_number}',
            font=dict(size=20)
        ),
        autosize=True,
        width=1200,
        height=800,
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis=dict(
            title='Time (24-hour)',
            tickformatstops=tickformatstops,
            tickangle=45,
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgrey',
            rangeslider=dict(visible=True),
            rangeselector=x_rangeselector,
            type='date',
            fixedrange=False,  # Allow x-axis zooming
            hoverformat='%H:%M:%S.%L',
            automargin=True
        ),
        yaxis=dict(
            title='PPG',
            fixedrange=True,  # IMPORTANT: Lock y-axis during x-axis zooming
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgrey',
            range=[y_min_display, y_max_display],  # Set initial view with padding
            autorange=False  # Disable auto-ranging to prevent automatic rescaling
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        dragmode='pan',  # Set back to 'pan' for easier navigation
        plot_bgcolor='white',
        paper_bgcolor='white',
        modebar=dict(
            orientation='v'
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
        updatemenus=[
            # Y-axis range controls
            dict(
                type="buttons",
                direction="right",
                buttons=y_buttons,
                pad={"r": 10, "t": 10},
                showactive=False,
                x=0.98,
                y=1.1,
                xanchor="right",
                yanchor="top",
                bgcolor="rgba(150, 200, 250, 0.4)",
                bordercolor="rgba(0, 0, 0, 0)"
            ),
            # Add Y-axis zoom toggle
            dict(
                type="buttons",
                direction="right",
                buttons=[
                    dict(
                        args=[{"yaxis.fixedrange": False}],
                        label="Enable Y Zoom",
                        method="relayout"
                    ),
                    dict(
                        args=[{"yaxis.fixedrange": True}],
                        label="Lock Y Axis",
                        method="relayout"
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                active=1,  # Default to locked (fixedrange=True)
                x=0.77,
                y=1.1,
                xanchor="right",
                yanchor="top",
                bgcolor="rgba(150, 200, 250, 0.4)",
                bordercolor="rgba(0, 0, 0, 0)"
            )
        ],
        annotations=[
            dict(
                text="Time Range:",
                showarrow=False,
                x=0,
                y=1.12,
                xref="paper",
                yref="paper",
                font=dict(size=12)
            ),
            dict(
                text="Y Range Controls:",
                showarrow=False,
                x=0.85,
                y=1.12,
                xref="paper",
                yref="paper",
                font=dict(size=12)
            ),
            dict(
                text="Y Zoom Control:",
                showarrow=False,
                x=0.65,
                y=1.12,
                xref="paper",
                yref="paper",
                font=dict(size=12)
            )
        ]
    )

    # Enhanced configuration
    config = {
        'scrollZoom': True,
        'displayModeBar': True,
        'modeBarButtonsToAdd': [
            'drawline',
            'drawopenpath', 
            'eraseshape',
            'select2d',
            'lasso2d',
            'zoomIn2d',
            'zoomOut2d',
            'resetScale2d'
        ],
        'displaylogo': False,
        'doubleClick': 'reset+autosize',
        'showTips': True,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': f'ppg_day_{day_number}',
            'height': 800,
            'width': 1200,
            'scale': 2
        }
    }

    return plot(fig, output_type='div', config=config)


def generate_ppg_graph(request, file_id):
    # Retrieve the file object
    file = get_object_or_404(ExcelFile, pk=file_id)
    file_path = file.file.path  # Path to the uploaded CSV file

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Extract the 'PPG' and 'Time' columns
    ppg_data = df[['Time', 'PPG']].dropna()  # Drop rows with NaN values if necessary

    # Create the plot
    plt.figure(figsize=(10, 5))
    plt.plot(ppg_data['Time'], ppg_data['PPG'], label='PPG')
    plt.xlabel('Time')
    plt.ylabel('PPG')
    plt.title('PPG Data Over Time')
    plt.legend()
    plt.grid(True)

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Return the image as a response
    return HttpResponse(img, content_type='image/png')

logger = logging.getLogger(__name__)

import numpy as np
from scipy import stats  # Import mode calculation from scipy

import numpy as np
import scipy.signal as signal
import scipy.stats as stats
import logging

import numpy as np
import logging
from scipy import signal

def calculate_heart_rate(ppg_data, time_data=None, sampling_rate=125):
    """
    Calculate heart rate statistics from PPG data, supporting both raw and preprocessed data.
    
    Parameters:
    -----------
    ppg_data : list or numpy.array
        PPG signal data (raw or preprocessed)
    time_data : list or numpy.array, optional
        Time values corresponding to PPG data. If None, time is inferred from sampling rate.
    sampling_rate : float, optional
        Sampling rate of the PPG data (default is 125 Hz)
    
    Returns:
    --------
    dict or None
        Dictionary containing heart rate statistics, or None if calculation fails
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Validate input data
        if not isinstance(ppg_data, (list, np.ndarray)) or len(ppg_data) == 0:
            logger.warning("Invalid or empty PPG data")
            return None
        
        ppg_array = np.array(ppg_data, dtype=float)
        
        # Handle time data
        if time_data is not None and len(time_data) == len(ppg_data):
            time_array = np.array(time_data, dtype=float)
            time_array -= time_array[0]  # Normalize time to start from 0
        else:
            time_array = np.arange(len(ppg_data)) / sampling_rate  # Generate time array
        
        # Preprocessing: Remove DC offset
        ppg_array -= np.mean(ppg_array)
        
        # Apply bandpass filter to isolate heart rate frequency range
        low_cutoff = 0.5  # Hz
        high_cutoff = 5.0  # Hz
        nyquist_freq = 0.5 * sampling_rate
        low = low_cutoff / nyquist_freq
        high = high_cutoff / nyquist_freq
        
        b, a = signal.butter(N=4, Wn=[low, high], btype='band')
        filtered_ppg = signal.filtfilt(b, a, ppg_array)
        
        # Peak detection
        peaks, _ = signal.find_peaks(
            filtered_ppg, height=np.std(filtered_ppg), distance=int(sampling_rate * 0.3)
        )
        
        if len(peaks) < 2:
            logger.warning("Not enough peaks detected to calculate heart rate")
            return None
        
        # Compute RR intervals and heart rate
        peak_intervals = np.diff(time_array[peaks])  # Time differences between peaks
        heart_rates = 60 / peak_intervals  # Convert to beats per minute (BPM)
        
        # Compute statistics
        stats_dict = {
            'min': round(float(np.min(heart_rates)), 2),
            'max': round(float(np.max(heart_rates)), 2),
            'avg': round(float(np.mean(heart_rates)), 2),
            'median': round(float(np.median(heart_rates)), 2),
            'std': round(float(np.std(heart_rates)), 2),
            'num_peaks': len(peaks)
        }
        
        return stats_dict
    
    except Exception as e:
        logger.error(f"Error calculating heart rate statistics: {e}")
        return None




def process_ppg_data(rows, day=None, from_seconds=None, to_seconds=None):
    """Process PPG data, starting a new day only when the timestamp decreases significantly."""
    try:
        daily_ppg = []
        daily_time = []
        daily_stats = []
        
        current_day_ppg = []
        current_day_time = []
        previous_seconds = None  # No assumption about starting time
        current_day = 1

        for row in rows:
            if not all(key in row for key in ['PPG', 'Time']):
                continue

            time_seconds = ppg_time_to_seconds(row['Time'])
            if time_seconds is None:
                continue

            try:
                ppg_value = float(row['PPG'])
                
                # Detect day transition when timestamp decreases significantly
                if previous_seconds is not None and time_seconds < previous_seconds - 10:  # 10-second threshold
                    if day is not None and current_day == day:
                        break  # Stop processing if we've reached the requested day

                    # Save previous day's data
                    if current_day_ppg:
                        hr_stats = calculate_heart_rate(np.array(current_day_ppg))
                        if hr_stats:
                            daily_stats.append(hr_stats)
                            daily_ppg.append(current_day_ppg)
                            daily_time.append(current_day_time)

                    # Move to the next day
                    current_day += 1
                    current_day_ppg = []
                    current_day_time = []
                
                # Apply time filter if needed
                if day is not None and current_day == day:
                    if from_seconds is not None and to_seconds is not None:
                        if not (from_seconds <= time_seconds <= to_seconds):
                            continue
                
                formatted_time = format_time_with_ms(time_seconds)
                if formatted_time:
                    current_day_ppg.append(ppg_value)
                    current_day_time.append(formatted_time)
                    previous_seconds = time_seconds  # Update previous time
                    
            except ValueError:
                continue
        
        # Process the last day's data
        if current_day_ppg and current_day_time:
            hr_stats = calculate_heart_rate(np.array(current_day_ppg))
            if hr_stats:
                daily_stats.append(hr_stats)
                daily_ppg.append(current_day_ppg)
                daily_time.append(current_day_time)

        return daily_ppg, daily_time, daily_stats
    except Exception as e:
        logger.error(f"Error processing PPG data: {e}")
        return [], [], []

@require_http_methods(["GET", "POST"])
def display_csv(request, file_id):
    """Main view function for displaying and filtering PPG data."""
    try:
        # Fetch the GoogleSheet object
        google_sheet = get_object_or_404(GoogleSheet, id=file_id)
        
        # Set up Google Sheets API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        try:
            sheet = client.open_by_url(google_sheet.sheet_url).sheet1
            rows = sheet.get_all_records()
        except Exception as e:
            logger.error(f"Error accessing Google Sheet: {e}")
            return JsonResponse({'error': 'Unable to access the data sheet'}, status=500)
        
        if request.method == 'POST':
            # Handle time range filtering
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            day = request.POST.get('day')
            
            if not all([from_time, to_time, day]):
                return JsonResponse({'error': 'Missing required filter parameters'}, status=400)
            
            try:
                day = int(day)
                from_seconds =ppg_time_to_seconds(from_time + ':00')
                to_seconds = ppg_time_to_seconds(to_time + ':00')
                
                if any(x is None for x in [from_seconds, to_seconds]):
                    return JsonResponse({'error': 'Invalid time format'}, status=400)
                
                if from_seconds > to_seconds:
                    return JsonResponse({'error': 'Start time must be before end time'}, status=400)
                
            except ValueError:
                return JsonResponse({'error': 'Invalid day or time format'}, status=400)
            
            # Process data with filters
            daily_ppg, daily_time, daily_stats = process_ppg_data(rows, day, from_seconds, to_seconds)
            
            if not daily_ppg or day > len(daily_ppg):
                return JsonResponse({'error': 'No data found for the specified filters'}, status=404)
            
            # Create filtered graph for the specific day
            graph_div = create_graph(daily_time[0], daily_ppg[0], day)
            
            return JsonResponse({
                'graph': graph_div,
                'stats': daily_stats[0] if daily_stats else {
                    'min': 'N/A', 'max': 'N/A', 'avg': 'N/A',
                    'median': 'N/A', 'mode': 'N/A'
                }
            })
        
        # Handle GET request - initial data load
        daily_ppg, daily_time, daily_stats = process_ppg_data(rows)
        
        # Create graphs for each day
        graph_divs = []
        for i, (day_time, day_ppg) in enumerate(zip(daily_time, daily_ppg), start=1):
            graph_div = create_graph(day_time, day_ppg, i)
            graph_divs.append({
                'day': i,  # Changed to match frontend expectations
                'graph': graph_div,
                'stats': daily_stats[i - 1] if i <= len(daily_stats) else {
                    'min': 'N/A', 'max': 'N/A', 'avg': 'N/A',
                    'median': 'N/A', 'mode': 'N/A'
                }
            })
        
        context = {
            'graphs': graph_divs,
            'file_id': file_id,
        }
        
        return render(request, 'rough.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in display_csv: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)


import chardet

def get_encoding(file_path):
    """Detect the encoding of the file."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


def ProfilePage(request):
    return render(request, 'profile.html')

def ContactPage(request):
    return render(request, 'contact.html')

def AboutPage(request):
    return render(request, 'about.html')
# views.py

def welcome_view(request):
    return render(request, 'welcome.html')

def welcome_about(request):
    return render(request, 'welcome_about.html')

def welcome_contact(request):
    return render(request, 'welcome_contact.html')

from django.shortcuts import render
from .models import GoogleSheet

from django.contrib.auth.decorators import login_required

@login_required  # Ensure the user is logged in
def view_files(request):
    if request.user.is_superuser:
        # Superuser sees all files
        google_sheets = GoogleSheet.objects.all().select_related('user')  # Prefetch user data if needed
    else:
        # Normal user sees only their files
        google_sheets = GoogleSheet.objects.filter(user=request.user)
    
    return render(request, 'view_files.html', {'google_sheets': google_sheets})


from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.mail import send_mail
import random
import string

User = get_user_model()

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        uid = self.kwargs.get('uidb64')
        token = self.kwargs.get('token')
        user_pk = force_text(urlsafe_base64_decode(uid))
        user = get_object_or_404(User, pk=user_pk)

        if default_token_generator.check_token(user, token):
            new_password = generate_random_password()
            user.set_password(new_password)
            user.save()

            # Send the new password to the user
            self.send_new_password_email(user, new_password)
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def send_new_password_email(self, user, new_password):
        subject = 'Your New Password'
        message = f'Hi {user.username},\n\nYour new password is: {new_password}\n\nPlease use this password to log in and change it once you are logged in.'
        from_email = 'your_email@example.com'
        recipient_list = [user.email]

        send_mail(subject, message, from_email, recipient_list)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # If the password has been generated, add it to the context for the template
        if 'new_password' in self.kwargs:
            context['new_password'] = self.kwargs['new_password']
        return context

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

    
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # If the password has been generated, add it to the context for the template
        if 'new_password' in self.kwargs:
            context['new_password'] = self.kwargs['new_password']
        return context




from django.shortcuts import render, redirect
from .forms import ContactForm

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import ContactMessage
from .forms import ContactForm



def contact_success_view(request):
    return render(request, 'contact_success.html')



from django.conf import settings
from django.shortcuts import redirect, HttpResponse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth
import gspread
import os
import pickle

# Define the scope for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def authorize(request):
    # Load credentials from the session or file
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    
    # Store the credentials in the session
    request.session['credentials'] = creds.to_json()

    return redirect('get-google-sheet-data')

from django.shortcuts import get_object_or_404

def get_google_sheet_data(request, file_id):
    file = get_object_or_404(GoogleSheet, id=file_id)  # Get the file using its ID
    return redirect(file.sheet_url)  # Redirect to the Google Sheet URL

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm
from .models import GoogleSheet

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm
from .models import GoogleSheet

@login_required
def upload_google_sheet(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST)
        if form.is_valid():
            # Create an instance of GoogleSheet
            google_sheet = GoogleSheet(
                user=request.user,  # Automatically get the logged-in user
                title=form.cleaned_data['title'],
                sheet_url=form.cleaned_data['google_sheet_url'],
                 # Extract sheet ID from URL
            )
            google_sheet.save()  # Save the model instance
            return redirect('upload_success')  # Redirect to a success page
    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})


# In views.py
from django.shortcuts import render, get_object_or_404

def file_detail(request, id):
    file = get_object_or_404(GoogleSheet, id=id)  # Assuming FileModel is your model for storing file data
    return render(request, 'file_detail.html', {'file': file})

# views.py
from django.shortcuts import render, redirect
from .forms import ContactForm
from django.contrib import messages
from django.shortcuts import render
from .forms import ContactForm

def contact_view(request):
    success_message = None

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = "Thank you! Your message has been sent."
            form = ContactForm()  # Reset the form after submission
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form, 'success': success_message})

def welcome_contact_view(request):
    success_message = None

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = "Thank you! Your message has been sent."
            form = ContactForm()  # Reset the form after submission
    else:
        form = ContactForm()

    return render(request, 'welcome_contact.html', {'form': form, 'success': success_message})

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@login_required
def form_submit(request):
    if request.method == "POST":
        # Google Sheets URL
        google_sheet_url = "https://docs.google.com/spreadsheets/d/1g_2UyeDqGjajt3YxAof3lMvlFJEoI59YjbXYu2vRnec/edit?usp=sharing"

        # Set up Google Sheets API credentials
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            '/home/megha21337/krish22253/M-Health-1/mHealth/credentials.json', scope)  # Replace with your credentials file path
        client = gspread.authorize(creds)

        try:
            # Open the Google Sheet and retrieve rows
            sheet = client.open_by_url(google_sheet_url).sheet1
            rows = sheet.get_all_records()

            # Extract the list of usernames
            username_list = [row['username'] for row in rows if 'username' in row]

            # Check if the logged-in user's username is in the list
            if request.user.username in username_list:
                # Update user's profile
                user_profile = request.user.userprofile
                user_profile.form_submitted = True
                user_profile.save()

                messages.success(request, "Form submission verified. You can now proceed.")
            else:
                messages.error(request, "Your form submission could not be verified. Please try again.")
        except Exception as e:
            messages.error(request, f"Error accessing Google Sheet: {e}")
    
    return redirect('home')


@login_required
def HomePage(request):
    # Check if the user's form submission status is already verified
    user_profile = request.user.userprofile
    if not user_profile.form_submitted:
        # Google Sheets URL
        google_sheet_url = "https://docs.google.com/spreadsheets/d/1g_2UyeDqGjajt3YxAof3lMvlFJEoI59YjbXYu2vRnec/edit?usp=sharing"

        # Set up Google Sheets API credentials
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            '/mHealth/credentials.json', scope)  # Replace with your credentials file path
        client = gspread.authorize(creds)

        try:
            # Open the Google Sheet by URL and get all rows
            sheet = client.open_by_url(google_sheet_url).sheet1
            rows = sheet.get_all_records()

            # Extract the list of usernames from the sheet
            username_list = [row['username'] for row in rows if 'username' in row]

            # Verify if the logged-in user is in the sheet
            if request.user.username in username_list:
                # Update the form submission status
                user_profile.form_submitted = True
                user_profile.save()
                messages.success(request, "Form submission verified. You can now proceed.")
            else:
                messages.warning(request, "Your username was not found in the form. Please complete it.")
        except Exception as e:
            messages.error(request, f"Error accessing Google Sheet: {e}")

    return render(request, "home.html")


import os
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
import os
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings

import os
import datetime
import logging
import io
import pandas as pd
import numpy as np
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.conf import settings
import plotly.graph_objs as go
from plotly.offline import plot
from scipy import stats  # For mode calculation
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods







logger = logging.getLogger(__name__)

def ppg_time_to_seconds(time_str):
    """Convert PPG time string (HH:MM:SS.sss) to total seconds."""
    try:
        if '.' in time_str:
            time_part, ms_part = time_str.split('.')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000
        else:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
    except (ValueError, IndexError, AttributeError):
        return None

def ppg_format_time_with_ms(seconds):
    """Convert seconds back to formatted time string with milliseconds."""
    try:
        if seconds is None or seconds < 0:
            return None
            
        total_seconds = int(seconds)
        milliseconds = int((seconds % 1) * 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours >= 24:
            hours = hours % 24
            
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return None

def ppg_calculate_stats(ppg_data):
    """Calculate statistics for PPG data."""
    if not ppg_data.size:
        return None
    
    try:
        # Find peaks in the PPG signal
        peaks, _ = find_peaks(ppg_data, height=np.mean(ppg_data), distance=50)
        
        if len(peaks) < 2:
            return {
                'min': round(float(np.min(ppg_data)), 2),
                'max': round(float(np.max(ppg_data)), 2),
                'avg': round(float(np.mean(ppg_data)), 2),
                'median': round(float(np.median(ppg_data)), 2),
                'hr': 'N/A (not enough peaks)',
                'hrv': 'N/A'
            }
        
        # Calculate heart rate (BPM) from peak intervals
        peak_intervals = np.diff(peaks)
        sampling_rate = 100  # Assuming 100Hz sampling rate
        heart_rates = 60 / (peak_intervals / sampling_rate)
        
        # Calculate HRV (RMSSD)
        rr_intervals_ms = peak_intervals * (1000 / sampling_rate)
        hrv_rmssd = np.sqrt(np.mean(np.square(np.diff(rr_intervals_ms))))
        
        return {
            'min': round(float(np.min(ppg_data)), 2),
            'max': round(float(np.max(ppg_data)), 2),
            'avg': round(float(np.mean(heart_rates)), 2),
            'median': round(float(np.median(heart_rates)), 2),
            'hr': round(float(np.mean(heart_rates)), 2),
            'hrv': round(float(hrv_rmssd), 2)
        }
    except Exception as e:
        logger.error(f"Error calculating PPG statistics: {e}")
        return None

def ppg_process_data(rows, day=None, from_seconds=None, to_seconds=None):
    """Process PPG data, splitting into days based on time decreases."""
    try:
        daily_ppg = []
        daily_time = []
        daily_stats = []
        current_day_ppg = []
        current_day_time = []
        previous_seconds = None
        current_day = 1

        for row in rows:
            if not all(key in row for key in ['PPG', 'Time']):
                continue

            time_seconds = ppg_time_to_seconds(row['Time'])
            if time_seconds is None:
                continue

            try:
                ppg_value = float(row['PPG'])
                
                # Detect day transition when timestamp decreases significantly
                if previous_seconds is not None and time_seconds < previous_seconds - 10:
                    if day is not None and current_day == day:
                        break
                    
                    if current_day_ppg:
                        stats = ppg_calculate_stats(np.array(current_day_ppg))
                        if stats:
                            daily_stats.append(stats)
                            daily_ppg.append(current_day_ppg)
                            daily_time.append(current_day_time)
                    
                    current_day += 1
                    current_day_ppg = []
                    current_day_time = []
                
                # Apply time filter if specified
                if day is not None and current_day == day:
                    if from_seconds is not None and to_seconds is not None:
                        if not (from_seconds <= time_seconds <= to_seconds):
                            continue
                
                formatted_time = ppg_format_time_with_ms(time_seconds)
                if formatted_time:
                    current_day_ppg.append(ppg_value)
                    current_day_time.append(formatted_time)
                    previous_seconds = time_seconds
                    
            except ValueError:
                continue
        
        # Process the last day's data
        if current_day_ppg and (day is None or current_day == day):
            stats = ppg_calculate_stats(np.array(current_day_ppg))
            if stats:
                daily_stats.append(stats)
                daily_ppg.append(current_day_ppg)
                daily_time.append(current_day_time)

        return daily_ppg, daily_time, daily_stats
    except Exception as e:
        logger.error(f"Error processing PPG data: {e}")
        return [], [], []

def ppg_prepare_chart_data(day_time, day_ppg, day_number):
    """Prepare PPG chart data for Lightweight Charts."""
    if not day_time or not day_ppg:
        return {'error': 'No data available'}
    
    try:
        x_times = [int(datetime.strptime(t, '%H:%M:%S.%f').timestamp() * 1000) for t in day_time]
        ppg_data = [{'time': t, 'value': v} for t, v in zip(x_times, day_ppg)]
        
        return {
            'day': day_number,
            'ppg': ppg_data,
            'min_time': min(x_times) if x_times else None,
            'max_time': max(x_times) if x_times else None,
            'min_value': min(day_ppg) if day_ppg else None,
            'max_value': max(day_ppg) if day_ppg else None
        }
    except Exception as e:
        logger.error(f"Error preparing PPG chart data: {e}")
        return {'error': str(e)}

@require_http_methods(["GET", "POST"])
def view_local_ppg(request, filename, username=None):
    """View function for PPG visualization."""
    username = request.user.username if request.user.is_authenticated else username or "krish"
    
    try:
        local_files_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
        file_path_f = os.path.join(local_files_dir, username)
        file_path = os.path.join(file_path_f, filename)

        if not os.path.exists(file_path):
            raise Http404("File not found")

        df = pd.read_csv(file_path)

        # Handle different CSV formats
        if {'Time', 'PPG'}.issubset(df.columns):
            df = df[['Time', 'PPG']].dropna()
        else:
            required_cols = {'Hour', 'Minute', 'Second', 'Millisecond', 'Red', 'IR'}
            if not required_cols.issubset(df.columns):
                return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

            df['Time'] = df.apply(
                lambda row: f"{int(row['Hour']):02d}:{int(row['Minute']):02d}:{int(row['Second']):02d}.{int(row['Millisecond']):03d}", 
                axis=1
            )
            df['PPG'] = df.apply(lambda row: row['Red'] / row['IR'] if row['IR'] != 0 else None, axis=1)
            df = df[['Time', 'PPG']].dropna()

        rows = df.to_dict(orient='records')

        if request.method == 'POST':
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            day = request.POST.get('day')

            if not all([from_time, to_time, day]):
                return JsonResponse({'error': 'Missing required filter parameters'}, status=400)

            try:
                day = int(day)
                from_seconds = ppg_time_to_seconds(from_time + ':00')
                to_seconds = ppg_time_to_seconds(to_time + ':00')

                if any(x is None for x in [from_seconds, to_seconds]):
                    return JsonResponse({'error': 'Invalid time format'}, status=400)

                if from_seconds > to_seconds:
                    return JsonResponse({'error': 'Start time must be before end time'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid day or time format'}, status=400)

            daily_ppg, daily_time, daily_stats = ppg_process_data(rows, day, from_seconds, to_seconds)
            if not daily_ppg or day > len(daily_ppg):
                return JsonResponse({'error': 'No data found for the specified filters'}, status=404)

            chart_data = ppg_prepare_chart_data(daily_time[0], daily_ppg[0], day)
            return JsonResponse({
                'graph': chart_data,
                'stats': daily_stats[0] if daily_stats else {
                    'min': 'N/A', 'max': 'N/A', 'avg': 'N/A',
                    'median': 'N/A', 'hr': 'N/A', 'hrv': 'N/A'
                }
            })

        # For GET requests - show all data
        daily_ppg, daily_time, daily_stats = ppg_process_data(rows)
        graphs = []
        
        for i, (day_time, day_ppg) in enumerate(zip(daily_time, daily_ppg), start=1):
            chart_data = ppg_prepare_chart_data(day_time, day_ppg, i)
            graphs.append({
                'day': i,
                'graph': chart_data,
                'stats': daily_stats[i-1] if i <= len(daily_stats) else {
                    'min': 'N/A', 'max': 'N/A', 'avg': 'N/A',
                    'median': 'N/A', 'hr': 'N/A', 'hrv': 'N/A'
                }
            })

        return render(request, 'local_ppg.html', {
            'graphs': graphs,
            'filename': filename,
            'username': username
        })

    except Exception as e:
        logger.error(f"Unexpected error in view_local_ppg: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.http import HttpResponseForbidden
import os
from datetime import datetime
import mimetypes
# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from datetime import datetime
import os
import mimetypes

@login_required
def local_files_view(request):
    base_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
    
    if request.user.is_superuser:
        # Handle superuser view - show all users' files
        users_data = []
        for username in os.listdir(base_dir):
            user_folder = os.path.join(base_dir, username)
            if os.path.isdir(user_folder):
                user_files = []
                for filename in os.listdir(user_folder):
                    file_path = os.path.join(user_folder, filename)
                    if os.path.isfile(file_path):
                        stats = os.stat(file_path)
                        user_files.append({
                            'name': filename,
                            'size': stats.st_size,
                            'created_at': datetime.fromtimestamp(stats.st_ctime)
                        })
                users_data.append({
                    'username': username,
                    'files': user_files
                })
        
        context = {
            'users_data': users_data,
            'is_superuser': True
        }
    else:
        # Handle normal user view - show only their files
        user_folder = os.path.join(base_dir, request.user.username)
        local_files = []
        
        if os.path.exists(user_folder):
            for filename in os.listdir(user_folder):
                file_path = os.path.join(user_folder, filename)
                if os.path.isfile(file_path):
                    stats = os.stat(file_path)
                    local_files.append({
                        'name': filename,
                        'size': stats.st_size,
                        'created_at': datetime.fromtimestamp(stats.st_ctime)
                    })
        
        context = {
            'local_files': local_files,
            'is_superuser': False,
            'user_data': {
                'username': request.user.username
            }
        }
    
    return render(request, 'local_files.html', context)

@login_required
def view_file_data(request, username, filename):
    # Base directory for all user files
    base_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
    
    # Determine which user's files to access
    if username and request.user.is_superuser:
        # Superuser accessing another user's files
        target_folder = os.path.join(base_dir, username)
    else:
        # Regular user accessing their own files
        target_folder = os.path.join(base_dir, request.user.username)
        username = request.user.username
    
    file_path = os.path.join(target_folder, filename)
    
    # Security checks
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return HttpResponse("File not found.", status=404)
        
        # Prevent directory traversal attacks
        if not os.path.normpath(file_path).startswith(os.path.normpath(base_dir)):
            return HttpResponseForbidden("Access denied.")
        
        # Check if user has permission to access this file
        if not request.user.is_superuser and username != request.user.username:
            return HttpResponseForbidden("You don't have permission to access this file.")
        
        # Get file information
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        created_time = datetime.fromtimestamp(file_stats.st_ctime)
        modified_time = datetime.fromtimestamp(file_stats.st_mtime)
        
        # Determine file type
        file_type, _ = mimetypes.guess_type(file_path)
        
        # Read file content based on file type
        if file_type and file_type.startswith('text/'):
            with open(file_path, 'r') as file:
                file_content = file.read()
        elif file_type and file_type.startswith('application/json'):
            with open(file_path, 'r') as file:
                file_content = file.read()
        else:
            file_content = "Binary file content cannot be displayed directly."
        
        # Additional file metadata
        file_info = {
            'name': filename,
            'size': file_size,
            'type': file_type or 'Unknown',
            'description': f'File uploaded by {username}',
            'content': file_content,
            'created_at': created_time,
            'modified_at': modified_time,
            'path': file_path,
            'owner': username
        }

        # Add PPG-specific information if applicable
        if filename.lower().endswith(('.ppg', '.csv')):
            file_info['has_ppg'] = True
            file_info['ppg_url'] = f'/view_local_ppg/{filename}'
        
        context = {
            'file': file_info,
            'is_superuser': request.user.is_superuser,
            'is_owner': username == request.user.username
        }
        
        return render(request, 'view_local_file.html', context)
        
    except PermissionError:
        return HttpResponseForbidden("Permission denied. Unable to access file.")
    except UnicodeDecodeError:
        return HttpResponse("This file cannot be displayed as text.", status=415)
    except Exception as e:
        return HttpResponse(f"An error occurred while accessing the file: {str(e)}", status=500)


import os
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse, Http404

def convert_local_csv_to_hl7(request, filename, username="krish"):
    try:
        # Define local files directory and construct file path
        local_files_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
        file_path = os.path.join(local_files_dir, username, filename)

        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Read the CSV file
        df = pd.read_csv(file_path)

        # Ensure required raw data columns exist
        required_cols = {'Hour', 'Minute', 'Second', 'Millisecond', 'Red', 'IR', 'AccelX', 'AccelY', 'AccelZ', 'GyroX', 'GyroY', 'GyroZ', 'GSR'}
        if not required_cols.issubset(df.columns):
            return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

        # Create Time column (HH:MM:SS.sss format)
        df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)

        # Compute PPG value (avoiding division by zero)
        df['PPG'] = df.apply(lambda row: row['Red'] / row['IR'] if row['IR'] != 0 else None, axis=1)

        # Drop rows with missing values
        df = df[['Time', 'PPG', 'AccelX', 'AccelY', 'AccelZ', 'GyroX', 'GyroY', 'GyroZ', 'GSR']].dropna()
        rows = df.to_dict(orient='records')

        # Initialize HL7 message template (MSH segment)
        hl7_message = (
            "MSH|^~\\&|YourApp|YourFacility|HL7Server|HL7Server|20230908170000||ORU^R01|123456|P|2.5|||\n"
        )

        # Process the CSV data and construct HL7 message
        for row in rows:
            time = row['Time']
            ppg = row['PPG']
            gsr = row['GSR']
            accel_x = row['AccelX']
            accel_y = row['AccelY']
            accel_z = row['AccelZ']
            gyro_x = row['GyroX']
            gyro_y = row['GyroY']
            gyro_z = row['GyroZ']

            hl7_message += f"PID|1||{time}||||\n"
            hl7_message += f"OBX|1|NM|GSR^Galvanic Skin Response^HL7|||{time}|||||AmplitudeData^{time}^Units|{gsr}\n"
            hl7_message += f"OBX|2|NM|PPG^Photoplethysmogram^HL7|||{time}|||||AmplitudeData^{time}^Units|{ppg}\n"
            hl7_message += f"OBX|3|NM|ACCEL_X^Accelerometer X^HL7|||{time}|||||AmplitudeData^{time}^Units|{accel_x}\n"
            hl7_message += f"OBX|4|NM|ACCEL_Y^Accelerometer Y^HL7|||{time}|||||AmplitudeData^{time}^Units|{accel_y}\n"
            hl7_message += f"OBX|5|NM|ACCEL_Z^Accelerometer Z^HL7|||{time}|||||AmplitudeData^{time}^Units|{accel_z}\n"
            hl7_message += f"OBX|6|NM|GYRO_X^Gyroscope X^HL7|||{time}|||||AmplitudeData^{time}^Units|{gyro_x}\n"
            hl7_message += f"OBX|7|NM|GYRO_Y^Gyroscope Y^HL7|||{time}|||||AmplitudeData^{time}^Units|{gyro_y}\n"
            hl7_message += f"OBX|8|NM|GYRO_Z^Gyroscope Z^HL7|||{time}|||||AmplitudeData^{time}^Units|{gyro_z}\n"

        # Return the HL7 data as plain text in the browser
        context = {'hl7_message': hl7_message}
        return render(request, 'hl7_display.html', context)

    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)


from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import pandas as pd
import os
import pandas as pd
from django.http import HttpResponse, JsonResponse, Http404
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def download_hl7_pdf(request, filename, username="krish"):
    try:
        # Define local files directory and construct file path
        local_files_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
        file_path = os.path.join(local_files_dir, username, filename)

        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Read the CSV file
        df = pd.read_csv(file_path)

        # Define available columns and process only existing ones
        time_columns = {'Hour', 'Minute', 'Second', 'Millisecond'}
        numeric_columns = {'Red', 'IR', 'AccelX', 'AccelY', 'AccelZ', 'GyroX', 'GyroY', 'GyroZ', 'GSR', 'PPG'}
        available_cols = set(df.columns)
        
        # Construct Time column if required components exist
        if time_columns.issubset(available_cols):
            df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)
            available_cols.add('Time')
        
        # Construct PPG column if Red and IR exist
        if {'Red', 'IR'}.issubset(available_cols):
            df['PPG'] = df.apply(lambda row: row['Red'] / row['IR'] if row['IR'] != 0 else None, axis=1)
            available_cols.add('PPG')
        
        selected_cols = sorted(available_cols & (time_columns | numeric_columns | {'Time', 'PPG'}))
        df = df[selected_cols].dropna()
        rows = df.to_dict(orient='records')

        hl7_message = "MSH|^~\\&|YourApp|YourFacility|HL7Server|HL7Server|20230908170000||ORU^R01|123456|P|2.5|||\n"
        
        for row in rows:
            time = row.get('Time', 'Unknown')
            hl7_message += f"PID|1||{time}||||\n"
            for col, value in row.items():
                if col != 'Time':
                    hl7_message += f"OBX|1|NM|{col.upper()}^Measurement^HL7|||{value}|||||AmplitudeData^{time}^Units\n"

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setFont("Helvetica", 10)

        y_position = 750
        for line in hl7_message.split("\n"):
            pdf.drawString(50, y_position, line)
            y_position -= 15
            if y_position < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = 750
        
        pdf.save()
        return response

    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)


import pandas as pd
import plotly.graph_objects as go
from django.shortcuts import render
from django.http import JsonResponse

from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render
from django.http import JsonResponse
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.shortcuts import render
from django.http import JsonResponse
import os
from django.conf import settings
import json
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from django.shortcuts import render
from django.http import JsonResponse
import plotly.io as pio

# Function to process datetime and detect day changes
import pandas as pd
import os

import logging
import io
import pandas as pd
import numpy as np
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.conf import settings
import plotly.graph_objs as go
from plotly.offline import plot
from scipy import stats  # For mode calculation
import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime, time
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# Bokeh imports
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import (
    ColumnDataSource, DatetimeTickFormatter, HoverTool, 
    RangeSlider, Range1d, BoxZoomTool, ResetTool, PanTool, 
    WheelZoomTool, SaveTool, BoxSelectTool, DatetimeRangeSlider
)
from bokeh.layouts import column
from bokeh.themes import Theme
from bokeh.io import curdoc
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def gsr_time_to_seconds(time_str):
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return None

def gsr_format_time_with_ms(seconds):
    try:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02}:{minutes:02}:{secs:06.3f}"
    except:
        return None

def gsr_calculate_stats(data):
    if not data.size:
        return None
    return {
        'min': round(np.min(data), 2),
        'max': round(np.max(data), 2),
        'avg': round(np.mean(data), 2),
    }

def gsr_process_data(rows, day=None, from_seconds=None, to_seconds=None):
    daily_gsr = []
    daily_time = []
    daily_stats = []
    current_day_gsr = []
    current_day_time = []
    previous_seconds = None
    current_day = 1

    for row in rows:
        if not all(key in row for key in ['GSR', 'Time']):
            continue

        time_seconds = gsr_time_to_seconds(row['Time'])
        if time_seconds is None:
            continue

        try:
            gsr_value = float(row['GSR'])

            if previous_seconds is not None and time_seconds < previous_seconds - 10:
                if day is not None and current_day == day:
                    break
                if current_day_gsr:
                    hr_stats = gsr_calculate_stats(np.array(current_day_gsr))
                    if hr_stats:
                        daily_stats.append(hr_stats)
                        daily_gsr.append(current_day_gsr)
                        daily_time.append(current_day_time)
                    current_day += 1
                    current_day_gsr = []
                    current_day_time = []

            if day is not None and current_day == day:
                if from_seconds is not None and to_seconds is not None:
                    if not (from_seconds <= time_seconds <= to_seconds):
                        continue

            current_day_gsr.append(gsr_value)
            current_day_time.append(row['Time'])
            previous_seconds = time_seconds

        except ValueError:
            continue

    if current_day_gsr and (day is None or current_day == day):
        hr_stats = gsr_calculate_stats(np.array(current_day_gsr))
        if hr_stats:
            daily_stats.append(hr_stats)
            daily_gsr.append(current_day_gsr)
            daily_time.append(current_day_time)

    return daily_gsr, daily_time, daily_stats

def gsr_prepare_chart_data(day_time, day_gsr, day_number):
    if not day_time or not day_gsr:
        return {'error': 'No data available'}

    x_times = [int(datetime.strptime(t, '%H:%M:%S.%f').timestamp() * 1000) for t in day_time]
    gsr_data = [{'time': t, 'value': v} for t, v in zip(x_times, day_gsr)]

    return {
        'day': day_number,
        'gsr': gsr_data,
        'min_time': min(x_times),
        'max_time': max(x_times)
    }

@require_http_methods(["GET", "POST"])
def view_local_gsr(request, filename, username=None):
    username = request.user.username
    try:
        local_files_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
        file_path_f = os.path.join(local_files_dir, username)
        file_path = os.path.join(file_path_f, filename)

        if not os.path.exists(file_path):
            raise Http404("File not found")

        df = pd.read_csv(file_path)

        if {'Time', 'GSR'}.issubset(df.columns):
            df = df[['Time', 'GSR']].dropna()
        else:
            required_cols = {'Hour', 'Minute', 'Second', 'Millisecond'}
            if not required_cols.issubset(df.columns):
                return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

            df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)
            # Assuming GSR is directly available or needs computation; adjust as needed
            if 'GSR' not in df.columns:
                return JsonResponse({'error': 'GSR column not found and cannot be computed'}, status=400)
            df = df[['Time', 'GSR']].dropna()

        rows = df.to_dict(orient='records')

        if request.method == 'POST':
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            day = request.POST.get('day')

            if not all([from_time, to_time, day]):
                return JsonResponse({'error': 'Missing required filter parameters'}, status=400)

            try:
                day = int(day)
                from_seconds = gsr_time_to_seconds(from_time + ':00')
                to_seconds = gsr_time_to_seconds(to_time + ':00')

                if any(x is None for x in [from_seconds, to_seconds]):
                    return JsonResponse({'error': 'Invalid time format'}, status=400)

                if from_seconds > to_seconds:
                    return JsonResponse({'error': 'Start time must be before end time'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid day or time format'}, status=400)

            daily_gsr, daily_time, daily_stats = gsr_process_data(rows, day, from_seconds, to_seconds)
            if not daily_gsr or day > len(daily_gsr):
                return JsonResponse({'error': 'No data found for the specified filters'}, status=404)

            chart_data = gsr_prepare_chart_data(daily_time[0], daily_gsr[0], day)
            return JsonResponse({'graph': chart_data, 'stats': daily_stats[0]})

        daily_gsr, daily_time, daily_stats = gsr_process_data(rows)
        graphs = []
        for i, (day_time, day_gsr) in enumerate(zip(daily_time, daily_gsr), start=1):
            chart_data = gsr_prepare_chart_data(day_time, day_gsr, i)
            graphs.append({
                'day': i,
                'graph': chart_data,
                'stats': daily_stats[i - 1]
            })

        return render(request, 'gsr.html', {'graphs': graphs, 'filename': filename})

    except Exception as e:
        logger.error(f"Unexpected error in view_local_gsr: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

# Helper functions that should be present in your code
def time_to_seconds(time_str):
    """Convert a time string (HH:MM:SS.sss) to seconds."""
    try:
        if '.' in time_str:
            time_part, ms_part = time_str.split('.')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000
        else:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
    except (ValueError, IndexError):
        return None

def format_time_with_ms(seconds):
    """Format seconds back to HH:MM:SS.sss."""
    try:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_part = seconds % 60
        whole_seconds = int(seconds_part)
        milliseconds = int((seconds_part - whole_seconds) * 1000)
        return f"{hours:02}:{minutes:02}:{whole_seconds:02}.{milliseconds:03}"
    except (ValueError, TypeError):
        return None

def calculate_heart_rate(gsr_values):
    """Calculate statistics for GSR data."""
    if len(gsr_values) == 0:
        return None
    
    try:
        stats = {
            'min': float(np.min(gsr_values)),
            'max': float(np.max(gsr_values)),
            'avg': float(np.mean(gsr_values)),
            'median': float(np.median(gsr_values)),
            'mode': float(np.argmax(np.bincount(gsr_values.astype(int))) if len(gsr_values) > 0 else 0)
        }
        return stats
    except Exception as e:
        logger.error(f"Error calculating GSR statistics: {e}")
        return None
def process_datetime(df):
    """Process time columns and detect day changes in the data"""
    # Convert time columns to datetime
    df["datetime"] = pd.to_datetime(
        df["Hour"].astype(str) + ":" +
        df["Minute"].astype(str) + ":" +
        df["Second"].astype(str) + "." +
        df["Millisecond"].astype(str),
        format="%H:%M:%S.%f", errors="coerce"
    )

    # Calculate total seconds since midnight for each time
    df["total_seconds"] = (
        df["Hour"] * 3600 +  # Hours to seconds
        df["Minute"] * 60 +  # Minutes to seconds
        df["Second"] +       # Seconds
        df["Millisecond"] / 1000  # Milliseconds to seconds
    )

    # Track when a new day starts
    day_counter = 0
    previous_seconds = None
    day_ids = []

    for seconds in df["total_seconds"]:
        # If current seconds are less than previous seconds, it's a new day
        if previous_seconds is not None and seconds < previous_seconds:
            day_counter += 1
        day_ids.append(day_counter)
        previous_seconds = seconds

    df["day_id"] = day_ids
    return df

import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

def get_data_file_path(username, filename):
    """
    Return the path to the data file based on username and filename.
    Raises an exception if username or filename is not provided.
    """
    if not username:
        raise ValueError("Username is required")
    if not filename:
        raise ValueError("Filename is required")

    local_files_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
    user_dir = os.path.join(local_files_dir, username)
    file_path = os.path.join(user_dir, filename)
    return file_path

def extract_username(request):
    """Extracts username from request and returns an error if missing."""
    username = request.user.username if request.user.is_authenticated else None
    if not username:
        return None, JsonResponse({'error': 'User authentication required'}, status=401)
    return username, None

def time_to_seconds(time_str):
    """Convert time string (HH:MM:SS) to seconds."""
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return None

def process_actigraphy_data(df, day=None, from_seconds=None, to_seconds=None):
    """Process Actigraphy data, splitting into days and applying time filters."""
    daily_actigraphy = []
    daily_time = []
    daily_stats = []
    current_day_data = []
    current_day_time = []
    previous_seconds = None
    current_day = 0

    for _, row in df.iterrows():
        time_seconds = time_to_seconds(row['Time'])
        if time_seconds is None:
            continue

        if previous_seconds is not None and time_seconds < previous_seconds - 10:
            if day is not None and current_day == day:
                break
            if current_day_data:
                daily_actigraphy.append(current_day_data)
                daily_time.append(current_day_time)
                daily_stats.append({
                    'avg': round(np.mean(current_day_data), 2) if current_day_data else 'N/A'
                })
            current_day += 1
            current_day_data = []
            current_day_time = []

        if day is not None and current_day == day:
            if from_seconds is not None and to_seconds is not None:
                if not (from_seconds <= time_seconds <= to_seconds):
                    continue

        current_day_data.append(float(row['Actigraphy']))
        current_day_time.append(row['Time'])
        previous_seconds = time_seconds

    if current_day_data and (day is None or current_day == day):
        daily_actigraphy.append(current_day_data)
        daily_time.append(current_day_time)
        daily_stats.append({
            'avg': round(np.mean(current_day_data), 2) if current_day_data else 'N/A'
        })

    logger.info(f"Processed data for day {day if day else 'all'}: {len(daily_actigraphy)} days, "
                f"Points per day: {[len(data) for data in daily_actigraphy]}")
    return daily_actigraphy, daily_time, daily_stats

def prepare_chart_data(day_time, day_actigraphy, day_number):
    """Prepare chart data for Lightweight Charts."""
    if not day_time or not day_actigraphy:
        logger.warning(f"No data for day {day_number}: time={len(day_time)}, actigraphy={len(day_actigraphy)}")
        return {'error': 'No data available'}

    x_times = [int(datetime.strptime(t, '%H:%M:%S.%f').timestamp() * 1000) for t in day_time]

    actigraphy_data = []
    for t, v in zip(x_times, day_actigraphy):
        actigraphy_data.append({
            'time': t,
            'value': v
        })

    logger.info(f"Day {day_number}: {len(actigraphy_data)} points")

    return {
        'day': day_number,
        'actigraphy_data': actigraphy_data,
        'min_time': min(x_times) if x_times else None,
        'max_time': max(x_times) if x_times else None
    }

@require_http_methods(["GET", "POST"])
def homme(request, filename, username=None):
    """
    Home page for actigraphy visualization.
    Extracts username from the request if not provided.
    """
    if username is None:
        username = request.user.username if request.user.is_authenticated else "krish"
    return render(request, "actigraphy/home.html", {"filename": filename, "username": username})

@require_http_methods(["GET", "POST"])
def actigraphy_weekly(request, username=None, filename=None):
    """Weekly view of actigraphy data with one chart per day."""
    username, error_response = extract_username(request)
    if error_response:
        return error_response

    try:
        file_path = get_data_file_path(username, filename)
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV: {file_path}, Shape: {df.shape}, Columns: {list(df.columns)}")

        required_cols = {'Hour', 'Minute', 'Second', 'Millisecond', 'AccelX', 'AccelY', 'AccelZ'}
        if not required_cols.issubset(df.columns):
            return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

        df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)
        df['Actigraphy'] = df.apply(lambda row: np.sqrt(row['AccelX']**2 + row['AccelY']**2 + row['AccelZ']**2), axis=1)
        df = df[['Time', 'Actigraphy']].dropna()

        if request.method == 'POST':
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            day = request.POST.get('day')

            if not all([from_time, to_time, day]):
                return JsonResponse({'error': 'Missing required filter parameters'}, status=400)

            try:
                day = int(day)
                from_seconds = time_to_seconds(from_time + ':00')
                to_seconds = time_to_seconds(to_time + ':00')

                if any(x is None for x in [from_seconds, to_seconds]):
                    return JsonResponse({'error': 'Invalid time format'}, status=400)

                if from_seconds > to_seconds:
                    return JsonResponse({'error': 'Start time must be before end time'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid day or time format'}, status=400)

            daily_actigraphy, daily_time, daily_stats = process_actigraphy_data(df, day, from_seconds, to_seconds)
            if not daily_actigraphy or day >= len(daily_actigraphy):
                return JsonResponse({'error': 'No data found for the specified filters'}, status=404)

            chart_data = prepare_chart_data(daily_time[0], daily_actigraphy[0], day)
            return JsonResponse({'graph': chart_data, 'stats': daily_stats[0]})

        daily_actigraphy, daily_time, daily_stats = process_actigraphy_data(df)
        graphs = []
        for i, (day_time, day_actigraphy) in enumerate(zip(daily_time, daily_actigraphy), start=0):
            chart_data = prepare_chart_data(day_time, day_actigraphy, i)
            graphs.append({
                'day': i,
                'graph': chart_data,
                'stats': daily_stats[i]
            })

        return render(request, "actigraphy/weekly.html", {
            "graphs": graphs,
            "filename": filename,
            "username": username
        })

    except Exception as e:
        logger.error(f"Unexpected error in actigraphy_weekly: {e}")
        return render(request, "actigraphy/weekly.html", {
            "error_message": f"An unexpected error occurred: {str(e)}",
            "filename": filename,
            "username": username
        })

@require_http_methods(["GET", "POST"])
def actigraphy_day_page(request, filename, day_id, username=None):
    """Page to display a single day's data."""
    username, error_response = extract_username(request)
    if error_response:
        return error_response

    try:
        file_path = get_data_file_path(username, filename)
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV: {file_path}, Shape: {df.shape}, Columns: {list(df.columns)}")

        required_cols = {'Hour', 'Minute', 'Second', 'Millisecond', 'AccelX', 'AccelY', 'AccelZ'}
        if not required_cols.issubset(df.columns):
            return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

        df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)
        df['Actigraphy'] = df.apply(lambda row: np.sqrt(row['AccelX']**2 + row['AccelY']**2 + row['AccelZ']**2), axis=1)
        df = df[['Time', 'Actigraphy']].dropna()

        if request.method == 'POST':
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            day = request.POST.get('day')

            if not all([from_time, to_time, day]):
                return JsonResponse({'error': 'Missing required filter parameters'}, status=400)

            try:
                day = int(day)
                from_seconds = time_to_seconds(from_time + ':00')
                to_seconds = time_to_seconds(to_time + ':00')

                if any(x is None for x in [from_seconds, to_seconds]):
                    return JsonResponse({'error': 'Invalid time format'}, status=400)

                if from_seconds > to_seconds:
                    return JsonResponse({'error': 'Start time must be before end time'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid day or time format'}, status=400)

            daily_actigraphy, daily_time, daily_stats = process_actigraphy_data(df, day, from_seconds, to_seconds)
            if not daily_actigraphy or day >= len(daily_actigraphy):
                return JsonResponse({'error': 'No data found for the specified filters'}, status=404)

            chart_data = prepare_chart_data(daily_time[0], daily_actigraphy[0], day)
            return JsonResponse({'graph': chart_data, 'stats': daily_stats[0]})

        daily_actigraphy, daily_time, daily_stats = process_actigraphy_data(df)
        day_id_int = int(day_id)
        if day_id_int >= len(daily_actigraphy):
            return render(request, "actigraphy/day.html", {
                "error_message": f"No data found for Day {day_id_int + 1}",
                "filename": filename,
                "username": username
            })

        chart_data = prepare_chart_data(daily_time[day_id_int], daily_actigraphy[day_id_int], day_id_int)
        unique_days = list(range(len(daily_actigraphy)))
        day_index = unique_days.index(day_id_int)
        prev_day = unique_days[day_index - 1] if day_index > 0 else None
        next_day = unique_days[day_index + 1] if day_index < len(unique_days) - 1 else None
        all_days = [{"id": d, "label": f"Day {d + 1}"} for d in unique_days]

        context = {
            "graphs": [{
                'day': day_id_int,
                'graph': chart_data,
                'stats': daily_stats[day_id_int]
            }],
            "day_id": day_id_int,
            "day_label": f"Day {day_id_int + 1}",
            "prev_day": prev_day,
            "next_day": next_day,
            "all_days": all_days,
            "filename": filename,
            "username": username
        }
        return render(request, "actigraphy/day.html", context)

    except Exception as e:
        logger.error(f"Unexpected error in actigraphy_day_page: {e}")
        return render(request, "actigraphy/day.html", {
            "error_message": f"An unexpected error occurred: {str(e)}",
            "filename": filename,
            "username": username
        })

@require_http_methods(["GET"])
def actigraphy_day_view(request, filename, day_id, username=None):
    """API endpoint to get detailed data for a specific day."""
    username, error_response = extract_username(request)
    if error_response:
        return error_response

    try:
        file_path = get_data_file_path(username, filename)
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV: {file_path}, Shape: {df.shape}, Columns: {list(df.columns)}")

        required_cols = {'Hour', 'Minute', 'Second', 'Millisecond', 'AccelX', 'AccelY', 'AccelZ'}
        if not required_cols.issubset(df.columns):
            return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

        df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)
        df['Actigraphy'] = df.apply(lambda row: np.sqrt(row['AccelX']**2 + row['AccelY']**2 + row['AccelZ']**2), axis=1)
        df = df[['Time', 'Actigraphy']].dropna()

        daily_actigraphy, daily_time, daily_stats = process_actigraphy_data(df)
        day_id_int = int(day_id)
        if day_id_int >= len(daily_actigraphy):
            return JsonResponse({"error": f"No data found for Day {day_id_int + 1}"}, status=404)

        chart_data = prepare_chart_data(daily_time[day_id_int], daily_actigraphy[day_id_int], day_id_int)
        return JsonResponse({'graph': chart_data, 'stats': daily_stats[day_id_int]})

    except Exception as e:
        logger.error(f"Unexpected error in actigraphy_day_view: {e}")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def actigraphy_stats(request, filename):
    """View for summary statistics across all days."""
    username, error_response = extract_username(request)
    if error_response:
        return error_response

    try:
        file_path = get_data_file_path(username, filename)
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV: {file_path}, Shape: {df.shape}, Columns: {list(df.columns)}")

        required_cols = {'Hour', 'Minute', 'Second', 'Millisecond', 'AccelX', 'AccelY', 'AccelZ'}
        if not required_cols.issubset(df.columns):
            return JsonResponse({'error': 'CSV file does not contain required columns'}, status=400)

        df['Time'] = df.apply(lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}", axis=1)
        df['Actigraphy'] = df.apply(lambda row: np.sqrt(row['AccelX']**2 + row['AccelY']**2 + row['AccelZ']**2), axis=1)
        df = df[['Time', 'Actigraphy']].dropna()

        daily_actigraphy, daily_time, _ = process_actigraphy_data(df)
        stats = [{
            "day_id": day,
            "day_number": day + 1,
            "accel_mean": round(np.mean(daily_actigraphy[day]), 2) if daily_actigraphy[day] else 'N/A'
        } for day in range(len(daily_actigraphy))]

        return render(request, "actigraphy/stats.html", {
            "stats": stats,
            "filename": filename,
            "username": username
        })

    except Exception as e:
        logger.error(f"Unexpected error in actigraphy_stats: {e}")
        return render(request, "actigraphy/stats.html", {
            "error_message": f"An unexpected error occurred: {str(e)}",
            "filename": filename,
            "username": username
        })

from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
from functools import lru_cache
from scipy.signal import butter, filtfilt, find_peaks
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def extract_username(request):
    """Extract username from request"""
    if request.user.is_authenticated:
        return request.user.username, None
    return None, JsonResponse({'error': 'Authentication required'}, status=401)

def time_to_seconds(time_str):
    """Convert time string to total seconds"""
    try:
        if '.' in time_str:
            h, m, s = time_str.split(':')
            s, ms = s.split('.')
            return int(h) * 3600 + int(m) * 60 + float(f"{s}.{ms}")
        else:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        logger.error(f"Failed to parse time '{time_str}': {e}")
        return None

def format_time_with_ms(total_seconds):
    """Convert total seconds back to formatted time string with milliseconds"""
    try:
        hours = int(total_seconds // 3600)
        remaining = total_seconds % 3600
        minutes = int(remaining // 60)
        seconds = remaining % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    except Exception as e:
        logger.error(f"Failed to format time {total_seconds}: {e}")
        return None

def process_compact_data(rows, day=None, from_seconds=None, to_seconds=None):
    """Process data, splitting into days based on significant time decreases."""
    try:
        daily_data = []
        daily_time = []
        current_day_data = {'GSR': [], 'PPG': [], 'Actigraphy': []}
        current_day_time = []
        previous_seconds = None
        current_day = 1

        for row in rows:
            time_seconds = time_to_seconds(row['Time'])
            if time_seconds is None:
                logger.warning(f"Skipping row with invalid time: {row['Time']}")
                continue

            if previous_seconds is not None and time_seconds < previous_seconds - 10:
                if day is not None and current_day == day:
                    break
                if current_day_data['GSR']:
                    daily_data.append(current_day_data)
                    daily_time.append(current_day_time)
                    logger.debug(f"Day {current_day} completed: {len(current_day_data['GSR'])} points")
                current_day += 1
                current_day_data = {'GSR': [], 'PPG': [], 'Actigraphy': []}
                current_day_time = []

            if day is not None and current_day == day:
                if from_seconds is not None and to_seconds is not None:
                    if not (from_seconds <= time_seconds <= to_seconds):
                        continue

            formatted_time = format_time_with_ms(time_seconds)
            if formatted_time:
                try:
                    current_day_data['GSR'].append(float(row['GSR']))
                    current_day_data['PPG'].append(float(row['PPG']))
                    current_day_data['Actigraphy'].append(float(row['Actigraphy']))
                    current_day_time.append(formatted_time)
                    previous_seconds = time_seconds
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid data in row: {row}, Error: {e}")
                    continue

        if current_day_data['GSR'] and (day is None or current_day == day):
            daily_data.append(current_day_data)
            daily_time.append(current_day_time)
            logger.debug(f"Final day {current_day}: {len(current_day_data['GSR'])} points")

        logger.info(f"Processed {len(daily_data)} days")
        return daily_data, daily_time

    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return [], []

def prepare_trading_chart_data(time_data, day_data, day_number):
    """Prepare data in format optimal for trading-style charts"""
    if not all([time_data, day_data['GSR'], day_data['PPG'], day_data['Actigraphy']]):
        logger.error(f"No data available for day {day_number}")
        return {'error': 'No data available'}
    
    try:
        x_times = [int(datetime.strptime(t, '%H:%M:%S.%f').timestamp() * 1000) for t in time_data]
        
        if len(x_times) > 5000:
            indices = np.linspace(0, len(x_times) - 1, 5000, dtype=int)
            x_times = [x_times[i] for i in indices]
            gsr_data = [day_data['GSR'][i] for i in indices]
            ppg_data = [day_data['PPG'][i] for i in indices]
            act_data = [day_data['Actigraphy'][i] for i in indices]
        else:
            gsr_data = day_data['GSR']
            ppg_data = day_data['PPG']
            act_data = day_data['Actigraphy']
        
        chart_data = {
            'day': day_number,
            'timestamps': x_times,
            'gsr': [{'time': t, 'value': v} for t, v in zip(x_times, gsr_data) if not np.isnan(v)],
            'ppg': [{'time': t, 'value': v} for t, v in zip(x_times, ppg_data) if not np.isnan(v)],
            'actigraphy': [{'time': t, 'value': v} for t, v in zip(x_times, act_data) if not np.isnan(v)],
            'min_time': min(x_times) if x_times else 0,
            'max_time': max(x_times) if x_times else 0,
            'gsr_min': min(gsr_data) if gsr_data else 0,
            'gsr_max': max(gsr_data) if gsr_data else 0,
            'ppg_min': min(ppg_data) if ppg_data else 0,
            'ppg_max': max(ppg_data) if ppg_data else 0,
            'act_min': min(act_data) if act_data else 0,
            'act_max': max(act_data) if act_data else 0
        }
        
        logger.debug(f"Chart data prepared for day {day_number}: {len(chart_data['gsr'])} points")
        return chart_data
    except Exception as e:
        logger.error(f"Error preparing chart data for day {day_number}: {e}")
        return {'error': f'Error preparing chart data: {str(e)}'}

def process_gsr(gsr, window=5):
    """Process GSR data with normalization and smoothing"""
    try:
        gsr = (gsr - np.min(gsr)) / (np.max(gsr) - np.min(gsr)) * 5000
        if len(gsr) >= window:
            gsr = pd.Series(gsr).rolling(window=window, center=True).mean().to_numpy()
        return gsr
    except Exception as e:
        logger.error(f"Error processing GSR: {e}")
        return np.nan

def process_actigraphy(accel_x, accel_y, accel_z, window=5):
    """Process actigraphy data with smoothing"""
    try:
        magnitude = np.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
        if len(magnitude) >= window:
            magnitude = pd.Series(magnitude).rolling(window=window, center=True).mean().to_numpy()
        return magnitude
    except Exception as e:
        logger.error(f"Error processing Actigraphy: {e}")
        return np.nan

@require_http_methods(["GET", "POST"])
def compact(request, filename, username=None):
    """
    View function to display GSR, PPG, and Actigraphy data from a local CSV file
    using a synchronized, multi-day chart layout. PPG plotting uses raw data.
    """
    username, error_response = extract_username(request)
    if error_response:
        return error_response

    try:
        local_files_dir = "/home/megha21337/krish22253/M-Health-1/mHealth/Users"
        file_path_f = os.path.join(local_files_dir, username)
        file_path = os.path.join(file_path_f, filename)

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise Http404("File not found")

        df = pd.read_csv(file_path)
        logger.info(f"CSV loaded. Shape: {df.shape}, Columns: {df.columns}")

        df['Time'] = df.apply(
            lambda row: f"{int(row['Hour']):02}:{int(row['Minute']):02}:{int(row['Second']):02}.{int(row['Millisecond']):03}",
            axis=1
        )
        df['PPG'] = df.apply(
            lambda row: row['Red'] / row['IR'] if row['IR'] != 0 else None, axis=1
        )
        df['GSR'] = process_gsr(df['GSR'].values)
        df['Actigraphy'] = process_actigraphy(
            df['AccelX'].values, df['AccelY'].values, df['AccelZ'].values
        )
        df = df[['Time', 'GSR', 'PPG', 'Actigraphy']].dropna()
        logger.info(f"Data after cleaning: {df.shape[0]} rows")

        rows = df.to_dict(orient='records')

        if request.method == 'POST':
            from_time = request.POST.get('from_time')
            to_time = request.POST.get('to_time')
            day = request.POST.get('day')

            if not all([from_time, to_time, day]):
                logger.error("Missing required filter parameters")
                return JsonResponse({'error': 'Missing required filter parameters'}, status=400)

            try:
                day = int(day)
                from_seconds = time_to_seconds(from_time + ':00')
                to_seconds = time_to_seconds(to_time + ':00')

                if any(x is None for x in [from_seconds, to_seconds]):
                    logger.error(f"Invalid time format: from_time={from_time}, to_time={to_time}")
                    return JsonResponse({'error': 'Invalid time format'}, status=400)

                if from_seconds > to_seconds:
                    logger.error("Start time must be before end time")
                    return JsonResponse({'error': 'Start time must be before end time'}, status=400)
            except ValueError as e:
                logger.error(f"Invalid day or time format: {e}")
                return JsonResponse({'error': 'Invalid day format'}, status=400)

            daily_data, daily_time = process_compact_data(rows, day, from_seconds, to_seconds)
            if not daily_data or day > len(daily_data):
                logger.error(f"No data found for day {day}")
                return JsonResponse({'error': 'No data found for the specified filters'}, status=404)

            chart_data = prepare_trading_chart_data(daily_time[0], daily_data[0], day)
            
            stats = {
                'ppg_avg': round(np.mean(daily_data[0]['PPG']), 2) if daily_data[0]['PPG'] else 'N/A',
                'gsr_avg': round(np.mean(daily_data[0]['GSR']), 2) if daily_data[0]['GSR'] else 'N/A',
                'actigraphy_avg': round(np.mean(daily_data[0]['Actigraphy']), 2) if daily_data[0]['Actigraphy'] else 'N/A'
            }
            
            logger.info(f"Returning filtered data for day {day}: {len(chart_data['gsr'])} points")
            return JsonResponse({'chart_data': chart_data, 'stats': stats})

        daily_data, daily_time = process_compact_data(rows)
        charts = []

        for i, (day_time, day_data) in enumerate(zip(daily_time, daily_data), start=1):
            chart_data = prepare_trading_chart_data(day_time, day_data, i)
            stats = {
                'ppg_avg': round(np.mean(day_data['PPG']), 2) if day_data['PPG'] else 'N/A',
                'gsr_avg': round(np.mean(day_data['GSR']), 2) if day_data['GSR'] else 'N/A',
                'actigraphy_avg': round(np.mean(day_data['Actigraphy']), 2) if day_data['Actigraphy'] else 'N/A'
            }
            charts.append({
                'day': i,
                'chart_data': chart_data,
                'stats': stats
            })

        logger.info(f"Rendering template with {len(charts)} charts")
        return render(request, 'compact.html', {'charts': charts, 'filename': filename})

    except Exception as e:
        logger.error(f"Unexpected error in compact view: {e}")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    """Prepare data in format optimal for trading-style charts"""
    if not all([time_data, day_data['GSR'], day_data['PPG'], day_data['Actigraphy']]):
        logger.error(f"No data available for day {day_number}")
        return {'error': 'No data available'}
    
    try:
        # Convert time strings to timestamps in milliseconds
        x_times = [int(datetime.strptime(t, '%H:%M:%S.%f').timestamp() * 1000) for t in time_data]
        
        # Downsample if data is large
        if len(x_times) > 5000:
            indices = np.linspace(0, len(x_times) - 1, 5000, dtype=int)
            x_times = [x_times[i] for i in indices]
            gsr_data = [day_data['GSR'][i] for i in indices]
            ppg_data = [day_data['PPG'][i] for i in indices]
            act_data = [day_data['Actigraphy'][i] for i in indices]
        else:
            gsr_data = day_data['GSR']
            ppg_data = day_data['PPG']
            act_data = day_data['Actigraphy']
        
        # Format data for chart
        chart_data = {
            'day': day_number,
            'timestamps': x_times,
            'gsr': [{'time': t, 'value': v} for t, v in zip(x_times, gsr_data) if not np.isnan(v)],
            'ppg': [{'time': t, 'value': v} for t, v in zip(x_times, ppg_data) if not np.isnan(v)],
            'actigraphy': [{'time': t, 'value': v} for t, v in zip(x_times, act_data) if not np.isnan(v)],
            'min_time': min(x_times) if x_times else 0,
            'max_time': max(x_times) if x_times else 0,
            'gsr_min': min(gsr_data) if gsr_data else 0,
            'gsr_max': max(gsr_data) if gsr_data else 0,
            'ppg_min': min(ppg_data) if ppg_data else 0,
            'ppg_max': max(ppg_data) if ppg_data else 0,
            'act_min': min(act_data) if act_data else 0,
            'act_max': max(act_data) if act_data else 0
        }
        
        logger.debug(f"Chart data prepared for day {day_number}: {len(chart_data['gsr'])} points")
        logger.debug(f"Chart data sample: {json.dumps(chart_data, indent=2)}")
        return chart_data
    except Exception as e:
        logger.error(f"Error preparing chart data for day {day_number}: {e}")
        return {'error': f'Error preparing chart data: {str(e)}'}
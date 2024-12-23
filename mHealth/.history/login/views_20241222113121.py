
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
            # Store the additional health-related information in the session
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

from django.contrib.auth.models import User
from .models import UserProfile  # Import the UserProfile model
from django.http import JsonResponse

def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')

        if otp == str(request.session.get('otp')):
            username = request.POST.get('username')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            if password1 != password2:
                return JsonResponse({'success': False, 'message': 'Passwords do not match'})

            # Check if the username or email already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username is already taken'})
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email is already registered'})

            try:
                # Create the user
                user = User.objects.create_user(username=username, email=email, password=password1)
                
                # Create the corresponding UserProfile entry
                UserProfile.objects.create(user=user)

                return JsonResponse({'success': True, 'message': 'Signup successful'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error creating user: {str(e)}'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid OTP. Please retry.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import random
import json

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

def calculate_heart_rate(ppg_values, sampling_rate=100):  # Assuming 100Hz sampling rate
    try:
        # Normalize the PPG signal
        ppg_normalized = (ppg_values - np.mean(ppg_values)) / np.std(ppg_values)
        
        # Find peaks in the PPG signal
        peaks, _ = find_peaks(ppg_normalized, 
                            distance=30,  # Minimum distance between peaks (adjust based on sampling rate)
                            height=0.1,   # Minimum height of peaks
                            prominence=0.2)  # Minimum prominence of peaks
        
        if len(peaks) < 2:
            return None
            
        # Calculate time differences between peaks
        peak_differences = np.diff(peaks)
        
        # Convert to heart rates (beats per minute)
        heart_rates = 60 * sampling_rate / peak_differences
        
        # Filter out physiologically impossible values
        valid_hrs = heart_rates[(heart_rates >= 40) & (heart_rates <= 200)]
        
        if len(valid_hrs) == 0:
            return None
            
        return {
            'min': round(np.min(valid_hrs), 1),
            'max': round(np.max(valid_hrs), 1),
            'avg': round(np.mean(valid_hrs), 1),
            'median': round(np.median(valid_hrs), 1),
            'mode': round(float(statistics.mode(valid_hrs.round(1))), 1)
        }
    except Exception as e:
        print(f"Error calculating heart rate: {e}")
        return None

def time_to_seconds(time_str):
    """Convert time string to seconds, supporting milliseconds format."""
    try:
        # Check if the time string contains milliseconds
        if '.' in time_str:
            time_parts, milliseconds = time_str.split('.')
            # Handle different lengths of millisecond precision
            ms_value = float(f"0.{milliseconds}")
        else:
            time_parts = time_str
            ms_value = 0

        # Split hours, minutes, seconds
        parts = time_parts.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            total_seconds = hours * 3600 + minutes * 60 + seconds + ms_value
            return total_seconds
    except (ValueError, AttributeError):
        return None
    return None



def format_time_with_ms(seconds):
    """Format seconds (including milliseconds) to time string."""
    whole_seconds = int(seconds)
    milliseconds = (seconds - whole_seconds) * 1000
    
    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    seconds = whole_seconds % 60
    
    if milliseconds > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{int(milliseconds):03d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

from datetime import datetime, timedelta, time
from django.shortcuts import render
from django.http import HttpResponse
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from plotly.offline import plot
import numpy as np
import pandas as pd
from scipy import stats

def time_to_seconds(time_str):
    """Convert time string to seconds, supporting milliseconds format."""
    try:
        # Check if the time string contains milliseconds
        if '.' in time_str:
            time_parts, milliseconds = time_str.split('.')
            # Handle different lengths of millisecond precision
            ms_value = float(f"0.{milliseconds}")
        else:
            time_parts = time_str
            ms_value = 0

        # Split hours, minutes, seconds
        parts = time_parts.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            total_seconds = hours * 3600 + minutes * 60 + seconds + ms_value
            return total_seconds
    except (ValueError, AttributeError):
        return None
    return None

def calculate_heart_rate(ppg_data):
    """Calculate heart rate statistics from PPG data."""
    try:
        if len(ppg_data) == 0:
            return None
            
        stats_dict = {
            'min': float(np.min(ppg_data)),
            'max': float(np.max(ppg_data)),
            'avg': float(np.mean(ppg_data)),
            'median': float(np.median(ppg_data)),
            'mode': float(stats.mode(ppg_data)[0])
        }
        return stats_dict
    except Exception:
        return None

def format_time_with_ms(seconds):
    """Format seconds (including milliseconds) to time string."""
    whole_seconds = int(seconds)
    milliseconds = (seconds - whole_seconds) * 1000
    
    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    seconds = whole_seconds % 60
    
    if milliseconds > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{int(milliseconds):03d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def display_csv(request, file_path):
    try:
        # Read the CSV file using pandas
        df = pd.read_csv(file_path)
        
        # Verify required columns exist
        if 'Time' not in df.columns or 'PPG' not in df.columns:
            return HttpResponse("Error: CSV file must contain 'Time' and 'PPG' columns", status=400)
        
        # Process data and prepare for plotting
        daily_ppg = []
        daily_time = []
        daily_stats = []
        search_time = request.GET.get('search_time')
        search_seconds = time_to_seconds(search_time) if search_time else None
        search_results = []

        current_day_ppg = []
        current_day_time = []
        previous_seconds = 0

        # Process each row in the dataframe
        for _, row in df.iterrows():
            time_seconds = time_to_seconds(row['Time'])
            if time_seconds is not None:
                try:
                    ppg_value = float(row['PPG'])

                    if time_seconds < previous_seconds:
                        # Calculate heart rate statistics for the current day
                        hr_stats = calculate_heart_rate(np.array(current_day_ppg))
                        if hr_stats:
                            daily_stats.append(hr_stats)
                        else:
                            daily_stats.append({
                                'min': 'N/A',
                                'max': 'N/A',
                                'avg': 'N/A',
                                'median': 'N/A',
                                'mode': 'N/A'
                            })
                        
                        daily_ppg.append(current_day_ppg)
                        daily_time.append(current_day_time)
                        current_day_ppg = []
                        current_day_time = []

                    formatted_time = format_time_with_ms(time_seconds)
                    current_day_ppg.append(ppg_value)
                    current_day_time.append(formatted_time)
                    previous_seconds = time_seconds

                    if search_seconds and abs(time_seconds - search_seconds) <= 300:
                        search_results.append({
                            'time': formatted_time,
                            'ppg': ppg_value,
                            'difference': abs(time_seconds - search_seconds)
                        })

                except ValueError:
                    continue

        # Append the last day's data
        if current_day_ppg and current_day_time:
            hr_stats = calculate_heart_rate(np.array(current_day_ppg))
            if hr_stats:
                daily_stats.append(hr_stats)
            else:
                daily_stats.append({
                    'min': 'N/A',
                    'max': 'N/A',
                    'avg': 'N/A',
                    'median': 'N/A',
                    'mode': 'N/A'
                })
            daily_ppg.append(current_day_ppg)
            daily_time.append(current_day_time)

        # Plot each day's data with improved layout
        graph_divs = []
        for i, (day_time, day_ppg) in enumerate(zip(daily_time, daily_ppg), start=1):
            fig = go.Figure()

            # Convert string times to datetime objects for proper plotting
            x_times = []
            for t in day_time:
                try:
                    # Parse time with milliseconds
                    if '.' in t:
                        time_parts, ms = t.split('.')
                        h, m, s = map(int, time_parts.split(':'))
                        ms = int(ms)
                        x_times.append(datetime.combine(
                            datetime.today().date(),
                            time(h, m, s, ms * 1000)  # Convert ms to microseconds
                        ))
                    else:
                        time_parts = t.split(':')
                        x_times.append(datetime.combine(
                            datetime.today().date(),
                            time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]))
                        ))
                except Exception:
                    continue

            fig.add_trace(go.Scatter(
                x=x_times,
                y=day_ppg,
                mode='lines',
                name=f'Day {i} PPG Data',
                line=dict(color='#007bff', width=1),
                hovertemplate='Time: %{x|%H:%M:%S.%L}<br>PPG: %{y:.2f}<extra></extra>'
            ))

            # Create time ticks for every hour
            tick_times = []
            tick_labels = []
            for hour in range(24):
                tick_time = datetime.combine(
                    datetime.today().date(),
                    time(hour, 0, 0)
                )
                tick_times.append(tick_time)
                tick_labels.append(f'{hour:02d}:00')

            fig.update_layout(
                title=dict(
                    text=f'PPG vs Time for Day {i}',
                    font=dict(size=20)
                ),
                xaxis=dict(
                    title='Time',
                    tickmode='array',
                    tickvals=tick_times,
                    ticktext=tick_labels,
                    tickangle=45,
                    tickfont=dict(size=10),
                    rangeslider=dict(
                        visible=True,
                        thickness=0.05
                    ),
                    type='date',
                    fixedrange=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgrey',
                    dtick='H1',
                    hoverformat='%H:%M:%S.%L',
                    automargin=True
                ),
                yaxis=dict(
                    title='PPG',
                    fixedrange=True,
                    range=[min(day_ppg) - (max(day_ppg) - min(day_ppg)) * 0.1,
                           max(day_ppg) + (max(day_ppg) - min(day_ppg)) * 0.1],
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='lightgrey'
                ),
                height=600,
                margin=dict(l=50, r=50, t=80, b=100),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
                dragmode='pan',
                plot_bgcolor='white',
                paper_bgcolor='white',
                modebar=dict(
                    remove=['zoomIn2d', 'zoomOut2d', 'autoScale2d'],
                    orientation='v'
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )

            # Configuration options
            config = {
                'scrollZoom': True,
                'displayModeBar': True,
                'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
                'displaylogo': False,
                'doubleClick': 'reset+autosize'
            }

            graph_div = plot(fig, output_type='div', config=config)
            graph_divs.append({
                'day': f'Day {i}',
                'graph': graph_div,
                'stats': daily_stats[i - 1]
            })

        context = {
            'graphs': graph_divs,
            'search_time': search_time,
            'search_results': search_results,
            'file_path': file_path,
        }

        return render(request, 'rough.html', context)

    except Exception as e:
        return HttpResponse(f"Error processing CSV file: {str(e)}", status=500)

# def display_csv(request, file_id):
#     # Fetch the GoogleSheet object using the file ID
#     google_sheet = get_object_or_404(GoogleSheet, id=file_id)

#     # Set up Google Sheets API credentials
#     scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
#     creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
#     client = gspread.authorize(creds)

#     # Open the Google Sheet by URL
#     try:
#         sheet = client.open_by_url(google_sheet.sheet_url).sheet1
#         rows = sheet.get_all_records()
#     except Exception as e:
#         return HttpResponse(f"Error accessing Google Sheet: {e}", status=500)

#     # Process data and prepare for plotting
#     daily_ppg = []
#     daily_time = []
#     daily_stats = []
#     search_time = request.GET.get('search_time')
#     search_seconds = time_to_seconds(search_time) if search_time else None
#     search_results = []

#     current_day_ppg = []
#     current_day_time = []
#     previous_seconds = 0

#     # Process each row in the sheet
#     for row in rows:
#         if 'PPG' in row and 'Time' in row:
#             time_seconds = time_to_seconds(row['Time'])
#             if time_seconds is not None:
#                 try:
#                     ppg_value = float(row['PPG'])

#                     if time_seconds < previous_seconds:
#                         # Calculate heart rate statistics for the current day
#                         hr_stats = calculate_heart_rate(np.array(current_day_ppg))
#                         if hr_stats:
#                             daily_stats.append(hr_stats)
#                         else:
#                             daily_stats.append({
#                                 'min': 'N/A',
#                                 'max': 'N/A',
#                                 'avg': 'N/A',
#                                 'median': 'N/A',
#                                 'mode': 'N/A'
#                             })
                        
#                         daily_ppg.append(current_day_ppg)
#                         daily_time.append(current_day_time)
#                         current_day_ppg = []
#                         current_day_time = []

#                     formatted_time = format_time_with_ms(time_seconds)
#                     current_day_ppg.append(ppg_value)
#                     current_day_time.append(formatted_time)
#                     previous_seconds = time_seconds

#                     if search_seconds and abs(time_seconds - search_seconds) <= 300:
#                         search_results.append({
#                             'time': formatted_time,
#                             'ppg': ppg_value,
#                             'difference': abs(time_seconds - search_seconds)
#                         })

#                 except ValueError:
#                     pass

#     # Append the last day's data
#     if current_day_ppg and current_day_time:
#         hr_stats = calculate_heart_rate(np.array(current_day_ppg))
#         if hr_stats:
#             daily_stats.append(hr_stats)
#         else:
#             daily_stats.append({
#                 'min': 'N/A',
#                 'max': 'N/A',
#                 'avg': 'N/A',
#                 'median': 'N/A',
#                 'mode': 'N/A'
#             })
#         daily_ppg.append(current_day_ppg)
#         daily_time.append(current_day_time)

#     # Plot each day's data with improved layout
#     graph_divs = []
#     for i, (day_time, day_ppg) in enumerate(zip(daily_time, daily_ppg), start=1):
#         fig = go.Figure()

#         # Convert string times to datetime objects for proper plotting
#         x_times = []
#         for t in day_time:
#             try:
#                 # Parse time with milliseconds
#                 if '.' in t:
#                     time_parts, ms = t.split('.')
#                     h, m, s = map(int, time_parts.split(':'))
#                     ms = int(ms)
#                     x_times.append(datetime.combine(
#                         datetime.today().date(),
#                         time(h, m, s, ms * 1000)  # Convert ms to microseconds
#                     ))
#                 else:
#                     time_parts = t.split(':')
#                     x_times.append(datetime.combine(
#                         datetime.today().date(),
#                         time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]))
#                     ))
#             except Exception:
#                 continue

#         fig.add_trace(go.Scatter(
#             x=x_times,
#             y=day_ppg,
#             mode='lines',
#             name=f'Day {i} PPG Data',
#             line=dict(color='#007bff', width=1),
#             hovertemplate='Time: %{x|%H:%M:%S.%L}<br>PPG: %{y:.2f}<extra></extra>'
#         ))

#         # Create time ticks for every hour
#         tick_times = []
#         tick_labels = []
#         for hour in range(24):
#             tick_time = datetime.combine(
#                 datetime.today().date(),
#                 time(hour, 0, 0)
#             )
#             tick_times.append(tick_time)
#             tick_labels.append(f'{hour:02d}:00')

#         fig.update_layout(
#             title=dict(
#                 text=f'PPG vs Time for Day {i}',
#                 font=dict(size=20)
#             ),
#             xaxis=dict(
#                 title='Time',
#                 tickmode='array',
#                 tickvals=tick_times,
#                 ticktext=tick_labels,
#                 tickangle=45,
#                 tickfont=dict(size=10),
#                 rangeslider=dict(
#                     visible=True,
#                     thickness=0.05
#                 ),
#                 type='date',
#                 fixedrange=False,
#                 showgrid=True,
#                 gridwidth=1,
#                 gridcolor='lightgrey',
#                 dtick='H1',
#                 hoverformat='%H:%M:%S.%L',
#                 automargin=True
#             ),
#             yaxis=dict(
#                 title='PPG',
#                 fixedrange=True,
#                 range=[min(day_ppg) - (max(day_ppg) - min(day_ppg)) * 0.1,
#                        max(day_ppg) + (max(day_ppg) - min(day_ppg)) * 0.1],
#                 showgrid=True,
#                 gridwidth=1,
#                 gridcolor='lightgrey'
#             ),
#             height=600,
#             margin=dict(l=50, r=50, t=80, b=100),
#             showlegend=True,
#             legend=dict(
#                 yanchor="top",
#                 y=0.99,
#                 xanchor="left",
#                 x=0.01
#             ),
#             dragmode='pan',
#             plot_bgcolor='white',
#             paper_bgcolor='white',
#             modebar=dict(
#                 remove=['zoomIn2d', 'zoomOut2d', 'autoScale2d'],
#                 orientation='v'
#             ),
#             hoverlabel=dict(
#                 bgcolor="white",
#                 font_size=12,
#                 font_family="Arial"
#             )
#         )

#         # Configuration options
#         config = {
#             'scrollZoom': True,
#             'displayModeBar': True,
#             'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
#             'displaylogo': False,
#             'doubleClick': 'reset+autosize'
#         }

#         graph_div = plot(fig, output_type='div', config=config)
#         graph_divs.append({
#             'day': f'Day {i}',
#             'graph': graph_div,
#             'stats': daily_stats[i - 1]
#         })

#     context = {
#         'graphs': graph_divs,
#         'search_time': search_time,
#         'search_results': search_results,
#         'file_id': file_id,
#     }

#     return render(request, 'rough.html', context)

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
            '/Users/krishbhoruka/Downloads/mHealth/credentials.json', scope)  # Replace with your credentials file path
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


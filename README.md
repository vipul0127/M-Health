# mHealth - PPG-based Health Monitoring System

## Description
**mHealth** is a **PPG-based health monitoring system** designed to track real-time physiological data for early detection of health issues. The system collects data from wearable devices using **Photoplethysmogram (PPG)** sensors and provides detailed insights into heart rate, sleep patterns, and stress levels. The application is designed to be **conscious**, requiring user consent to proceed, ensuring that health data is handled responsibly.

## Features

- **Login and Signup**
  - **User Signup**: New users can register on the platform by creating an account.
  - **No Email Verification**: Users are not required to verify their email before signing up.
  - **Consent Form**: After successful signup, users must fill a consent form before accessing the website. The system will not allow users to proceed without filling out the consent form.

- **File Upload and Viewing**
  - **Upload File**: Users can upload data files recorded by their sensors.
    - Users must provide a **file name** and **sheet link** to upload.
  - **View Files**: Users can view all the files they have uploaded, including timestamps and file names.

- **File Options After Upload**
  Once a file is uploaded, the user can take the following actions:
  - **Download HL7**: Download the data in HL7 format.
  - **View PPG**: View the PPG graph generated from the data in the file.
  - **View File**: View the raw file content.
  - **View HL7**: View the HL7 format version of the file data.

- **PPG Graph**
  - **View PPG Graph**: The system generates and displays a graph of the **PPG data** from the uploaded file.
    - The graph is plotted for **different days separately**, using **time-stamped data** from the sheet in the backend.

## Screenshots

Below are the images depicting various pages of the **mHealth** system:

- **Login Page**:  
  ![User Login](https://your-image-url.com/login.png)  
  *User Login Page*

- **Consent Form**:  
  ![Consent Form](https://your-image-url.com/consent-form.png)  
  *Consent Form Page*

- **File Upload Page**:  
  ![File Upload](https://your-image-url.com/upload.png)  
  *File Upload Page*

- **PPG Graph Display**:  
  ![PPG Graph](https://your-image-url.com/ppg-graph.png)  
  *PPG Graph Display*

## How It Works

1. **Login and Signup**
   - Users must sign up with a unique **username** and **password**.
   - No email verification is required, but after signing up, users must **fill the consent form** before they can proceed.

   ![Signup and Login](https://your-image-url.com/signup-login.png)  
   *Login and Signup Page*

2. **Consent Form**
   - The **consent form** is a mandatory step. Without agreeing to the terms, users cannot access any other features of the site.
   - After successful signup, users are redirected to fill out the consent form. Only after submitting this form can they access the rest of the website.

   ![Consent Form](https://your-image-url.com/consent-form.png)  
   *Consent Form Page*

3. **Uploading Files**
   - Users can upload files that contain data recorded by sensors.
   - Each file must be accompanied by a **file name** and **sheet link**. This ensures that the data is correctly linked and can be processed.
   
   ![File Upload](https://your-image-url.com/upload-file.png)  
   *File Upload Page*

4. **Viewing Files**
   - Once files are uploaded, users can view a list of all their uploaded files.
   - The system will display **timestamps** and **file names**, allowing users to easily track their uploaded data.

   ![View Files](https://your-image-url.com/view-files.png)  
   *View Uploaded Files Page*

5. **File Actions**
   For each uploaded file, users have four options:
   - **Download HL7**: Download the data in HL7 format.
   - **View PPG**: View a graphical representation of the PPG data.
   - **View File**: View the raw content of the uploaded file.
   - **View HL7**: View the data in HL7 format.

   ![File Actions](https://your-image-url.com/file-actions.png)  
   *File Actions Page*

6. **PPG Graph**
   - When users click on **View PPG**, a graph is displayed using data fetched from the uploaded file.
   - The graph will show **PPG readings** over time, with data separated by **different days** for better visualization.

   ![PPG Graph](https://your-image-url.com/ppg-graph.png)  
   *PPG Graph Display*

## Requirements

- Python 3.x
- Libraries: `Flask`, `matplotlib`, `numpy`, `pandas`, `ppg-analytics` (or custom PPG library)
- MySQL or similar database for managing user accounts and file uploads.
- **Frontend**: HTML, CSS (Bootstrap for UI), JavaScript
- **Backend**: Python Flask or Django

## Installation

1. Clone or download the repository to your local machine.
2. Install Python 3.x and necessary libraries:
   ```bash
   pip install -r requirements.txt

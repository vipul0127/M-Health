To incorporate the home page at the beginning of the user journey and ensure it serves as a central hub for accessing features, here’s how you can update the flow and structure of the **mHealth - PPG-based Health Monitoring System**:

---

# mHealth - PPG-based Health Monitoring System

## Home Page

### 🏠 **Home Page**
- Upon logging in, users will be redirected to the **Home Page**.
- The **Home Page** provides an overview of the system's available functionalities, including access to file uploads, file viewing, and data visualization.
- The layout includes quick links to the following:
  - **Upload Data File**
  - **View Uploaded Files**
  - **View Graphs**
  - **Download HL7 Data**

### 🚀 **User Login and Signup**
- **Sign Up**: Users must sign up with a **unique username** and **password**.
- **Login**: Returning users can log in to access their data.
- **Post-signup Action**: After signing up, users must fill the **consent form** before proceeding to the home page.

   ![Signup and Login](https://your-image-url.com/signup-login.png)  
   *Login and Signup Page*

---

### 📑 **Consent Form**
- The **consent form** is mandatory. Users cannot proceed to other pages unless the form is filled.

   ![Consent Form](https://your-image-url.com/consent-form.png)  
   *Consent Form Page*

---

### 📂 **Uploading Files**
- After signing up and accepting the consent form, users can upload data files containing **sensor recordings**.
- Each file must have a **file name** and a **sheet link** for the user to reference.

   ![File Upload](https://your-image-url.com/upload-file.png)  
   *File Upload Page*

---

### 🗂️ **Viewing Files**
- On the **Home Page**, users can view all **uploaded files**, with **timestamps** and **file names** displayed.

   ![View Files](https://your-image-url.com/view-files.png)  
   *View Uploaded Files Page*

---

### ⚙️ **File Actions**
For each uploaded file, users can:
- **⬇️ Download HL7**: Download the file in **HL7 format**.
- **📊 View PPG**: View a **graphical representation** of the **PPG data**.
- **📄 View File**: View the **raw file contents**.
- **🔍 View HL7**: View the data in **HL7 format**.

   ![File Actions](https://your-image-url.com/file-actions.png)  
   *File Actions Page*

---

### 📉 **PPG Graph**
- When users click on **View PPG**, a graph is generated using the **PPG data**.
- The graph displays **PPG readings** over time, with separate graphs for each day.

   ![PPG Graph](https://your-image-url.com/ppg-graph.png)  
   *PPG Graph Display*

---

### 🔎 **View HL7 Data**
- Users can view the **HL7 format data** for each uploaded file.
- This provides a detailed breakdown of the health metrics in HL7 format.

   ![HL7 View](https://your-image-url.com/view-hl7.png)  
   *View HL7 Data Page*

---

### ⬇️ **Download HL7**
- Users can download the **HL7** formatted data file for further analysis or storage.

   ![Download HL7](https://your-image-url.com/download-hl7.png)  
   *Download HL7 Page*

---

### 📄 **View Sheet Data**
- Users can view the **raw data sheet** of the uploaded file in tabular format, offering transparency of the data.

   ![View Sheet](https://your-image-url.com/view-sheet.png)  
   *View Sheet Data Page*

---

## Requirements

- Python 3.x
- Django 3.x or later
- MySQL or SQLite for database
- Required Libraries: `numpy`, `matplotlib`, `pandas`, etc.

---

## Installation and Setup

Follow the instructions provided earlier for **cloning the repository**, **installing dependencies**, **setting up the database**, and running the development server.

---

By integrating the **Home Page** as a starting point after login, it serves as a hub for users to access various functionalities like uploading files, viewing data, and downloading HL7-formatted reports. This updated structure enhances usability and ensures a streamlined user experience.

### Step 1: Clone the Repository

Clone the repository to your local machine:
```bash
git clone https://github.com/your-username/mhealth-django.git
cd mhealth-django
```

### Step 2: Install Dependencies

Create a virtual environment and install required dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### Step 3: Set Up the Database

Create a database in MySQL or use the default SQLite database.
Update the database settings in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Or 'sqlite3' for SQLite
        'NAME': 'mhealth_db',
        'USER': 'your-database-user',
        'PASSWORD': 'your-database-password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Step 4: Migrate the Database

Run the database migrations to create tables:
```bash
python manage.py migrate
```

### Step 5: Create a Superuser

Create a superuser to access the Django admin interface:
```bash
python manage.py createsuperuser
```

### Step 6: Run the Development Server

Start the server:
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Django Project Structure

Here’s an overview of the key Django files:

- **urls.py**: URL routing for the project.
  - Defines the URL patterns for the different views like login, consent form, file uploads, etc.

- **views.py**: Contains the logic for handling the HTTP requests.
  - Views for handling user authentication, consent form, file upload, etc.

- **models.py**: Defines the data models for users, files, and consent forms.

- **admin.py**: Registers models with the Django admin interface for easy management.

- **settings.py**: Contains the configuration for the Django project, including database settings and middleware.

- **manage.py**: Django's command-line utility for managing various administrative tasks (e.g., running the server, migrating the database).

## Code Snippets

Here’s an example of a database setup and running the server:

1. **Set up a database for user authentication and file uploads**:

   In `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',  # Or 'sqlite3' for SQLite
           'NAME': 'mhealth_db',
           'USER': 'your-database-user',
           'PASSWORD': 'your-database-password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

2. **Configure the Django server and connect to the database**:
   
   Ensure your database settings in `settings.py` match your database configuration. Then run migrations to create the necessary tables.

3. **Run the server**:

   For **Django**:
   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/` in your browser.
```

This update integrates the analysis of PPG data during various times and activities, as well as the conversion of the measured parameters into HL7 format for medical data exchange.

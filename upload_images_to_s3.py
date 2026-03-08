import os
import sys
import django
from django.core.files import File
from dotenv import load_dotenv

# Load environment variables from .env if needed
load_dotenv()

# Setup Django path resolution (since this script is outside school-backend)
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'school-backend')
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Import models now that Django is initialized
from users.models import User
from management.models import School

# ---------------------------------------------------------
# Local Configuration
# ---------------------------------------------------------
# The folder containing the images you want to upload
# Place "bulk_images" in the same directory as this script (/var/www/backend/)
LOCAL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bulk_images")

print("\nStarting Django ORM Bulk Image Upload...\n")

if not os.path.exists(LOCAL_FOLDER):
    print(f"Directory '{LOCAL_FOLDER}' does not exist. Creating it now.")
    print("Please put your images in there and re-run this script.")
    os.makedirs(LOCAL_FOLDER, exist_ok=True)
    sys.exit(0)

# ---------------------------------------------------------
# Upload Logic
# ---------------------------------------------------------
# We will match the filename (without extension) to a username or school code
import mimetypes

for filename in os.listdir(LOCAL_FOLDER):
    local_path = os.path.join(LOCAL_FOLDER, filename)
    
    # Skip directories, process only files
    if not os.path.isfile(local_path):
        continue
    
    # --- Example: Link to User by Username ---
    # Assume the filename is structured like 'username.jpg' or 'username.png'
    # For example, if filename is 'satyamrattan.png', username = 'satyamrattan'
    name_without_ext, ext = os.path.splitext(filename)
    
    try:
        # 1. Try matching a User by username
        user = User.objects.filter(username=name_without_ext).first()
        
        if user:
            print(f"Found User: {name_without_ext}. Uploading profile picture...")
            with open(local_path, 'rb') as f:
                # `user.profile_picture.save()` uses S3 automatically because of settings.py
                # It also uses the `upload_user_profile_picture` function we defined!
                user.profile_picture.save(filename, File(f), save=True)
            print(f"✅ Uploaded and linked to User: {name_without_ext}")
            continue # Move to next file
            
        # 2. Try matching a School by code
        school = School.objects.filter(code=name_without_ext).first()
        if school:
            print(f"Found School: {name_without_ext}. Uploading logo...")
            with open(local_path, 'rb') as f:
                school.logo.save(filename, File(f), save=True)
            print(f"✅ Uploaded and linked to School: {name_without_ext}")
            continue # Move to next file

        # 3. If neither matched
        print(f"⚠️ Skipped: {filename} (No matching username or school code found)")
                
    except Exception as e:
        print(f"❌ Failed processing {filename} | Error: {e}")

print("\nUpload process completed.\n")

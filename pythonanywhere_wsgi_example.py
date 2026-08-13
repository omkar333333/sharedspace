import sys
import os

# 1. Provide the path to your project folder
project_home = '/home/YOUR_USERNAME/YOUR_PROJECT_FOLDER'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# 2. Load environment variables (Optional, if you use .env)
# from dotenv import load_dotenv
# load_dotenv(os.path.join(project_home, '.env'))

# 3. Import the Flask app and name it "application" for WSGI to recognize it
from run import app as application

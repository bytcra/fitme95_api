# Exit on error
set -o errexit

pip install -r requirements.txt

# Apply any outstanding database migrations
python manage.py makemigrations
python manage.py migrate
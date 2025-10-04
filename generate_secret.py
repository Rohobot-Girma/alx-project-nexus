# generate_secret.py
from django.core.management.utils import get_random_secret_key

secret_key = get_random_secret_key()
print(f"DJANGO_SECRET_KEY: {secret_key}")
print(f"JWT_SECRET_KEY: {get_random_secret_key()}")
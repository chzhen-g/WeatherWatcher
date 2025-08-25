from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.create_user(username="geo", password="123")
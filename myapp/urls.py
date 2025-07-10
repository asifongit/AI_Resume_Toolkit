# myapp/urls.py

from django.urls import path
from myapp import views

app_name = 'myapp'  # This creates a namespace for this app's URLs.

urlpatterns = [
   path("index/", views.index, name='index'), # This will now be found at /app/
   path("about/", views.about, name='about'),
   path('services/', views.services, name='services'),
   path('contact/', views.contact, name='contact'),
]
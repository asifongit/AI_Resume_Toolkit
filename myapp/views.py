# myapp/views.py

from django.shortcuts import render
from datetime import datetime
from myapp.models import Contact
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect



@login_required(login_url='/')
def index(request):
    context = {
        'name': 'i am studing Django'
    }
    return render(request, 'index.html', context) # UPDATED

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        desc = request.POST.get('desc')
        date = datetime.today()
        new_contact = Contact(name=name, email=email, phone=phone, desc=desc, date=date)
        new_contact.save()
        messages.success(request, "Your message has been submitted successfully!")
        return redirect('myapp:contact')  # Redirect to avoid form resubmission

    return render(request, 'contact.html')



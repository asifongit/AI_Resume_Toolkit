from django.shortcuts import render, HttpResponse
from datetime import datetime
from myapp.models import Contact

def index(request):

    context={
        'name': 'i am studing Django'
        }# This function renders the index.html template when the home page is accessed.    
    return render(request,'index.html', context)


def about(request):
    # return HttpResponse("this is about page")
    return render(request, 'about.html')

def services(request):
    # return HttpResponse("this is services page")
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

    return render(request, 'contact.html')
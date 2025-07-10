# login_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from asgiref.sync import sync_to_async
from myapp.urls import urlpatterns
from myapp.views import index  # Importing index view from myapp



# Import the crewAI functionality from our new agents file
from .agents import run_crew

# Helper function to check if a user is a superuser (admin)
def is_admin(user):
    return user.is_superuser

# View for the login page
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_page')
        else:
            return redirect('myapp:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_page')
            else:
                return redirect('myapp:index')
    
    return render(request, 'login.html')

# View for user registration
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Add a success message to be displayed on the next page
            messages.success(request, 'Your account has been created successfully! You can now log in.')
            # Redirect to the login page
            return redirect('login')
        else:
            # If form is invalid, show errors
            return render(request, 'register.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# Asynchronous wrapper for checking authentication
@sync_to_async
def is_user_authenticated(user):
    return user.is_authenticated

# Asynchronous wrapper for checking superuser status
@sync_to_async
def is_user_superuser(user):
    return user.is_superuser

# View for the AI Resume Enhancer page - now fully asynchronous
async def resume_enhancer_view(request):
    # Manual authentication check using the async wrapper
    if not await is_user_authenticated(request.user):
        return redirect('login')

    # Manual check for superuser using the async wrapper
    if await is_user_superuser(request.user):
        return redirect('admin_page')

    context = {}
    if request.method == 'POST':
        resume_text = request.POST.get('resume', '')
        job_description_text = request.POST.get('job_description', '')
        
        context = {
            'resume_text': resume_text,
            'job_description_text': job_description_text
        }

        try:
            final_result = await sync_to_async(run_crew, thread_sensitive=True)(resume_text, job_description_text)
            formatted_result = final_result.replace('\n', '<br>')
            context['result'] = mark_safe(formatted_result)

        except Exception as e:
            print(f"Error during agent execution: {e}")
            context['error'] = "Sorry, we encountered an error while enhancing your resume. Please try again later."
        
        return render(request, 'resume_enhancer.html', context)

    return render(request, 'resume_enhancer.html', context)


@login_required(login_url='/')
def welcome_view(request):
    if request.user.is_superuser:
        return redirect('admin_page')
    return redirect('resume_enhancer')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')

# --- Admin Section ---

@user_passes_test(is_admin, login_url='/')
def admin_page_view(request):
    return render(request, 'admin_page.html')

@user_passes_test(is_admin, login_url='/')
def manage_users_view(request):
    users = User.objects.all()
    return render(request, 'manage_users.html', {'users': users})

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')

@user_passes_test(is_admin, login_url='/')
def add_user_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = CustomUserCreationForm()
    return render(request, 'add_edit_user.html', {'form': form})

class CustomUserChangeForm(UserChangeForm):
    password = None 
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')

@user_passes_test(is_admin, login_url='/')
def edit_user_view(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = CustomUserChangeForm(instance=user_to_edit)
    return render(request, 'add_edit_user.html', {'form': form})

@user_passes_test(is_admin, login_url='/')
def delete_user_view(request, user_id):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, id=user_id)
        if user_to_delete != request.user:
            user_to_delete.delete()
    return redirect('manage_users')

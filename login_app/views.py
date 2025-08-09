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

import tempfile # Added import
import os # Added import

# Import the crewAI functionality from our agents file
from .agents import run_crew

# Import the new section functions directly from section.py
from .section import get_headings_from_pdf, get_enhanced_section

# New import for the ATS functionality
from .ats_service import extract_text_from_pdf, generate_ats_evaluation

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
async def section_enhancer_view(request):
    context = {}

    if request.method == 'POST':
        # Handle PDF upload
        if 'resume_file' in request.FILES:
            uploaded_file = request.FILES['resume_file']
            if not uploaded_file.name.endswith('.pdf'):
                messages.error(request, "Please upload a PDF file.")
                return render(request, 'section.html', context)

            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name

            try:
                # Call the function from section.py
                headings, doc_content = await sync_to_async(get_headings_from_pdf, thread_sensitive=True)(tmp_file_path)
                request.session['full_resume_content'] = doc_content # Store in session
                request.session['extracted_headings'] = headings
                context['headings'] = headings
                context['resume_uploaded'] = True # Flag to show headings section
            except Exception as e:
                messages.error(request, f"Error processing PDF: {e}")
            finally:
                # Clean up the temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        # Handle section enhancement request (when a heading is clicked)
        elif 'selected_heading' in request.POST:
            selected_heading = request.POST.get('selected_heading')
            full_resume_content = request.session.get('full_resume_content')
            headings = request.session.get('extracted_headings')

            if not full_resume_content or not selected_heading:
                messages.error(request, "Please upload a resume and select a heading first.")
                context['headings'] = headings # Keep headings visible if they were there
                context['resume_uploaded'] = True # Keep this flag true
                return render(request, 'section.html', context)

            context['headings'] = headings # Keep headings visible
            context['resume_uploaded'] = True # Keep this flag true
            context['selected_heading_display'] = selected_heading # To highlight selected heading

            try:
                # Call the function from section.py
                enhanced_result = await sync_to_async(get_enhanced_section, thread_sensitive=True)(full_resume_content, selected_heading)
                context['enhanced_section_result'] = enhanced_result
            except Exception as e:
                messages.error(request, f"Error enhancing section: {e}")

    # For initial GET request or after POST, retrieve existing session data if any
    if 'extracted_headings' in request.session:
        context['headings'] = request.session['extracted_headings']
        context['resume_uploaded'] = True
    if 'full_resume_content' in request.session and 'extracted_headings' in request.session:
        context['resume_uploaded'] = True # Ensure this is true if any data is in session


    return render(request, 'section.html', context)

# New view for the ATS Resume Scanner
@login_required(login_url='/')
def ats_scanner_view(request):
    context = {}
    if request.method == 'POST':
        job_description = request.POST.get('job_description', '')
        
        # Check if a file was uploaded and get the 'file' from the request
        if 'resume_file' in request.FILES and job_description:
            uploaded_file = request.FILES['resume_file']
            try:
                # Call the refactored logic from ats_service.py
                resume_text = extract_text_from_pdf(uploaded_file)
                
                # Determine which button was clicked
                if 'hr_review' in request.POST:
                    response = generate_ats_evaluation(resume_text, job_description, 'hr_review')
                    context['response'] = mark_safe(response.replace('\n', '<br>'))
                    context['title'] = "HR Manager's Evaluation"
                elif 'ats_match' in request.POST:
                    response = generate_ats_evaluation(resume_text, job_description, 'ats_match')
                    context['response'] = mark_safe(response.replace('\n', '<br>'))
                    context['title'] = "ATS Percentage Match"

                # Keep the form values
                context['job_description'] = job_description
            
            except FileNotFoundError:
                messages.error(request, "Please upload a valid PDF resume.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, "Please upload a resume and provide a job description.")

    return render(request, 'ats_scanner.html', context)

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

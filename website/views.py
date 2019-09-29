from django.shortcuts import render, reverse, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import requests

from .forms import UserLoginForm, UserRegisterForm


# user login view
def login_view(request):
	context = {}
	template = 'website/login.html'
	# creating a form instance
	form = UserLoginForm(request.POST or None)

	if form.is_valid():
		# fetching the data
		username = form.cleaned_data.get('username')
		password = form.cleaned_data.get('password')
		# authenticate the user with validations
		user = authenticate(username=username, password=password)
		# creating a user session
		login(request, user)
		# flash message
		messages.success(request, "You're logged in Successfully.")
		return HttpResponseRedirect(reverse('home'))

	context['form'] = form
	return render(request, template, context)


# register view
def register_view(request):
	context = {}
	template = 'website/register.html'
	# creating a form instance
	form = UserRegisterForm(request.POST or None)

	if form.is_valid():
		user = form.save(commit=False)
		password = form.cleaned_data.get('password')
		user.set_password(password)
		# save the user credentials
		user.save()
		# # authenticate the user with validations
		# new_user = authenticate(username=username, password=password)
		# # creating a user session
		# login(request, new_user)
		# flash message
		messages.success(request, "Please login to continue.")
		return HttpResponseRedirect(reverse('login_view'))

	context['form'] = form
	return render(request, template, context)


@login_required()
def logout_view(request):
	messages.success(request, "You're Successfully logged out.")
	logout(request)
	return redirect(login_view)


@login_required(login_url=login_view)
def home(request):
	context = {}

	context['user'] = request.user
	return render(request, 'website/home.html', context)

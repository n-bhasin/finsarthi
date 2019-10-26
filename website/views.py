import requests
import csv, io, pandas
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import UserLoginForm, \
	UploadFile, EmployeeForm, Campaign, CampaignUser
from .models import Contact, Documents, NewCampaign, Information

camp_fetch = NewCampaign.objects.order_by('id').all()
doc_fetch = Documents.objects.order_by('id').all()


# confirm session view


# user login view
def login_view(request):
	context = {}
	template = 'website/login.html'
	# creating a form instance
	form = UserLoginForm(request.POST or None)
	user = None
	if form.is_valid():
		# fetching the data
		username = form.cleaned_data.get('username')
		password = form.cleaned_data.get('password')
		# authenticate the user with validations
		user = authenticate(username=username, password=password)
		# creating a user session
		login(request, user)

		# flash message
		if user:
			request.session['user_session'] = username

			messages.success(request, "You're logged in Successfully.")
			return HttpResponseRedirect(reverse('home'))

	context['form'] = form
	return render(request, template, context)


def form_view(request):
	if request.session.has_key('user_session'):
		# user = request.session['user_session']
		return HttpResponseRedirect(reverse('home'))
	else:
		return HttpResponseRedirect(reverse('login_view'))


# logout view
@login_required(login_url=login_view)
def logout_view(request):
	messages.success(request, "You're Successfully logged out.")
	logout(request)
	return redirect(login_view)


# home
@login_required(login_url=login_view)
def home(request):
	context = {}
	session_user = request.user
	if session_user is None:
		return HttpResponseRedirect(reverse(login_view))
	else:
		context['user'] = session_user
		context['camp_fetch'] = camp_fetch

		return render(request, 'website/home.html', context)


@login_required(login_url=login_view)
def add_employee(request):
	context = {}
	if request.user.first_name == 'Admin':
		employee_form = EmployeeForm(request.POST or None)

		if employee_form.is_valid():
			employee_form.save()
			messages.success(request, "User is Added")
			return HttpResponseRedirect(reverse('add_employee'))
		context['employee_form'] = employee_form
		context['users'] = User.objects.order_by("id").all()
		return render(request, 'website/add_employee.html', context)
	messages.error(request, "You are not authorized.")
	return HttpResponseRedirect(reverse('home'))


@login_required(login_url=login_view)
def edit(request, id):
	context = {}

	employee = get_object_or_404(User, id=id)
	if request.method == 'POST':
		employee_form = EmployeeForm(request.POST, instance=employee)
		if employee_form.is_valid():
			employee_form.save()
			messages.success(request, "User has been edited.")
			return HttpResponseRedirect(reverse('add_employee'))
	else:
		employee_form = EmployeeForm(instance=employee)
		context['employee_form'] = employee_form
		return render(request, 'website/edit.html', context)


@login_required(login_url=login_view)
def delete(request, id):
	context = {}
	if request.user.first_name == 'Admin':
		employee = get_object_or_404(User, id=id)
		if request.method == 'POST':
			employee.delete()
			messages.success(request, "User is deleted.")
			return HttpResponseRedirect(reverse('add_employee'))
		else:
			messages.error(request, "User is deleted.")
			context['employee'] = employee
			return render(request, 'website/delete.html', context)
	messages.error(request, "You are not authorized.")
	return HttpResponseRedirect(reverse('home'))


# @role_required(allowed_roles=['Admin', ])
@login_required(login_url=login_view)
def create_campaign(request):
	context = {}
	# print(request.user.groups.values().get())
	if request.user.first_name == 'Admin':
		campaign_form = Campaign(request.POST or None)

		if campaign_form.is_valid():
			print('yes')
			campaign_form.save()
			messages.success(request, "Campaign is created.")
			return HttpResponseRedirect(reverse(home))

		context['campaign_form'] = campaign_form
		messages.error(request, "Fill the details again.")
		return render(request, 'website/campaign.html', context)
	messages.error(request, "You are not authorized.")
	return HttpResponseRedirect(reverse('home'))


@login_required(login_url=login_view)
def detail_campaign(request, id):
	context = {}
	detail = get_object_or_404(NewCampaign, id=id)
	session_user = request.user

	context['camp_detail'] = detail

	context['user'] = session_user
	return render(request, 'website/detail_campaign.html', context)


# @role_required(allowed_roles=['Admin', ])
@login_required(login_url=login_view)
def add_campaign_user(request, id):
	context = {}
	if request.user.first_name == 'Admin':
		camp_id = get_object_or_404(NewCampaign, id=id)
		camp_user = CampaignUser(request.POST, instance=camp_id)
		if request.method == 'POST':
			if camp_user.is_valid():
				camp_user.save()
				messages.success(request, "User is added.")
				return HttpResponseRedirect(reverse('detail_campaign', args=[camp_id.id, ]))
		else:
			cu = CampaignUser(instance=camp_id)
			context['camp_user'] = cu
			context['camp_id'] = camp_id
			return render(request, 'website/add_campaign_user.html', context)
	return render(request, 'website/home.html', context)


@login_required(login_url=login_view)
def edit_camp(request, id):
	cid = get_object_or_404(NewCampaign, id=id)
	print(cid)
	if request.user.first_name == 'Admin':
		if request.method == 'POST':
			campaign_form = Campaign(request.POST, instance=cid)
			if campaign_form.is_valid():
				campaign_form.save()
				messages.success(request, 'Changes are done successfully.')
				return HttpResponseRedirect(reverse('detail_campaign', args=[cid.id, ]))
			else:
				messages.error(request, 'Failed.')
		else:
			campaign_form = Campaign(instance=cid)
			return render(request, 'website/edit_camp.html', {'campaign_form': campaign_form})
	messages.error(request, "You are not authorized.")
	return HttpResponseRedirect(reverse('home'))


@login_required(login_url=login_view)
def delete_camp(request, id):
	cid = get_object_or_404(NewCampaign, id=id)
	print(cid)
	if request.user.first_name == 'Admin':
		if request.method == 'POST':
			cid.delete()
			messages.success(request, 'Campaign is deleted.')
			return HttpResponseRedirect(reverse('home'))
		else:
			print('no')
			return render(request, 'website/delete_camp.html', {'campaign_form': cid})
	messages.error(request, "You are not authorized.")
	return HttpResponseRedirect(reverse('home'))


@login_required(login_url=login_view)
def user_detail(request, id):
	user_id = get_object_or_404(NewCampaign, id=id)
	print(user_id)
	return render(request, 'website/user_detail.html', {'user_id': user_id})


@login_required(login_url=login_view)
def file_upload(request):
	context = {}

	form = UploadFile(request.POST, request.FILES)
	print(form)
	if request.method == 'POST':
		csv_file = request.FILES['document']
		new_camp_id = request.POST['new_camp']
		print(new_camp_id)
		if not csv_file.name.endswith('.csv'):
			print(csv_file.name.endswith('.csv'))
			messages.error(request, 'Upload only csv files.')
			return HttpResponseRedirect(reverse('prospect'))
		else:
			if form.is_valid():
				csv_file = pandas.read_csv(csv_file, header=0)
				csv_file_list = csv_file.values.tolist()
				print(csv_file_list)
				for column in csv_file_list:
					_, created = Contact.objects.update_or_create(
						name=column[0],
						phone_number=column[1],
						new_cont_id=new_camp_id
					)

				context['csv_file'] = csv_file
				form.save()
				messages.success(request, "FIle is uploaded")
				return HttpResponseRedirect(reverse('prospect'))

	context["form"] = form
	return render(request, 'website/prospect.html', context)


@login_required(login_url=login_view)
def prospect(request):
	context = {}

	form_upload = UploadFile(request.POST or None)

	context['form_upload'] = form_upload

	context['fetch'] = doc_fetch

	return render(request, 'website/prospect.html', context)


@login_required(login_url=login_view)
def browse_prospects(request, id):
	context = {}
	pid = get_object_or_404(NewCampaign, id=id)
	fetch_data = Contact.objects.filter(new_cont_id=pid.id).all()
	fetch_info = Information.objects.filter(contact_id=pid.id).all()
	# print(fetch_data)
	context['camp_fetch'] = pid
	context['fetch_data'] = fetch_data
	context['fetch_info'] = fetch_info

	return render(request, 'website/browse_prospects.html', context)


@login_required(login_url=login_view)
def prospect_detail(request, id):
	context = {}
	pid = get_object_or_404(Contact, id=id)
	# form = ContactInformation(request.POST or None)
	# print(pid.id)

	if request.method == "POST":
		email = request.POST['email']
		disposition = request.POST['disposition']
		remark = request.POST['remarks']
		Information.objects.update_or_create(
			email=email, status=disposition, remarks=remark, contact_id=pid.id
		)
		return HttpResponseRedirect(reverse(browse_prospects, args=[pid.id, ]))

	else:
		context['contact'] = pid
		return render(request, 'website/prospect_detail.html', context)

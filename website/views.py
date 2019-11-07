import requests
import pandas, random, string
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .tokens import account_activation_token

from .forms import UserLoginForm, \
	UploadFile, EmployeeForm, Campaign, CampaignUser, UserDetail
from .models import Contact, Documents, NewCampaign, Information

camp_fetch = NewCampaign.objects.order_by('id').all()
doc_fetch = Documents.objects.order_by('id').all()


# confirm session view
def form_view(request):
	if request.session.has_key('user_session'):
		# user = request.session['user_session']
		return HttpResponseRedirect(reverse('home'))
	else:
		return HttpResponseRedirect(reverse('login_view'))


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
	if request.method == 'POST':
		form = EmployeeForm(request.POST or None)
		if form.is_valid():
			email = form.cleaned_data.get('email')

			user = form.save(commit=False)
			user.username = email.split('@')[0]
			password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
			print(password)
			user.password = make_password(password=password, salt=None)
			user.is_active = False

			user.save()
			form.roleSave()
			current_site = get_current_site(request)
			message = render_to_string('acc_activate_email.html', {
				'user': user,
				'password': password,
				'domain': current_site.domain,
				'uid': urlsafe_base64_encode(force_bytes(user.pk)),
				'token': account_activation_token.make_token(user),
			})
			mail_subject = 'Activate your account.'
			to_email = form.cleaned_data.get('email')
			email = EmailMessage(mail_subject, message, to=[to_email])
			email.send()
			messages.success(request, "Activation Link is Sent Successfully.")
			return HttpResponseRedirect(reverse('home'))

	else:
		form = EmployeeForm()
		context['employee_form'] = form
		context['users'] = User.objects.order_by("id").all()
		return render(request, 'website/add_employee.html', context)


def activate(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		print()
		user = User.objects.get(pk=uid)

	except(TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None
	if user is not None and account_activation_token.check_token(user, token):
		user.is_active = True
		user.save()
		login(request, user)
		messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
		return redirect(login_view)
	else:
		return HttpResponse('Activation link is invalid!')


@login_required(login_url=login_view)
def edit(request, id):
	context = {}

	employee = get_object_or_404(User, id=id)
	if request.user.first_name == 'Admin':

		if request.method == 'POST':
			form = EmployeeForm(request.POST, instance=employee)
			email = request.POST['email']
			role = request.POST['role']
			print(email, role)
			print(form.is_valid())
			if form.is_valid():
				print('yes valid')
				form.roleSave()
				form.save()
				messages.success(request, "User edited Successfully.")
				context['employee_form'] = form
				return HttpResponseRedirect(reverse(add_employee))
			else:
				messages.error(request, 'return none')
				raise Http404
		else:
			employee_form = EmployeeForm(instance=employee)
			context['employee_form'] = employee_form
			return render(request, 'website/edit.html', context)

	elif request.user.first_name == 'Admin' or 'Telecaller' or 'Field Exec' or 'Manager':
		employee_form = UserDetail(request.POST, instance=employee)
		if request.method == 'POST':
			if employee_form.is_valid():
				employee_form.save()
				messages.success(request, "User has been edited.")
				context['employee_form'] = employee_form
				return render(request, 'website/add_employee.html', context)
		else:
			employee_form = UserDetail(instance=employee)
			context['employee_form'] = employee_form
			return render(request, 'website/edit.html', context)
	else:
		messages.success(request, "You are not Authorized.")
		return HttpResponseRedirect(reverse(home))


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
		new_camp_id = request.POST['campId']
		doc = form.save(commit=False)
		print(new_camp_id)
		if not csv_file.name.endswith('.csv'):
			print(csv_file.name.endswith('.csv'))
			messages.error(request, 'Upload only csv files.')
			return HttpResponseRedirect(reverse(home))
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
				doc.new_camp_id = new_camp_id
				doc.save()
				context['csv_file'] = csv_file
				messages.success(request, "FIle is uploaded")
				return HttpResponseRedirect('%s/prospect' % new_camp_id)

	context["form"] = form
	return render(request, 'website/prospect.html', context)


@login_required(login_url=login_view)
def prospect(request, id):
	context = {}

	form_upload = UploadFile(request.POST or None)

	context['form_upload'] = form_upload

	context['fetch'] = doc_fetch
	context['camp_id'] = id

	return render(request, 'website/prospect.html', context)


@login_required(login_url=login_view)
def browse_prospects(request, id):
	context = {}
	pid = get_object_or_404(NewCampaign, id=id)
	fetch_data = Contact.objects.filter(new_cont_id=pid.id).all()

	# print(fetch_data)
	context['camp_fetch'] = pid
	context['fetch_data'] = fetch_data

	return render(request, 'website/browse_prospects.html', context)


@login_required(login_url=login_view)
def prospect_detail(request, id):
	context = {}

	pid = get_object_or_404(Contact, id=id)
	handler = request.user.username
	fetch_info = Information.objects.filter(contact_id=pid.id).order_by('-id').all()

	# Information.objects.create(user_assign=handler)
	# updated_id = Information.objects.filter(user_assign=handler).order_by('-id').first()
	# print(updated_id.id)

	if request.method == "POST":
		wrong_number = request.POST.get('wrongNumber')
		print(wrong_number)

		disposition = request.POST.get('disposition')
		sub_disposition = request.POST.get('unqualified_disposition')
		callback = request.POST['callback_datetime']
		appointment_callback = request.POST['appointment_datetime']
		remark = request.POST['remarks']
		Information.objects.update_or_create(
			wrong_number=wrong_number, disposition=disposition, sub_disposition=sub_disposition,
			callback_follow_up=callback, appointment_follow_up=appointment_callback,
			remarks=remark, contact_id=pid.id, user_assign=handler
		)
		messages.success(request, 'Successfully saved')
		return HttpResponseRedirect('prospect_detail')

	else:
		context['contact'] = pid
		context['contact_info'] = fetch_info
		return render(request, 'website/prospect_detail.html', context)

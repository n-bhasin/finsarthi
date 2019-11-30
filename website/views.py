import os, time, timeit

import requests
import pandas, random, string
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.db import connection
from .tokens import account_activation_token

from .forms import UserLoginForm, \
	UploadFile, EmployeeForm, Campaign, CampaignUser, UserDetail, Contacts
from .models import Contact, Documents, NewCampaign, Information
from tele_caller.decorator import role_required

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
	messages.success(request, form.errors)
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
	print(request.user.id)
	# cursor = connection.cursor()
	# cursor.execute("select website_newcampaign.name AS campaignId, website_newcampaign.name AS campaignName from  ")
	if session_user is None:
		return HttpResponseRedirect(reverse(login_view))
	else:
		context['user'] = session_user
		camp_data = NewCampaign.objects.filter(camp_user=request.user.id).order_by('id').all()
		camp_data_admin = NewCampaign.objects.order_by('id').all()
		context['camp_fetch'] = camp_data
		context['camp_fetch_admin'] = camp_data_admin

		context['callback'] = notification(request)

		return render(request, 'website/home.html', context)


@login_required(login_url=login_view)
@role_required(allowed_roles=True)
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
		messages.success(request, 'Thank you for your email confirmation. Now you can update your account password.')
		return redirect('password_set')
	else:
		return HttpResponse('Activation link is invalid!')


@login_required(login_url=login_view)
def password_set(request):
	context = {}
	if request.method == 'POST':
		employee_form = UserDetail(request.POST, instance=request.user)
		print('yes')
		password1 = request.POST.get('password1')
		password2 = request.POST.get('password2')
		print(password1, password2)
		print(employee_form.errors)

		if employee_form.is_valid():
			print('valid')

			employee_form.save()
			messages.success(request, "Password updated successfully")
			context['employee_form'] = employee_form

			return redirect(home)
		else:
			print('yes else')
			messages.success(request, employee_form.errors)
			return HttpResponseRedirect(reverse('password_set'))
	else:
		employee_form = UserDetail(instance=request.user)
		context['employee_form'] = employee_form
		return render(request, 'website/edit.html', context)


@login_required(login_url=login_view)
def edit(request, id):
	context = {}

	employee = get_object_or_404(User, id=id)

	if request.user.is_superuser:

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

	elif request.user.is_superuser is False:

		if request.method == 'POST':
			employee_form = UserDetail(request.POST, instance=employee)
			print('yes')
			password1 = request.POST.get('password1')
			password2 = request.POST.get('password2')
			print(password1, password2)
			print(employee_form.errors)

			if employee_form.is_valid():
				print('valid')

				employee_form.save()
				messages.success(request, "User has been edited.")
				context['employee_form'] = employee_form
				return render(request, 'website/add_employee.html', context)
			else:
				print('yes else')
				messages.success(request, employee_form.errors)
				return HttpResponseRedirect(reverse('edit', args=[id, ]))
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
	if request.user.is_superuser == True:
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
	if request.user.is_superuser == True:
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
	fetch_data = Contact.objects.filter(new_cont_id=detail.id).all()
	session_user = request.user

	context['camp_detail'] = detail
	context['user'] = session_user
	context['fetch_data'] = fetch_data
	context['pending_calls'] = pending_call_notification(request, detail.id)
	return render(request, 'website/detail_campaign.html', context)


# @role_required(allowed_roles=['Admin', ])
@login_required(login_url=login_view)
def add_campaign_user(request, id):
	context = {}
	cursor = connection.cursor()
	cursor1 = connection.cursor()
	if request.user.is_superuser == True:
		camp_id = get_object_or_404(NewCampaign, id=id)
		print("camp user id", camp_id.id)
		camp_user = CampaignUser(request.POST or None)
		if request.method == 'POST':
			user_value = request.POST["camp_user"]
			# print(user_value)
			cursor1.execute("select user_id from website_newcampaign_camp_user "
			                "where website_newcampaign_camp_user.newcampaign_id={0} AND website_newcampaign_camp_user.user_id={1}".format(
				camp_id.id, user_value))

			if cursor1.fetchone():
				print('yes')
				cu = CampaignUser(instance=camp_id)
				context['camp_user'] = cu
				context['camp_id'] = camp_id
				context['pending_calls'] = pending_call_notification(request, camp_id.id)
				messages.success(request, "User already exist.")
				return render(request, 'website/add_campaign_user.html', context)
			else:
				cursor.execute(
					"INSERT INTO website_newcampaign_camp_user(newcampaign_id, user_id) values({0}, {1})".format(
						camp_id.id,
						user_value))
				print(cursor.fetchall())
				messages.success(request, "User is added.")
				return HttpResponseRedirect(reverse('detail_campaign', args=[camp_id.id, ]))

		else:
			cu = CampaignUser(instance=camp_id)
			context['camp_user'] = cu
			context['camp_id'] = camp_id
			context['pending_calls'] = pending_call_notification(request, camp_id.id)
			return render(request, 'website/add_campaign_user.html', context)

	return render(request, 'website/home.html', context)


@login_required(login_url=login_view)
def edit_camp(request, id):
	cid = get_object_or_404(NewCampaign, id=id)
	print(cid)
	if request.user.is_superuser == True:
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
	if request.user.is_superuser == True:
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
				doc.new_camp_id = new_camp_id
				doc.save()
				# csv_file = pandas.read_csv(csv_file, header=0)
				# csv_file_list = csv_file.values.tolist()
				# print(csv_file_list)
				# for column in csv_file_list:
				# 	_, created = Contact.objects.update_or_create(
				# 		name=column[0],
				# 		phone_number=column[1],
				# 		new_cont_id=new_camp_id
				# 	)

				context['csv_file'] = csv_file
				messages.success(request, "FIle is uploaded")
				return redirect('%s/prospect' % new_camp_id)

	context["form"] = form
	return render(request, 'website/prospect.html', context)


@login_required(login_url=login_view)
def prospect(request, id):
	context = {}

	form_upload = UploadFile(request.POST or None)

	context['form_upload'] = form_upload

	context['fetch'] = doc_fetch
	context['camp_id'] = id
	context['pending_calls'] = pending_call_notification(request, id)
	return render(request, 'website/prospect.html', context)


def csv_import(request):
	context = {}

	if request.method == 'POST':
		strt_time = time.time()
		print('post')
		new_camp_id = request.POST['campId']
		file_id = request.POST['fileId']
		print(file_id)
		filename = Documents.objects.filter(id=file_id).all()
		fetch_file = ''
		for u in filename:
			fetch_file = u.document.name
			print(fetch_file)

		csv_file = pandas.read_csv('documents/'+fetch_file, header=0)
		print(csv_file)
		csv_file_list = csv_file.values.tolist()
		print(csv_file_list)
		for column in csv_file_list:
			_, created = Contact.objects.update_or_create(
				name=column[0],
				phone_number=column[1],
				new_cont_id=new_camp_id
			)
		context['csvdata'] = csv_file_list
		messages.success(request, "data imported")
		end_time = time.time()
		print("execution time: ", end_time - strt_time)
		return redirect('%s/prospect' % new_camp_id)
	else:
		print('else')
		messages.success(request, "data importing")
		return render(request, 'userdetail.html', )


@login_required(login_url=login_view)
def browse_prospects(request, id):
	context = {}
	cursor = connection.cursor()
	pid = get_object_or_404(NewCampaign, id=id)

	handler_contacts = Contacts()
	cursor.execute(
		"select auth_user.username from auth_user inner join website_contact on auth_user.id=website_contact.user_id "
		"where new_cont_id={0}".format(pid.id))
	contact_handler = ''

	if request.method == 'POST':
		form = Contacts(request.POST, None)
		# handler = request.POST.getlist('handler')
		# print("handler: ", handler)
		user = request.POST['user']
		print("user", user)
		if form.is_valid():
			print('yes')
			Contact.objects.filter(new_cont_id=pid.id).update(user_id=user)
			messages.success(request, "Handler is assigned succesfully.")
			return HttpResponseRedirect('browse_prospects')
		else:
			print('no')
		# print(handler)
		print(user)
		print(form)

	for hand in cursor.fetchall():
		print(hand)
		if hand == '':
			contact_handler = 'Not Assigned'
			context['hand'] = contact_handler
		else:
			contact_handler = hand
			context['hand'] = contact_handler[0]
	print(contact_handler)
	context['camp_fetch'] = pid
	context['handler'] = handler_contacts
	context['pending_calls'] = pending_call_notification(request, int(pid.id))

	fetch_data = Contact.objects.filter(new_cont_id=pid.id).all()
	fetch_data_called = Contact.objects.filter(user_id=request.user.id, status=False and True).all()

	paginator = Paginator(fetch_data, 10)
	page = request.GET.get('page')
	contacts = paginator.get_page(page)
	context['fetch_data'] = contacts
	context['fetch_data_called'] = fetch_data_called
	print(fetch_data)
	return render(request, 'website/browse_prospects.html', context)


@login_required(login_url=login_view)
def prospect_detail(request, id):
	context = {}
	# id here is contact id
	pid = get_object_or_404(Contact, id=id)
	print(id)
	print(pid.id)

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
		contact = Information.objects.filter(contact_id=pid.id)
		print("***", contact)
		Information.objects.filter(contact_id=pid.id).update_or_create(
			wrong_number=wrong_number, disposition=disposition, sub_disposition=sub_disposition,
			callback_follow_up=callback, appointment_follow_up=appointment_callback,
			remarks=remark, contact_id=pid.id
		)
		if disposition == "Interested":
			# print('yes')
			Contact.objects.filter(id=pid.id).update(status=True)
		if disposition == "Unqualified":
			# print('u')
			Contact.objects.filter(id=pid.id).update(status=True)
		if callback != "":
			# print(callback)
			# print('cc')
			Contact.objects.filter(id=pid.id).update(status=False)
		if appointment_callback != "":
			# print('ac')
			Contact.objects.filter(id=pid.id).update(status=False)

		notification(request)
		messages.success(request, 'Successfully saved')

		return HttpResponseRedirect('prospect_detail')

	else:
		context['contact'] = pid
		context['contact_info'] = fetch_info
		return render(request, 'website/prospect_detail.html', context)


def pending_calls(request, id):
	context = {}
	# id here is contact id
	name = NewCampaign.objects.filter(id=id).all()

	cursor = connection.cursor()
	cursor.execute(
		"SELECT website_contact.id, website_contact.name, website_contact.phone_number FROM website_contact where website_contact.status IS NULL AND "
		"website_contact.new_cont_id={0} OR website_contact.status=false AND website_contact.new_cont_id={1} "
		"ORDER BY id ASC ".format(id, id))

	contact_list = []
	for cid in cursor.fetchall():
		contact_list.append(cid)
		# contact_list.append(name)
		# contact_list.append(phone)
		print(cid)

	if contact_list is not None:
		print("m not none")
		# print(cursor.fetchone())

		print(contact_list)
		context['contact_list'] = contact_list[0][0]
		print(contact_list[0][0])
		context['pending_calls'] = pending_call_notification(request, int(id))
		context['camp_detail'] = name[0]

		return render(request, "website/pending_calls.html", context)
	else:
		context['contact_list'] = contact_list
		context['pending_calls'] = pending_call_notification(request, int(id))
		return render(request, "website/pending_calls.html", context)


def pending_calls_details(request, id):
	context = {}
	# id here is contact id
	cursor = connection.cursor()
	cursor.execute(
		"select website_contact.new_cont_id from website_contact where website_contact.id='%s' " % id)
	new_cont_id = ''
	for new_cont in cursor.fetchone():
		context['new_cont'] = new_cont
		new_cont_id = new_cont
	pid = get_object_or_404(Contact, id=id)
	campaign_name = NewCampaign.objects.filter(id=new_cont_id).all()

	print(id)
	print(campaign_name)

	fetch_info = Information.objects.filter(contact_id=pid.id).order_by('-id').all()
	print("**fetch_info", fetch_info)
	# Information.objects.create(user_assign=handler)
	# updated_id = Information.objects.filter(user_assign=handler).order_by('-id').first()
	# print(updated_id.id)

	if request.method == "POST":
		btn = request.POST.get('btn-next')
		btnstop = request.POST.get('btn-stop')
		print("btnn: ", btn)
		print("btnstop: ", btnstop)
		if request.POST.get('btn-next'):
			print("btn-next none")
			wrong_number = request.POST.get('wrongNumber')
			print(wrong_number)

			disposition = request.POST.get('disposition')
			sub_disposition = request.POST.get('unqualified_disposition')
			callback = request.POST['callback_datetime']
			appointment_callback = request.POST['appointment_datetime']
			remark = request.POST['remarks']
			contact = Information.objects.filter(contact_id=pid.id)
			print("***", contact)
			Information.objects.filter(contact_id=pid.id).update_or_create(
				wrong_number=wrong_number, disposition=disposition, sub_disposition=sub_disposition,
				callback_follow_up=callback, appointment_follow_up=appointment_callback,
				remarks=remark, contact_id=pid.id
			)
			if disposition == "Interested":
				# print('yes')
				Contact.objects.filter(id=pid.id).update(status=True)
			if disposition == "Unqualified":
				# print('u')
				Contact.objects.filter(id=pid.id).update(status=True)
			if callback != "":
				# print(callback)
				# print('cc')
				Contact.objects.filter(id=pid.id).update(status=False)
			if appointment_callback != "":
				# print('ac')
				Contact.objects.filter(id=pid.id).update(status=False)

			notification(request)
			messages.success(request, 'Successfully saved')

			new_id = pid.id + 1
			print(new_id)
			return HttpResponseRedirect('/%s/pending_calls_details' % new_id)
		elif request.POST.get('btn-stop'):
			print("btn-stop")
			wrong_number = request.POST.get('wrongNumber')

			disposition = request.POST.get('disposition')
			sub_disposition = request.POST.get('unqualified_disposition')
			callback = request.POST['callback_datetime']
			appointment_callback = request.POST['appointment_datetime']
			remark = request.POST['remarks']
			contact = Information.objects.filter(contact_id=pid.id)
			print("***", contact)
			Information.objects.filter(contact_id=pid.id).update_or_create(
				wrong_number=wrong_number, disposition=disposition, sub_disposition=sub_disposition,
				callback_follow_up=callback, appointment_follow_up=appointment_callback,
				remarks=remark, contact_id=pid.id
			)
			if disposition == "Interested":
				# print('yes')
				Contact.objects.filter(id=pid.id).update(status=True)
			if disposition == "Unqualified":
				# print('u')
				Contact.objects.filter(id=pid.id).update(status=True)
			if callback != "":
				# print(callback)
				# print('cc')
				Contact.objects.filter(id=pid.id).update(status=False)
			if appointment_callback != "":
				# print('ac')
				Contact.objects.filter(id=pid.id).update(status=False)

			notification(request)
			messages.success(request, 'Successfully saved')

			return HttpResponseRedirect('pending_calls_details')
		else:
			return HttpResponse('Not valid')

	else:
		context['contact'] = pid
		context['contact_info'] = fetch_info
		context['camp_detail'] = campaign_name[0]
		context['pending_calls'] = pending_call_notification(request, new_cont_id)
		return render(request, 'website/pending_calls_details.html', context)


def calls_overdue(request):
	context = {}

	overdue_list = Contact.objects.filter(status=False, user_id=request.user.id).all()
	context['overdue_calls'] = overdue_list
	context['notification'] = notification(request)
	return render(request, 'website/overdue.html', context)


def pending_call_notification(request, new_cont):
	cursor = connection.cursor()
	cursor.execute(
		"select COUNT(website_contact.name) from website_contact where website_contact.status IS NULL AND "
		"website_contact.new_cont_id={0} OR website_contact.status=false AND website_contact.new_cont_id={1}".format(
			new_cont, new_cont))

	status_null = ''
	for status in cursor.fetchall():
		status_null = status[0]
		print("status: ", status_null)
	return status_null


def notification(request):
	# print("pid", pid)
	cursor1 = connection.cursor()
	cursor2 = connection.cursor()

	cursor1.execute("select COUNT(website_contact.status) from website_contact where website_contact.status = 'false' "
	                "AND website_contact.user_id={0}".format(request.user.id))
	cursor2.execute("select COUNT(website_contact.status) from website_contact where website_contact.status = 'false'")
	if request.user.is_superuser:
		status_false = ''
		for status in cursor2.fetchall():
			status_false = status[0]
		# print("status: ", status_false)
		return status_false
	else:
		status_false = ''
		for status in cursor1.fetchall():
			status_false = status[0]
		# print("status: ", status_false)
		return status_false


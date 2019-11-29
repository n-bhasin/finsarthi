from django.contrib.auth import authenticate, \
	get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User, Group
from .models import Documents, Contact, NewCampaign

RegisterUser = get_user_model()


# user login form
class UserLoginForm(forms.Form):
	username = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
	password = forms.CharField(max_length=200, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

	def clean(self, *args, **kwargs):
		username = self.cleaned_data.get('username')
		password = self.cleaned_data.get('password')

		if username and password:
			user = authenticate(username=username, password=password)
			if not user:
				raise forms.ValidationError("Invalid Username or Password")
			if not user.check_password:
				raise forms.ValidationError("Invalid Password.")
			if not user.is_active:
				raise forms.ValidationError("User is not active.")
			return super(UserLoginForm, self).clean(*args, **kwargs)


#
# # user registration form
# class UserRegisterForm(forms.ModelForm):
# 	email = forms.EmailField(label='Email Address', widget=forms.TextInput(attrs={'class': 'form-control'}))
# 	email2 = forms.EmailField(label='Confirm Email', widget=forms.TextInput(attrs={'class': 'form-control'}))
# 	password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
#
# 	class Meta:
# 		model = RegisterUser
# 		fields = [
# 			'username',
# 			'email',
# 			'email2',
# 			'password'
# 		]
# 		widgets = {
# 			'username': forms.TextInput(attrs={'class': 'form-control'})
# 		}
#
# 		def clean_email(self):
# 			email = self.cleaned_data.get('email')
# 			email2 = self.cleaned_data.get('email2')
# 			if email != email2:
# 				raise forms.ValidationError("Email must match.")
# 			email_qs = RegisterUser.objects.filter(email=email)
# 			if email_qs.exists():
# 				raise forms.ValidationError("Email already exist.")
# 			return email


# conatct form
class Contacts(forms.ModelForm):
	user = forms.ModelChoiceField(queryset=User.objects.filter(is_superuser=False).all(),
	                              widget=forms.Select(attrs={'class': 'custom-select mr-sm-2'}))

	class Meta:
		model = Contact
		fields = [
			'user',
		]
		label = {
			'user': 'Handler'
		}


# csv upload form
class UploadFile(forms.ModelForm):
	# new_camp = forms.ModelChoiceField(queryset=NewCampaign.objects.all(),
	#                                   widget=forms.Select(attrs={'class': 'custom-select mr-sm-2'}))

	class Meta:
		model = Documents
		fields = (
			'document',
			# 'new_camp',
		)

		labels = {
			'document': 'Document',
			'new_camp': 'Choose Campaign',
		}


# campaign form
class Campaign(forms.ModelForm):
	assign_to = forms.ModelMultipleChoiceField(queryset=Group.objects.all(),
	                                           widget=forms.SelectMultiple(attrs={'class': 'custom-select mr-sm-2'}))

	class Meta:
		model = NewCampaign
		fields = [
			'name',
			'script',
			'assign_to',

		]
		labels = {
			'name': 'Name',
			'script': 'Script',
			'assign_to': 'Assign',

		}
		widgets = {
			'name': forms.TextInput(attrs={'class': 'form-control'}),
			'script': forms.Textarea(attrs={'class': 'form-control'}),
			# 'assign_to': forms.MultipleChoiceField(attrs={'class': 'form-control'})
		}


# campaign User
class CampaignUser(forms.ModelForm):
	camp_user = forms.ModelMultipleChoiceField(
		queryset=User.objects.filter(is_superuser=False).all(),
		widget=forms.Select(attrs={'class': 'custom-select mr-sm-2'}))

	class Meta:
		model = NewCampaign
		fields = [
			'camp_user',
		]
		labels = {
			'camp_user': 'User',
		}



# add_employee
class EmployeeForm(forms.ModelForm):
	email = forms.EmailField(label='Email Address',
	                         widget=forms.TextInput(attrs={'class': 'form-control'}))
	role = forms.ModelChoiceField(queryset=Group.objects.all(),
	                              widget=forms.Select(attrs={'class': 'custom-select mr-sm-2'}))

	class Meta:
		model = User
		fields = [
			'email'
		]
		labels = {
			'email': 'Email'
		}
		widgets = {
			'email': forms.EmailInput(attrs={'class': 'form-control'}),

		}

	def __init__(self, *args, **kwargs):
		if kwargs.get('instance'):
			# we get the initial keyword argument or initialise it as a dict if didn't exist
			initial = kwargs.setdefault('initial', {})
			# the widget for a ModelChoiceField expects a list of primary key a selected area
			if kwargs['instance'].groups.all():
				initial['role'] = kwargs['instance'].groups.all()[0]
			else:
				initial['role'] = None
		forms.ModelForm.__init__(self, *args, **kwargs)

	# def clean_email(self):
	# 	email = self.cleaned_data.get('email')
	# 	email_qs = RegisterUser.objects.filter(email=email)
	# 	if email_qs.exists():
	# 		raise forms.ValidationError("Email already exist.")
	# 	return email

	def roleSave(self):
		role = self.cleaned_data.pop('role')
		# updated_role = []
		# # iterating the queryset and appending the values in empty list
		# for name in role:
		# 	print(name['id'])
		# 	updated_role.append(name['id'])

		u = super().save()
		u.groups.set([role])
		u.save()
		return u


class UserDetail(UserCreationForm):
	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'password1', 'password2')

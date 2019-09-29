from django import forms
from django.contrib.auth import authenticate,\
	get_user_model

User = get_user_model()


class UserLoginForm(forms.Form):
	username = forms.CharField(max_length=8, widget=forms.TextInput(attrs={'class': 'form-control'}))
	password = forms.CharField(max_length=8, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

	def clean(self, *args, **kwargs):
		username = self.cleaned_data.get('username')
		password = self.cleaned_data.get('password')

		if username and password:
			user = authenticate(username=username, password=password)
			if not user:
				raise forms.ValidationError("User does not exist.")
			if not user.check_password:
				raise forms.ValidationError("Invalid Password.")
			if not user.is_active:
				raise forms.ValidationError("User is not active.")
			return super(UserLoginForm, self).clean(*args, **kwargs)


class UserRegisterForm(forms.ModelForm):
	email = forms.EmailField(label='Email Address', widget=forms.TextInput(attrs={'class': 'form-control'}))
	email2 = forms.EmailField(label='Confirm Email', widget=forms.TextInput(attrs={'class': 'form-control'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

	class Meta:
		model = User
		fields = [
			'username',
			'email',
			'email2',
			'password'
		]
		widgets = {
			'username': forms.TextInput(attrs={'class': 'form-control'})
		}

		def clean_email(self):
			email = self.cleaned_data.get('email')
			email2 = self.cleaned_data.get('email2')
			if email != email2:
				raise forms.ValidationError("Email must match.")
			email_qs = User.objects.filter(email=email)
			if email_qs.exists():
				raise forms.ValidationError("Email already exist.")
			return email

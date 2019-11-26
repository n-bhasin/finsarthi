from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from website import views

def role_required(allowed_roles):
	def decorator(view_func):
		def wrap(request, *args, **kwargs):
			print('allowed_roles: ',allowed_roles)
			print('user: ',request.user)
			print('superuser: ', request.user.is_superuser)
			print('status: ',request.user.is_superuser == allowed_roles)
			if request.user.is_superuser == allowed_roles:

				return view_func(request, *args, **kwargs)
			else:
				messages.error(request, "You are not authorized**.")
				return HttpResponseRedirect(reverse(views.home))
		return wrap
	return decorator

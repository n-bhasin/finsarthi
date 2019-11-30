from django.urls import path
from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	path('login_view', views.login_view, name='login_view'),
	path('', views.form_view, name='form_view'),
	# path('register', views.register_view, name='register_view'),
	path('logout', views.logout_view, name='logout_view'),
	path('home', views.home, name='home'),
	path('password_set', views.password_set, name='password_set'),
	path('csv_import', views.csv_import, name='csv_import'),

	# csv uploads
	path('<int:id>/prospect', views.prospect, name='prospect'),
	path('file_upload', views.file_upload, name='file_upload'),
	path('<int:id>/prospect_detail', views.prospect_detail, name='prospect_detail'),
	path('<id>/browse_prospects', views.browse_prospects, name='browse_prospects'),
	path('<id>/pending_calls', views.pending_calls, name='pending_calls'),
	path('<id>/pending_calls_details', views.pending_calls_details, name='pending_calls_details'),

	path('browse_prospects', views.browse_prospects, name='browse_prospects'),

	# employees
	path('add_employee', views.add_employee, name='add_employee'),
	url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate,
	    name='activate'),
	path('<id>/edit', views.edit, name='edit',),
	path('<int:id>/delete', views.delete, name='delete'),
	# campaigns
	path('create_campaign', views.create_campaign, name='create_campaign'),
	path('<int:id>/detail_campaign', views.detail_campaign, name='detail_campaign'),
	path('<int:id>/add_campaign_user', views.add_campaign_user, name='add_campaign_user'),
	path('<int:id>/edit_camp', views.edit_camp, name='edit_camp'),
	path('<int:id>/delete_camp', views.delete_camp, name='delete_camp'),
	# campaign users
	path('<int:id>/user_detail', views.user_detail, name='user_detail'),
	path('calls_overdue', views.calls_overdue, name='calls_overdue'),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_URL)

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

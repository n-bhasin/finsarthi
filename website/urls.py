from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	path('', views.form_view, name='form_view'),
	path('login_view', views.login_view, name='login_view'),
	# path('register', views.register_view, name='register_view'),
	path('logout', views.logout_view, name='logout_view'),
	path('home', views.home, name='home'),

	# csv uploads
	path('prospect', views.prospect, name='prospect'),
	path('file_upload', views.file_upload, name='file_upload'),
	path('<int:id>/prospect_detail', views.prospect_detail, name='prospect_detail'),
	path('<int:id>/browse_prospects', views.browse_prospects, name='browse_prospects'),
	# path('browse_prospects', views.browse_prospects, name='browse_prospects'),

	# employees
	path('add_employee', views.add_employee, name='add_employee'),
	path('<int:id>/edit', views.edit, name='edit'),
	path('<int:id>/delete', views.delete, name='delete'),
	# campaigns
	path('create_campaign', views.create_campaign, name='create_campaign'),
	path('<int:id>/detail_campaign', views.detail_campaign, name='detail_campaign'),
	path('<int:id>/add_campaign_user', views.add_campaign_user, name='add_campaign_user'),
	path('<int:id>/edit_camp', views.edit_camp, name='edit_camp'),
	path('<int:id>/delete_camp', views.delete_camp, name='delete_camp'),
	# campaign users
	path('<int:id>/user_detail', views.user_detail, name='user_detail'),

]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

import os

from django import forms
from django.db import models
from django.contrib.auth.models import User, Group
from datetime import datetime


# Create your models here.

class NewCampaign(models.Model):
	name = models.CharField(max_length=50)
	script = models.CharField(max_length=2000)
	assign_to = models.ManyToManyField(Group)
	camp_user = models.ManyToManyField(User)
	date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return '{}'.format(self.name)


class Documents(models.Model):
	document = models.FileField(upload_to='documents/')
	new_camp = models.ForeignKey(NewCampaign, on_delete=models.CASCADE, related_name='newcamp_docs', null=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	def filename(self):
		return os.path.basename(self.document.name)

	def __str__(self):
		return '{}'.format(self.document.name.split('/')[-1])


class Contact(models.Model):
	name = models.CharField(max_length=20, null=True)
	phone_number = models.CharField(max_length=15, null=True)
	new_cont = models.ForeignKey(NewCampaign, on_delete=models.CASCADE, null=True, default=1)

	# email = models.EmailField(null=True)

	def __str__(self):
		return '{} {}'.format(self.name, self.phone_number)

	def id(self):
		for u in self.contact_info.values():
			return u['id']

	def disposition(self):
		for u in self.contact_info.values():
			return u['disposition']

	def sub_disposition(self):
		for u in self.contact_info.values():
			return u['sub_disposition']

	def appointment_follow_up(self):
		for u in self.contact_info.values():
			str = u['appointment_follow_up']
			if str is '':
				return u['appointment_follow_up']
				break
			elif str is None:
				return u['appointment_follow_up']
				break
			else:
				new_str = datetime.strptime(str, '%Y-%m-%d %H:%M')
				return new_str

	def callback_follow_up(self):
		for u in self.contact_info.values():
			str = u['callback_follow_up']
			if str is '':
				return u['callback_follow_up']
				break
			elif str is None:
				return u['callback_follow_up']
				break
			else:
				new_str = datetime.strptime(str, '%Y-%m-%d %H:%M')
				return new_str


def remarks(self):
	for u in self.contact_info.values():
		return u['remarks']


CONTACT_STATUS = [
	('call_back', 'Call Back'),
	('not_interested', 'Not Interested'),
	('not_eligible', 'Not Eligible'),
	('not_reachable', 'Not Reachable'),
	('Interested', 'Interested')
]


class Information(models.Model):
	disposition = models.CharField(max_length=100, blank=True)
	sub_disposition = models.CharField(max_length=100, blank=True, null=True)
	callback_follow_up = models.CharField(max_length=100, null=True, blank=True)
	appointment_follow_up = models.CharField(max_length=100, null=True, blank=True)
	remarks = models.CharField(max_length=1000, blank=True)
	contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='contact_info', null=True)

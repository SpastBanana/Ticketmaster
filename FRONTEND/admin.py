from django.contrib import admin
from .models import Ticket, TicketPrice

admin.site.register(Ticket)
admin.site.register(TicketPrice)
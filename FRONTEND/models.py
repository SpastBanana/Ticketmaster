from django.db import models

class Ticket(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=50)
    ticket_count = models.CharField(max_length=5)
    total_amount = models.CharField(max_length=10)
    invoice_nr = models.CharField(max_length=20)
    invoice_date = models.DateField()
    has_payed = models.CharField(max_length=1)
    checked_in = models.CharField(max_length=1)

    class Meta:
        verbose_name_plural = "Ticket aanvragen"

    def __str__(self):
        return self.invoice_nr

class TicketPrice(models.Model):
    ticket_price = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = "Prijs van één ticket"

    def __str__(self):
        return self.ticket_price
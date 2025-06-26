from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from .models import Ticket
import imaplib, os
from datetime import datetime
import shutil

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
BROKER_DIR = f'{BASE_DIR}'.replace('FRONTEND', 'BROKER')
LOG_DIR = f'{BASE_DIR}'.replace('FRONTEND', 'LOG')
BROKER_ATTACHMENTS = f'{BASE_DIR}'.replace('FRONTEND', 'Attachments')
SITE_ATTACHMENTS = f'{BASE_DIR}'.replace('FRONTEND', 'AttachmentsDone')
FINISHED_ATTACHMENTS = f'{BASE_DIR}'.replace('FRONTEND', 'AttachmentsDone')
INVOICE_DIR = f'{BASE_DIR}'.replace('FRONTEND', 'PDF')

TICKET_PRICE_INT = 12.5
TICKET_PRICE_STR_COMMA = '12,50'
TICKET_PRICE_STR_DOT = '12.50'

def page_home(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    
    # mail_scanner()
    write_attachments_to_db()

    tickets = Ticket.objects.all()
    list_payed = Ticket.objects.filter(has_payed='1').values()
    list_unpayed = Ticket.objects.filter(has_payed='0').values()
    total_payed, total_unpayed, total_ordered, total_ordered_payed = 0,0,0,0

    if len(list_payed) == 0:
        total_payed = 0
    else:
        for item in list_payed:
            ammount = float(item['total_amount'].replace(',', '.'))
            count = float(item['ticket_count'].replace(',', '.'))
            total_payed = total_payed + ammount
            total_ordered_payed = total_ordered_payed + count

    if len(list_unpayed) == 0:
        total_unpayed = 0
    else:
        for item in list_unpayed:
            ammount = float(item['total_amount'].replace(',', '.'))
            count = float(item['ticket_count'].replace(',', '.'))
            total_unpayed = total_unpayed + ammount
            total_ordered = total_ordered + count

    if request.method == 'POST':
        for item in tickets:
            if item.invoice_nr in request.POST:
                if item.has_payed == '1':
                    item.has_payed = '0'
                    site_log(f'User "{request.user.username}" has refused payment for "{item.invoice_nr}"')
                    site_log(f'Remote address: "{get_client_ip(request)}"')
                else:
                    item.has_payed = '1'
                    site_log(f'User "{request.user.username}" has accepted payment for "{item.invoice_nr}"')
                    site_log(f'Remote address: "{get_client_ip(request)}"')

                item.save()
                return redirect('/')
    
    if request.user.is_authenticated:
        logged_user = request.user
        site_log(f'User "{logged_user.username}" has accessed "/" from remote address: "{get_client_ip(request)}"')

    data = {
        'page': 'home.html',
        'user': request.user,
        'tickets': tickets,
        'payed': "{:.2f}".format(total_payed),
        'unpayed': "{:.2f}".format(total_unpayed),
        'ordered': int(total_ordered),
        'ordered_payed': int(total_ordered_payed),
        'sum_tickets_payed': "{:.2f}".format(total_payed + total_unpayed),
        'sum_ticket_count': int(total_ordered + total_ordered_payed),
    }

    return render(request, 'index.html', data)

def page_checkout(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    
    # mail_scanner()
    write_attachments_to_db()

    tickets = Ticket.objects.all()
    
    if request.user.is_authenticated:
        logged_user = request.user
        site_log(f'User "{logged_user.username}" has accessed "/checkout" from remote address: "{get_client_ip(request)}"')

    data = {
        'page': 'checkout.html',
        'user': request.user,
        'tickets': tickets,
    }

    return render(request, 'index.html', data)

def page_digital_checkin(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    
    tickets = Ticket.objects.all()

    found_email = False
    checked_in = False
    
    if request.method == 'POST':
        for item in tickets:
            if str(item.email).lower() in str(request.POST).lower():
                found_email = True

                if item.has_payed == '0':
                    return redirect('/checkout/invoice/error/2')
                
                if item.checked_in == '1':
                    return redirect('/checkout/invoice/error/1')

                if item.checked_in == '0':
                    item.checked_in = '1'
                    site_log(f'User "{request.user.username}" has registered "{item.first_name} {item.last_name}"')
                    site_log(f'Remote address: "{get_client_ip(request)}"')

                    item.save()
                    return redirect('/checkout')
                
        if found_email == False:
            return redirect('/checkout/invoice/error/3')
               
    data = {
        'page': 'digital.html',
    }

    return render(request, 'index.html', data)


def page_digital_checkin_error(request, id):
    if not request.user.is_authenticated:
        return redirect('/login')
    
    error_msg = ''

    if id == '1':
        error_msg = 'Gast is al aangemeld'
    elif id == '2':
        error_msg = 'Deze gast heeft nog niet betaald'
    elif id == '3':
        error_msg = 'Geen gast gevonden met dit email adres'
    else:
        error_msg = 'Geen valide invoer, bekijk de site log voor meer informatie'
    
    data = {
        'page': 'digital-error.html',
        'error': error_msg,
    }

    return render(request, 'index.html', data)


def page_cash_checkin(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    
    if request.method == 'POST':
        ticket = Ticket(
            first_name= request.POST.get('firstname'),
            last_name=request.POST.get('lastname'),
            ticket_count=request.POST.get('ticketcount'),
            email=request.POST.get('email'),
            total_amount=request.POST.get('totalamount'),
            invoice_nr=f'cash-payment {datetime.now().strftime("%d-%m-%Y %H:%M")}',
            invoice_date=datetime.now(),
            has_payed='1',
            checked_in='1'
            )
        
        try:
            ticket.save()
            site_log(f'User {request.user.username} registered a cash payment:')
        except Exception as e:
            site_log(f'Something went wrong when trying to register a cash payment:')
            site_log(str(e))
        
        return redirect('/checkout')

    data = {
        'page': 'cash.html',
    }

    return render(request, 'index.html', data)


def page_login(request):
    if not request.user.is_authenticated:
        site_log(f'Guest has astablished connection to the site from remote address "{get_client_ip(request)}"')

    if request.method == 'POST':

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            site_log(f'User "{username}" has logged in from remote address "{get_client_ip(request)}"')
        else:
            site_log(f'SOMEONE ISSUED WRONG LOGIN CREDENTIALS')
            site_log(f'REMOTE ADDRESS: {get_client_ip(request)}')
            site_log(f'USED-USERNAME: {username}')
            site_log(f'USED-PASSWORD: {password}')
    
    if request.user.is_authenticated:
        return redirect('/')

    data = {
        'page': 'login.html'
    }

    return render(request, 'index.html', data)

def func_logout(request):
    logout(request)

    return redirect('/')

def delete_ticket(request, id):
    if not request.user.is_authenticated:
        return redirect('/login')
    
    ticket = Ticket.objects.filter(invoice_nr=id).values()

    if request.method == 'POST':
        ticket = Ticket.objects.filter(invoice_nr=id)
        try:
            # Remove ticket from DB
            try:
                ticket.delete()
                site_log(f'User "{request.user.username}" has deleted entry "{id}"')
                site_log(f'Remote address: "{get_client_ip(request)}"')
            except Exception as e:
                site_log(f'Could not remove ticket with invoice nr "{id}" from the database:')
                site_log(str(e))

            # Remove ticket files (attachments and invoices)
            try:
                os.remove(f'{INVOICE_DIR}/{id}.pdf')
                os.remove(f'{SITE_ATTACHMENTS}/{id}.csv')
            except Exception as e:
                site_log(f'Could not remove attachment and invoice file of ticket with invoice nr "{id}":')
                site_log(str(e))
            
            # Remove invoice nr from BROKER DB
            try:
                broker_db = []
                new_line = ''

                with open(f'{BROKER_DIR}/invoices.txt', 'r') as f:
                    line = ''
                    for line in f:
                        broker_db.append(line)

                    broker_db.remove(f'{id}\n')

                    for nr in broker_db:
                        new_line += nr

                with open(f'{BROKER_DIR}/invoices.txt', 'w') as f:
                    f.write(new_line)

            except Exception as e:
                site_log(f'Could not remove invoice nr {id} from BROKER database:')
                site_log(str(e))
        except:
            site_log(f'User "{request.user.username}" tryd to delete "{id}" but failed')
            site_log(f'Remote address: "{get_client_ip(request)}"')
        return redirect('/')

    site_log(f'User "{request.user.username}" has accessed "/delete/{id}" from remote address: "{get_client_ip(request)}"')

    data = {
        'page': 'delete.html',
        'tickets': ticket,
    }

    return render(request, 'index.html', data)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_view(request, logfile):
    if request.user.is_authenticated:
        log_file = f'{LOG_DIR}/{logfile}'
        log = ""

        with open(log_file, 'r') as f:
            for line in f:
                log += f'{line}<br>'

        site_log(f'User "{request.user.username}" has accessed "/log/{logfile}" from remote address: "{get_client_ip(request)}"')
        return HttpResponse(log)
    else:
        return redirect('/login')

def site_log(msg):
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    with open(f'{LOG_DIR}/site_log.txt', 'a') as f:
        f.write(f'{timestamp}: {msg}\n')

def write_attachments_to_db():
    dir = os.listdir(BROKER_ATTACHMENTS)

    if len(dir) > 0:
        submittions = []
        send_invoices = []

        for file in dir:
            invoice_nr = str(file).replace('.csv', '')

            with open(f'{BROKER_ATTACHMENTS}/{file}', 'r') as f:
                temp = []

                for line in f:
                    context = line.replace('"', '').replace('\n', '').split(',')
                    temp.append(context)
                
                submittion = temp[1]

                ticket = Ticket(
                    first_name=submittion[1],
                    last_name=submittion[2],
                    ticket_count=submittion[3],
                    email=submittion[4],
                    total_amount=str("{:.2f}".format(float(submittion[3])*TICKET_PRICE_INT)).replace('.', ','),
                    invoice_nr=invoice_nr,
                    invoice_date=datetime.now(),
                    has_payed='0',
                    checked_in='0'
                    )
                
            try:
                ticket.save()
                try:
                    shutil.move(f"{BROKER_ATTACHMENTS}/{file}", f"{FINISHED_ATTACHMENTS}/{invoice_nr}.csv")
                except:
                    site_log('Could not move request file to finished folder:')
                    site_log(file)
            except:
                site_log('Could not save ticket request to the database:')
                site_log(file)

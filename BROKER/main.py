import email, os, time, imaplib, fitz
from io import BytesIO
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from os.path import basename


IMAP_SERVER = 'imap.bhosted.nl'
IMAP_PORT = 993
SMTP_SERVER = 'smtp.bhosted.nl'
SMTP_PORT = 465
AUTOMATIONS_ACCOUNT = 'automations@liefenlied.nl'
AUTOMATIONS_PASSWORD = 'hQA5Zy4FxX'
KAARTEN_ACCOUNT = 'kaarten@liefenlied.nl'
KAARTEN_PASSWORD = 'fX7Za2zTdD'
DOWNLOAD_FOLDER = 'ticket-requests'
FOLDER_INBOX = 'Inbox'
FOLDER_SEND = 'Inbox.Send'
FOLDER_DB = 'Inbox.DB'
FOLDER_ERROR = 'Inbox.Error'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_DIR = f'{BASE_DIR}'.replace('BROKER', 'LOG')
BROKER_ATTACHMENTS = f'{BASE_DIR}'.replace('BROKER', 'Attachments')
HOME_DIR = f'{BASE_DIR}'.replace('/BROKER', '')
INVOICE_DIR = f'{BASE_DIR}'.replace('BROKER', 'PDF')

TICKET_PRICE_INT = 12.5
TICKET_PRICE_STR_COMMA = '12,50'
TICKET_PRICE_STR_DOT = '12.50'

def mail_scanner():
    # Create output directory
    if not os.path.exists(BROKER_ATTACHMENTS):
        os.makedirs(BROKER_ATTACHMENTS)

    try:
        # Connect to email server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(AUTOMATIONS_ACCOUNT, AUTOMATIONS_PASSWORD)

        # Try to select the 'Send' folder
        folder_names_to_try = [FOLDER_INBOX]
        folder_selected = False

        for folder_name in folder_names_to_try:
            try:
                status, messages = mail.select(folder_name)
                if status == 'OK':
                    #write_log(f'Connected to mail {AUTOMATIONS_ACCOUNT}')
                    folder_selected = True
                    break
                else:
                    write_log(f'Could not connect to mail {AUTOMATIONS_ACCOUNT}')
            except:
                continue

        if not folder_selected:
            write_log('folder not selected, try these suggestions:')
            status, folders = mail.list()
            for folder in folders:
                write_log(folder.decode())
            return

        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            write_log("Failed to search emails")
            return

        email_ids = messages[0].split()
        if len(email_ids) != 0:
            write_log(f"Found {len(email_ids)} emails in the Inbox")
<<<<<<< HEAD
        
=======

>>>>>>> refs/remotes/origin/main
        if not email_ids:
            write_log("No emails found in the Inbox")
            return

        csv_count = 0
        processed_emails = []  # Track emails and their processing status

        # Process each email
        for email_id in email_ids:
            email_success = True
            email_subject = "Unknown"

            try:
                # Fetch and parse email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    write_log(f"Failed to fetch email ID: {email_id}")
                    processed_emails.append((email_id, False, "Failed to fetch"))
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                email_subject = msg.get('Subject', 'No Subject')
                write_log(f"Processing email: {email_subject}")

                # Extract and save CSV attachments
                email_has_csv = False
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename and filename.lower().endswith('.csv'):
                            email_has_csv = True
                            try:
                                content = part.get_payload(decode=True)
                                write_log(f"Found CSV attachment: {filename}")

                                # Get invoice numbers and create new number based on last one
                                try:
                                    invoice_numbers = []

                                    with open(f'{BASE_DIR}/invoices.txt', 'r') as f:
                                        for line in f:
                                            invoice_numbers.append(line)

                                    last_number = invoice_numbers[-1]
                                    last_number = last_number.split('-')
                                    last_number = int(last_number[1])
                                    new_number = f'2025-{"{:04d}".format(last_number + 1)}'
                                except Exception as e:
                                    write_log('Could not get latest invoice number from Broker DataBase:')
                                    write_log(str(e))
                                    email_success = False
                                    pass

                                # Save file with new invoice number as title
                                try:
                                    new_filename = f"{new_number}.csv"
                                    filepath = os.path.join(BROKER_ATTACHMENTS, new_filename)

                                    with open(filepath, 'wb') as f:
                                        f.write(content)
                                    write_log(f"Saved CSV file: {filepath}")
                                    csv_count += 1

                                    with open(f'{BASE_DIR}/invoices.txt', 'a') as f:
                                        f.write(f'{new_number}\n')
                                except Exception as e:
                                    write_log('Could not save fetched csv file:')
                                    write_log(str(e))
                                    email_success = False
                                    pass

                                # Create data for invoice file
                                try:
                                    with open(filepath, 'r') as f:
                                        temp = []

                                        for line in f:
                                            context = line.replace('"', '').replace('\n', '').split(',')
                                            temp.append(context)

                                        submittion = temp[1]

                                        data = {
                                            '#NAME' : f'{submittion[1]} {submittion[2]}',
                                            '#COUNT' : f'{submittion[3]}',
                                            '#AMOUNT' : f'{str("{:.2f}".format(float(submittion[3])*TICKET_PRICE_INT)).replace('.', ',')}',
                                            '#TOTALAMOUNT' : f'{str("{:.2f}".format(float(submittion[3])*TICKET_PRICE_INT)).replace('.', ',')}',
                                            '#FANUMB' : f'{new_number}',
                                            '#DATE' : f'{datetime.now().strftime("%d-%m-%Y")}',
                                        }

                                        create_invoice_pdf(f'{HOME_DIR}/factuur.pdf', f'{INVOICE_DIR}/{new_number}.pdf', data)
                                except Exception as e:
                                    email_success = False
                                    write_log('Could not create invoice:')
                                    write_log(str(e))
                                    pass

                                # Sending invoice to custommer
                                try:
                                    with open(filepath, 'r') as f:
                                        temp = []

                                        for line in f:
                                            context = line.replace('"', '').replace('\n', '').split(',')
                                            temp.append(context)

                                        submittion = temp[1]

                                        data = {
                                            '#NAME' : f'{submittion[1]} {submittion[2]}',
                                            '#COUNT' : f'{submittion[3]}',
                                            '#AMOUNT' : f'{str("{:.2f}".format(float(submittion[3])*TICKET_PRICE_INT)).replace('.', ',')}',
                                            '#TOTALAMOUNT' : f'{str("{:.2f}".format(float(submittion[3])*TICKET_PRICE_INT)).replace('.', ',')}',
                                            '#FANUMB' : f'{new_number}',
                                            '#DATE' : f'{datetime.now().strftime("%d-%m-%Y")}',
                                        }

                                        msg = f'''Beste {submittion[1]} {submittion[2]},

Wij zijn ontzettend blij dat u naar ons concert wilt komen! Bij deze sturen wij u de factuur om de betaling van uw kaarten te kunnen voldoen.

LET OP: Het email adres waarop u deze mail ontvangt is tevens uw toegang tot het concert.

Wij zien u graag op het concert!

Met vriendelijke groet,
Stichting Lief & Lied
                                        '''

                                        send_invoice(str(submittion[4]), f'Betreffende bestelde kaarten | Factuur: {new_number}', msg, [f'{INVOICE_DIR}/{new_number}.pdf'])

                                except Exception as e:
                                    write_log('Could not send the invoice to the custommer:')
                                    write_log(str(e))
                                    email_success = False

                            except Exception as e:
                                write_log(f"Something went wrong in the email loop:")
                                write_log(str(e))
                                email_success = False

                # Mark email as successful if it had CSV attachments and all were processed
                if not email_has_csv:
                    write_log(f"Email '{email_subject}' has no CSV attachments")

                processed_emails.append((email_id, email_success, email_subject))

            except Exception as e:
                write_log(f"Error processing email ID {email_id}: {str(e)}")
                processed_emails.append((email_id, False, email_subject))
                continue

        write_log(f"Processing complete. Saved {csv_count} CSV file(s) to '{BROKER_ATTACHMENTS}' folder")

        # Move emails to appropriate folders based on processing success
        write_log("Moving emails to appropriate folders...")

        # Ensure target folders exist
        db_folder = FOLDER_SEND
        error_folder = FOLDER_ERROR

        # Try to create folders if they don't exist
        try:
            mail.create(db_folder)
        except:
            pass  # Folder might already exist

        try:
            mail.create(error_folder)
        except:
            pass  # Folder might already exist

        # Move emails based on processing results
        for email_id, success, subject in processed_emails:
            try:
                target_folder = db_folder if success else error_folder

                # Copy email to target folder
                mail.copy(email_id, target_folder)

                # Mark original email for deletion
                mail.store(email_id, '+FLAGS', '\\Deleted')

                status_msg = "successfully processed" if success else "failed to process"
                write_log(f"Moved email '{subject}' to {target_folder} ({status_msg})")

            except Exception as e:
                write_log(f"Failed to move email '{subject}': {str(e)}")

        # Expunge deleted emails from original folder
        try:
            mail.expunge()
            write_log("Completed moving emails to appropriate folders")
        except Exception as e:
            write_log(f"Failed to expunge deleted emails: {str(e)}")

    except Exception as e:
        write_log(f"Script execution failed: {str(e)}")

    finally:
        # Close connection
        try:
            mail.close()
            mail.logout()
            #write_log("Email connection closed")
        except:
            write_log('Could not close Email connection')
            pass

# def send_invoice_via_mail(sender_email, sender_password, recipient_email,
#                              subject, body, attachment_path):
#     # Create message container
#     msg = MIMEMultipart()

#     # Set email headers
#     msg['From'] = sender_email
#     msg['To'] = recipient_email
#     msg['Subject'] = subject

#     # Add body to email
#     msg.attach(MIMEText(body, 'plain'))

#     # Open and attach file
#     with open(attachment_path, "rb") as attachment:
#         # Instance of MIMEBase and named as part
#         part = MIMEBase('application', 'octet-stream')
#         part.set_payload(attachment.read())

#     # Encode file in ASCII characters to send by email
#     encoders.encode_base64(part)

#     # Add header as key/value pair to attachment part
#     part.add_header(
#         'Content-Disposition',
#         f'attachment; filename= {os.path.basename(attachment_path)}'
#     )

#     # Attach the part to message
#     msg.attach(part)

#     # Create SMTP session
#     server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)  # Gmail SMTP
#     server.starttls()  # Enable TLS encryption
#     server.login(sender_email, sender_password)

#     # Send email
#     text = msg.as_string()
#     server.sendmail(sender_email, recipient_email, text)
#     server.quit()

#     write_log('E-mail send successfully')

def send_invoice(send_to, subject, text, files=None):
    msg = MIMEMultipart()
    msg['From'] = KAARTEN_ACCOUNT
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)


    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(KAARTEN_ACCOUNT, KAARTEN_PASSWORD)
        server.sendmail(KAARTEN_ACCOUNT, send_to, msg.as_string())
        server.close()

def create_invoice_pdf(input_path, output_path, word_replacements):
    """
    Advanced word replacement preserving all original formatting
    """
    doc = fitz.open(input_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Get all text blocks with formatting information
        blocks = page.get_text("dict")

        # Process each word replacement
        for old_word, new_word in word_replacements.items():
            # Search for all instances of the old word
            text_instances = page.search_for(old_word)

            for inst in text_instances:
                # Find the text block that contains this instance
                text_info = None
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                span_rect = fitz.Rect(span["bbox"])
                                if span_rect.intersects(inst):
                                    text_info = span
                                    break
                            if text_info:
                                break
                    if text_info:
                        break

                if text_info:
                    # Extract original formatting
                    font = text_info["font"]
                    fontsize = text_info["size"]
                    flags = text_info["flags"]  # bold, italic, etc.
                    color = text_info.get("color", 0)  # text color

                    # Cover the old text with a white rectangle
                    page.draw_rect(inst, color=(1, 1, 1), fill=(1, 1, 1))

                    x = inst[0]  # X coordinate stays the same
                    y = inst[1] + 9  # Y coordinate moves down

                    # Insert new text with preserved formatting
                    page.insert_text(
                        (x,y),  # position
                        new_word,
                        fontsize=fontsize
                    )

    # Save the modified PDF
    doc.save(output_path)
    doc.close()
    write_log(f'Saved {output_path}')

def write_log(msg):
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    with open(f'{LOG_DIR}/broker_log.txt', 'a') as f:
        f.write(f'{timestamp}: {msg}\n')


if __name__ == "__main__":
    while True:
        mail_scanner()
        time.sleep(60)

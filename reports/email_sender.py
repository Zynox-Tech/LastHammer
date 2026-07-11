import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import database


def send_report(pdf_path, mode, value, period_label):
    sender   = database.get_setting("sender_email").strip()
    password = database.get_setting("gmail_app_password").strip()
    owner    = database.get_setting("owner_email").strip()
    company  = database.get_setting("company_name") or "Last Hammer"

    if not sender:
        return False, "Sender email not set.\nGo to Settings → Email."
    if not password:
        return False, "Gmail App Password not set.\nGo to Settings → Email."
    if not owner:
        return False, "Owner email not set.\nGo to Settings → Email."
    if not os.path.exists(pdf_path):
        return False, f"PDF not found:\n{pdf_path}"

    # Build subject
    if mode == "day":
        subject = f"{company} — Daily Report — {period_label}"
    elif mode == "month":
        subject = f"{company} — Monthly Report — {period_label}"
    else:
        subject = f"{company} — Complete Expenditure Report"

    # Fetch totals
    from reports.daily_report import _get_entries_for_range, _get_fleet_entries
    data = _get_entries_for_range(mode, value)
    fleet_entries, loader_entries = _get_fleet_entries(mode, value)
    t1 = sum(float(r["amount"] or 0) for r in data["ch1"])
    t2 = sum(float(r["amount"] or 0) for r in data["ch2"])
    t3 = sum(float(r["total_amount"] or 0) for r in data["ch3"])
    t4 = sum(float(r["payment_received"] or 0) for r in data["ch4"])
    t5 = sum(float(r["payment"] or 0) for r in fleet_entries)
    t6 = sum(float(r["amount"] or 0) for r in data["ch6"])
    grand = t1 + t2 + t3 + t4 + t5 + t6
    bal   = database.ch7_get_current_balance()

    # Extra stats for email
    e_wt_kg    = sum(float(r["weight_tons"] or 0) for r in data["ch2"])
    e_payment2 = sum(float(r["amount"] or 0)      for r in data["ch2"])
    e_hrs      = sum(float(r["hours_worked"] or 0) for r in data["ch3"])
    e_trips    = sum(int(r["total_trips"] or 0)    for r in data["ch4"])
    e_dum_pay  = sum(float(r["payment"] or 0)      for r in fleet_entries)
    e_ldr_days = sum(float(r["days_worked"] or 0)  for r in loader_entries)
    e_ldr_pay  = sum(float(r["cash_paid"] or 0) + float(r["diesel_worth"] or 0)
                     for r in loader_entries)

    body = f"""Assalamu Alaikum,

Please find attached the expenditure report for:
{period_label}

SUMMARY
{"─"*56}
CH 1  General Expenditures     :  PKR {t1:>12,.2f}
      ({len(data["ch1"])} entries)

CH 2  Royalty to Government    :  PKR {t2:>12,.2f}
      Weight: {e_wt_kg:,.0f} kg  |  Payment: PKR {e_payment2:,.0f}  |  ({len(data["ch2"])} entries)

CH 3  Excavator Expenditure    :  PKR {t3:>12,.2f}
      Total Hours: {e_hrs:.1f} hrs  |  ({len(data["ch3"])} entries)

CH 4  Dumprei Expenditure      :  PKR {t4:>12,.2f}
      Total Trips: {e_trips}  |  ({len(data["ch4"])} entries)

CH 5  Trucks / Dumpers         :  PKR {e_dum_pay:>12,.2f}
      ({len(fleet_entries)} dumper entries)
CH 5  Loaders                  :  PKR {e_ldr_pay:>12,.2f}
      {e_ldr_days:.1f} days worked  |  ({len(loader_entries)} loader entries)

CH 6  Memory Notes             :  PKR {t6:>12,.2f}
{"─"*56}
GRAND TOTAL                    :  PKR {grand:>12,.2f}
{"─"*56}
Current Ledger Balance         :  PKR {bal:>12,.2f}

Full details are in the attached PDF.

Regards,
{company} — Expenditure Management System
"""

    msg = MIMEMultipart()
    msg["From"]    = f"{company} EMS <{sender}>"
    msg["To"]      = owner
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as srv:
            srv.login(sender, password)
            srv.sendmail(sender, owner, msg.as_string())
        return True, (f"✅  Report sent!\n\nTo:  {owner}\n"
                      f"Period:  {period_label}\n"
                      f"Total:  PKR {grand:,.2f}")
    except smtplib.SMTPAuthenticationError:
        return False, ("Authentication failed.\n\n"
                       "Check your Gmail App Password in Settings.\n"
                       "(Use App Password, not your normal password.)")
    except Exception as e:
        return False, f"Error:\n{str(e)}"


def send_invoice_email(pdf_path, parent=None):
    """Send a generated invoice PDF by email."""
    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    from PyQt5.QtWidgets import QMessageBox, QInputDialog

    sender   = database.get_setting("email_sender")   or ""
    password = database.get_setting("email_password") or ""
    receiver = database.get_setting("email_receiver") or ""
    company  = database.get_setting("company_name")   or "Last Hammer"

    if not sender or not password or not receiver:
        QMessageBox.warning(parent, "Email Not Configured",
            "Please configure email in Settings before sending.")
        return

    fname = os.path.basename(pdf_path)
    subject = f"{company} — Invoice: {fname.replace('.pdf','').replace('_',' ')}"

    body = f"""Assalamu Alaikum,

Please find attached the invoice generated by Last Hammer EMS.

File: {fname}

This invoice was generated on {datetime.now().strftime('%d %B %Y at %H:%M')}.

Please review all figures and confirm receipt.

Regards,
{company} — Expenditure Management System
"""
    msg = MIMEMultipart()
    msg["From"]    = f"{company} EMS <{sender}>"
    msg["To"]      = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={fname}")
    msg.attach(part)

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(sender, password)
            s.sendmail(sender, receiver, msg.as_string())
        QMessageBox.information(parent, "Sent",
            f"✅ Invoice emailed successfully to {receiver}")
    except Exception as e:
        QMessageBox.critical(parent, "Email Failed", f"Could not send email:\n{e}")
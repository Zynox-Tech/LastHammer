"""
Invoice Generator — Last Hammer EMS

FINANCIAL LOGIC (verified and correct):
────────────────────────────────────────────────────────────────────
EXCAVATOR:
  total_work    = sum of all (hours × rate)  → what they EARNED
  total_advance = cash + diesel given upfront → what we ALREADY PAID
  we_still_owe  = max(total_work - total_advance, 0)
    → excavator earned MORE than we paid → WE OWE THEM
  they_owe_us   = max(total_advance - total_work, 0)
    → we paid MORE than they earned → THEY OWE US (overpaid)

DUMPREI / TRUCK:
  total_paid    = cash + diesel already paid
  balance_due   = agreed amount still unpaid (from DB, positive = we owe them)
  we_still_owe  = max(balance_due, 0)
  they_owe_us   = max(-balance_due, 0)

LOADER:
  grand_total   = cash + diesel paid out
  we_still_owe  = grand_total (wages we paid/owe)
  they_owe_us   = 0

ROYALTY:
  purely a payment record — no balance concept
────────────────────────────────────────────────────────────────────
"""
import os
from datetime import datetime

import database
import config

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, Image)

C_RED    = colors.HexColor("#C0392B")
C_DARK   = colors.HexColor("#1A1A2E")
C_BLUE   = colors.HexColor("#1B4F72")
C_GREEN  = colors.HexColor("#1E8449")
C_ORANGE = colors.HexColor("#CA6F1E")
C_PURPLE = colors.HexColor("#6C3483")
C_TEAL   = colors.HexColor("#0E6655")
C_GRAY   = colors.HexColor("#CCCCCC")
C_LGRAY  = colors.HexColor("#F5F5F5")
C_WHITE  = colors.white
PAGE_W, PAGE_H = A4

INV_TYPES = {
    "dumprei":   {"label": "Dumprei Expenditure",       "color": C_ORANGE},
    "excavator": {"label": "Excavator Expenditure",     "color": C_TEAL},
    "dumper":    {"label": "Truck / Dumper Fleet",      "color": C_BLUE},
    "loader":    {"label": "Loader Fleet",              "color": C_GREEN},
    "royalty":   {"label": "Royalty to Government",     "color": C_PURPLE},
    "land":      {"label": "Surface / Land Rent",       "color": colors.HexColor("#2C7873")},
    "person":    {"label": "Individual Account Statement","color": colors.HexColor("#1B4F72")},
}


def _safe(r, *keys, default=0.0, as_str=False):
    rk = r.keys()
    for k in keys:
        if k in rk and r[k] is not None:
            v = r[k]
            return str(v) if as_str else float(v)
    return "" if as_str else default


def _pkr(v, zero_dash=True):
    if zero_dash and v == 0:
        return "—"
    return f"PKR {v:,.0f}"


def _base_tbl_style(hdr_color):
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  hdr_color),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("FONTSIZE",      (0, 1), (-1, -1), 7.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (2, 1), (2, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_GRAY),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.2, hdr_color),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_LGRAY]),
    ])


def _total_row_style():
    return [
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8E8E8")),
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, -1), (-1, -1), 8),
        ("LINEABOVE",  (0, -1), (-1, -1), 1.0, C_DARK),
    ]


def _build_header(story, uw, company, address, phone,
                  inv_number, inv_date, payee_name, payee_detail,
                  date_from, date_to, inv_type, notes=""):
    color      = INV_TYPES[inv_type]["color"]
    type_label = INV_TYPES[inv_type]["label"]

    s_co  = ParagraphStyle("hco",  fontName="Helvetica-Bold", fontSize=20,
                           textColor=C_WHITE, alignment=TA_CENTER)
    s_inv = ParagraphStyle("hinv", fontName="Helvetica-Bold", fontSize=11,
                           textColor=C_WHITE, alignment=TA_RIGHT)

    logo_path = config.LOGO_PATH
    col_logo  = 1.6*cm if os.path.exists(logo_path) else 0.1*cm
    logo_cell = Image(logo_path, width=1.3*cm, height=1.3*cm) if os.path.exists(logo_path) else ""

    hdr_data = [[
        logo_cell,
        Paragraph(f"<b>{company.upper()}</b><br/>"
                  "<font size='9' color='#AAAAAA'>Expenditure Management System</font>", s_co),
        Paragraph(f"<b>INVOICE</b><br/>"
                  f"<font size='8' color='#CCCCCC'>{type_label}</font>", s_inv),
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[col_logo, uw - col_logo - 3.2*cm, 3.2*cm])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_DARK),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBELOW",     (0, 0), (-1, -1), 4, color),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 0.3*cm))

    s_lbl  = ParagraphStyle("ml",  fontName="Helvetica-Bold", fontSize=8,   textColor=C_DARK)
    s_val  = ParagraphStyle("mv",  fontName="Helvetica",      fontSize=8.5, textColor=C_DARK)
    s_pay  = ParagraphStyle("pay", fontName="Helvetica-Bold", fontSize=14,  textColor=C_DARK)
    s_psub = ParagraphStyle("psb", fontName="Helvetica",      fontSize=8.5,
                            textColor=colors.HexColor("#555555"))

    date_range = (f"{date_from}  to  {date_to}"
                  if date_from != date_to else date_from)

    left = Table([
        [Paragraph("<b>INVOICE TO:</b>", s_lbl)],
        [Paragraph(payee_name,           s_pay)],
        [Paragraph(payee_detail,         s_psub)],
        [Paragraph(f"Period: {date_range}", s_psub)],
    ], colWidths=[uw * 0.54])
    left.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F8F8F8")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, 1), (0, 1),   1, color),
    ]))

    right = Table([
        [Paragraph("<b>Invoice No:</b>", s_lbl), Paragraph(inv_number,      s_val)],
        [Paragraph("<b>Date:</b>",       s_lbl), Paragraph(inv_date,        s_val)],
        [Paragraph("<b>Type:</b>",       s_lbl), Paragraph(type_label,      s_val)],
        [Paragraph("<b>Address:</b>",    s_lbl), Paragraph(address or "—",  s_val)],
        [Paragraph("<b>Phone:</b>",      s_lbl), Paragraph(phone   or "—",  s_val)],
    ], colWidths=[uw * 0.17, uw * 0.29])
    right.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ALIGN",         (0, 0), (0, -1),  "RIGHT"),
        ("FONTNAME",      (0, 0), (0, -1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
    ]))

    meta = Table([[left, right]], colWidths=[uw * 0.54, uw * 0.46])
    meta.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(meta)

    if notes and notes.strip():
        story.append(Spacer(1, 0.25*cm))
        s_note = ParagraphStyle("nb", fontName="Helvetica", fontSize=8, textColor=C_DARK)
        note_tbl = Table([
            [Paragraph("<b>NOTES / REMARKS:</b>", s_note)],
            [Paragraph(notes.strip(), s_note)],
        ], colWidths=[uw])
        note_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#FFFDE7")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("BOX",           (0, 0), (-1, -1), 0.8, colors.HexColor("#F39C12")),
        ]))
        story.append(note_tbl)

    story.append(Spacer(1, 0.35*cm))


def _build_summary_box(story, uw, color, stats_rows, grand_total,
                       we_still_owe, they_owe_us):
    """
    we_still_owe : PKR we still need to pay THEM  (our liability — shown in RED)
    they_owe_us  : PKR they need to return to us  (overpaid — shown in GREEN)
    Exactly one of these is > 0 at a time.
    """
    s_wh = ParagraphStyle("swh", fontName="Helvetica-Bold", fontSize=10, textColor=C_WHITE)
    s_wv = ParagraphStyle("swv", fontName="Helvetica-Bold", fontSize=14,
                          textColor=C_WHITE, alignment=TA_RIGHT)

    gt = Table([[Paragraph("<b>GRAND TOTAL</b>", s_wh),
                 Paragraph(f"<b>PKR {grand_total:,.2f}</b>", s_wv)]],
               colWidths=[uw * 0.5, uw * 0.5])
    gt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(gt)
    story.append(Spacer(1, 0.12*cm))

    s_sl = ParagraphStyle("ssl", fontName="Helvetica-Bold", fontSize=8,
                          textColor=colors.HexColor("#555555"))
    s_sv = ParagraphStyle("ssv", fontName="Helvetica-Bold", fontSize=9,
                          textColor=C_DARK, alignment=TA_RIGHT)

    stats_data = [[Paragraph(f"<b>{lbl}</b>", s_sl),
                   Paragraph(val, s_sv)] for lbl, val in stats_rows]
    stats_tbl = Table(stats_data, colWidths=[uw * 0.22, uw * 0.15])
    stats_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_GRAY),
    ]))

    we_active = we_still_owe > 0
    s_we_lbl = ParagraphStyle("wl", fontName="Helvetica-Bold", fontSize=9,
                              textColor=C_RED if we_active else colors.HexColor("#AAAAAA"),
                              alignment=TA_CENTER)
    s_we_val = ParagraphStyle("wv", fontName="Helvetica-Bold",
                              fontSize=15 if we_active else 12,
                              textColor=C_RED if we_active else colors.HexColor("#CCCCCC"),
                              alignment=TA_CENTER)
    s_we_sub = ParagraphStyle("ws", fontName="Helvetica", fontSize=7.5,
                              textColor=colors.HexColor("#888888"), alignment=TA_CENTER)

    we_tbl = Table([
        [Paragraph("WE OWE THEM", s_we_lbl)],
        [Paragraph(f"PKR {we_still_owe:,.2f}", s_we_val)],
        [Paragraph("Amount we still need to pay them", s_we_sub)],
    ], colWidths=[uw * 0.315])
    we_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1),
         colors.HexColor("#FEF0F0") if we_active else colors.HexColor("#FAFAFA")),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1),
         1.5 if we_active else 0.5,
         C_RED if we_active else C_GRAY),
    ]))

    th_active = they_owe_us > 0
    s_th_lbl = ParagraphStyle("tl", fontName="Helvetica-Bold", fontSize=9,
                              textColor=C_GREEN if th_active else colors.HexColor("#AAAAAA"),
                              alignment=TA_CENTER)
    s_th_val = ParagraphStyle("tv", fontName="Helvetica-Bold",
                              fontSize=15 if th_active else 12,
                              textColor=C_GREEN if th_active else colors.HexColor("#CCCCCC"),
                              alignment=TA_CENTER)
    s_th_sub = ParagraphStyle("ts", fontName="Helvetica", fontSize=7.5,
                              textColor=colors.HexColor("#888888"), alignment=TA_CENTER)

    th_tbl = Table([
        [Paragraph("THEY OWE US", s_th_lbl)],
        [Paragraph(f"PKR {they_owe_us:,.2f}", s_th_val)],
        [Paragraph("We overpaid — they must return this", s_th_sub)],
    ], colWidths=[uw * 0.315])
    th_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1),
         colors.HexColor("#EAFAF1") if th_active else colors.HexColor("#FAFAFA")),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1),
         1.5 if th_active else 0.5,
         C_GREEN if th_active else C_GRAY),
    ]))

    bottom = Table([[stats_tbl, we_tbl, th_tbl]],
                   colWidths=[uw * 0.37, uw * 0.315, uw * 0.315])
    bottom.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(bottom)
    story.append(Spacer(1, 0.25*cm))

    s_foot = ParagraphStyle("ft", fontName="Helvetica-Oblique", fontSize=7.5,
                            textColor=colors.HexColor("#AAAAAA"), alignment=TA_CENTER)
    story.append(Paragraph(
        "This invoice is generated by Last Hammer Expenditure Management System. "
        "Please verify all figures carefully before making any payment.",
        s_foot))


# ── Private helpers ───────────────────────────────────────────────────────────
def _default_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def _make_doc(path):
    return SimpleDocTemplate(path, pagesize=A4,
        topMargin=1.2*cm, bottomMargin=1.2*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm)

def _usable_w():
    return PAGE_W - 3.6*cm

def _today():
    return datetime.now().strftime("%d %b %Y")

def _sec(story, title):
    s = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=9.5, textColor=C_DARK)
    story.append(Paragraph(f"<b>{title}</b>", s))
    story.append(Spacer(1, 0.18*cm))

def _append_table(story, data, col_widths, color):
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle(
        _base_tbl_style(color).getCommands() + _total_row_style()))
    story.append(tbl)
    story.append(Spacer(1, 0.35*cm))


# ── DUMPREI INVOICE ───────────────────────────────────────────────────────────
def generate_dumprei_invoice(reg_number, owner_name, date_from, date_to,
                              output_dir=None, notes=""):
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM dumprei_expenditure "
        "WHERE reg_number=? AND date>=? AND date<=? ORDER BY date ASC, id ASC",
        (reg_number, date_from, date_to)
    ).fetchall()
    conn.close()
    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_trips  = sum(int(_safe(r, "total_trips")) for r in rows)
    total_cash   = sum(_safe(r, "paid_cash")         for r in rows)
    total_diesel = sum(_safe(r, "paid_diesel_worth", "paid_diesel") for r in rows)
    total_paid   = total_cash + total_diesel
    total_balance= sum(_safe(r, "balance_due") for r in rows)
    grand_total  = total_paid + max(total_balance, 0)
    we_still_owe = max(total_balance,  0)
    they_owe_us  = max(-total_balance, 0)

    out_path = os.path.join(output_dir or _default_dir(),
        f"Invoice_Dumprei_{reg_number}_{date_from}_to_{date_to}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = _make_doc(out_path); uw = _usable_w(); story = []

    _build_header(story, uw, company, address, phone,
                  f"DMP-{reg_number}-{date_from.replace('-','')}", _today(),
                  owner_name, f"Vehicle: {reg_number}  |  Dumprei / Tipper",
                  date_from, date_to, "dumprei", notes)
    _sec(story, f"TRIP RECORDS  —  {reg_number}  /  {owner_name}")

    d = [["#","Date","Details","Trips","Cash Paid","Diesel Paid","Total Paid","Balance Due"]]
    for i, r in enumerate(rows):
        pc  = _safe(r, "paid_cash")
        pd_ = _safe(r, "paid_diesel_worth", "paid_diesel")
        tp  = pc + pd_
        bal = _safe(r, "balance_due")
        d.append([str(i+1), r["date"],
                  _safe(r,"details","reg_number",as_str=True) or "—",
                  str(int(_safe(r,"total_trips"))),
                  _pkr(pc), _pkr(pd_), _pkr(tp,zero_dash=False), _pkr(bal)])
    d.append(["","TOTALS","",f"{total_trips} trips",
              _pkr(total_cash,zero_dash=False), _pkr(total_diesel,zero_dash=False),
              _pkr(total_paid,zero_dash=False), _pkr(total_balance,zero_dash=False)])
    _append_table(story, d,
        [uw*.05,uw*.12,uw*.20,uw*.08,uw*.15,uw*.15,uw*.13,uw*.12], C_ORANGE)
    _build_summary_box(story, uw, C_ORANGE,
        [("Total Trips",  f"{total_trips}"),
         ("Cash Paid",    _pkr(total_cash,   zero_dash=False)),
         ("Diesel Paid",  _pkr(total_diesel, zero_dash=False)),
         ("Total Paid",   _pkr(total_paid,   zero_dash=False)),
         ("Balance Due",  _pkr(total_balance,zero_dash=False))],
        grand_total, we_still_owe, they_owe_us)
    doc.build(story)
    return out_path


# ── EXCAVATOR INVOICE ─────────────────────────────────────────────────────────
def generate_excavator_invoice(details_filter, date_from, date_to,
                                output_dir=None, notes=""):
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM excavator_expenditure "
        "WHERE date>=? AND date<=? ORDER BY date ASC, id ASC",
        (date_from, date_to)
    ).fetchall()
    conn.close()
    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_hours   = sum(_safe(r, "hours_worked")               for r in rows)
    total_work    = sum(_safe(r, "total_amount")               for r in rows)
    total_ca      = sum(_safe(r, "cash_advance", "paid_cash")  for r in rows)
    # Only cash advance counts — user does not use diesel advance/used
    we_still_owe = max(total_work - total_ca, 0)
    they_owe_us  = max(total_ca - total_work, 0)
    net_balance  = total_work - total_ca

    out_path = os.path.join(output_dir or _default_dir(),
        f"Invoice_Excavator_{date_from}_to_{date_to}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = _make_doc(out_path); uw = _usable_w(); story = []

    _build_header(story, uw, company, address, phone,
                  f"EXC-{date_from.replace('-','')}", _today(),
                  "Excavator / Showal Machine",
                  f"Period: {date_from}  to  {date_to}",
                  date_from, date_to, "excavator", notes)
    _sec(story, "WORK SESSIONS & ADVANCE ACCOUNT")

    d = [["#", "Date", "Details", "Hours", "Work Total", "Cash Advance", "Net Balance"]]
    for i, r in enumerate(rows):
        hrs     = _safe(r, "hours_worked")
        tot     = _safe(r, "total_amount")
        ca      = _safe(r, "cash_advance", "paid_cash")
        row_net = tot - ca
        d.append([str(i+1), r["date"],
                  _safe(r, "details", as_str=True) or "—",
                  f"{hrs:.1f}" if hrs else "—",
                  _pkr(tot), _pkr(ca),
                  _pkr(row_net, zero_dash=False)])
    d.append(["", "TOTALS", "", f"{total_hours:.1f} hrs",
              _pkr(total_work, zero_dash=False),
              _pkr(total_ca,   zero_dash=False),
              _pkr(net_balance,zero_dash=False)])
    _append_table(story, d,
        [uw*.05, uw*.12, uw*.28, uw*.08, uw*.16, uw*.16, uw*.15], C_TEAL)
    _build_summary_box(story, uw, C_TEAL,
        [("Total Hours",  f"{total_hours:.1f} hrs"),
         ("Work Earned",  _pkr(total_work, zero_dash=False)),
         ("Cash Advance", _pkr(total_ca,   zero_dash=False)),
         ("Balance Due",  _pkr(net_balance,zero_dash=False))],
        total_work, we_still_owe, they_owe_us)
    doc.build(story)
    return out_path


# ── TRUCK / DUMPER INVOICE ────────────────────────────────────────────────────
def generate_truck_invoice(truck_id, reg_number, owner_name, truck_type,
                            date_from, date_to, output_dir=None, notes=""):
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM truck_entries WHERE truck_id=? AND date>=? AND date<=? "
        "ORDER BY date ASC, id ASC",
        (truck_id, date_from, date_to)
    ).fetchall()
    conn.close()
    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_trips  = sum(int(_safe(r,"trips")) for r in rows)
    total_cash   = sum(_safe(r,"paid_cash")   for r in rows)
    total_diesel = sum(_safe(r,"paid_diesel") for r in rows)
    total_paid   = sum(_safe(r,"payment")     for r in rows)
    total_bal    = sum(_safe(r,"balance_due") for r in rows)
    grand_total  = total_paid + max(total_bal, 0)
    we_still_owe = max(total_bal,  0)
    they_owe_us  = max(-total_bal, 0)

    out_path = os.path.join(output_dir or _default_dir(),
        f"Invoice_Dumper_{reg_number}_{date_from}_to_{date_to}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = _make_doc(out_path); uw = _usable_w(); story = []

    _build_header(story, uw, company, address, phone,
                  f"TRK-{reg_number}-{date_from.replace('-','')}", _today(),
                  owner_name, f"Vehicle: {reg_number}  |  {truck_type}",
                  date_from, date_to, "dumper", notes)
    _sec(story, f"TRIP PAYMENT RECORDS  —  {reg_number}  /  {owner_name}")

    d = [["#","Date","Details","Trips","Cash Paid","Diesel Paid","Total Paid","Balance Due"]]
    for i, r in enumerate(rows):
        pc  = _safe(r,"paid_cash")
        pd_ = _safe(r,"paid_diesel")
        tot = _safe(r,"payment")
        bal = _safe(r,"balance_due")
        d.append([str(i+1), r["date"],
                  _safe(r,"details",as_str=True) or "—",
                  str(int(_safe(r,"trips"))),
                  _pkr(pc), _pkr(pd_), _pkr(tot,zero_dash=False), _pkr(bal)])
    d.append(["","TOTALS","",f"{total_trips} trips",
              _pkr(total_cash,  zero_dash=False), _pkr(total_diesel,zero_dash=False),
              _pkr(total_paid,  zero_dash=False), _pkr(total_bal,   zero_dash=False)])
    _append_table(story, d,
        [uw*.05,uw*.12,uw*.22,uw*.08,uw*.13,uw*.13,uw*.13,uw*.14], C_BLUE)
    _build_summary_box(story, uw, C_BLUE,
        [("Total Trips", f"{total_trips}"),
         ("Cash Paid",   _pkr(total_cash,   zero_dash=False)),
         ("Diesel Paid", _pkr(total_diesel, zero_dash=False)),
         ("Total Paid",  _pkr(total_paid,   zero_dash=False)),
         ("Balance Due", _pkr(total_bal,    zero_dash=False))],
        grand_total, we_still_owe, they_owe_us)
    doc.build(story)
    return out_path


# ── LOADER INVOICE ────────────────────────────────────────────────────────────
def generate_loader_invoice(truck_id, reg_number, owner_name,
                             date_from, date_to, output_dir=None, notes=""):
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM loader_entries WHERE truck_id=? AND date>=? AND date<=? "
        "ORDER BY date ASC, id ASC",
        (truck_id, date_from, date_to)
    ).fetchall()
    conn.close()
    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_days   = sum(_safe(r,"days_worked")  for r in rows)
    total_cash   = sum(_safe(r,"cash_paid")    for r in rows)
    total_diesel = sum(_safe(r,"diesel_worth") for r in rows)
    grand_total  = total_cash + total_diesel
    we_still_owe = grand_total
    they_owe_us  = 0.0

    out_path = os.path.join(output_dir or _default_dir(),
        f"Invoice_Loader_{reg_number}_{date_from}_to_{date_to}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = _make_doc(out_path); uw = _usable_w(); story = []

    reg_display = reg_number.strip() if reg_number and reg_number.strip() and reg_number.strip().upper() not in ("NIL","NONE","N/A","") else "Loader Vehicle"
    _build_header(story, uw, company, address, phone,
                  f"LDR-{owner_name[:6].replace(' ','')}-{date_from.replace('-','')}", _today(),
                  owner_name, f"Vehicle: {reg_display}  |  Loader",
                  date_from, date_to, "loader", notes)
    _sec(story, f"WORK & PAYMENT LEDGER  —  {reg_number}  /  {owner_name}")

    d = [["#","Date","Type","Description","Days Worked","Cash Paid","Diesel (PKR)"]]
    for i, r in enumerate(rows):
        dw = _safe(r,"days_worked")
        cp = _safe(r,"cash_paid")
        dv = _safe(r,"diesel_worth")
        d.append([str(i+1), r["date"],
                  _safe(r,"entry_type",as_str=True) or "Work",
                  _safe(r,"description",as_str=True) or "—",
                  f"{dw:.1f} days" if dw else "—",
                  _pkr(cp), _pkr(dv)])
    d.append(["","TOTALS","","",f"{total_days:.1f} days",
              _pkr(total_cash,zero_dash=False), _pkr(total_diesel,zero_dash=False)])
    _append_table(story, d,
        [uw*.05,uw*.12,uw*.12,uw*.31,uw*.13,uw*.13,uw*.14], C_GREEN)
    _build_summary_box(story, uw, C_GREEN,
        [("Days Worked",  f"{total_days:.1f} days"),
         ("Cash Paid",    _pkr(total_cash,   zero_dash=False)),
         ("Diesel Paid",  _pkr(total_diesel, zero_dash=False)),
         ("Grand Total",  _pkr(grand_total,  zero_dash=False))],
        grand_total, we_still_owe, they_owe_us)
    doc.build(story)
    return out_path


# ── ROYALTY INVOICE ───────────────────────────────────────────────────────────
def generate_royalty_invoice(vehicle_number, date_from, date_to,
                              output_dir=None, notes=""):
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM royalty_payments "
        "WHERE (vehicle_number=? OR details=?) AND date>=? AND date<=? "
        "ORDER BY date ASC, id ASC",
        (vehicle_number, vehicle_number, date_from, date_to)
    ).fetchall()
    conn.close()
    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_weight  = sum(_safe(r,"weight_tons") for r in rows)
    total_payment = sum(_safe(r,"amount")      for r in rows)

    out_path = os.path.join(output_dir or _default_dir(),
        f"Invoice_Royalty_{vehicle_number}_{date_from}_to_{date_to}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = _make_doc(out_path); uw = _usable_w(); story = []

    _build_header(story, uw, company, address, phone,
                  f"ROY-{vehicle_number}-{date_from.replace('-','')}", _today(),
                  "Government — Royalty Office", f"Vehicle: {vehicle_number}",
                  date_from, date_to, "royalty", notes)
    _sec(story, f"ROYALTY PAYMENT RECORDS  —  {vehicle_number}")

    d = [["#","Date","Vehicle No.","Weight (kg)","Payment (PKR)"]]
    for i, r in enumerate(rows):
        veh = (_safe(r,"vehicle_number",as_str=True)
               or _safe(r,"details",as_str=True)
               or vehicle_number)
        d.append([str(i+1), r["date"], veh,
                  f"{_safe(r,'weight_tons'):,.0f} kg",
                  _pkr(_safe(r,"amount"),zero_dash=False)])
    d.append(["","TOTALS","",f"{total_weight:,.0f} kg",
              _pkr(total_payment,zero_dash=False)])
    _append_table(story, d, [uw*.07,uw*.20,uw*.28,uw*.20,uw*.25], C_PURPLE)
    _build_summary_box(story, uw, C_PURPLE,
        [("Total Entries", str(len(rows))),
         ("Total Weight",  f"{total_weight:,.0f} kg"),
         ("Total Payment", _pkr(total_payment,zero_dash=False))],
        total_payment, 0, 0)
    doc.build(story)
    return out_path


# ── LAND / SURFACE RENT INVOICE ───────────────────────────────────────────────
def generate_land_rent_invoice(owner_name, date_from, date_to,
                                output_dir=None, notes=""):
    """Generate a rent payment receipt/invoice for a specific land owner."""
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM land_rent "
        "WHERE owner_name=? AND payment_date>=? AND payment_date<=? "
        "ORDER BY payment_date ASC",
        (owner_name, date_from, date_to)
    ).fetchall()
    conn.close()

    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_amount = sum(_safe(r, "amount") for r in rows)
    cash_total   = sum(_safe(r, "amount") for r in rows if (r["payment_mode"] or "") == "Cash")
    cheque_total = sum(_safe(r, "amount") for r in rows if (r["payment_mode"] or "") != "Cash")

    out_path = os.path.join(
        output_dir or _default_dir(),
        f"Invoice_LandRent_{owner_name.replace(' ','_')}_{date_from}_to_{date_to}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = _make_doc(out_path); uw = _usable_w(); story = []

    owner_short = owner_name[:20] if len(owner_name) > 20 else owner_name
    _build_header(story, uw, company, address, phone,
                  f"RENT-{owner_short.replace(' ','')[:8]}-{date_from.replace('-','')}",
                  _today(),
                  owner_name,
                  f"Surface / Land Rent  |  Period: {date_from}  to  {date_to}",
                  date_from, date_to, "land", notes)

    _sec(story, "RENT PAYMENT RECORDS")

    d = [["#", "Payment Date", "Rent Period From", "Rent Period To",
          "Land / Location", "Mode", "Cheque / Bank", "Amount (PKR)"]]
    for i, r in enumerate(rows):
        mode = r["payment_mode"] or "Cash"
        chq  = ""
        if mode == "Cheque":
            cn = r["cheque_number"] or ""
            bn = r["bank_name"] or ""
            chq = f"#{cn}" + (f" {bn}" if bn else "") if cn else bn
        chq = chq or "—"
        d.append([
            str(i + 1),
            r["payment_date"] or "—",
            r["rent_from"]    or "—",
            r["rent_to"]      or "—",
            r["land_desc"]    or "—",
            mode,
            chq,
            _pkr(_safe(r, "amount"), zero_dash=False),
        ])
    d.append(["", "TOTAL RENT PAID", "", "", "", "", "",
              _pkr(total_amount, zero_dash=False)])

    _append_table(story, d,
        [uw*.04, uw*.11, uw*.11, uw*.11, uw*.17,
         uw*.08, uw*.18, uw*.20],
        colors.HexColor("#2C7873"))

    _build_summary_box(story, uw, colors.HexColor("#2C7873"),
        [("Total Entries",  str(len(rows))),
         ("Cash Payments",  _pkr(cash_total,   zero_dash=False)),
         ("Cheque Payments",_pkr(cheque_total, zero_dash=False)),
         ("Total Paid",     _pkr(total_amount, zero_dash=False))],
        total_amount, 0, 0)

    doc.build(story)
    return out_path


# ── PEOPLE REGISTER — INDIVIDUAL STATEMENT PDF ────────────────────────────────
def generate_person_statement(person_id, output_dir=None):
    """Generate a full ledger statement PDF for one person."""
    person = database.people_get_by_id(person_id)
    if not person:
        raise ValueError(f"Person id {person_id} not found")
    entries = database.people_ledger_get(person_id)
    company = database.get_setting("company_name")    or "Last Hammer"
    address = database.get_setting("company_address") or ""
    phone   = database.get_setting("company_phone")   or ""

    total_given, total_received, net = database.people_ledger_summary(person_id)
    # net > 0  → they OWE US  (we gave more)
    # net < 0  → WE OWE THEM (they gave more)

    safe_name = person["name"].replace(" ", "_").replace("/", "-")
    out_path  = os.path.join(
        output_dir or _default_dir(),
        f"Statement_{safe_name}.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    doc = _make_doc(out_path); uw = _usable_w(); story = []

    C_PERSON = colors.HexColor("#1B4F72")

    # ── Header ──
    _build_header(story, uw, company, address, phone,
                  f"STMT-{safe_name[:10]}-{_today().replace('-','')}",
                  _today(),
                  person["name"],
                  f"{person['category']}  |  {person['phone'] or 'No phone'}",
                  "", "", "person", "")

    # ── Person info box ──
    s_info = ParagraphStyle("pi", fontName="Helvetica", fontSize=9,
                            textColor=C_DARK, leading=14)
    s_info_b = ParagraphStyle("pib", fontName="Helvetica-Bold", fontSize=9,
                               textColor=C_DARK, leading=14)
    info_rows = []
    if person["phone"]:
        info_rows.append([Paragraph("<b>Phone:</b>", s_info_b),
                          Paragraph(person["phone"], s_info)])
    if person["category"]:
        info_rows.append([Paragraph("<b>Category:</b>", s_info_b),
                          Paragraph(person["category"], s_info)])
    if person["notes"]:
        info_rows.append([Paragraph("<b>Notes:</b>", s_info_b),
                          Paragraph(person["notes"], s_info)])
    if info_rows:
        t_info = Table(info_rows, colWidths=[uw*0.20, uw*0.80])
        t_info.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), C_LGRAY),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 0.3*cm))

    # ── Ledger table ──
    _sec(story, "FULL TRANSACTION LEDGER")
    running = 0.0
    d = [["#", "Date", "Type", "Description", "Cash Given", "Cash Received", "Balance"]]
    for i, e in enumerate(entries):
        given    = float(e["cash_given"]    or 0)
        received = float(e["cash_received"] or 0)
        running  = running + given - received
        etype    = e["entry_type"] or "Note"
        # colour code the type
        type_colors = {
            "Cash Given":    "#C0392B",
            "Cash Received": "#1E8449",
            "Note":          "#555555",
        }
        d.append([
            str(i + 1),
            e["date"] or "—",
            etype,
            e["description"] or "—",
            f"PKR {given:,.0f}"    if given    else "—",
            f"PKR {received:,.0f}" if received else "—",
            f"PKR {running:,.0f}",
        ])
    d.append(["", "TOTALS", "", "",
              f"PKR {total_given:,.0f}",
              f"PKR {total_received:,.0f}",
              f"PKR {net:,.0f}"])

    _append_table(story, d,
        [uw*.04, uw*.10, uw*.12, uw*.32, uw*.13, uw*.14, uw*.15],
        C_PERSON)

    # ── Summary box ──
    we_owe   = max(-net, 0)   # net < 0 means we owe them
    they_owe = max(net,  0)   # net > 0 means they owe us
    _build_summary_box(story, uw, C_PERSON,
        [("Total Cash Given",    f"PKR {total_given:,.0f}"),
         ("Total Cash Received", f"PKR {total_received:,.0f}"),
         ("Net Balance",         f"PKR {abs(net):,.0f}")],
        abs(net), we_owe, they_owe)

    doc.build(story)
    return out_path
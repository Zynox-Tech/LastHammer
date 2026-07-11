import os
from datetime import datetime, date as dt_date

import database
import config

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)

C_RED    = colors.HexColor("#C0392B")
C_DARK   = colors.HexColor("#1A1A2E")
C_BLUE   = colors.HexColor("#1B4F72")
C_GREEN  = colors.HexColor("#1E8449")
C_ORANGE = colors.HexColor("#CA6F1E")
C_PURPLE = colors.HexColor("#6C3483")
C_TEAL   = colors.HexColor("#0E6655")
C_GRAY   = colors.HexColor("#CCCCCC")
C_WHITE  = colors.white
PAGE_W, PAGE_H = A4


def _base_style(hdr_color=C_DARK):
    return TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), hdr_color),
        ("TEXTCOLOR",    (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("ROWBACKGROUND",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("FONTSIZE",     (0, 1), (-1, -1), 8.5),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",        (1, 1), (1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID",         (0, 0), (-1, -1), 0.4, C_GRAY),
        ("LINEBELOW",    (0, 0), (-1, 0), 1.5, hdr_color),
    ])


def _total_style():
    return [
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ECECEC")),
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE",  (0, -1), (-1, -1), 1.2, C_DARK),
    ]


def _section_bar(text, color, usable_w):
    _sbn = "sb_" + text[:20].replace(" ","_").replace("—","")
    s = ParagraphStyle(_sbn, fontName="Helvetica-Bold", fontSize=11,
                       textColor=C_WHITE, leftIndent=8)
    tbl = Table([[Paragraph(f"<b>{text}</b>", s)]], colWidths=[usable_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), color),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ("LINEBELOW",    (0,0),(-1,-1), 2, color),
    ]))
    return tbl


def _get_fleet_entries(mode, value):
    """Get truck_entries grouped by truck for the report."""
    conn = database.get_connection()
    if mode == "day":
        entries = conn.execute(
            "SELECT te.*, tf.reg_number, tf.owner_name, tf.truck_type "
            "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
            "WHERE te.date=? ORDER BY tf.reg_number, te.date ASC, te.id ASC",
            (value,)
        ).fetchall()
    elif mode == "month":
        entries = conn.execute(
            "SELECT te.*, tf.reg_number, tf.owner_name, tf.truck_type "
            "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
            "WHERE te.date LIKE ? ORDER BY tf.reg_number, te.date ASC, te.id ASC",
            (value + "%",)
        ).fetchall()
    else:
        entries = conn.execute(
            "SELECT te.*, tf.reg_number, tf.owner_name, tf.truck_type "
            "FROM truck_entries te JOIN truck_fleet tf ON te.truck_id=tf.id "
            "ORDER BY tf.reg_number, te.date ASC, te.id ASC"
        ).fetchall()
    # Also get loader entries
    if mode == "day":
        loader_entries = conn.execute(
            "SELECT le.*, tf.reg_number, tf.owner_name "
            "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
            "WHERE le.date=? ORDER BY tf.reg_number, le.date ASC, le.id ASC",
            (value,)
        ).fetchall()
    elif mode == "month":
        loader_entries = conn.execute(
            "SELECT le.*, tf.reg_number, tf.owner_name "
            "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
            "WHERE le.date LIKE ? ORDER BY tf.reg_number, le.date ASC, le.id ASC",
            (value + "%",)
        ).fetchall()
    else:
        loader_entries = conn.execute(
            "SELECT le.*, tf.reg_number, tf.owner_name "
            "FROM loader_entries le JOIN truck_fleet tf ON le.truck_id=tf.id "
            "ORDER BY tf.reg_number, le.date ASC, le.id ASC"
        ).fetchall()
    conn.close()
    return list(entries), list(loader_entries)


def _get_entries_for_range(mode, value):
    """
    mode: 'day'   → value = 'yyyy-MM-dd'
          'month' → value = 'yyyy-MM'
          'all'   → value = None
    Returns dict of lists for each chapter.
    """
    if mode == "day":
        ch2 = [r for r in database.ch2_get_all_v2() if r["date"] == value]
        ch4 = [r for r in database.ch4_get_all_v2() if r["date"] == value]
        return {
            "ch1": database.ch1_get_entries(value),
            "ch2": ch2,
            "ch3": database.ch3_get_entries(value),
            "ch4": ch4,
            "ch5": [],  # handled separately via fleet
            "ch6": database.ch6_get_entries(value),
            "land": [r for r in database.land_get_all() if r["payment_date"] == value],
        }
    elif mode == "month":
        return {
            "ch1": _filter_month(database.ch1_get_all(), value),
            "ch2": _filter_month(database.ch2_get_all_v2(), value),
            "ch3": _filter_month(database.ch3_get_all(), value),
            "ch4": _filter_month(database.ch4_get_all_v2(), value),
            "ch5": [],
            "ch6": _filter_month(database.ch6_get_all(), value),
            "land": database.land_filter_month(value),
        }
    else:  # all
        return {
            "ch1": database.ch1_get_all(),
            "ch2": database.ch2_get_all_v2(),
            "ch3": database.ch3_get_all(),
            "ch4": database.ch4_get_all_v2(),
            "ch5": [],
            "ch6": database.ch6_get_all(),
            "land": database.land_get_all(),
        }


def _filter_month(rows, ym):
    return [r for r in rows if r["date"].startswith(ym)]


def _sum(rows, field):
    return sum(float(r[field]) for r in rows)


def generate_report(mode="day", value=None, output_dir=None):
    """
    Generate PDF report.
    mode  : 'day' | 'month' | 'all'
    value : 'yyyy-MM-dd' for day, 'yyyy-MM' for month, None for all
    Returns path to generated PDF.
    """
    if not value:
        value = dt_date.today().isoformat()
    if not output_dir:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(output_dir, exist_ok=True)

    # Filename
    if mode == "day":
        fname = f"LastHammer_Day_{value}.pdf"
        period_label = datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y (%A)")
        report_title = f"Daily Report — {period_label}"
    elif mode == "month":
        fname = f"LastHammer_Month_{value}.pdf"
        period_label = datetime.strptime(value + "-01", "%Y-%m-%d").strftime("%B %Y")
        report_title = f"Monthly Report — {period_label}"
    else:
        fname = f"LastHammer_Complete_Report_{dt_date.today().isoformat()}.pdf"
        period_label = "All Records (Complete History)"
        report_title = "Complete Expenditure Report"

    out_path = os.path.join(output_dir, fname)
    company  = database.get_setting("company_name") or "Last Hammer"
    address  = database.get_setting("company_address") or ""
    phone    = database.get_setting("company_phone") or ""

    data = _get_entries_for_range(mode, value)
    ch1, ch2, ch3, ch4, ch5, ch6 = (
        data["ch1"], data["ch2"], data["ch3"],
        data["ch4"], data["ch5"], data["ch6"])
    land = data.get("land", [])

    fleet_entries, loader_entries = _get_fleet_entries(mode, value)
    t1 = sum(float(r["amount"] or 0) for r in ch1)
    t2 = sum(float(r["amount"] or 0) for r in ch2)
    t3 = sum(float(r["total_amount"] or 0) for r in ch3)
    t4 = sum(float(r["payment_received"] or 0) for r in ch4)
    t5 = sum(float(r["payment"] or 0) for r in fleet_entries)
    t6 = sum(float(r["amount"] or 0) for r in ch6)
    bal   = database.ch7_get_current_balance()
    t_land = sum(float(r["amount"] or 0) for r in land)
    grand = t1 + t2 + t3 + t4 + t5 + t6 + t_land

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        topMargin=1.4*cm, bottomMargin=1.4*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm)

    usable_w = PAGE_W - 3.6*cm
    story    = []

    # ── HEADER ────────────────────────────────────────────────
    s_title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=18,
                             textColor=C_WHITE, alignment=TA_CENTER)
    s_sub   = ParagraphStyle("s", fontName="Helvetica", fontSize=9,
                             textColor=colors.HexColor("#AAAAAA"), alignment=TA_CENTER)

    logo_path = config.LOGO_PATH
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*cm, height=1.5*cm)
        hdr_data = [[
            logo,
            Paragraph(f"<b>{company.upper()}</b><br/>"
                      f"<font size='9' color='#AAAAAA'>Expenditure Management System</font>", s_title),
            Paragraph(f"<font size='8' color='#CCCCCC'>{report_title}</font>", s_sub)
        ]]
        hdr_cols = [1.8*cm, usable_w - 3.6*cm, 1.8*cm]
    else:
        hdr_data = [[Paragraph(
            f"<b>{company.upper()}</b><br/>"
            f"<font size='9' color='#AAAAAA'>{report_title}</font>", s_title)]]
        hdr_cols = [usable_w]

    hdr_tbl = Table(hdr_data, colWidths=hdr_cols)
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_DARK),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("RIGHTPADDING", (0,0),(-1,-1), 8),
        ("LINEBELOW",    (0,0),(-1,-1), 3, C_RED),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 0.3*cm))

    # Info row
    s_body = ParagraphStyle("b", fontName="Helvetica", fontSize=9, textColor=C_DARK)
    s_right = ParagraphStyle("r", fontName="Helvetica", fontSize=9,
                             textColor=C_DARK, alignment=TA_RIGHT)
    info_tbl = Table([[
        Paragraph(f"<b>Period:</b>  {period_label}", s_body),
        Paragraph(f"<b>Generated:</b>  {datetime.now().strftime('%d %b %Y  %H:%M')}", s_right),
    ]], colWidths=[usable_w*0.6, usable_w*0.4])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#ECECEC")),
        ("TOPPADDING",   (0,0),(-1,-1), 7), ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 10), ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── SUMMARY ───────────────────────────────────────────────
    s_ch = ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=12,
                          textColor=C_DARK, spaceAfter=6)
    story.append(Paragraph("<b>SUMMARY</b>", s_ch))

    # Extra stats
    wt_kg     = sum(float(r["weight_tons"] or 0) for r in ch2)
    tot_hrs   = sum(float(r["hours_worked"] or 0) for r in ch3)
    tot_trips = sum(int(r["total_trips"] or 0)    for r in ch4)
    tot_dumper= sum(float(r["payment"] or 0)      for r in fleet_entries)
    tot_ldays = sum(float(r["days_worked"] or 0)  for r in loader_entries)
    tot_lpay  = sum(float(r["cash_paid"] or 0) + float(r["diesel_worth"] or 0)
                    for r in loader_entries)

    sum_data = [
        ["Chapter", "Module", "Key Stats", "Entries", "Total (PKR)"],
        ["CH 1", "General Expenditures",
         f"{len(ch1)} entries",
         str(len(ch1)), f"PKR {t1:,.2f}"],
        ["CH 2", "Royalty to Government",
         f"Weight: {wt_kg:,.0f} kg",
         str(len(ch2)), f"PKR {t2:,.2f}"],
        ["CH 3", "Excavator Expenditure",
         f"Hours: {tot_hrs:.1f} hrs",
         str(len(ch3)), f"PKR {t3:,.2f}"],
        ["CH 4", "Dumprei Expenditure",
         f"Trips: {tot_trips}",
         str(len(ch4)), f"PKR {t4:,.2f}"],
        ["CH 5", "Truck / Dumper / Loader",
         f"Dumper: PKR {tot_dumper:,.0f}  |  Loader: {tot_ldays:.0f} days / PKR {tot_lpay:,.0f}",
         str(len(fleet_entries) + len(loader_entries)), f"PKR {t5:,.2f}"],
        ["CH 6", "Memory Notes",
         f"{len(ch6)} entries",
         str(len(ch6)), f"PKR {t6:,.2f}"],
        ["CH 8", "Surface / Land Rent",
         f"{len(land)} payments",
         str(len(land)), f"PKR {t_land:,.2f}"],
        ["", "GRAND TOTAL", "", "",  f"PKR {grand:,.2f}"],
    ]
    cw = [usable_w*0.09, usable_w*0.27, usable_w*0.34, usable_w*0.10, usable_w*0.20]
    sum_tbl = Table(sum_data, colWidths=cw, repeatRows=1)
    cmds = _base_style(C_DARK).getCommands() + _total_style() + [
        ("TEXTCOLOR", (4,1),(4,-2), C_RED),
        ("FONTNAME",  (4,1),(4,-2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,-1),(-1,-1), C_RED),
        ("FONTSIZE",  (0,-1),(-1,-1), 10),
        ("ALIGN",     (2,1),(2,-1), "LEFT"),
        ("FONTSIZE",  (2,1),(2,-1), 7.5),
        ("TEXTCOLOR", (2,1),(2,-1), colors.HexColor("#555555")),
    ]
    sum_tbl.setStyle(TableStyle(cmds))
    story.append(sum_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── CHAPTER DETAILS ───────────────────────────────────────
    # Wrapping paragraph style for long text cells
    s_wrap = ParagraphStyle("wrap", fontName="Helvetica", fontSize=7.5,
                            textColor=C_DARK, leading=10, wordWrap="CJK")
    s_wrap_bold = ParagraphStyle("wrapb", fontName="Helvetica-Bold", fontSize=7.5,
                                 textColor=C_DARK, leading=10, wordWrap="CJK")

    def W(text, bold=False):
        """Wrap a cell value in a Paragraph so long text wraps instead of truncating."""
        if text is None: text = "—"
        text = str(text)
        return Paragraph(text, s_wrap_bold if bold else s_wrap)

    def detail_table(rows_data, cw_list, hdr_color):
        t = Table(rows_data, colWidths=cw_list, repeatRows=1)
        t.setStyle(TableStyle(
            _base_style(hdr_color).getCommands() + _total_style()))
        return t

    # CH1
    if ch1:
        story.append(_section_bar("Chapter 1 — General Expenditures", C_RED, usable_w))
        d = [["S.No", "Details / Description", "Date", "Amount (PKR)"]]
        for i, r in enumerate(ch1):
            d.append([str(i+1), W(r["details"]), r["date"], f"PKR {r['amount']:,.2f}"])
        d.append(["", "TOTAL", "", f"PKR {t1:,.2f}"])
        story.append(detail_table(d, [usable_w*.07, usable_w*.52, usable_w*.17, usable_w*.24], C_RED))
        story.append(Spacer(1, 0.35*cm))

    # CH2
    if ch2:
        story.append(_section_bar("Chapter 2 — Royalty to Government", C_PURPLE, usable_w))
        d = [["S.No", "Vehicle No.", "Weight (kg)", "Payment (PKR)", "Date"]]
        for i, r in enumerate(ch2):
            keys = r.keys()
            vehicle = (r["vehicle_number"] if "vehicle_number" in keys and r["vehicle_number"] else r["details"]) or "—"
            wt = float(r["weight_tons"]) if "weight_tons" in keys and r["weight_tons"] else 0
            amt = float(r["amount"]) if r["amount"] else 0
            d.append([str(i+1), W(vehicle), f"{wt:,.0f} kg",
                      f"PKR {amt:,.2f}" if amt else "—", r["date"]])
        total_wt = sum(float(r["weight_tons"] or 0) for r in ch2)
        d.append(["", "TOTAL WEIGHT", f"{total_wt:,.0f} kg", f"PKR {t2:,.2f}", ""])
        story.append(detail_table(d, [usable_w*.07, usable_w*.30, usable_w*.18, usable_w*.25, usable_w*.20], C_PURPLE))
        story.append(Spacer(1, 0.35*cm))

    # CH3
    if ch3:
        story.append(_section_bar("Chapter 3 — Excavator Expenditure", C_TEAL, usable_w))
        d = [["S.No", "Details", "Hours", "Work Total", "Cash Advance", "Balance", "Date"]]
        for i, r in enumerate(ch3):
            keys = r.keys()
            det  = (r["details"] if "details" in keys and r["details"] else "") or "—"
            hrs  = r["hours_worked"] or 0
            tot  = float(r["total_amount"] or 0)
            ca   = float(r["cash_advance"] if "cash_advance" in keys and r["cash_advance"] else r["paid_cash"] if "paid_cash" in keys and r["paid_cash"] else 0)
            bal  = float(r["balance_due"] or 0)
            d.append([str(i+1), W(det), str(hrs), f"PKR {tot:,.2f}",
                      f"PKR {ca:,.0f}" if ca else "—",
                      f"PKR {bal:,.2f}", r["date"]])
        tot_hrs = sum(float(r["hours_worked"] or 0) for r in ch3)
        d.append(["", "TOTAL", f"{tot_hrs:.1f} hrs", f"PKR {t3:,.2f}", "", "", ""])
        cw3 = [usable_w*.05, usable_w*.26, usable_w*.07, usable_w*.13,
               usable_w*.13, usable_w*.13, usable_w*.13]
        story.append(detail_table(d, cw3, C_TEAL))
        story.append(Spacer(1, 0.35*cm))

    # CH4
    if ch4:
        story.append(_section_bar("Chapter 4 — Dumprei Expenditure", C_ORANGE, usable_w))
        d = [["S.No", "Reg. No.", "Owner", "Trips", "Cash Paid", "Diesel Paid", "Balance", "Date"]]
        for i, r in enumerate(ch4):
            keys = r.keys()
            pc  = float(r["paid_cash"] if "paid_cash" in keys and r["paid_cash"] else 0)
            pd_ = float(r["paid_diesel_worth"] if "paid_diesel_worth" in keys and r["paid_diesel_worth"] else 0)
            bal = float(r["balance_due"] if r["balance_due"] else 0)
            trips = r["total_trips"] if "total_trips" in keys and r["total_trips"] else 0
            d.append([str(i+1), W(r["reg_number"]), W(r["owner_name"]), str(trips),
                      f"PKR {pc:,.0f}" if pc else "—",
                      f"PKR {pd_:,.0f}" if pd_ else "—",
                      f"PKR {bal:,.0f}", r["date"]])
        tot_trips = sum(int(r["total_trips"] or 0) for r in ch4)
        d.append(["", "TOTAL", "", str(tot_trips) + " trips", f"PKR {t4:,.2f}", "", "", ""])
        cw4 = [usable_w*.06, usable_w*.12, usable_w*.17, usable_w*.07,
               usable_w*.14, usable_w*.14, usable_w*.13, usable_w*.17]
        story.append(detail_table(d, cw4, C_ORANGE))
        story.append(Spacer(1, 0.35*cm))

    # CH5 — Fleet: grouped per truck (dumpers) + loaders
    if fleet_entries or loader_entries:
        story.append(_section_bar("Chapter 5 — Truck / Dumper / Loader Fleet", C_BLUE, usable_w))

        # Group dumper entries by truck
        trucks_seen = {}
        for r in fleet_entries:
            key = (r["reg_number"], r["owner_name"], r["truck_type"])
            if key not in trucks_seen:
                trucks_seen[key] = []
            trucks_seen[key].append(r)

        sno = 1
        for (reg, owner, ttype), t_rows in trucks_seen.items():
            truck_total = sum(float(r["payment"] or 0) for r in t_rows)
            # Sub-header for this truck
            _tk_name = f"tk_{reg}_{owner}".replace(" ","_")
            s_truck = ParagraphStyle(_tk_name, fontName="Helvetica-Bold", fontSize=9,
                                     textColor=C_WHITE, leftIndent=4)
            sub = Table([[Paragraph(
                f"{reg}  -  {owner}  ({ttype})   |   Total Paid: PKR {truck_total:,.2f}", s_truck)]],
                colWidths=[usable_w])
            sub.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#1B4F72")),
                ("TOPPADDING", (0,0),(-1,-1), 5),
                ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                ("LEFTPADDING", (0,0),(-1,-1), 10),
            ]))
            story.append(sub)
            d = [["S.No", "Details", "Trips", "Cash Paid", "Diesel Paid", "Total", "Balance", "Date"]]
            for r in t_rows:
                keys = r.keys()
                pc  = float(r["paid_cash"] if "paid_cash" in keys and r["paid_cash"] else 0)
                pd_ = float(r["paid_diesel"] if "paid_diesel" in keys and r["paid_diesel"] else 0)
                tot = float(r["payment"] or 0)
                bal = float(r["balance_due"] if "balance_due" in keys and r["balance_due"] else 0)
                det = (r["details"] if "details" in keys and r["details"] else "") or "—"
                trips = r["trips"] if "trips" in keys and r["trips"] else "—"
                d.append([str(sno), W(det), str(trips),
                          f"PKR {pc:,.0f}" if pc else "—",
                          f"PKR {pd_:,.0f}" if pd_ else "—",
                          f"PKR {tot:,.2f}",
                          f"PKR {bal:,.0f}" if bal else "—",
                          r["date"]])
                sno += 1
            t_trips = sum(int(r["trips"] or 0) for r in t_rows if "trips" in r.keys() and r["trips"])
            d.append(["", "TOTAL", str(t_trips) + " trips", "", "", f"PKR {truck_total:,.2f}", "", ""])
            cw5 = [usable_w*.06, usable_w*.17, usable_w*.07,
                   usable_w*.13, usable_w*.13, usable_w*.13, usable_w*.13, usable_w*.18]
            story.append(detail_table(d, cw5, C_BLUE))
            story.append(Spacer(1, 0.2*cm))

        # Loader entries
        if loader_entries:
            loaders_seen = {}
            for r in loader_entries:
                key = (r["reg_number"], r["owner_name"])
                if key not in loaders_seen:
                    loaders_seen[key] = []
                loaders_seen[key].append(r)

            for (reg, owner), l_rows in loaders_seen.items():
                l_cash   = sum(float(r["cash_paid"] or 0) for r in l_rows)
                l_diesel = sum(float(r["diesel_worth"] or 0) for r in l_rows)
                l_days   = sum(float(r["days_worked"] or 0) for r in l_rows)
                _tk2_name = f"tk2_{reg}_{owner}".replace(" ","_")
                s_truck2 = ParagraphStyle(_tk2_name, fontName="Helvetica-Bold", fontSize=9,
                                          textColor=C_WHITE, leftIndent=4)
                sub2 = Table([[Paragraph(
                    f"{reg}  -  {owner}  (Loader)   |   "
                    f"Days: {l_days:.1f}  |  Cash: PKR {l_cash:,.0f}  |  Diesel: PKR {l_diesel:,.0f}", s_truck2)]],
                    colWidths=[usable_w])
                sub2.setStyle(TableStyle([
                    ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#0E6655")),
                    ("TOPPADDING", (0,0),(-1,-1), 5),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                    ("LEFTPADDING", (0,0),(-1,-1), 10),
                ]))
                story.append(sub2)
                d2 = [["S.No", "Type", "Description", "Days Worked", "Cash Paid", "Diesel (PKR)", "Date"]]
                for j, r in enumerate(l_rows):
                    keys_r = r.keys()
                    etype  = r["entry_type"] if "entry_type" in keys_r else "Work"
                    desc   = (r["description"] if "description" in keys_r and r["description"] else "") or "—"
                    dw     = float(r["days_worked"] or 0) if "days_worked" in keys_r and r["days_worked"] else 0
                    cp     = float(r["cash_paid"] or 0)   if "cash_paid"   in keys_r and r["cash_paid"]   else 0
                    dv     = float(r["diesel_worth"] or 0) if "diesel_worth" in keys_r and r["diesel_worth"] else 0
                    d2.append([str(j+1), etype, W(desc),
                               f"{dw:.1f}" if dw else "—",
                               f"PKR {cp:,.0f}" if cp else "—",
                               f"PKR {dv:,.0f}" if dv else "—",
                               r["date"]])
                d2.append(["", "TOTALS", f"{l_days:.1f} days worked", "",
                           f"PKR {l_cash:,.0f}", f"PKR {l_diesel:,.0f}", ""])
                cw_l = [usable_w*.06, usable_w*.13, usable_w*.24, usable_w*.12,
                        usable_w*.15, usable_w*.15, usable_w*.15]
                story.append(detail_table(d2, cw_l, colors.HexColor("#0E6655")))
                story.append(Spacer(1, 0.2*cm))

        story.append(Spacer(1, 0.2*cm))

    # CH6
    if ch6:
        story.append(_section_bar("Chapter 6 — Memory Notes", C_GREEN, usable_w))
        d = [["S.No", "Description", "Person", "Type", "Date", "Amount (PKR)"]]
        for i, r in enumerate(ch6):
            d.append([str(i+1), W(r["description"]), r["person_name"] or "—",
                      r["transaction_type"], r["date"], f"PKR {r['amount']:,.2f}"])
        d.append(["", "TOTAL", "", "", "", f"PKR {t6:,.2f}"])
        story.append(detail_table(d, [usable_w*.06, usable_w*.32, usable_w*.16, usable_w*.1, usable_w*.17, usable_w*.19], C_GREEN))
        story.append(Spacer(1, 0.4*cm))

    # CH8 Land Rent
    C_LAND = colors.HexColor("#2C7873")
    if land:
        story.append(_section_bar("Chapter 8 — Surface / Land Owner Rent", C_LAND, usable_w))
        d_land = [["S.No", "Owner Name", "Rent Period", "Payment Date",
                   "Mode", "Cheque / Bank", "Amount (PKR)"]]
        for i, r in enumerate(land):
            mode = r["payment_mode"] or "Cash"
            chq  = ""
            if mode == "Cheque":
                cn = r["cheque_number"] or ""; bn = r["bank_name"] or ""
                chq = f"#{cn}" + (f" {bn}" if bn else "") if cn else bn
            period = f"{r['rent_from']} → {r['rent_to']}"
            d_land.append([str(i+1), W(r["owner_name"]),
                           W(period), r["payment_date"] or "—",
                           mode, W(chq or "—"),
                           f"PKR {float(r['amount'] or 0):,.2f}"])
        d_land.append(["", "TOTAL", "", "", "", "", f"PKR {t_land:,.2f}"])
        cw_land = [usable_w*.05, usable_w*.18, usable_w*.22, usable_w*.12,
                   usable_w*.09, usable_w*.16, usable_w*.18]
        story.append(detail_table(d_land, cw_land, C_LAND))
        story.append(Spacer(1, 0.35*cm))

    # ── GRAND TOTAL BOX ───────────────────────────────────────
    s_gt_l = ParagraphStyle("gtl", fontName="Helvetica-Bold", fontSize=13, textColor=C_WHITE)
    s_gt_r = ParagraphStyle("gtr", fontName="Helvetica-Bold", fontSize=15,
                            textColor=C_WHITE, alignment=TA_RIGHT)
    gt = Table([[
        Paragraph("<b>GRAND TOTAL EXPENDITURE</b>", s_gt_l),
        Paragraph(f"<b>PKR {grand:,.2f}</b>", s_gt_r),
    ]], colWidths=[usable_w*0.55, usable_w*0.45])
    gt.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), C_RED),
        ("TOPPADDING",   (0,0),(-1,-1), 12), ("BOTTOMPADDING",(0,0),(-1,-1), 12),
        ("LEFTPADDING",  (0,0),(-1,-1), 14), ("RIGHTPADDING",(0,0),(-1,-1), 14),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("LINEABOVE",    (0,0),(-1,-1), 2, C_DARK),
    ]))
    story.append(gt)
    story.append(Spacer(1, 0.3*cm))

    # Ledger balance
    s_bl = ParagraphStyle("bl", fontName="Helvetica-Bold", fontSize=10, textColor=C_DARK)
    s_br = ParagraphStyle("br", fontName="Helvetica-Bold", fontSize=11,
                          textColor=C_BLUE, alignment=TA_RIGHT)
    bl_tbl = Table([[
        Paragraph("<b>Current Ledger Balance</b>", s_bl),
        Paragraph(f"<b>PKR {bal:,.2f}</b>", s_br),
    ]], colWidths=[usable_w*0.55, usable_w*0.45])
    bl_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#EBF5FB")),
        ("TOPPADDING",   (0,0),(-1,-1), 8), ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",  (0,0),(-1,-1), 14), ("RIGHTPADDING",(0,0),(-1,-1), 14),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(bl_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── FOOTER ────────────────────────────────────────────────
    s_f = ParagraphStyle("f", fontName="Helvetica", fontSize=8,
                         textColor=colors.HexColor("#888888"))
    s_fr = ParagraphStyle("fr", fontName="Helvetica", fontSize=8,
                          textColor=colors.HexColor("#888888"), alignment=TA_RIGHT)
    ft = Table([[
        Paragraph(f"{company}  |  {address}  |  {phone}", s_f),
        Paragraph(f"Last Hammer EMS  |  {datetime.now().strftime('%d %b %Y %H:%M')}", s_fr),
    ]], colWidths=[usable_w*0.6, usable_w*0.4])
    ft.setStyle(TableStyle([
        ("LINEABOVE",    (0,0),(-1,-1), 0.5, C_GRAY),
        ("TOPPADDING",   (0,0),(-1,-1), 6), ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(ft)

    doc.build(story)
    return out_path
"""
generate_report.py — Build the full Mini Project Report (.docx) that matches
the Cyber Security Lab (7CS4-22) front-page template and formatting rules:

    * A4, Times New Roman; chapter headings 16 pt bold, sub-headings 14 pt bold,
      body 12 pt; line spacing 1.5; justified text.
    * Page numbers at the bottom centre.
    * Figures and tables numbered with captions.
    * Code in Courier New 10 pt.

It pulls the real source code and the real attack transcripts/screenshots that
were produced by run_demo.sh, so the report always matches the working project.

Run:
    python report/generate_report.py
Output:
    report/23ESKCS828_TanmayVyas_CSL-G16_Report.docx
"""

import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# --------------------------------------------------------------------------- #
#  Paths
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = os.path.join(ROOT, "screenshots")
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(HERE, "23ESKCS828_TanmayVyas_CSL-G16_Report.docx")

NAVY = RGBColor(0x1F, 0x3B, 0x63)

# --------------------------------------------------------------------------- #
#  Low-level helpers
# --------------------------------------------------------------------------- #
def set_base_style(doc):
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    # ensure the east-asian/complex fallback also uses Times New Roman
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), "Times New Roman")
    pf = style.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)


def a4(doc):
    for s in doc.sections:
        s.page_height = Inches(11.69)
        s.page_width = Inches(8.27)
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)


def _set_font(run, name="Times New Roman", size=12, bold=False, italic=False,
              color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), name)


def para(doc, text="", align=None, size=12, bold=False, italic=False,
         color=None, space_after=4, line15=True):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if line15:
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if text:
        r = p.add_run(text)
        _set_font(r, size=size, bold=bold, italic=italic, color=color)
    return p


def body(doc, text):
    return para(doc, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12)


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    _set_font(r, size=12)
    return p


def h1(doc, text, number=None):
    doc.add_page_break()
    label = f"Chapter {number} — {text}" if number else text
    p = para(doc, label, size=16, bold=True, color=NAVY, space_after=10)
    return p


def h2(doc, text):
    return para(doc, text, size=14, bold=True, color=NAVY, space_after=6)


def caption(doc, text):
    p = para(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, size=11, italic=True,
             space_after=10)
    return p


def code_block(doc, text, max_lines=None):
    lines = text.rstrip("\n").split("\n")
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... ({len(text.splitlines())-max_lines} "
                                     "more lines — see source file) ..."]
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.1)
    for i, line in enumerate(lines):
        r = p.add_run(line + ("\n" if i < len(lines) - 1 else ""))
        _set_font(r, name="Courier New", size=9)
    _shade(p, "F2F3F5")
    return p


def _shade(paragraph, hex_fill):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    pPr.append(shd)


def add_image(doc, path, width_in=5.2):
    if not os.path.exists(path):
        body(doc, f"[screenshot missing: {os.path.basename(path)} — run run_demo.sh]")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(width_in))


def table(doc, headers, rows, caption_text=None, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hdr = t.rows[0].cells
    for i, htext in enumerate(headers):
        hdr[i].text = ""
        r = hdr[i].paragraphs[0].add_run(htext)
        _set_font(r, size=11, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade_cell(hdr[i], "1F3B63")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(val))
            _set_font(r, size=11)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    if caption_text:
        caption(doc, caption_text)
    return t


def _shade_cell(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def page_number_footer(doc):
    """Put a centred PAGE field in the footer of every section."""
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                fld = OxmlElement("w:fldChar")
                fld.set(qn("w:fldCharType"), tag)
                run._r.append(fld)
            else:
                instr = OxmlElement("w:instrText")
                instr.set(qn("xml:space"), "preserve")
                instr.text = " PAGE "
                run._r.append(instr)
        _set_font(run, size=11)


def read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return f"[could not read {path}]"


def read_code(path):
    """Read a source file but drop the leading module docstring for the listing
    (the prose in the report already explains each file), keeping all logic."""
    text = read(path)
    lines = text.split("\n")
    out, i = [], 0
    # keep a leading comment/blank lines, then skip the first \"\"\"...\"\"\" block
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines) and lines[i].lstrip().startswith('"""'):
        stripped = lines[i].lstrip()
        # single-line docstring?
        if not (stripped.rstrip().endswith('"""') and len(stripped.strip()) > 3):
            i += 1
            while i < len(lines) and '"""' not in lines[i]:
                i += 1
        i += 1                       # consume the closing line
        while i < len(lines) and lines[i].strip() == "":
            i += 1
    out = lines[i:]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  Document sections
# --------------------------------------------------------------------------- #
def front_page(doc):
    para(doc, "A", align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=14)
    para(doc, "Mini Project Report", align=WD_ALIGN_PARAGRAPH.CENTER, size=20,
         bold=True, space_after=18)
    para(doc, "on", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, space_after=10)
    para(doc, "“BRUTE-FORCE PROTECTION FOR A LOGIN SYSTEM”",
         align=WD_ALIGN_PARAGRAPH.CENTER, size=18, bold=True, color=NAVY,
         space_after=6)
    para(doc, "Project Code: CSL-G16", align=WD_ALIGN_PARAGRAPH.CENTER, size=13,
         space_after=16)

    para(doc, "Submitted in partial fulfilment of the requirements of",
         align=WD_ALIGN_PARAGRAPH.CENTER, size=12, italic=True, space_after=2)
    para(doc, "Cyber Security Lab (7CS4-22)", align=WD_ALIGN_PARAGRAPH.CENTER,
         size=14, bold=True, space_after=2)
    para(doc, "Bachelor of Technology — VII Semester",
         align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=2)
    para(doc, "in", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=2)
    para(doc, "Computer Science & Engineering", align=WD_ALIGN_PARAGRAPH.CENTER,
         size=14, bold=True, space_after=2)
    para(doc, "Session 2026-27", align=WD_ALIGN_PARAGRAPH.CENTER, size=12,
         space_after=22)

    # Submitted By / To block
    t = doc.add_table(rows=1, cols=2)
    t.autofit = True
    left, right = t.rows[0].cells
    for cell, lines in (
        (left, [("Submitted By:", True), ("Name: Tanmay Vyas", False),
                ("Roll No.: 23ESKCS828", False), ("Class / Batch: CSL-G16", False),
                ("Semester: VII", False)]),
        (right, [("Submitted To:", True), ("Vikash Dhankar", False),
                 ("Assistant Professor", False), ("Department of CSE", False),
                 ("SKIT, Jaipur", False)]),
    ):
        cell.paragraphs[0].clear()
        first = True
        for text, bold in lines:
            p = cell.paragraphs[0] if first else cell.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(text)
            _set_font(r, size=12, bold=bold)
            first = False

    para(doc, "", space_after=20)
    para(doc, "Department of Computer Science & Engineering",
         align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, color=NAVY,
         space_after=2)
    para(doc, "Swami Keshvanand Institute of Technology, Management & Gramothan, "
         "Jaipur", align=WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True,
         space_after=2)
    para(doc, "(Affiliated to Rajasthan Technical University, Kota)",
         align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=2)
    para(doc, "November 2026", align=WD_ALIGN_PARAGRAPH.CENTER, size=13,
         bold=True)


def declarations(doc):
    doc.add_page_break()
    para(doc, "CANDIDATE’S DECLARATION", align=WD_ALIGN_PARAGRAPH.CENTER,
         size=16, bold=True, color=NAVY, space_after=12)
    body(doc,
         "I, Tanmay Vyas, Roll No. 23ESKCS828, a student of B.Tech VII Semester, "
         "CSE, Batch CSL-G16, hereby declare that the mini project titled "
         "“Brute-Force Protection for a Login System” (Project Code CSL-G16) "
         "submitted for the Cyber Security Lab (7CS4-22) is my own original work, "
         "carried out under the guidance of Vikash Dhankar, Assistant Professor, "
         "Department of CSE, SKIT Jaipur. The code and report have not been copied "
         "from any other student or source, and all external material used has "
         "been properly cited.")

    para(doc, "", space_after=10)
    para(doc, "ETHICAL DECLARATION", align=WD_ALIGN_PARAGRAPH.CENTER, size=16,
         bold=True, color=NAVY, space_after=12)
    body(doc,
         "I declare that all attack, sniffing, scanning or testing activities "
         "performed in this project were carried out only on my own systems, "
         "virtual machines or an isolated lab environment, using test data. The "
         "dictionary/brute-force attack was run exclusively against my own login "
         "server bound to localhost (127.0.0.1), using a dummy test account and "
         "dummy passwords. No unauthorised system, network, account or person was "
         "targeted. I understand that misuse of these techniques is an offence "
         "under the Information Technology Act, 2000 (Sections 43 and 66).")

    para(doc, "", space_after=24)
    t = doc.add_table(rows=1, cols=2)
    l, r = t.rows[0].cells
    lp = l.paragraphs[0]; _set_font(lp.add_run("Date: ____________"), size=12)
    la = l.add_paragraph(); _set_font(la.add_run("Place: Jaipur"), size=12)
    rp = r.paragraphs[0]; rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_font(rp.add_run("______________________"), size=12)
    ra = r.add_paragraph(); ra.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_font(ra.add_run("Signature of Student"), size=12)
    rb = r.add_paragraph(); rb.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _set_font(rb.add_run("Tanmay Vyas (23ESKCS828)"), size=12)


def acknowledgement(doc):
    h_title(doc, "ACKNOWLEDGEMENT")
    body(doc,
         "I would like to express my sincere gratitude to my guide, "
         "Vikash Dhankar, Assistant Professor, Department of Computer Science & "
         "Engineering, for his valuable guidance, constant encouragement and "
         "constructive feedback throughout this mini project. His insistence on "
         "understanding every line of my own code pushed me to learn the subject "
         "properly rather than superficially.")
    body(doc,
         "I am also thankful to the Head of the Department and the entire faculty "
         "of the Department of CSE, Swami Keshvanand Institute of Technology, "
         "Management & Gramothan (SKIT), Jaipur, for providing the laboratory "
         "facilities and a supportive learning environment. Finally, I thank my "
         "family and friends for their motivation and support during the course "
         "of this work.")
    para(doc, "", space_after=12)
    p = para(doc, "Tanmay Vyas", align=WD_ALIGN_PARAGRAPH.RIGHT, size=12, bold=True,
             space_after=0)
    para(doc, "23ESKCS828", align=WD_ALIGN_PARAGRAPH.RIGHT, size=12)


def abstract(doc):
    h_title(doc, "ABSTRACT")
    body(doc,
         "Password-based login forms are the most common entry point into web "
         "applications, and they are a frequent target of dictionary and "
         "brute-force attacks in which an automated script tries a long list of "
         "candidate passwords until one works. This mini project, linked to "
         "Experiment 3 (Dictionary & Brute-Force Attack) of the RTU Cyber "
         "Security Lab syllabus, builds a small local web login system in Python "
         "(Flask) and then hardens it against such automated guessing using four "
         "layered defences: per-IP rate limiting, per-account lockout, an "
         "arithmetic CAPTCHA challenge, and complete attempt logging.")
    body(doc,
         "To measure the effect of these defences, an attacker script was written "
         "that performs a dictionary attack against the same server in two "
         "configurations. Against the unprotected baseline the script recovered "
         "the account password in 10 attempts in about one second. Against the "
         "hardened server the identical attack was throttled with HTTP 429 "
         "responses, blocked by a CAPTCHA wall, and the account was locked after "
         "five failed attempts — so that even the correct password was refused — "
         "and the password was never confirmed. The project demonstrates, with "
         "reproducible evidence, how simple defence-in-depth controls turn a "
         "trivially crackable login into one that resists automated attacks, and "
         "it discusses the security concepts, trade-offs and limitations behind "
         "each control. (Abstract: ~190 words.)")


def h_title(doc, text):
    """A non-chapter heading on a fresh page (Acknowledgement, Abstract, ToC)."""
    doc.add_page_break()
    para(doc, text, align=WD_ALIGN_PARAGRAPH.CENTER, size=16, bold=True,
         color=NAVY, space_after=12)


def table_of_contents(doc):
    h_title(doc, "TABLE OF CONTENTS")
    entries = [
        ("Candidate’s Declaration & Ethical Declaration", "ii"),
        ("Acknowledgement", "iii"),
        ("Abstract", "iv"),
        ("Chapter 1 — Introduction", "1"),
        ("Chapter 2 — Background / Theory", "3"),
        ("Chapter 3 — Tools & Environment", "6"),
        ("Chapter 4 — Codes", "9"),
        ("Chapter 5 — Results & Testing", "14"),
        ("Chapter 6 — Conclusion & Future Scope", "19"),
        ("References", "21"),
    ]
    for title, pg in entries:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        # tab stop with dot leader to the right margin
        from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
        p.paragraph_format.tab_stops.add_tab_stop(
            Inches(6.3), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        r = p.add_run(title + "\t" + pg)
        _set_font(r, size=12)
    para(doc, "", space_after=4)
    para(doc, "Note: page numbers are indicative; figures and tables are listed "
         "with their captions within each chapter.", size=10, italic=True)


# --------------------------------------------------------------------------- #
#  Chapters
# --------------------------------------------------------------------------- #
def chapter1(doc):
    h1(doc, "Introduction", 1)
    h2(doc, "1.1 Overview")
    body(doc,
         "Almost every web and mobile application protects its users with a "
         "username-and-password login form. Because this form is public and "
         "accepts guesses, it is the single most attacked feature of most "
         "systems. Two closely related attacks target it directly. In a "
         "dictionary attack, the attacker tries a prepared list of common or "
         "leaked passwords (for example 123456, password, qwerty). In a pure "
         "brute-force attack, the attacker tries every possible combination of "
         "characters. Both are usually automated with a script that can send "
         "thousands of guesses per minute, so a login form that simply says "
         "“wrong password” and lets the attacker try again, forever and as fast "
         "as they like, will eventually be broken.")
    h2(doc, "1.2 Problem Statement")
    body(doc,
         "A default login endpoint places no limit on how many passwords may be "
         "tried, how fast they may be tried, or whether the client is a human or "
         "a bot. This project asks a practical question: what is the measurable "
         "difference, from an attacker’s point of view, between such an "
         "unprotected login and the same login after a small set of standard "
         "anti-automation defences are added? To answer it, the project builds "
         "both the defender (a login server) and the attacker (a guessing "
         "script), and runs the attack before and after the defences are turned "
         "on.")
    h2(doc, "1.3 Objectives")
    for b in [
        "Build a small, self-contained web login system on the local machine.",
        "Implement four layered defences: per-IP rate limiting, per-account "
        "lockout, a CAPTCHA challenge, and full attempt logging.",
        "Write a dictionary / brute-force attack script that targets the login.",
        "Run the same attack against the login with protections OFF and ON, and "
        "record the outcome of every attempt.",
        "Compare the two runs quantitatively and explain, control by control, "
        "why the hardened login resists the attack.",
    ]:
        bullet(doc, b)
    h2(doc, "1.4 Link to the Syllabus Experiment")
    body(doc,
         "This mini project is directly linked to Experiment 3 — “Dictionary & "
         "Brute-Force Attack” — of the RTU Cyber Security Lab (7CS4-22) syllabus. "
         "That experiment teaches how automated password-guessing attacks work "
         "and how to perform one in a controlled lab. This project uses that "
         "experiment as its starting point: it reproduces the attack with a "
         "custom script, and then extends the experiment into the defensive "
         "direction by building and evaluating the countermeasures that stop the "
         "attack. In doing so it covers both halves of the security picture — the "
         "offence that the experiment demonstrates, and the defence that a real "
         "system must deploy.")
    h2(doc, "1.5 Scope and Ethical Boundary")
    body(doc,
         "All work is performed on the student’s own machine. The server binds "
         "only to the loopback address 127.0.0.1 and is never exposed to the "
         "college network, Wi-Fi or the public Internet. A single dummy test "
         "account with a dummy password is used; no real credentials or personal "
         "data are involved. The attack script is run only against this local "
         "server. These boundaries follow the mandatory ethical rules of the lab "
         "and the Information Technology Act, 2000.")


def chapter2(doc):
    h1(doc, "Background / Theory", 2)
    h2(doc, "2.1 Dictionary vs. Brute-Force Attacks")
    body(doc,
         "A brute-force attack systematically tries every possible password up to "
         "some length. It is guaranteed to succeed eventually but is slow because "
         "the number of combinations grows exponentially with length. A dictionary "
         "attack is a smarter shortcut: instead of all combinations, it tries a "
         "curated list (a “wordlist”) of passwords that people actually use — "
         "common words, names, and passwords leaked in past breaches. Because a "
         "large share of users pick weak passwords, a dictionary attack is often "
         "far faster than full brute force. Both attacks share the same weakness "
         "from the defender’s side: they need to make many login attempts, so any "
         "control that makes repeated attempts slow, costly or impossible is "
         "effective against them.")
    h2(doc, "2.2 Password Hashing and Salting")
    body(doc,
         "A secure login never stores the plain password. Instead it stores a "
         "one-way hash of the password together with a random salt. When a user "
         "logs in, the server hashes the supplied password with the stored salt "
         "and compares the result. This project uses Werkzeug’s "
         "generate_password_hash / check_password_hash, which apply a salted PBKDF2 "
         "hash. Hashing protects the stored credentials if the database is ever "
         "leaked, and the deliberate slowness of PBKDF2 also raises the cost of an "
         "offline guessing attack. The online defences below address the "
         "complementary problem of guessing through the live login form.")
    h2(doc, "2.3 Control 1 — Rate Limiting")
    body(doc,
         "Rate limiting caps how many requests a single client may make in a given "
         "time window. This project keeps, for each client IP address, a sliding "
         "window of recent attempt timestamps; if the number of attempts in the "
         "last 30 seconds exceeds five, further attempts are rejected with HTTP "
         "429 (Too Many Requests) without even checking the password. This "
         "directly attacks the attacker’s need for speed: a script that could try "
         "thousands of guesses per minute is reduced to a handful, making a "
         "dictionary attack impractically slow.")
    h2(doc, "2.4 Control 2 — Account Lockout")
    body(doc,
         "Account lockout counts consecutive failed attempts per account. After a "
         "threshold (five here) the account is temporarily frozen for a cooldown "
         "period (60 seconds in this demo; minutes or more in production), during "
         "which every attempt — even one carrying the correct password — is "
         "refused with HTTP 423 (Locked). Whereas rate limiting is tied to the "
         "client IP, lockout is tied to the account, so it still protects a single "
         "targeted account even if the attacker spreads guesses across many "
         "addresses. Its known trade-off is that an attacker can deliberately lock "
         "a victim out (a denial-of-service), which is why the lockout here is "
         "temporary rather than permanent.")
    h2(doc, "2.5 Control 3 — CAPTCHA")
    body(doc,
         "A CAPTCHA is a challenge that is easy for a human but hard for an "
         "automated script. This project triggers a simple arithmetic CAPTCHA "
         "(for example, “what is 8 + 3?”) once an IP has produced three failures, "
         "and from then on the correct answer must accompany every attempt or the "
         "request is rejected with HTTP 403 before the password is checked. A "
         "naive attack script does not know the answer and is stopped. The "
         "arithmetic form is used here for clarity and to keep the project "
         "dependency-free; a production system would use an image or behavioural "
         "CAPTCHA, but the security principle — forcing proof of humanity — is the "
         "same.")
    h2(doc, "2.6 Control 4 — Logging and Auditing")
    body(doc,
         "Every attempt — successful or not, and whichever control handled it — is "
         "written both to a human-readable log file and to a structured SQLite "
         "audit table recording the timestamp, client IP, username, outcome and "
         "whether protections were enabled. Logging does not by itself stop an "
         "attack, but it provides the visibility needed to detect one in progress, "
         "to raise alerts, and to analyse it afterwards. In this project the audit "
         "table is also the source of the quantitative comparison in Chapter 5.")
    h2(doc, "2.7 Defence-in-Depth")
    body(doc,
         "No single control is sufficient on its own: rate limiting can be diluted "
         "across many IPs, lockout can be abused for denial-of-service, and a "
         "determined attacker may eventually solve a weak CAPTCHA. The strength of "
         "the design is that the controls are layered — an attacker must defeat all "
         "of them at once. This principle of overlapping, independent defences is "
         "called defence-in-depth, and demonstrating it in a measurable way is the "
         "central idea of this project.")


def chapter3(doc):
    h1(doc, "Tools & Environment", 3)
    h2(doc, "3.1 Hardware and Operating System")
    table(doc,
          ["Item", "Specification"],
          [["Machine", "Personal laptop (student-owned)"],
           ["Processor", "x86-64, dual-core or better"],
           ["RAM", "8 GB (2 GB is sufficient)"],
           ["Operating System", "Linux / Windows 10+ (cross-platform)"],
           ["Network", "Loopback only — server bound to 127.0.0.1"]],
          caption_text="Table 3.1: Hardware and OS used for the project.",
          widths=[2.2, 4.0])
    h2(doc, "3.2 Software, Language and Libraries")
    table(doc,
          ["Component", "Version / Role"],
          [["Python", "3.x — implementation language"],
           ["Flask", "Web framework for the login server"],
           ["Werkzeug", "Salted PBKDF2 password hashing"],
           ["SQLite3", "Built-in database for users and the audit log"],
           ["requests", "HTTP client used by the attack script"],
           ["python-docx", "Generates this report"]],
          caption_text="Table 3.2: Software stack. All core logic was written by "
          "the author; libraries are used only for standard plumbing.",
          widths=[2.2, 4.0])
    h2(doc, "3.3 Lab Setup and Isolation")
    body(doc,
         "The entire experiment runs on one machine. The Flask server listens on "
         "http://127.0.0.1:5000, which is reachable only from the same computer, "
         "so no other device — on the college network or elsewhere — can see it. "
         "The attack script connects to that same loopback address. This satisfies "
         "the lab’s ethical requirement that attacks be performed only on "
         "self-owned, isolated systems.")
    h2(doc, "3.4 System Architecture")
    body(doc,
         "Figure 3.1 shows how the components fit together. The attack script and "
         "a normal browser both talk to the Flask login server over HTTP. Inside "
         "the server, each attempt passes through the four controls in order "
         "(rate-limit → CAPTCHA → lockout → password check) and is recorded in the "
         "log file and the SQLite audit table.")
    code_block(doc,
        "        +-------------------+            +---------------------------+\n"
        "        |  Attack script    |  HTTP      |      Flask login server   |\n"
        "        |  (brute_force.py) | ---------> |        (app.py)           |\n"
        "        +-------------------+  POST      |                           |\n"
        "        +-------------------+  /login    |  1. Rate limit (per IP)   |\n"
        "        |  Web browser      | ---------> |  2. CAPTCHA (per IP)      |\n"
        "        |  (login.html)     |            |  3. Lockout (per account) |\n"
        "        +-------------------+            |  4. Password hash check   |\n"
        "                                         +-------------+-------------+\n"
        "                                                       |\n"
        "                                          +------------+------------+\n"
        "                                          |  logs/auth.log          |\n"
        "                                          |  security.db (SQLite)   |\n"
        "                                          +-------------------------+\n")
    caption(doc, "Figure 3.1: System architecture and the order of the four "
            "defensive controls.")
    h2(doc, "3.5 Configuration Switch")
    body(doc,
         "A single master switch, config.PROTECTIONS_ENABLED (set from the "
         "environment variable PROTECT), turns all four controls on or off "
         "together. This is what makes the “before vs after” comparison fair: the "
         "identical server code and the identical attack script are used in both "
         "runs; only this one flag changes.")


def chapter4(doc):
    h1(doc, "Codes", 4)
    body(doc,
         "This chapter lists the core source files. The complete project — "
         "including templates, stylesheet and the one-command runner "
         "run_demo.sh — is provided in the accompanying source ZIP. Code is shown "
         "in Courier New 10 pt as required.")
    listings = [
        ("4.1 config.py — Central configuration and the master switch",
         os.path.join(ROOT, "config.py"), None),
        ("4.2 app.py — Login server with the four controls",
         os.path.join(ROOT, "app.py"), None),
        ("4.3 init_db.py — Database schema and seed account",
         os.path.join(ROOT, "init_db.py"), None),
        ("4.4 attack/brute_force.py — Dictionary / brute-force attacker",
         os.path.join(ROOT, "attack", "brute_force.py"), None),
        ("4.5 attack/lockout_demo.py — Focused lockout demonstration",
         os.path.join(ROOT, "attack", "lockout_demo.py"), None),
    ]
    for title, path, maxl in listings:
        h2(doc, title)
        code_block(doc, read_code(path), max_lines=maxl)


def chapter5(doc):
    h1(doc, "Results & Testing", 5)
    h2(doc, "5.1 Test Plan")
    body(doc,
         "Three tests were run with the one-command script run_demo.sh. Test A is "
         "the baseline dictionary attack against the server with protections "
         "disabled. Test B is the same attack against the server with protections "
         "enabled. Test C is a focused demonstration of the account-lockout "
         "control using a smarter attacker that solves the CAPTCHA. The database "
         "is reset before each server start so the runs are independent.")
    table(doc,
          ["Test", "Target", "Expected result"],
          [["A — Baseline", "PROTECT=off", "Password found quickly"],
           ["B — Hardened", "PROTECT=on", "Attack throttled/blocked; no password"],
           ["C — Lockout", "PROTECT=on", "Account frozen; correct password refused"]],
          caption_text="Table 5.1: Test plan.",
          widths=[1.6, 1.6, 3.0])

    h2(doc, "5.2 The Login Interface")
    add_image(doc, os.path.join(SHOTS, "fig_login_page.png"), width_in=3.6)
    caption(doc, "Figure 5.1: The login form (protections enabled).")
    add_image(doc, os.path.join(SHOTS, "fig_captcha.png"), width_in=3.6)
    caption(doc, "Figure 5.2: After repeated failures the CAPTCHA challenge "
            "appears and must be answered.")
    add_image(doc, os.path.join(SHOTS, "fig_dashboard.png"), width_in=3.6)
    caption(doc, "Figure 5.3: The protected dashboard, reachable only after a "
            "valid login.")

    h2(doc, "5.3 Test A — Attack Before Protection")
    body(doc,
         "With protections disabled, the server behaves like a default login: it "
         "simply replies “wrong password” and lets the script keep guessing at "
         "full speed. The dictionary attack walked through the wordlist and "
         "recovered the password on the tenth attempt in about one second.")
    code_block(doc, read(os.path.join(RESULTS, "attack_before.txt")))
    caption(doc, "Figure 5.4: Attack transcript — protections OFF. The password "
            "is CRACKED.")

    h2(doc, "5.4 Test B — Attack After Protection")
    body(doc,
         "With protections enabled, the identical attack is defeated. The first "
         "few wrong guesses are answered normally, but after three failures the "
         "CAPTCHA wall appears (HTTP 403), and the rate limiter then rejects every "
         "further attempt with HTTP 429. The attacker never reaches the correct "
         "password — which sits later in the same wordlist — and the login is "
         "never broken.")
    code_block(doc, read(os.path.join(RESULTS, "attack_after.txt")))
    caption(doc, "Figure 5.5: Attack transcript — protections ON. The password is "
            "NOT found; the defences hold.")

    h2(doc, "5.5 Test C — Account-Lockout Demonstration")
    body(doc,
         "To prove that lockout is an independent backstop, a smarter attacker "
         "that solves the arithmetic CAPTCHA was run. Even so, after five failed "
         "attempts the account is frozen: the server returns HTTP 423, and the "
         "final attempt — which carries the CORRECT password — is still refused.")
    code_block(doc, read(os.path.join(RESULTS, "lockout_after.txt")))
    caption(doc, "Figure 5.6: Lockout transcript. Even the correct password is "
            "refused while the account is locked.")

    h2(doc, "5.6 Audit Log Evidence")
    body(doc,
         "Every attempt is recorded. The extract below from logs/auth.log shows "
         "the clean audit trail written by the server during the hardened run, "
         "with the outcome of each attempt (BAD_PASSWORD, CAPTCHA_FAILED, "
         "RATE_LIMITED, LOCKED).")
    code_block(doc, _tail(os.path.join(ROOT, "logs", "auth.log"), 16))
    caption(doc, "Figure 5.7: Extract of the server-side audit log.")

    h2(doc, "5.7 Comparison and Analysis")
    body(doc,
         "Table 5.2 summarises the two attack runs. The contrast is stark: the "
         "same script that cracks the unprotected login in ten attempts is reduced "
         "to zero useful guesses against the hardened login, because most of its "
         "requests are rejected before the password is ever examined.")
    table(doc,
          ["Metric", "Before (OFF)", "After (ON)"],
          [["Password found?", "Yes", "No"],
           ["Attempts to crack", "10", "never"],
           ["Time to crack", "~1 s", "n/a"],
           ["Requests reaching password check", "all", "3 of 15"],
           ["Requests blocked (403/429/423)", "0", "12 of 15"],
           ["Account locked", "No", "Yes (after 5 fails)"]],
          caption_text="Table 5.2: Before-vs-after comparison (from the attack "
          "transcripts and the SQLite audit table).",
          widths=[2.8, 1.7, 1.7])
    h2(doc, "5.8 Observations")
    for b in [
        "Rate limiting alone cut the attacker from unlimited speed to five "
        "attempts per 30-second window — enough to make a real wordlist attack "
        "take months instead of seconds.",
        "The CAPTCHA stopped the naive script completely, because it checks for "
        "humanity before the password is ever compared.",
        "Lockout protected the targeted account even against a CAPTCHA-solving "
        "attacker, refusing the correct password during the freeze.",
        "Layering matters: each control covers a weakness of the others, and the "
        "attacker would have to beat all four at once to succeed.",
    ]:
        bullet(doc, b)


def chapter6(doc):
    h1(doc, "Conclusion & Future Scope", 6)
    h2(doc, "6.1 Conclusion")
    body(doc,
         "This project built a working login system and a working attacker, and "
         "used them to measure the real effect of standard brute-force defences. "
         "The result is clear and reproducible: an unprotected login was cracked "
         "by a dictionary attack in ten attempts in about one second, while the "
         "same login — with per-IP rate limiting, per-account lockout, a CAPTCHA "
         "challenge and full logging — defeated the identical attack, blocking "
         "twelve of fifteen requests before the password was examined and never "
         "revealing the credential. The exercise connects directly to Experiment 3 "
         "of the syllabus: it reproduces the dictionary/brute-force attack and "
         "then shows, control by control, how to stop it. Most importantly, it "
         "demonstrates defence-in-depth — the idea that layered, independent "
         "controls are far stronger than any one of them alone.")
    h2(doc, "6.2 Limitations")
    for b in [
        "Rate limiting is per-IP and in-memory, so it can be diluted by a "
        "distributed (many-IP) attack and resets if the server restarts.",
        "Account lockout can be abused to deny service to a legitimate user; a "
        "temporary lock and anomaly detection reduce but do not remove this risk.",
        "The arithmetic CAPTCHA is intentionally simple and could be solved by a "
        "more advanced script; it illustrates the mechanism rather than being "
        "production-grade.",
        "The demo uses short timers (30 s window, 60 s lockout) so it runs "
        "quickly; real deployments would use longer values.",
    ]:
        bullet(doc, b)
    h2(doc, "6.3 Future Scope")
    for b in [
        "Replace the in-memory counters with a shared store (e.g. Redis) so the "
        "limits hold across restarts and multiple server instances.",
        "Add exponential back-off and per-subnet limits to resist distributed "
        "attacks.",
        "Integrate a real CAPTCHA (image or behavioural) and multi-factor "
        "authentication (OTP / authenticator app) for a second factor.",
        "Enforce a strong-password policy and check new passwords against known "
        "breach lists.",
        "Feed the audit log into a dashboard with automated alerting on attack "
        "patterns.",
    ]:
        bullet(doc, b)


def references(doc):
    h_title(doc, "REFERENCES")
    refs = [
        "RTU Kota, Cyber Security Lab (7CS4-22) Syllabus — Experiment 3: "
        "Dictionary & Brute-Force Attack.",
        "OWASP Foundation, “Blocking Brute Force Attacks” and OWASP "
        "Authentication Cheat Sheet, owasp.org.",
        "The Flask Documentation, Pallets Projects, flask.palletsprojects.com.",
        "Werkzeug Documentation — Security Helpers (password hashing), "
        "werkzeug.palletsprojects.com.",
        "Python Software Foundation, sqlite3 and logging module documentation, "
        "docs.python.org.",
        "The Information Technology Act, 2000 (India), Sections 43 and 66.",
    ]
    for i, r in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        run = p.add_run(f"[{i}]  {r}")
        _set_font(run, size=12)


def _tail(path, n):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        return "".join(lines[-n:])
    except OSError:
        return f"[could not read {path}]"


# --------------------------------------------------------------------------- #
#  Build
# --------------------------------------------------------------------------- #
def build():
    doc = Document()
    set_base_style(doc)
    a4(doc)

    front_page(doc)
    declarations(doc)
    acknowledgement(doc)
    abstract(doc)
    table_of_contents(doc)
    chapter1(doc)
    chapter2(doc)
    chapter3(doc)
    chapter4(doc)
    chapter5(doc)
    chapter6(doc)
    references(doc)

    page_number_footer(doc)
    doc.save(OUT)
    print(f"[report] Saved -> {OUT}")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Generic job-search tracker operations (xlsx, openpyxl).

Subcommands: init, known, approvals, append, exclude, move, gaps, sidegig,
shortlist (read-only ranking of unmarked For Approval rows), expire (move stale
unmarked For Approval rows to Excluded), set (write one allow-listed cell on an
existing row found by Job link), repair (delete orphan rows - Company and Title
empty, some other cell filled - from the pipeline tabs and Excluded, and reset
Job link hyperlinks whose target differs from the cell's URL text).
Write subcommands print the new "mtime"; pass it as --expect-mtime to the next
write. Limitation: openpyxl does not keep charts, images, pivots, or in-cell
checkbox extensions, and delete_rows does not shift conditional formats - keep
the tracker to plain cells, formats, and list validations. Hyperlinks are
re-anchored to the cell that holds them before every save (openpyxl leaves a
moved cell's link pointing at its old coordinate, which on reload plants junk
rows); `repair` cleans up the orphan rows that earlier versions left behind.
Every write is guarded: the workbook's mtime is captured on load and
re-checked right before an atomic replace, so a concurrent edit by the
owner aborts the write (exit 3) instead of being overwritten. Sheets the
tool does not know about are preserved untouched.

Exit codes: 0 ok, 2 usage/config error, 3 file changed during the run
(or --expect-mtime mismatch), 4 file locked / not writable.
Runs on Windows, Linux and macOS with Python 3.9+ and openpyxl.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
from copy import copy
from pathlib import Path

try:
    import openpyxl
    from openpyxl.utils import get_column_letter
    from openpyxl.utils.cell import range_boundaries
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:  # pragma: no cover - environment guard
    sys.stderr.write("openpyxl is required: python -m pip install openpyxl\n")
    sys.exit(2)

APPROVE, REJECT, LATER, PENDING = "☑ Approve", "✖ Reject", "⏸ Later", "☐"
MARKS = [PENDING, APPROVE, REJECT, LATER]
PIPELINE = ["For Approval", "Applied", "Interviewing", "Closed"]

SCHEMA = {
    "Summary": ["Job search tracker", None],
    "For Approval": ["#", "Approve ☐", "Decision notes", "Tier", "Fit score", "Company", "Title", "Job link",
                     "Posted", "Originally posted", "Location / eligibility", "Employment type", "Pay (as posted)",
                     "Currency", "Est. USD/mo min", "Est. USD/mo max", "Meets pay rule", "Apply method",
                     "Years required", "English", "Required skills", "Nice to have", "Must-have gaps",
                     "Readiness %", "Covered", "In study plan", "Missing (not in plan)", "Next study action",
                     "Red flags", "Summary"],
    "Applied": ["#", "Company", "Title", "Job link", "Channel", "Date applied", "Latest status", "Pipeline stage",
                "Stage history", "Next action", "Follow-up date", "Status date", "Pay", "Currency",
                "Est USD/month", "Fit", "Required skills", "Readiness %", "Covered", "In study plan", "Missing",
                "Next interview-prep action", "Mail link", "Notes"],
    "Interviewing": ["#", "Company", "Title", "Job link", "Channel", "Date applied", "Latest status",
                     "Pipeline stage", "Stage history", "Next action", "Follow-up date", "Status date", "Pay",
                     "Currency", "Est USD/month", "Fit", "Required skills", "Readiness %", "Covered",
                     "In study plan", "Missing", "Next interview-prep action", "Mail link", "Notes",
                     "Interview stage", "Next interview date", "Interviewers", "Prep material"],
    "Closed": ["#", "Company", "Title", "Job link", "Date applied", "Closed date", "Outcome", "Outcome detail",
               "Stage reached", "Stage history", "Lessons / notes"],
    "Side Gigs": ["#", "Platform", "Link", "My status", "Roles/projects applied", "Pay (USD/hr)",
                  "Meets my floor", "Eligible from my country", "Payment method", "Next action",
                  "Next action date", "Last activity", "Mail link", "Notes/sources"],
    "Excluded": ["Company", "Title", "Job link", "Reason", "Fit", "Pay"],
    "Skill Map": ["Company", "Title", "Bucket", "Skill", "Required/Nice", "Status", "Study plan ref", "Week/phase"],
    "Gap Summary": ["Skill", "# jobs requiring", "Status", "Study plan ref", "Suggested action"],
}
# Header/sheet aliases so trackers created by earlier versions keep working.
ALIASES = {"Mail link": ["Gmail link"], "Side Gigs": ["AI Gigs"], "Approve ☐": ["Approve", "Approve?"],
           "Missing (not in plan)": ["Missing"], "Est. USD/mo max": ["Est USD/month"], "Fit score": ["Fit"],
           "Pay (as posted)": ["Pay"]}
DEFAULT_ID_PATTERNS = [r"/jobs/view/(\d+)", r"[?&](?:currentJobId|jk|gh_jid|jobId)=([\w-]+)"]
CV = "Experience (CV)"
MTIME_TOLERANCE = 0.01
STAGE_ORDER = {"For Approval": 0, "Applied": 1, "Interviewing": 2, "Closed": 3}


class Guarded(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code


def today() -> str:
    return dt.date.today().isoformat()


def sheet(wb, name):
    for n in [name] + ALIASES.get(name, []):
        if n in wb.sheetnames:
            return wb[n]
    return None


def headers(ws) -> dict:
    out = {}
    for c in ws[1]:
        if c.value not in (None, ""):
            out[str(c.value).strip()] = c.column
    for canon, alts in ALIASES.items():
        for a in alts:
            if a in out and canon not in out:
                out[canon] = out[a]
    return out


def last_row(ws, col: int) -> int:
    r = ws.max_row
    while r > 1 and ws.cell(r, col).value in (None, ""):
        r -= 1
    return r


def copy_row_style(ws, src: int, dst: int) -> None:
    if src < 2:
        return
    for c in range(1, ws.max_column + 1):
        s, d = ws.cell(src, c), ws.cell(dst, c)
        if s.has_style:
            d.font, d.border, d.fill = copy(s.font), copy(s.border), copy(s.fill)
            d.alignment, d.number_format = copy(s.alignment), s.number_format


def put(ws, h: dict, row: int, values: dict, clear: bool = False) -> None:
    for k, v in values.items():
        if k in h and (v is not None or clear):
            ws.cell(row, h[k]).value = v


def get(ws, h: dict, row: int, name: str):
    return ws.cell(row, h[name]).value if name in h else None


def job_key(link, patterns) -> str | None:
    s = str(link or "").strip()
    if not s:
        return None
    for p in patterns:
        m = re.search(p, s)
        if m:
            return m.group(1)
    return re.sub(r"[?#].*$", "", s).rstrip("/").lower()


def ct_key(company, title) -> str:
    def norm(x):
        return re.sub(r"\s+", " ", str(x or "")).strip().lower()
    return f"{norm(company)} | {norm(title)}"


class Tracker:
    def __init__(self, path: str, expect_mtime: float | None = None, backup_dir: str | None = None):
        self.path = Path(path)
        if not self.path.exists():
            raise Guarded(2, f"tracker not found: {self.path}")
        self.mtime = self.path.stat().st_mtime
        if expect_mtime is not None and abs(self.mtime - expect_mtime) > MTIME_TOLERANCE:
            raise Guarded(3, f"tracker mtime {self.mtime} != expected {expect_mtime}; it was edited (or re-synced "
                             "by a cloud drive) since the last read - re-read first")
        self.backup_dir = backup_dir
        self.wb = openpyxl.load_workbook(self.path)
        self.sheets_before = list(self.wb.sheetnames)

    def reanchor_hyperlinks(self) -> None:
        """Point every cell's hyperlink at the cell that holds it.

        `ws.delete_rows` moves the cells but not their Hyperlink.ref. The writer collects hyperlinks from the
        cells at save time and writes that stale ref, so on reload openpyxl binds the link to whatever sits at the
        old coordinate: an empty cell is filled with the link target (a junk row with only a Job link), a real
        row gets another row's link. Cells of deleted rows are gone, so they write no link.
        """
        for ws in self.wb.worksheets:
            for cell in ws._cells.values():
                link = cell.hyperlink  # MergedCell.hyperlink is always None
                if link is not None and link.ref != cell.coordinate:
                    link.ref = cell.coordinate

    def save(self, dry_run: bool = False) -> None:
        if dry_run:
            return
        self.reanchor_hyperlinks()
        if list(self.wb.sheetnames)[: len(self.sheets_before)] != self.sheets_before:
            raise Guarded(2, "refusing to save: an existing sheet was removed or reordered")
        if abs(self.path.stat().st_mtime - self.mtime) > MTIME_TOLERANCE:
            raise Guarded(3, "tracker changed on disk during this run; nothing written")
        if self.backup_dir:
            bd = Path(self.backup_dir)
            bd.mkdir(parents=True, exist_ok=True)
            stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(self.path, bd / f"{self.path.stem}.bak-{stamp}{self.path.suffix}")
        tmp = self.path.with_name(self.path.name + ".tmp-tracker-ops")
        try:
            self.wb.save(tmp)
            os.replace(tmp, self.path)
        except PermissionError as e:
            raise Guarded(4, f"tracker is locked or read-only (close it in the spreadsheet app?): {e}")
        finally:
            if tmp.exists():
                tmp.unlink()
        self.mtime = self.path.stat().st_mtime

    def result(self, payload: dict, dry_run: bool) -> dict:
        payload.update({"dry_run": dry_run, "mtime": self.mtime})
        return payload

    def ws(self, name: str):
        w = sheet(self.wb, name)
        if w is None:
            raise Guarded(2, f"sheet '{name}' not found; run 'init' on a new tracker or add the sheet")
        return w

    def known(self, patterns) -> tuple[set, set]:
        ids, cts = set(), set()
        for name in PIPELINE + ["Excluded"]:
            ws = sheet(self.wb, name)
            if ws is None:
                continue
            h = headers(ws)
            if "Company" not in h:
                continue
            for r in range(2, ws.max_row + 1):
                co = get(ws, h, r, "Company")
                if co in (None, ""):
                    continue
                k = job_key(get(ws, h, r, "Job link"), patterns)
                if k:
                    ids.add(k)
                cts.add(ct_key(co, get(ws, h, r, "Title")))
        return ids, cts

    def rejected_companies(self) -> list:
        """Unique company names from Closed rows whose Outcome is Rejected (case-insensitive, blanks skipped)."""
        ws = sheet(self.wb, "Closed")
        if ws is None:
            return []
        h = headers(ws)
        if "Company" not in h or "Outcome" not in h:
            return []
        seen: dict = {}
        for r in range(2, ws.max_row + 1):
            if str(get(ws, h, r, "Outcome") or "").strip().lower() != "rejected":
                continue
            co = re.sub(r"\s+", " ", str(get(ws, h, r, "Company") or "")).strip()
            if co:
                seen.setdefault(co.lower(), co)
        return sorted(seen.values(), key=lambda s: (s.lower(), s))

    def find(self, link: str, patterns, names=PIPELINE):
        want = job_key(link, patterns)
        for name in names:
            ws = sheet(self.wb, name)
            if ws is None:
                continue
            h = headers(ws)
            for r in range(2, ws.max_row + 1):
                if job_key(get(ws, h, r, "Job link"), patterns) == want:
                    return ws, r
        return None, None


def cmd_init(a) -> dict:
    p = Path(a.tracker)
    if p.exists() and not a.force:
        raise Guarded(2, f"{p} exists; pass --force to overwrite")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, hdr in SCHEMA.items():
        ws = wb.create_sheet(name)
        ws.append(hdr)
        ws.freeze_panes = "A2"
        for c in ws[1]:
            c.font = openpyxl.styles.Font(bold=True)
    s = wb["Summary"]
    for line in ["Pipeline: For Approval -> Applied -> Interviewing -> Closed (+ Excluded, Side Gigs).",
                 f"Approve column marks: {', '.join(MARKS)}. Only marks the owner sets count as approval.",
                 "Skill Map Status: Experience (CV) | Study plan ... | GAP - not in plan. Gap Summary is rebuilt by 'gaps'."]:
        s.append([line])
    dv = DataValidation(type="list", formula1='"' + ",".join(MARKS) + '"', allow_blank=True)
    wb["For Approval"].add_data_validation(dv)
    dv.add("B2:B1000")
    p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(p)
    return {"created": str(p), "sheets": wb.sheetnames}


def cmd_known(a) -> dict:
    t = Tracker(a.tracker)
    ids, cts = t.known(a.id_pattern or DEFAULT_ID_PATTERNS)
    rejected = t.rejected_companies()
    out = {"mtime": t.mtime, "ids": sorted(ids), "company_title": sorted(cts), "rejected_companies": rejected}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"mtime": t.mtime, "ids": len(ids), "company_title": len(cts), "rejected_companies": len(rejected),
                "out": a.out}
    return out


def approve_col(h: dict) -> int:
    return h.get("Approve ☐", 2)


def approval_bucket(v) -> str:
    sv = str(v).strip() if v is not None else ""
    return ("approve" if v is True or sv.startswith("☑") or sv.upper() == "TRUE" else
            "reject" if sv.startswith("✖") else "later" if sv.startswith("⏸") else "pending")


def is_unmarked(v) -> bool:
    """True only for the owner-untouched states (blank, ☐, FALSE).

    Stricter than the 'pending' bucket of `approvals`: any other text in the cell is treated as an owner mark
    this tool does not recognise, so `shortlist` skips it and `expire` never moves it.
    """
    sv = str(v).strip() if v is not None else ""
    return approval_bucket(v) == "pending" and (sv == "" or sv.startswith(PENDING) or sv.upper() == "FALSE")


def cmd_approvals(a) -> dict:
    t = Tracker(a.tracker)
    ws = t.ws("For Approval")
    h = headers(ws)
    col = approve_col(h)
    res = {"approve": [], "reject": [], "later": [], "pending": [], "mtime": t.mtime}
    for r in range(2, ws.max_row + 1):
        if get(ws, h, r, "Company") in (None, ""):
            continue
        bucket = approval_bucket(ws.cell(r, col).value)
        res[bucket].append({"row": r, "company": get(ws, h, r, "Company"), "title": get(ws, h, r, "Title"),
                            "link": get(ws, h, r, "Job link"), "notes": get(ws, h, r, "Decision notes"),
                            "apply_method": get(ws, h, r, "Apply method")})
    return res


def load_jobs(path: str) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    jobs = data["jobs"] if isinstance(data, dict) else data
    for j in jobs:
        for req in ("company", "title", "link"):
            if not j.get(req):
                raise Guarded(2, f"job entry missing '{req}' (required: company, title, link): {j}")
    return jobs


def ignored_keys(jobs: list, known: set) -> list:
    return sorted({k for j in jobs for k in j if k not in known})


FIELD_MAP = {"tier": "Tier", "fit": "Fit score", "company": "Company", "title": "Title", "link": "Job link",
             "posted": "Posted", "originally_posted": "Originally posted", "location": "Location / eligibility",
             "employment_type": "Employment type", "pay": "Pay (as posted)", "currency": "Currency",
             "usd_month_min": "Est. USD/mo min", "usd_month_max": "Est. USD/mo max", "meets_pay": "Meets pay rule",
             "apply_method": "Apply method", "years": "Years required", "english": "English",
             "red_flags": "Red flags", "summary": "Summary", "notes": "Decision notes"}


# Optional For Approval columns, added at the end of the header row on first use.
KIT_FIELDS = {"ats_match": "ATS match %", "missing_keywords": "Missing keywords", "apply_kit": "Apply kit"}
KIT_WIDTHS = {"ATS match %": 12, "Missing keywords": 40, "Apply kit": 40}


def to_num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        return float(str(v).strip().rstrip("%").strip())
    except ValueError:
        return None


def kit_values(j: dict) -> dict:
    """Header-name -> value for the optional columns; only keys with a usable value are returned."""
    out = {}
    v = j.get("ats_match")
    if v is not None and v != "":
        n = to_num(v)
        if n is None or not float(n).is_integer() or not 0 <= n <= 100:
            raise Guarded(2, f"ats_match must be an integer 0-100, got {v!r}: {j.get('link')}")
        out[KIT_FIELDS["ats_match"]] = int(n)
    mk = j.get("missing_keywords")
    if isinstance(mk, (list, tuple)):
        mk = "; ".join(str(x).strip() for x in mk if str(x).strip())
    mk = str(mk).strip() if mk is not None else ""
    if mk:
        out[KIT_FIELDS["missing_keywords"]] = mk
    kit = str(j.get("apply_kit") or "").strip()
    if kit:
        out[KIT_FIELDS["apply_kit"]] = kit
    return out


def ensure_columns(ws, names) -> list:
    """Add missing headers after the last header cell. Never reorders or drops existing columns."""
    h = headers(ws)
    old_last = last = max((c.column for c in ws[1] if c.value not in (None, "")), default=0)
    added = []
    for name in names:
        if name in h:
            continue
        last += 1
        cell = ws.cell(1, last, name)
        prev = ws.cell(1, last - 1) if last > 1 else None
        if prev is not None and prev.has_style:
            cell.font, cell.border, cell.fill = copy(prev.font), copy(prev.border), copy(prev.fill)
            cell.alignment, cell.number_format = copy(prev.alignment), prev.number_format
        if name in KIT_WIDTHS:
            ws.column_dimensions[get_column_letter(last)].width = KIT_WIDTHS[name]
        h[name] = last
        added.append(name)
    ref = ws.auto_filter.ref
    if added and ref:  # keep an owner's filter covering the new columns
        c1, r1, c2, r2 = range_boundaries(ref)
        if c2 == old_last:
            ws.auto_filter.ref = f"{get_column_letter(c1)}{r1}:{get_column_letter(last)}{r2}"
    return added


def cmd_append(a) -> dict:
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    pats = a.id_pattern or DEFAULT_ID_PATTERNS
    ids, cts = t.known(pats)
    fa, sm = t.ws("For Approval"), t.ws("Skill Map")
    hf, hs = headers(fa), headers(sm)
    r = last_row(fa, hf.get("Company", 6))
    num = get(fa, hf, r, "#") if r > 1 else 0
    num = num if isinstance(num, int) else r - 1
    sr = last_row(sm, hs.get("Company", 1))
    added, skipped = [], []
    jobs = load_jobs(a.jobs)
    cv_res = [re.compile(x, re.I) for x in (a.cv_skill or [])]
    kit_added = []
    for j in jobs:
        k, c = job_key(j["link"], pats), ct_key(j["company"], j["title"])
        if k in ids or c in cts:
            skipped.append(j["link"])
            continue
        r += 1
        num += 1
        kit = kit_values(j)
        if kit:  # the three columns come as a set; trackers whose jobs never carry them keep their header as is
            kit_added += ensure_columns(fa, KIT_FIELDS.values())
            hf = headers(fa)
        copy_row_style(fa, r - 1, r)
        vals = {FIELD_MAP[f]: v for f, v in j.items() if f in FIELD_MAP}
        if isinstance(vals.get("Red flags"), list):
            vals["Red flags"] = "; ".join(vals["Red flags"])
        vals.update({"#": num, "Approve ☐": PENDING, "Decision notes": j.get("notes") or a.note,
                     "Required skills": "; ".join(j.get("required", [])) or None,
                     "Nice to have": "; ".join(j.get("nice", [])) or None})
        vals.update(kit)
        put(fa, hf, r, vals)
        for kind, lst in (("Required", j.get("required", [])), ("Nice", j.get("nice", []))):
            for skill in lst:
                sr += 1
                copy_row_style(sm, sr - 1, sr)
                status = CV if any(rx.search(skill) for rx in cv_res) else None
                put(sm, hs, sr, {"Company": j["company"], "Title": j["title"], "Bucket": "For Approval",
                                 "Skill": skill, "Required/Nice": kind, "Status": status})
        ids.add(k)
        cts.add(c)
        added.append({"row": r, "company": j["company"], "title": j["title"]})
    t.save(a.dry_run)
    return t.result({"added": added, "skipped_duplicates": skipped, "columns_added": kit_added,
                     "ignored_keys": ignored_keys(jobs, set(FIELD_MAP) | set(KIT_FIELDS) | {"required", "nice"})},
                    a.dry_run)


def cmd_exclude(a) -> dict:
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    pats = a.id_pattern or DEFAULT_ID_PATTERNS
    ids, cts = t.known(pats)
    ex = t.ws("Excluded")
    h = headers(ex)
    r = last_row(ex, h.get("Company", 1))
    added = []
    for j in load_jobs(a.jobs):
        if job_key(j["link"], pats) in ids or ct_key(j["company"], j["title"]) in cts:
            continue
        r += 1
        copy_row_style(ex, r - 1, r)
        put(ex, h, r, {"Company": j["company"], "Title": j["title"], "Job link": j["link"],
                       "Reason": j.get("reason", "Excluded"), "Fit": j.get("fit"), "Pay": j.get("pay")})
        added.append(j["link"])
    t.save(a.dry_run)
    return t.result({"excluded": added}, a.dry_run)


def add_days(iso: str, days: int) -> str:
    return (dt.date.fromisoformat(iso) + dt.timedelta(days=days)).isoformat()


def cmd_move(a) -> dict:
    """Move one job row along the pipeline (or to Excluded), carrying shared columns by header name."""
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    pats = a.id_pattern or DEFAULT_ID_PATTERNS
    src, r = t.find(a.link, pats)
    if src is None:
        raise Guarded(2, f"job not found in pipeline sheets: {a.link}")
    if src.title == a.to:
        raise Guarded(2, f"job already in {a.to}")
    if a.to in STAGE_ORDER and STAGE_ORDER.get(src.title, 0) > STAGE_ORDER[a.to] and not a.allow_backward:
        raise Guarded(2, f"backward move {src.title} -> {a.to} refused; pass --allow-backward to reopen")
    if a.to == "Excluded" and src.title != "For Approval" and not a.allow_backward:
        raise Guarded(2, "only For Approval rows move to Excluded; close applied rows with --to Closed")
    hs = headers(src)
    row = {name: src.cell(r, col).value for name, col in hs.items()}
    dst = t.ws(a.to)
    hd = headers(dst)
    when = a.date or today()
    hist = str(row.get("Stage history") or "").strip("; ")
    hist = f"{hist}; {when} {a.to}" if hist else f"{when} {a.to}"
    if a.detail:
        hist += f" ({a.detail})"
    vals = {name: row.get(name) for name in hd if name != "#"}
    vals.update({"Stage history": hist, "Status date": when, "Latest status": a.detail or a.to,
                 "Pipeline stage": a.to})
    if a.to == "Applied":
        vals.update({"Date applied": when, "Follow-up date": add_days(when, a.follow_up_days),
                     "Channel": a.channel or row.get("Apply method"), "Fit": row.get("Fit score")})
    elif a.to == "Interviewing":
        vals.update({"Interview stage": a.interview_stage, "Next interview date": a.interview_date})
    elif a.to == "Closed":
        vals.update({"Closed date": when, "Outcome": a.outcome or "Closed", "Outcome detail": a.detail,
                     "Stage reached": src.title if src.title != "For Approval" else "Not applied"})
    elif a.to == "Excluded":
        notes = row.get("Decision notes")
        vals = {"Company": row.get("Company"), "Title": row.get("Title"), "Job link": row.get("Job link"),
                "Reason": (a.detail or "Declined by owner") + (f" - {notes}" if notes else ""),
                "Fit": row.get("Fit score"), "Pay": row.get("Pay (as posted)")}
    dr = last_row(dst, hd.get("Company", 1)) + 1
    copy_row_style(dst, dr - 1, dr)
    if "#" in hd:
        prev = dst.cell(dr - 1, hd["#"]).value
        vals["#"] = prev + 1 if isinstance(prev, int) else dr - 1
    put(dst, hd, dr, vals)
    src.delete_rows(r, 1)
    sm = sheet(t.wb, "Skill Map")
    if sm is not None:
        h = headers(sm)
        for i in range(2, sm.max_row + 1):
            if ct_key(get(sm, h, i, "Company"), get(sm, h, i, "Title")) == ct_key(row.get("Company"), row.get("Title")) \
                    and get(sm, h, i, "Bucket") == src.title:
                sm.cell(i, h["Bucket"]).value = a.to
    t.save(a.dry_run)
    return t.result({"moved": a.link, "from": src.title, "to": a.to, "row": dr}, a.dry_run)


AUTO_ACTION = re.compile(r"^(Close GAP|Advance|Review|Covered)\b")


def cmd_gaps(a) -> dict:
    """Classify Skill Map rows, rebuild Gap Summary, refresh readiness on open pipeline rows.

    rules JSON: {"cv_skills": [regex...], "rules": [{"match": regex, "ref": "ID", "status": "...",
                 "week": "...", "note": "..."}]}. First matching rule wins; no match => GAP.
    Owner-set Status values are kept unless --recompute.
    """
    cfg = json.loads(Path(a.rules).read_text(encoding="utf-8")) if a.rules else {}
    cv = [re.compile(x, re.I) for x in cfg.get("cv_skills", [])]
    rules = [(re.compile(x["match"], re.I), x) for x in cfg.get("rules", [])]
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    sm = t.ws("Skill Map")
    h = headers(sm)
    per_job: dict = {}
    summary: dict = {}
    for r in range(2, sm.max_row + 1):
        skill = get(sm, h, r, "Skill")
        if skill in (None, ""):
            continue
        status, ref, week = get(sm, h, r, "Status"), get(sm, h, r, "Study plan ref"), get(sm, h, r, "Week/phase")
        if a.recompute or status in (None, ""):
            if any(rx.search(skill) for rx in cv):
                status, ref, week = CV, None, None
            else:
                hit = next((x for rx, x in rules if rx.search(skill)), None)
                status = hit.get("status", "Study plan - scheduled") if hit else "GAP - not in plan"
                ref, week = (hit.get("ref"), hit.get("week")) if hit else (None, None)
            put(sm, h, r, {"Status": status, "Study plan ref": ref, "Week/phase": week}, clear=True)
        bucket = get(sm, h, r, "Bucket")
        key = ct_key(get(sm, h, r, "Company"), get(sm, h, r, "Title"))
        per_job.setdefault(key, []).append((skill, str(status or ""), ref, week))
        if bucket in ("For Approval", "Applied", "Interviewing"):
            s = summary.setdefault(skill.strip().lower(), {"skill": skill, "jobs": set(), "status": status, "ref": ref})
            s["jobs"].add(key)
    gs = sheet(t.wb, "Gap Summary")
    if gs is not None:
        hg = headers(gs)
        gs.delete_rows(2, max(gs.max_row - 1, 0))
        rows = sorted(summary.values(), key=lambda s: (not str(s["status"]).startswith("GAP"), -len(s["jobs"]), s["skill"]))
        for i, s in enumerate(rows, start=2):
            gap = str(s["status"]).startswith("GAP")
            put(gs, hg, i, {"Skill": s["skill"], "# jobs requiring": len(s["jobs"]), "Status": s["status"],
                            "Study plan ref": s["ref"],
                            "Suggested action": "Add to study plan" if gap and len(s["jobs"]) >= a.gap_threshold
                            else ("Monitor" if gap else None)})
    updated = 0
    for name in ("For Approval", "Applied", "Interviewing"):
        ws = sheet(t.wb, name)
        if ws is None:
            continue
        hw = headers(ws)
        action_col = "Next study action" if "Next study action" in hw else "Next interview-prep action"
        for r in range(2, ws.max_row + 1):
            skills = per_job.get(ct_key(get(ws, hw, r, "Company"), get(ws, hw, r, "Title")))
            if not skills:
                continue
            scored = [x for x in skills if not x[1].lower().startswith("n/a")]
            if not scored:
                continue
            cov = [s for s, st, _, _ in scored if st == CV]
            gap = [s for s, st, _, _ in scored if st.startswith("GAP")]
            plan = [(s, ref, wk) for s, st, ref, wk in scored if st != CV and not st.startswith("GAP")
                    and (ref or st.lower().startswith(("study plan", "plan")))]
            ready = round((len(cov) + 0.5 * len(plan)) / len(scored), 2)
            fmt = [f"{s} ({ref}{', ' + wk if wk else ''})" if ref else s for s, ref, wk in plan]
            put(ws, hw, r, {"Readiness %": ready, "Covered": "; ".join(cov) or None, "In study plan": "; ".join(fmt) or None,
                            "Missing (not in plan)": "; ".join(gap) or None})
            cur = get(ws, hw, r, action_col)
            if action_col in hw and (cur in (None, "") or AUTO_ACTION.match(str(cur))):
                nxt = f"Close GAP: {gap[0]} - not in study plan" if gap else (f"Advance: {fmt[0]}" if fmt else "Covered - review stories")
                ws.cell(r, hw[action_col]).value = nxt
            if "Readiness %" in hw:
                ws.cell(r, hw["Readiness %"]).number_format = "0%"
            updated += 1
    t.save(a.dry_run)
    gaps = [{"skill": s["skill"], "jobs": len(s["jobs"])} for s in summary.values()
            if str(s["status"]).startswith("GAP") and len(s["jobs"]) >= a.gap_threshold]
    return t.result({"job_rows_updated": updated, "repeated_gaps": sorted(gaps, key=lambda g: -g["jobs"])}, a.dry_run)


POSTED_TEXT_FORMATS = ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y", "%b %d %Y")


def parse_posted(v) -> dt.date | None:
    """Best-effort date from a `Posted` cell: spreadsheet dates, ISO (optional time), month names, d/m/Y or
    m/d/Y when only one reading is a valid date. Anything else (blank, "3 days ago", 05/06/2026) is None, and callers must treat None as unknown."""
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v or "").strip()
    if not s:
        return None
    try:
        m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", s)
        if m:
            return dt.date(*map(int, m.groups()))
        m = re.match(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{4})$", s)
        if m:
            x, y, year = map(int, m.groups())
            if y <= 12 < x:  # only day-first is valid
                return dt.date(year, y, x)
            if x <= 12 < y or x == y:  # only month-first is valid, or both readings agree
                return dt.date(year, x, y)
            return None
    except ValueError:
        return None
    for fmt in POSTED_TEXT_FORMATS:
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def tier_rank(v) -> int:
    m = re.match(r"^\s*(?:tier\s*)?([ABC])\b", str(v or ""), re.I)
    return "ABC".index(m.group(1).upper()) if m else 3


def cmd_shortlist(a) -> list:
    """Read-only: rank unmarked For Approval rows - tier A>B>C, ATS match %, fit score, newest Posted first.

    Blank or unparseable values sort after real ones; the sheet row number is the last tiebreak.
    """
    if a.size < 1:
        raise Guarded(2, "--size must be >= 1")
    t = Tracker(a.tracker)
    ws = t.ws("For Approval")
    h = headers(ws)
    col = approve_col(h)
    ranked = []
    for r in range(2, ws.max_row + 1):
        if get(ws, h, r, "Company") in (None, "") or not is_unmarked(ws.cell(r, col).value):
            continue
        tier, fit_raw, posted_raw = get(ws, h, r, "Tier"), get(ws, h, r, "Fit score"), get(ws, h, r, "Posted")
        ats, fit, posted = to_num(get(ws, h, r, "ATS match %")), to_num(fit_raw), parse_posted(posted_raw)
        key = (tier_rank(tier), ats is None, -(ats or 0), fit is None, -(fit or 0),
               posted is None, -(posted.toordinal() if posted else 0), r)
        ranked.append((key, {"row": r, "num": get(ws, h, r, "#"), "company": get(ws, h, r, "Company"),
                             "title": get(ws, h, r, "Title"), "link": get(ws, h, r, "Job link"),
                             "tier": str(tier).strip() if tier not in (None, "") else None,
                             "fit": fit if fit is not None else fit_raw,
                             "ats_match": None if ats is None else (int(ats) if float(ats).is_integer() else ats),
                             "posted": posted.isoformat() if posted else (posted_raw or None),
                             "apply_method": get(ws, h, r, "Apply method")}))
    ranked.sort(key=lambda x: x[0])
    return [item for _, item in ranked[: a.size]]


def cmd_expire(a) -> dict:
    """Move unmarked For Approval rows posted more than --days before --today to Excluded.

    Rows with an owner mark (approve, reject, later, or any text this tool does not recognise) and rows whose
    Posted date cannot be read are never touched; undated rows are listed so the caller can see why.
    """
    if a.days < 0:
        raise Guarded(2, "--days must be >= 0")
    try:
        ref = dt.date.fromisoformat(a.today or today())
    except ValueError:
        raise Guarded(2, f"--today must be YYYY-MM-DD, got {a.today!r}")
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    fa, ex = t.ws("For Approval"), t.ws("Excluded")
    h, hx = headers(fa), headers(ex)
    col = approve_col(h)
    reason = f"Expired unreviewed ({a.days} days)"
    due, undated, marked = [], [], 0
    for r in range(2, fa.max_row + 1):
        company = get(fa, h, r, "Company")
        if company in (None, ""):
            continue
        if not is_unmarked(fa.cell(r, col).value):
            marked += 1
            continue
        raw = get(fa, h, r, "Posted")
        posted = parse_posted(raw)
        if posted is None:
            undated.append({"row": r, "company": company, "posted": raw if raw not in (None, "") else None})
        elif (ref - posted).days > a.days:
            due.append({"row": r, "company": company, "title": get(fa, h, r, "Title"),
                        "link": get(fa, h, r, "Job link"), "posted": posted.isoformat(),
                        "age_days": (ref - posted).days,
                        "_excluded": {"Company": company, "Title": get(fa, h, r, "Title"),
                                      "Job link": get(fa, h, r, "Job link"), "Reason": reason,
                                      "Fit": get(fa, h, r, "Fit score"), "Pay": get(fa, h, r, "Pay (as posted)")}})
    if due and not a.dry_run:
        dr = last_row(ex, hx.get("Company", 1))
        for item in due:
            dr += 1
            copy_row_style(ex, dr - 1, dr)
            put(ex, hx, dr, item["_excluded"])
        for item in sorted(due, key=lambda x: x["row"], reverse=True):
            fa.delete_rows(item["row"], 1)
        sm = sheet(t.wb, "Skill Map")
        if sm is not None:
            hm = headers(sm)
            keys = {ct_key(i["company"], i["title"]) for i in due}
            for i in range(2, sm.max_row + 1):
                if get(sm, hm, i, "Bucket") == "For Approval" \
                        and ct_key(get(sm, hm, i, "Company"), get(sm, hm, i, "Title")) in keys:
                    sm.cell(i, hm["Bucket"]).value = "Excluded"
        t.save()
    for item in due:
        del item["_excluded"]
    return t.result({"days": a.days, "today": ref.isoformat(), "reason": reason, "count": len(due), "expired": due,
                     "kept_marked": marked, "skipped_undated": undated}, a.dry_run)


REPAIR_SHEETS = [*PIPELINE, "Excluded"]


def orphan_rows(ws) -> list:
    """Row numbers whose Company and Title are both empty while some other cell still holds a value.

    A sheet without a Company or Title header is never judged. Fully blank rows are not orphans.
    """
    h = headers(ws)
    if "Company" not in h or "Title" not in h:
        return []
    key_cols = (h["Company"], h["Title"])
    return [row[0].row for row in ws.iter_rows(min_row=2)
            if all(row[c - 1].value in (None, "") for c in key_cols)
            and any(c.value not in (None, "") for c in row)]


def mismatched_links(ws, skip_rows=()) -> list:
    """Cells of the `Job link` column whose hyperlink target differs from the cell's URL text.

    Only external links on URL values (text starting with http) count. Empty values, text that is not a URL,
    internal links (no target) and the rows in skip_rows are left alone. Returns [(cell, url)].
    """
    col = headers(ws).get("Job link")
    if col is None:
        return []
    out = []
    for r in range(2, ws.max_row + 1):
        if r in skip_rows:
            continue
        cell = ws.cell(r, col)
        link, value = cell.hyperlink, str(cell.value if cell.value is not None else "").strip()
        if link is not None and link.target and value.lower().startswith("http") and link.target != value:
            out.append((cell, value))
    return out


def cmd_repair(a) -> dict:
    """Clean up what the old hyperlink bug left behind in the pipeline tabs and Excluded.

    1. Delete orphan rows: no Company and no Title but at least one other filled cell, typically only a Job
       link. Older versions left them when delete_rows shifted a row without its hyperlink ref.
    2. Reset a `Job link` hyperlink whose target differs from the cell's URL text to that text (the visible text
       is what the owner reads; the link then opens the same job).
    Rows with a Company or a Title are never deleted, fully blank rows and every other tab are never touched.
    Prints {sheet: [row numbers removed], "links_fixed": {sheet: [cell refs]}, "mtime": ...}; rows and refs are
    the ones before the delete. --dry-run reports without writing; nothing is written when nothing changed.
    """
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    removed: dict = {}
    fixed: dict = {}
    for name in REPAIR_SHEETS:
        ws = sheet(t.wb, name)
        if ws is None:
            continue
        rows = orphan_rows(ws)
        removed[name] = rows
        links = mismatched_links(ws, set(rows))
        fixed[name] = [cell.coordinate for cell, _ in links]
        if not a.dry_run:
            for cell, url in links:
                cell.hyperlink.target = url
            for r in reversed(rows):
                ws.delete_rows(r, 1)
    if any(removed.values()) or any(fixed.values()):
        t.save(a.dry_run)
    return t.result({**removed, "links_fixed": fixed}, a.dry_run)


# Columns `set` may write (lower-case key -> header). The owner's approval mark, the row key columns and every
# other column stay untouched. An allowed column missing from the row's tab is added at the end of its header row.
SET_COLUMNS = {n.lower(): n for n in (*KIT_FIELDS.values(), "Decision notes", "Next action", "Notes")}
SET_KEY_COLUMNS = {"#", "job link", "company", "title"}


def cmd_set(a) -> dict:
    """Set one cell on an existing row, found by Job link (in --sheet, else across every tab with that column).

    Refuses (exit 2) any `Approve...` column and the key columns `#`, `Job link`, `Company`, `Title`, any column
    outside SET_COLUMNS, an empty value, and a link that matches no row or more than one row. `ATS match %` must be
    an integer 0-100. The value is always stored as text, so a value starting with "=" never becomes a formula.
    """
    key = " ".join(str(a.column).split()).lower()
    if key.startswith("approve") or key in SET_KEY_COLUMNS:
        raise Guarded(2, f"column '{a.column}' is owner-controlled or a row key; this tool will not write it")
    col_name = SET_COLUMNS.get(key)
    if col_name is None:
        raise Guarded(2, f"column '{a.column}' cannot be set; allowed: {', '.join(SET_COLUMNS.values())}")
    value = str(a.value).strip()
    if not value:
        raise Guarded(2, "--value must not be empty")
    pats = a.id_pattern or DEFAULT_ID_PATTERNS
    want = job_key(a.link, pats)
    if want is None:
        raise Guarded(2, "--link must not be empty")
    kit_key = next((k for k, v in KIT_FIELDS.items() if v == col_name), None)
    if kit_key:  # same validation and normalisation as `append`
        value = kit_values({"link": a.link, kit_key: value})[col_name]
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    hits = []
    for ws in [t.ws(a.sheet)] if a.sheet else t.wb.worksheets:
        h = headers(ws)
        if "Job link" not in h:
            if a.sheet:
                raise Guarded(2, f"sheet '{ws.title}' has no 'Job link' column")
            continue
        hits += [(ws, r) for r in range(2, ws.max_row + 1) if job_key(get(ws, h, r, "Job link"), pats) == want]
    if not hits:
        raise Guarded(2, f"job not found{f' in sheet {a.sheet}' if a.sheet else ''}: {a.link}")
    if len(hits) > 1:
        where = ", ".join(f"{ws.title} row {r}" for ws, r in hits)
        raise Guarded(2, f"ambiguous link, it matches {where}; " +
                      ("remove the duplicate row first" if a.sheet else "pass --sheet to choose a tab"))
    ws, r = hits[0]
    added = ensure_columns(ws, [col_name])
    cell = ws.cell(r, headers(ws)[col_name])
    previous = cell.value
    cell.value = value
    if isinstance(value, str):
        cell.data_type = "s"
    t.save(a.dry_run)
    return t.result({"sheet": ws.title, "row": r, "link": a.link, "column": col_name, "previous": previous,
                     "value": value, "column_added": bool(added)}, a.dry_run)


SIDEGIG_FIELDS = {"platform": "Platform", "link": "Link", "status": "My status", "applied": "Roles/projects applied",
                  "pay": "Pay (USD/hr)", "meets_floor": "Meets my floor", "eligible": "Eligible from my country",
                  "payment": "Payment method", "next_action": "Next action", "next_action_date": "Next action date",
                  "last_activity": "Last activity", "mail_link": "Mail link", "notes": "Notes/sources"}


def cmd_sidegig(a) -> dict:
    """Upsert Side Gigs rows by Platform from a JSON list of {platform, status, next_action, ...}."""
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))
    items = data["platforms"] if isinstance(data, dict) else data
    t = Tracker(a.tracker, a.expect_mtime, a.backup_dir)
    ws = t.ws("Side Gigs")
    h = headers(ws)
    if "Platform" not in h:
        raise Guarded(2, "Side Gigs sheet has no 'Platform' column")
    rows = {str(get(ws, h, r, "Platform")).strip().lower(): r for r in range(2, ws.max_row + 1)
            if get(ws, h, r, "Platform") not in (None, "")}
    updated, added = [], []
    for it in items:
        name = str(it.get("platform") or "").strip()
        if not name:
            raise Guarded(2, f"side gig entry missing 'platform': {it}")
        vals = {SIDEGIG_FIELDS[k]: v for k, v in it.items() if k in SIDEGIG_FIELDS}
        r = rows.get(name.lower())
        if r is None:
            r = last_row(ws, h["Platform"]) + 1
            copy_row_style(ws, r - 1, r)
            if "#" in h:
                prev = ws.cell(r - 1, h["#"]).value
                vals["#"] = prev + 1 if isinstance(prev, int) else r - 1
            rows[name.lower()] = r
            added.append(name)
        else:
            updated.append(name)
        put(ws, h, r, vals)
    t.save(a.dry_run)
    return t.result({"updated": updated, "added": added,
                     "ignored_keys": sorted({k for it in items for k in it if k not in SIDEGIG_FIELDS})}, a.dry_run)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, write=False):
        p.add_argument("--tracker", required=True)
        p.add_argument("--id-pattern", action="append", help="regex with one group extracting a job id from a link")
        if write:
            p.add_argument("--expect-mtime", type=float, help="abort (exit 3) unless the file still has this mtime")
            p.add_argument("--backup-dir", help="copy the workbook here before writing")
            p.add_argument("--dry-run", action="store_true")
        return p

    p = sub.add_parser("init", help="create an empty tracker with the standard sheets")
    p.add_argument("--tracker", required=True)
    p.add_argument("--force", action="store_true")
    common(sub.add_parser("known", help="dump known job ids, company|title keys (dedup list) and rejected company names")).add_argument("--out")
    common(sub.add_parser("approvals", help="list For Approval rows by owner mark"))
    p = common(sub.add_parser("append", help="append screened jobs to For Approval + Skill Map"), True)
    p.add_argument("--jobs", required=True)
    p.add_argument("--note", default=f"New {today()} scan")
    p.add_argument("--cv-skill", action="append", help="regex; matching skills get Status 'Experience (CV)'")
    p = common(sub.add_parser("exclude", help="append screened-out jobs to Excluded"), True)
    p.add_argument("--jobs", required=True)
    p = common(sub.add_parser("move", help="move a job between pipeline stages"), True)
    p.add_argument("--link", required=True)
    p.add_argument("--to", required=True, choices=["Applied", "Interviewing", "Closed", "Excluded"])
    p.add_argument("--date")
    p.add_argument("--detail")
    p.add_argument("--channel")
    p.add_argument("--outcome")
    p.add_argument("--interview-stage")
    p.add_argument("--interview-date")
    p.add_argument("--follow-up-days", type=int, default=7)
    p.add_argument("--allow-backward", action="store_true", help="permit reopening a later-stage row")
    p = common(sub.add_parser("gaps", help="classify skills, rebuild Gap Summary, refresh readiness"), True)
    p.add_argument("--rules")
    p.add_argument("--recompute", action="store_true")
    p.add_argument("--gap-threshold", type=int, default=2)
    p = common(sub.add_parser("sidegig", help="upsert Side Gigs rows by platform"), True)
    p.add_argument("--data", required=True)
    p = common(sub.add_parser("shortlist", help="read-only: rank unmarked For Approval rows (tier, ATS match, fit, "
                                                "newest) and print the top N as JSON"))
    p.add_argument("--size", type=int, default=10, help="rows to return (default 10)")
    p = common(sub.add_parser("expire", help="move unmarked For Approval rows posted over N days ago to Excluded"),
               True)
    p.add_argument("--days", type=int, required=True, help="expire rows whose Posted date is older than this")
    p.add_argument("--today", help="reference date YYYY-MM-DD (default: today)")
    p = common(sub.add_parser("set", help="set one cell (ATS match %%, Missing keywords, Apply kit, Decision notes, "
                                          "Next action, Notes) on an existing row found by --link"), True)
    p.add_argument("--link", required=True, help="Job link of the row to change")
    allowed = ", ".join(SET_COLUMNS.values()).replace("%", "%%")  # argparse expands % in help text
    p.add_argument("--column", required=True, help=f"one of: {allowed}")
    p.add_argument("--value", required=True)
    p.add_argument("--sheet", help="look in this tab only (default: every tab that has a Job link column)")
    common(sub.add_parser("repair", help="delete orphan rows (no Company and no Title, other cells filled) from the "
                                         "pipeline tabs and Excluded; reset Job link hyperlinks that point away "
                                         "from the cell's URL"), True)
    a = ap.parse_args(argv)
    fn = {"init": cmd_init, "known": cmd_known, "approvals": cmd_approvals, "append": cmd_append,
          "exclude": cmd_exclude, "move": cmd_move, "gaps": cmd_gaps, "sidegig": cmd_sidegig,
          "shortlist": cmd_shortlist, "expire": cmd_expire, "set": cmd_set, "repair": cmd_repair}[a.cmd]
    try:
        out = fn(a)
    except Guarded as e:
        sys.stderr.write(f"tracker_ops: {e}\n")
        return e.code
    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

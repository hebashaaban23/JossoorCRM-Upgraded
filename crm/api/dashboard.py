"""
dashboard.py — Real Estate CRM Analytics API
Three sections: Leads Performance, Projects Performance, Tasks Performance
All user inputs are parameterised (no f-string interpolation of user values).
"""

import json
import frappe
from frappe import _
from crm.fcrm.doctype.crm_dashboard.crm_dashboard import create_default_manager_dashboard
from crm.utils import sales_user_only

CHART_COLOURS = [
    "#378ADD", "#1D9E75", "#D85A30", "#BA7517", "#534AB7",
    "#D4537E", "#E24B4A", "#639922", "#888780", "#0F6E56",
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_team_members_for_leader(team_leader):
    if not team_leader:
        return []
    teams = frappe.get_all("Team", filters={"team_leader": team_leader}, fields=["name"], limit=1)
    if not teams:
        return []
    return frappe.get_all(
        "Member",
        filters={"parent": teams[0].name, "parenttype": "Team"},
        pluck="member",
    ) or []


def _get_user_condition(user):
    if not user:
        return "", {}
    if user == "__TEAM__":
        members = _get_team_members_for_leader(frappe.session.user)
        team = tuple(members + [frappe.session.user])
        return "AND l.lead_owner IN %(team_users)s", {"team_users": team}
    return "AND l.lead_owner = %(user)s", {"user": user}


def _build_lead_where(fd, td, user_cond, user_params, alias="l", project=None, status=None, search=None):
    parts, params = [], dict(user_params)
    p = f"{alias}." if alias else ""

    if fd and td:
        parts.append(f"DATE({p}creation) BETWEEN %(from_date)s AND %(to_date)s")
        params.update(from_date=fd, to_date=td)

    if user_cond:
        stripped = user_cond.lstrip("AND ").strip()
        parts.append(stripped.replace("l.lead_owner", f"{p}lead_owner"))

    if project:
        parts.append(f"{p}project = %(project)s")
        params["project"] = project

    if status:
        parts.append(f"{p}status = %(status_filter)s")
        params["status_filter"] = status

    if search:
        parts.append(
            f"({p}first_name LIKE %(search)s OR {p}last_name LIKE %(search)s OR {p}mobile_no LIKE %(search)s)"
        )
        params["search"] = f"%{search}%"

    where = ("WHERE " + " AND ".join(parts)) if parts else ""
    return where, params


def get_base_currency_symbol():
    base = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
    return frappe.db.get_value("Currency", base, "symbol") or ""


# ─── Dashboard layout ─────────────────────────────────────────────────────────

def _add_links_to_layout_items(layout):
    for item in layout:
        if item.get("link"):
            continue
        name = item.get("name", "")
        if name == "total_leads":
            item["link"] = {"name": "Leads"}
        elif name == "delayed_leads":
            item["link"] = {"name": "Leads", "query": {"delayed": "1"}}
        elif name == "total_deals":
            item["link"] = {"name": "Deals"}
        elif name.startswith("lead_status_") and "status" in item:
            item["link"] = {"name": "Leads", "query": {"status": item["status"]}}
    return layout


@frappe.whitelist()
def reset_to_default():
    frappe.only_for("System Manager")
    create_default_manager_dashboard(force=True)


@frappe.whitelist()
@sales_user_only
def get_dashboard(from_date="", to_date="", user="", project=""):
    if from_date == "" and to_date == "":
        pass
    elif not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

    roles = frappe.get_roles(frappe.session.user)
    is_sales_user = "Sales User" in roles and "Sales Manager" not in roles and "System Manager" not in roles
    is_sales_manager = "Sales Manager" in roles and "System Manager" not in roles

    if is_sales_user and not user:
        user = frappe.session.user

    team_users = None
    if is_sales_manager and not user:
        members = _get_team_members_for_leader(frappe.session.user)
        team_users = members + [frappe.session.user]
        user = "__TEAM__"

    project = project.strip() if project and project.strip() else ""

    dashboard = frappe.db.exists("CRM Dashboard", "Manager Dashboard")
    if not dashboard:
        layout = json.loads(create_default_manager_dashboard())
        frappe.db.commit()
    else:
        layout = json.loads(frappe.db.get_value("CRM Dashboard", "Manager Dashboard", "layout") or "[]")

    layout = _add_links_to_layout_items(layout)

    methods_supporting_empty_dates = [
        "get_total_leads", "get_delayed_leads", "get_lead_status_count",
        "get_leads_by_status", "get_leads_by_status_chart", "get_total_deals",
    ]

    import inspect
    module = frappe.get_attr("crm.api.dashboard")

    for l in layout:
        if l["name"].startswith("lead_status_") and "status" in l:
            l["data"] = get_lead_status_count(from_date, to_date, user, l["status"], project, team_users=team_users)
        else:
            method_name = f"get_{l['name']}"
            method = getattr(module, method_name, None)
            if not method:
                l["data"] = None
                continue
            sig = inspect.signature(method)
            if method_name not in methods_supporting_empty_dates and (not from_date or not to_date):
                call_fd = frappe.utils.get_first_day(frappe.utils.nowdate())
                call_td = frappe.utils.get_last_day(frappe.utils.nowdate())
            else:
                call_fd, call_td = from_date, to_date
            kwargs = {}
            if "team_users" in sig.parameters and team_users:
                kwargs["team_users"] = team_users
            if "project" in sig.parameters:
                l["data"] = method(call_fd, call_td, user, project, **kwargs)
            else:
                l["data"] = method(call_fd, call_td, user, **kwargs)

    return layout


# ─── Scalar helpers ───────────────────────────────────────────────────────────

def _diff(fd, td):
    return max(frappe.utils.date_diff(td, fd), 1)


def _deal_user_cond(user):
    if not user:
        return "", {}
    return "AND d.deal_owner = %(deal_user)s", {"deal_user": user}


def get_total_leads(from_date, to_date, user="", project="", team_users=None):
    conds, params = [], {}
    if from_date and to_date:
        diff = _diff(from_date, to_date)
        params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    else:
        from_date = to_date = None
    if user == "__TEAM__" and team_users:
        conds.append("lead_owner IN %(team_users)s"); params["team_users"] = tuple(team_users)
    elif user and user != "__TEAM__":
        conds.append("lead_owner = %(user)s"); params["user"] = user
    if project:
        conds.append("project = %(project)s"); conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    if from_date and to_date:
        r = frappe.db.sql(f"SELECT COUNT(CASE WHEN creation>=%(from_date)s AND creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) THEN name END) AS v FROM `tabCRM Lead` {where}", params, as_dict=1)
    else:
        r = frappe.db.sql(f"SELECT COUNT(*) AS v FROM `tabCRM Lead` {where}", params, as_dict=1)
    return {"title": _("Total leads"), "tooltip": _("Total number of leads"), "value": r[0].v or 0}


def get_lead_status_count(from_date, to_date, user, status_name, project="", team_users=None):
    conds, params = ["status = %(status)s"], {"status": status_name}
    if from_date and to_date:
        diff = _diff(from_date, to_date)
        params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    else:
        from_date = to_date = None
    if user == "__TEAM__" and team_users:
        conds.append("lead_owner IN %(team_users)s"); params["team_users"] = tuple(team_users)
    elif user and user != "__TEAM__":
        conds.append("lead_owner = %(user)s"); params["user"] = user
    if project:
        conds.append("project = %(project)s"); conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    where = "WHERE " + " AND ".join(conds)
    if from_date and to_date:
        r = frappe.db.sql(f"SELECT COUNT(CASE WHEN creation>=%(from_date)s AND creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) THEN name END) AS v FROM `tabCRM Lead` {where}", params, as_dict=1)
    else:
        r = frappe.db.sql(f"SELECT COUNT(*) AS v FROM `tabCRM Lead` {where}", params, as_dict=1)
    return {"title": _(status_name), "tooltip": _(f"{status_name} leads"), "value": r[0].v or 0}


def get_total_deals(from_date, to_date, user=""):
    conds, params = [], {}
    if from_date and to_date:
        diff = _diff(from_date, to_date)
        params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    else:
        from_date = to_date = None
    if user:
        conds.append("deal_owner = %(deal_user)s"); params["deal_user"] = user
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    if from_date and to_date:
        r = frappe.db.sql(f"SELECT COUNT(CASE WHEN creation>=%(from_date)s AND creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) THEN name END) AS v FROM `tabCRM Deal` {where}", params, as_dict=1)
    else:
        r = frappe.db.sql(f"SELECT COUNT(*) AS v FROM `tabCRM Deal` {where}", params, as_dict=1)
    return {"title": _("Total deals"), "tooltip": _("Total number of deals"), "value": r[0].v or 0}


def get_delayed_leads(from_date, to_date, user="", project="", team_users=None):
    if not frappe.get_meta("CRM Lead").has_field("delayed"):
        return {"title": _("Delayed leads"), "tooltip": _("Field not available"), "value": 0}
    conds, params = [], {}
    if from_date and to_date:
        diff = _diff(from_date, to_date)
        params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    else:
        from_date = to_date = None
    if user == "__TEAM__" and team_users:
        conds.append("lead_owner IN %(team_users)s"); params["team_users"] = tuple(team_users)
    elif user and user != "__TEAM__":
        conds.append("lead_owner = %(user)s"); params["user"] = user
    if project:
        conds.append("project = %(project)s"); conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    if from_date and to_date:
        r = frappe.db.sql(f"SELECT COUNT(CASE WHEN creation>=%(from_date)s AND creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) AND `delayed`=1 THEN name END) AS v FROM `tabCRM Lead` {where}", params, as_dict=1)
    else:
        r = frappe.db.sql(f"SELECT COUNT(CASE WHEN `delayed`=1 THEN name END) AS v FROM `tabCRM Lead` {where}", params, as_dict=1)
    return {"title": _("Delayed leads"), "tooltip": _("Total delayed leads"), "value": r[0].v or 0}


def get_leads_by_status(from_date, to_date, user="", project="", team_users=None):
    conds, params = [], {}
    if from_date and to_date:
        diff = _diff(from_date, to_date)
        params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    else:
        from_date = to_date = None
    if user == "__TEAM__" and team_users:
        conds.append("lead_owner IN %(team_users)s"); params["team_users"] = tuple(team_users)
    elif user and user != "__TEAM__":
        conds.append("lead_owner = %(user)s"); params["user"] = user
    if project:
        conds.append("project = %(project)s"); conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    if from_date and to_date:
        rows = frappe.db.sql(f"""
            SELECT l.status, s.color, s.position,
                COUNT(CASE WHEN l.creation>=%(from_date)s AND l.creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) THEN l.name END) AS current_count,
                COUNT(CASE WHEN l.creation>=%(prev_from_date)s AND l.creation<%(from_date)s THEN l.name END) AS prev_count
            FROM `tabCRM Lead` l
            LEFT JOIN `tabCRM Lead Status` s ON l.status=s.lead_status
            {where} GROUP BY l.status,s.color,s.position ORDER BY COALESCE(s.position,999) ASC""", params, as_dict=1)
    else:
        rows = frappe.db.sql(f"""
            SELECT l.status, s.color, s.position, COUNT(*) AS current_count, 0 AS prev_count
            FROM `tabCRM Lead` l LEFT JOIN `tabCRM Lead Status` s ON l.status=s.lead_status
            {where} GROUP BY l.status,s.color,s.position ORDER BY COALESCE(s.position,999) ASC""", params, as_dict=1)
    result = []
    for r in rows:
        cur, prev = r.current_count or 0, r.prev_count or 0
        result.append({"status": r.status, "count": cur, "color": r.color, "delta": ((cur-prev)/prev*100) if prev else 0})
    return {"data": result, "title": _("Leads by status"), "categoryColumn": "status", "valueColumn": "count"}


def get_leads_by_status_chart(from_date="", to_date="", user="", project=""):
    lead_conds, params = [], {}
    if from_date and to_date:
        params.update(**{"from": from_date, "to": to_date})
    else:
        from_date = to_date = None
    if user:
        lead_conds.append("l.lead_owner=%(user)s"); params["user"] = user
    if project:
        lead_conds.append("l.project=%(project)s"); lead_conds.append("COALESCE(l.is_duplicate,0)=0"); params["project"] = project
    if from_date and to_date:
        where = "WHERE DATE(l.creation) BETWEEN %(from)s AND %(to)s"
        if lead_conds: where += " AND " + " AND ".join(lead_conds)
    elif lead_conds:
        where = "WHERE " + " AND ".join(lead_conds)
    else:
        where = ""
    r = frappe.db.sql(f"""
        SELECT l.status, COUNT(*) AS count, s.color
        FROM `tabCRM Lead` l JOIN `tabCRM Lead Status` s ON l.status=s.lead_status
        {where} GROUP BY l.status,s.position,s.color ORDER BY s.position ASC""", params, as_dict=True)
    return {"data": r or [], "title": _("Leads by status"), "xAxis": {"key": "status", "type": "category"}, "series": [{"name": "count", "type": "bar"}]}


def get_all_lead_statuses():
    return frappe.db.sql("SELECT lead_status,color,position FROM `tabCRM Lead Status` ORDER BY position ASC", as_dict=1)


# ─── Scalar deal methods ──────────────────────────────────────────────────────

def _deal_scalar(from_date, to_date, user, sql_template, extra_params=None):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    if extra_params:
        params.update(extra_params)
    return frappe.db.sql(sql_template.format(user_cond=cond), params, as_dict=1)


def get_ongoing_deals(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    r = frappe.db.sql(f"""
        SELECT COUNT(CASE WHEN d.creation>=%(from_date)s AND d.creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) AND s.type NOT IN ('Won','Lost') {cond} THEN d.name END) AS v
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name""", params, as_dict=1)
    return {"title": _("Ongoing deals"), "value": r[0].v or 0}


def get_won_deals(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    r = frappe.db.sql(f"""
        SELECT COUNT(CASE WHEN d.closed_date>=%(from_date)s AND d.closed_date<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) AND s.type='Won' {cond} THEN d.name END) AS v
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name""", params, as_dict=1)
    return {"title": _("Won deals"), "value": r[0].v or 0}


def get_average_ongoing_deal_value(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    r = frappe.db.sql(f"""
        SELECT AVG(CASE WHEN d.creation>=%(from_date)s AND d.creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) AND s.type NOT IN ('Won','Lost') {cond} THEN d.deal_value*IFNULL(d.exchange_rate,1) END) AS cur,
               AVG(CASE WHEN d.creation>=%(prev_from_date)s AND d.creation<%(from_date)s AND s.type NOT IN ('Won','Lost') {cond} THEN d.deal_value*IFNULL(d.exchange_rate,1) END) AS prev
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name""", params, as_dict=1)
    cur, prev = r[0].cur or 0, r[0].prev or 0
    return {"title": _("Avg. ongoing deal value"), "value": cur, "delta": cur-prev if prev else 0, "prefix": get_base_currency_symbol()}


def get_average_won_deal_value(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    r = frappe.db.sql(f"""
        SELECT AVG(CASE WHEN d.closed_date>=%(from_date)s AND d.closed_date<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) AND s.type='Won' {cond} THEN d.deal_value*IFNULL(d.exchange_rate,1) END) AS cur,
               AVG(CASE WHEN d.closed_date>=%(prev_from_date)s AND d.closed_date<%(from_date)s AND s.type='Won' {cond} THEN d.deal_value*IFNULL(d.exchange_rate,1) END) AS prev
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name""", params, as_dict=1)
    cur, prev = r[0].cur or 0, r[0].prev or 0
    return {"title": _("Avg. won deal value"), "value": cur, "delta": cur-prev if prev else 0, "prefix": get_base_currency_symbol()}


def get_average_deal_value(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=frappe.utils.add_days(from_date, -diff))
    r = frappe.db.sql(f"""
        SELECT AVG(CASE WHEN d.creation>=%(from_date)s AND d.creation<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) AND s.type!='Lost' {cond} THEN d.deal_value*IFNULL(d.exchange_rate,1) END) AS cur,
               AVG(CASE WHEN d.creation>=%(prev_from_date)s AND d.creation<%(from_date)s AND s.type!='Lost' {cond} THEN d.deal_value*IFNULL(d.exchange_rate,1) END) AS prev
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name""", params, as_dict=1)
    cur, prev = r[0].cur or 0, r[0].prev or 0
    return {"title": _("Avg. deal value"), "value": cur, "delta": cur-prev if prev else 0, "prefix": get_base_currency_symbol()}


def get_average_time_to_close_a_lead(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    prev_fd = frappe.utils.add_days(from_date, -diff)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=prev_fd, prev_to_date=from_date)
    r = frappe.db.sql(f"""
        SELECT AVG(CASE WHEN d.closed_date>=%(from_date)s AND d.closed_date<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) THEN TIMESTAMPDIFF(DAY,COALESCE(l.creation,d.creation),d.closed_date) END) AS cur,
               AVG(CASE WHEN d.closed_date>=%(prev_from_date)s AND d.closed_date<%(prev_to_date)s THEN TIMESTAMPDIFF(DAY,COALESCE(l.creation,d.creation),d.closed_date) END) AS prev
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name LEFT JOIN `tabCRM Lead` l ON d.lead=l.name
        WHERE d.closed_date IS NOT NULL AND s.type='Won' {cond}""", params, as_dict=1)
    cur, prev = r[0].cur or 0, r[0].prev or 0
    return {"title": _("Avg. time to close a lead"), "value": cur, "suffix": " days", "delta": cur-prev if prev else 0, "deltaSuffix": " days", "negativeIsBetter": True}


def get_average_time_to_close_a_deal(from_date, to_date, user=""):
    cond, params = _deal_user_cond(user)
    diff = _diff(from_date, to_date)
    prev_fd = frappe.utils.add_days(from_date, -diff)
    params.update(from_date=from_date, to_date=to_date, prev_from_date=prev_fd, prev_to_date=from_date)
    r = frappe.db.sql(f"""
        SELECT AVG(CASE WHEN d.closed_date>=%(from_date)s AND d.closed_date<DATE_ADD(%(to_date)s,INTERVAL 1 DAY) THEN TIMESTAMPDIFF(DAY,d.creation,d.closed_date) END) AS cur,
               AVG(CASE WHEN d.closed_date>=%(prev_from_date)s AND d.closed_date<%(prev_to_date)s THEN TIMESTAMPDIFF(DAY,d.creation,d.closed_date) END) AS prev
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name LEFT JOIN `tabCRM Lead` l ON d.lead=l.name
        WHERE d.closed_date IS NOT NULL AND s.type='Won' {cond}""", params, as_dict=1)
    cur, prev = r[0].cur or 0, r[0].prev or 0
    return {"title": _("Avg. time to close a deal"), "value": cur, "suffix": " days", "delta": cur-prev if prev else 0, "deltaSuffix": " days", "negativeIsBetter": True}


def get_sales_trend(from_date="", to_date="", user="", project=""):
    lead_conds, params = [], {}
    cond, u_params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    if user:
        lead_conds.append("lead_owner=%(user)s"); params["user"] = user
    if project:
        lead_conds.append("project=%(project)s"); lead_conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    lead_where = "DATE(creation) BETWEEN %(from)s AND %(to)s"
    if lead_conds: lead_where += " AND " + " AND ".join(lead_conds)
    r = frappe.db.sql(f"""
        SELECT DATE_FORMAT(date,'%%Y-%%m-%%d') AS date, SUM(leads) AS leads, SUM(deals) AS deals, SUM(won) AS won_deals
        FROM (
            SELECT DATE(creation) AS date, COUNT(*) AS leads, 0 AS deals, 0 AS won FROM `tabCRM Lead` WHERE {lead_where} GROUP BY DATE(creation)
            UNION ALL
            SELECT DATE(d.creation), 0, COUNT(*), SUM(CASE WHEN s.type='Won' THEN 1 ELSE 0 END) FROM `tabCRM Deal` d
            JOIN `tabCRM Deal Status` s ON d.status=s.name
            WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s {cond} GROUP BY DATE(d.creation)
        ) t GROUP BY date ORDER BY date""", params, as_dict=True)
    return {
        "data": [{"date": row.date, "leads": row.leads or 0, "deals": row.deals or 0, "won_deals": row.won_deals or 0} for row in r],
        "title": _("Sales trend"), "xAxis": {"key": "date", "type": "time", "timeGrain": "day"}, "yAxis": {"title": _("Count")},
        "series": [{"name": "leads","type":"line","showDataPoints":True},{"name":"deals","type":"line","showDataPoints":True},{"name":"won_deals","type":"line","showDataPoints":True}],
    }


def get_forecasted_revenue(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    r = frappe.db.sql(f"""
        SELECT DATE_FORMAT(d.expected_closure_date,'%Y-%m') AS month,
            SUM(CASE WHEN s.type='Lost' THEN d.expected_deal_value*IFNULL(d.exchange_rate,1) ELSE d.expected_deal_value*IFNULL(d.probability,0)/100*IFNULL(d.exchange_rate,1) END) AS forecasted,
            SUM(CASE WHEN s.type='Won' THEN d.deal_value*IFNULL(d.exchange_rate,1) ELSE 0 END) AS actual
        FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name
        WHERE d.expected_closure_date >= DATE_SUB(CURDATE(),INTERVAL 12 MONTH) {cond}
        GROUP BY DATE_FORMAT(d.expected_closure_date,'%Y-%m') ORDER BY month""", params, as_dict=True)
    for row in r:
        row["month"] = frappe.utils.get_datetime(row["month"]).strftime("%Y-%m-01")
        row["forecasted"] = row["forecasted"] or ""
        row["actual"] = row["actual"] or ""
    return {"data": r or [], "title": _("Forecasted revenue"), "xAxis": {"key": "month", "type": "time", "timeGrain": "month"}, "series": [{"name":"forecasted","type":"line"},{"name":"actual","type":"line"}]}


def get_funnel_conversion(from_date="", to_date="", user="", project=""):
    lead_conds, params = [], {}
    cond, u_params = _deal_user_cond(user)
    params.update(u_params)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    if user: lead_conds.append("lead_owner=%(user)s"); params["user"] = user
    if project: lead_conds.append("project=%(project)s"); lead_conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    lead_where = "DATE(creation) BETWEEN %(from)s AND %(to)s"
    if lead_conds: lead_where += " AND " + " AND ".join(lead_conds)
    total = frappe.db.sql(f"SELECT COUNT(*) AS c FROM `tabCRM Lead` WHERE {lead_where}", params, as_dict=True)
    result = [{"stage": "Leads", "count": total[0].c if total else 0}]
    result += get_deal_status_change_counts(from_date, to_date, cond, params)
    return {"data": result or [], "title": _("Funnel conversion"), "xAxis": {"key": "stage", "type": "category"}, "swapXY": True, "series": [{"name":"count","type":"bar","echartOptions":{"colorBy":"data"}}]}


def get_deals_by_stage_axis(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    r = frappe.db.sql(f"""SELECT d.status AS stage, COUNT(*) AS count FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s AND s.type NOT IN ('Lost') {cond} GROUP BY d.status ORDER BY count DESC""", params, as_dict=True)
    return {"data": r or [], "title": _("Deals by stage"), "xAxis": {"key": "stage", "type": "category"}, "series": [{"name":"count","type":"bar"}]}


def get_deals_by_stage_donut(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    r = frappe.db.sql(f"""SELECT d.status AS stage, COUNT(*) AS count FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s {cond} GROUP BY d.status ORDER BY count DESC""", params, as_dict=True)
    return {"data": r or [], "title": _("Deals by stage"), "categoryColumn": "stage", "valueColumn": "count"}


def get_lost_deal_reasons(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    r = frappe.db.sql(f"""SELECT d.lost_reason AS reason, COUNT(*) AS count FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s AND s.type='Lost' {cond} GROUP BY d.lost_reason HAVING reason IS NOT NULL AND reason!='' ORDER BY count DESC""", params, as_dict=True)
    return {"data": r or [], "title": _("Lost deal reasons"), "xAxis": {"key": "reason", "type": "category"}, "series": [{"name":"count","type":"bar"}]}


def get_leads_by_source(from_date="", to_date="", user="", project=""):
    lead_conds, params = [], {}
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    if user: lead_conds.append("lead_owner=%(user)s"); params["user"] = user
    if project: lead_conds.append("project=%(project)s"); lead_conds.append("COALESCE(is_duplicate,0)=0"); params["project"] = project
    lead_where = "DATE(creation) BETWEEN %(from)s AND %(to)s"
    if lead_conds: lead_where += " AND " + " AND ".join(lead_conds)
    r = frappe.db.sql(f"SELECT IFNULL(source,'Empty') AS source, COUNT(*) AS count FROM `tabCRM Lead` WHERE {lead_where} GROUP BY source ORDER BY count DESC", params, as_dict=True)
    return {"data": r or [], "title": _("Leads by source"), "categoryColumn": "source", "valueColumn": "count"}


def get_deals_by_source(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    r = frappe.db.sql(f"SELECT IFNULL(source,'Empty') AS source, COUNT(*) AS count FROM `tabCRM Deal` WHERE DATE(creation) BETWEEN %(from)s AND %(to)s {cond} GROUP BY source ORDER BY count DESC", params, as_dict=True)
    return {"data": r or [], "title": _("Deals by source"), "categoryColumn": "source", "valueColumn": "count"}


def get_deals_by_territory(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    r = frappe.db.sql(f"""SELECT IFNULL(d.territory,'Empty') AS territory, COUNT(*) AS deals, SUM(COALESCE(d.deal_value,0)*IFNULL(d.exchange_rate,1)) AS value FROM `tabCRM Deal` d WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s {cond} GROUP BY d.territory ORDER BY value DESC""", params, as_dict=True)
    return {"data": r or [], "title": _("Deals by territory"), "xAxis": {"key": "territory", "type": "category"}, "series": [{"name":"deals","type":"bar"},{"name":"value","type":"line","axis":"y2"}]}


def get_deals_by_salesperson(from_date="", to_date="", user=""):
    cond, params = _deal_user_cond(user)
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())
    params.update({"from": from_date, "to": to_date})
    r = frappe.db.sql(f"""SELECT IFNULL(u.full_name,d.deal_owner) AS salesperson, COUNT(*) AS deals, SUM(COALESCE(d.deal_value,0)*IFNULL(d.exchange_rate,1)) AS value FROM `tabCRM Deal` d LEFT JOIN `tabUser` u ON u.name=d.deal_owner WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s {cond} GROUP BY d.deal_owner ORDER BY value DESC""", params, as_dict=True)
    return {"data": r or [], "title": _("Deals by salesperson"), "xAxis": {"key": "salesperson", "type": "category"}, "series": [{"name":"deals","type":"bar"},{"name":"value","type":"line","axis":"y2"}]}


def get_deal_status_change_counts(from_date, to_date, deal_conds="", extra_params=None):
    params = {"from": from_date, "to": to_date}
    if extra_params:
        params.update(extra_params)
    r = frappe.db.sql(f"""
        SELECT scl.to AS stage, COUNT(*) AS count
        FROM `tabCRM Status Change Log` scl
        JOIN `tabCRM Deal` d ON scl.parent=d.name
        JOIN `tabCRM Deal Status` s ON d.status=s.name
        JOIN `tabCRM Deal Status` st ON scl.to=st.name
        WHERE scl.to IS NOT NULL AND scl.to!='' AND s.type!='Lost' AND DATE(d.creation) BETWEEN %(from)s AND %(to)s {deal_conds}
        GROUP BY scl.to, st.position ORDER BY st.position ASC""", params, as_dict=True)
    return r or []


@frappe.whitelist()
@sales_user_only
def get_all_projects():
    return frappe.db.sql("SELECT name,project_name FROM `tabReal Estate Project` WHERE disabled=0 ORDER BY creation DESC", as_dict=True)


@frappe.whitelist()
@sales_user_only
def get_all_crm_users():
    current = frappe.session.user
    roles = frappe.get_roles(current)
    is_sm = "Sales Manager" in roles and "System Manager" not in roles
    if is_sm:
        members = _get_team_members_for_leader(current)
        team = tuple(members + [current])
        if not team:
            return []
        return frappe.db.sql("""
            SELECT u.name, u.full_name, u.creation FROM `tabUser` u
            JOIN `tabHas Role` hr ON hr.parent=u.name AND hr.role IN ('Sales User','Sales Manager')
            WHERE u.name IN %(members)s AND u.enabled=1 GROUP BY u.name ORDER BY u.creation DESC""",
            {"members": team}, as_dict=True)
    return frappe.db.sql("""
        SELECT u.name, u.full_name, u.creation FROM `tabUser` u
        JOIN `tabHas Role` hr ON hr.parent=u.name AND hr.role IN ('Sales User','Sales Manager')
        WHERE u.enabled=1 GROUP BY u.name ORDER BY u.creation DESC""", as_dict=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Leads Performance Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
@sales_user_only
def get_leads_dashboard(from_date="", to_date="", user="", project=None, status=None, search=None):
    roles = frappe.get_roles(frappe.session.user)
    is_sales_user = "Sales User" in roles and "Sales Manager" not in roles and "System Manager" not in roles
    if is_sales_user and not user:
        user = frappe.session.user
    user_cond, user_params = _get_user_condition(user)
    return {
        "stats":          _get_lead_status_stats(from_date, to_date, user, user_cond, user_params, project, status, search),
        "activities":     _get_lead_activity_counts(from_date, to_date, user, project, status, search),
        "conversion":     _get_lead_conversion_metrics(from_date, to_date, user, user_cond, user_params, project, status, search),
        "lost_reasons":   _get_lead_lost_reasons(from_date, to_date, user, user_cond, user_params, project, status, search),
        "source_chart":   _get_lead_source_performance(from_date, to_date, user, user_cond, user_params, project, status, search),
        "monthly_target": _get_monthly_target(user),
        "status_funnel":  _get_lead_status_funnel(from_date, to_date, user, user_cond, user_params, project, status, search),
    }


def _get_lead_status_stats(fd, td, user, user_cond, user_params, project=None, status_filter=None, search=None):
    where, params = _build_lead_where(fd, td, user_cond, user_params, alias="l", project=project, status=status_filter, search=search)
    rows = frappe.db.sql(f"""
        SELECT l.status, COUNT(*) AS count, s.color, s.position
        FROM `tabCRM Lead` l LEFT JOIN `tabCRM Lead Status` s ON l.status=s.lead_status
        {where} GROUP BY l.status,s.color,s.position ORDER BY COALESCE(s.position,999) ASC""", params, as_dict=True)
    total = sum(r.count or 0 for r in rows)
    return {
        "items": [{"status": r.status, "count": r.count or 0, "color": r.color or CHART_COLOURS[i % len(CHART_COLOURS)]} for i, r in enumerate(rows)],
        "total": total,
    }


def _get_lead_status_funnel(fd, td, user, user_cond, user_params, project=None, status_filter=None, search=None):
    where, params = _build_lead_where(fd, td, user_cond, user_params, alias="l", project=project, status=status_filter, search=search)
    rows = frappe.db.sql(f"""
        SELECT l.status, COUNT(*) AS count, s.color, COALESCE(s.position,99) AS pos
        FROM `tabCRM Lead` l LEFT JOIN `tabCRM Lead Status` s ON l.status=s.lead_status
        {where} GROUP BY l.status,s.color,s.position ORDER BY pos ASC""", params, as_dict=True)
    total = sum(r.count or 0 for r in rows)
    return [
        {"status": r.status, "count": r.count or 0, "color": r.color or CHART_COLOURS[i % len(CHART_COLOURS)],
         "pct": round((r.count or 0) / total * 100, 1) if total else 0}
        for i, r in enumerate(rows)
    ]


def _get_lead_activity_counts(fd, td, user, project=None, status_filter=None, search=None):
    """
    Count activities linked to CRM Leads.
    - tabCRM Call Log: joined via reference_name = lead name
    - tabComment: joined via reference_doctype='CRM Lead' AND reference_name = lead name
    - tabCommunication: joined via reference_doctype='CRM Lead' AND reference_name = lead name
    - tabCRM Lead itself: direct count with extra filters
    """
    # Build lead-level filters (used in subquery to find matching lead names)
    lead_conds, lead_params = [], {}

    if user:
        u_cond, u_params = _get_user_condition(user)
        stripped = u_cond.lstrip("AND ").strip()
        # Replace alias "l." with "lead." for the subquery
        if stripped:
            lead_conds.append(stripped.replace("l.lead_owner", "lead.lead_owner"))
        lead_params.update(u_params)

    if project:
        lead_conds.append("lead.project = %(project)s")
        lead_params["project"] = project

    if status_filter:
        lead_conds.append("lead.status = %(status_filter)s")
        lead_params["status_filter"] = status_filter

    if search:
        lead_conds.append(
            "(lead.first_name LIKE %(search)s OR lead.last_name LIKE %(search)s OR lead.mobile_no LIKE %(search)s)"
        )
        lead_params["search"] = f"%{search}%"

    if fd and td:
        lead_params.update(fd=fd, td=td)

    # Subquery that returns matching lead names
    lead_where_parts = list(lead_conds)
    if fd and td:
        lead_where_parts.append("DATE(lead.creation) BETWEEN %(fd)s AND %(td)s")
    lead_subquery_where = ("WHERE " + " AND ".join(lead_where_parts)) if lead_where_parts else ""
    lead_subquery = f"SELECT lead.name FROM `tabCRM Lead` lead {lead_subquery_where}"

    def cnt(table, date_col, extra_cond="", ref_doctype_cond=""):
        """
        Count rows in `table` t where:
        - date range applies to t.{date_col}
        - t.reference_name IN (matching lead names subquery)
        - optional extra_cond (e.g. communication_medium filter)
        """
        parts = [f"t.reference_name IN ({lead_subquery})"]
        if ref_doctype_cond:
            parts.append(ref_doctype_cond)
        if fd and td:
            parts.append(f"DATE(t.{date_col}) BETWEEN %(fd)s AND %(td)s")
        if extra_cond:
            parts.append(extra_cond)
        where = "WHERE " + " AND ".join(parts)
        try:
            r = frappe.db.sql(f"SELECT COUNT(*) AS c FROM `{table}` t {where}", lead_params, as_dict=True)
            return r[0].c if r else 0
        except Exception:
            return 0

    def cnt_direct(extra_cond=""):
        """Count rows directly on tabCRM Lead matching the subquery + extra filter."""
        parts = [f"name IN ({lead_subquery})"]
        if fd and td:
            parts.append("DATE(creation) BETWEEN %(fd)s AND %(td)s")
        if extra_cond:
            parts.append(extra_cond)
        where = "WHERE " + " AND ".join(parts)
        try:
            r = frappe.db.sql(f"SELECT COUNT(*) AS c FROM `tabCRM Lead` {where}", lead_params, as_dict=True)
            return r[0].c if r else 0
        except Exception:
            return 0

    return {
        # BUG FIX: tabComment needs reference_doctype filter to avoid cross-doctype collisions
        "feedback": cnt("tabComment",       "creation", "t.comment_type='Comment'",  "t.reference_doctype='CRM Lead'"),
        "whatsapp": cnt("tabCommunication", "creation", "t.communication_medium='WhatsApp'", "t.reference_doctype='CRM Lead'"),
        "email":    cnt("tabCommunication", "creation", "t.communication_medium='Email'",    "t.reference_doctype='CRM Lead'"),
        "meetings": cnt("tabComment",       "creation", "t.comment_type='Meeting'",   "t.reference_doctype='CRM Lead'"),
        "viewings": cnt("tabComment",       "creation", "t.comment_type='Viewing'",   "t.reference_doctype='CRM Lead'"),
        "bookings": cnt("tabComment",       "creation", "t.comment_type='Booking'",   "t.reference_doctype='CRM Lead'"),
        # tabCRM Call Log uses reference_name but no reference_doctype column — filter by lead subquery only
        "calls":    cnt("tabCRM Call Log",  "creation"),
        # Direct lead counts
        "website":  cnt_direct("source='Website'"),
        "others":   cnt_direct("source NOT IN ('Website','WhatsApp','Email','Direct')"),
        # Deals linked to matching leads
        "deals":    frappe.db.sql(
            f"SELECT COUNT(*) AS c FROM `tabCRM Deal` WHERE lead IN ({lead_subquery})"
            + (" AND DATE(creation) BETWEEN %(fd)s AND %(td)s" if fd and td else ""),
            lead_params, as_dict=True
        )[0].c or 0,
    }


def _get_lead_conversion_metrics(fd, td, user, user_cond, user_params, project=None, status_filter=None, search=None):
    if not fd or not td:
        return {"avg_days": 0, "delta": 0, "optimal_days": 12}
    diff = max(frappe.utils.date_diff(td, fd), 1)
    prev_fd = frappe.utils.add_days(fd, -diff)
    params = dict(user_params)
    params.update(fd=fd, td=td, prev_fd=prev_fd)
    if project: params["project"] = project
    if search: params["search"] = f"%{search}%"
    if not (frappe.db.exists("DocType", "CRM Deal") and frappe.db.exists("DocType", "CRM Deal Status")):
        return {"avg_days": 0, "delta": 0, "optimal_days": 12}
    deal_cond = user_cond.replace("l.lead_owner", "d.deal_owner") if user_cond else ""
    proj_cond = "AND l.project=%(project)s" if project else ""
    srch_cond = "AND (l.first_name LIKE %(search)s OR l.last_name LIKE %(search)s OR l.mobile_no LIKE %(search)s)" if search else ""
    if status_filter: params["status_filter"] = status_filter
    stat_cond = "AND l.status=%(status_filter)s" if status_filter else ""
    try:
        r = frappe.db.sql(f"""
            SELECT AVG(CASE WHEN d.closed_date>=%(fd)s AND d.closed_date<DATE_ADD(%(td)s,INTERVAL 1 DAY) THEN TIMESTAMPDIFF(DAY,l.creation,d.closed_date) END) AS cur,
                   AVG(CASE WHEN d.closed_date>=%(prev_fd)s AND d.closed_date<%(fd)s THEN TIMESTAMPDIFF(DAY,l.creation,d.closed_date) END) AS prev
            FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name JOIN `tabCRM Lead` l ON d.lead=l.name
            WHERE d.closed_date IS NOT NULL AND s.type='Won' {deal_cond} {proj_cond} {stat_cond} {srch_cond}""", params, as_dict=True)
        cur = round(r[0].cur or 0, 1); prev = round(r[0].prev or 0, 1)
        return {"avg_days": cur, "delta": round(cur-prev, 1) if prev else 0, "optimal_days": 12}
    except Exception:
        return {"avg_days": 0, "delta": 0, "optimal_days": 12}


def _get_lead_lost_reasons(fd, td, user, user_cond, user_params, project=None, status_filter=None, search=None):
    if not frappe.db.has_column("CRM Lead", "lost_reason"):
        return []
    where, params = _build_lead_where(fd, td, user_cond, user_params, alias="l", project=project, status=status_filter, search=search)
    lost_cond = "" if status_filter else "AND l.status='Lost'"
    rows = frappe.db.sql(f"""
        SELECT lost_reason AS reason, COUNT(*) AS count FROM `tabCRM Lead` l
        {where} {lost_cond} AND COALESCE(lost_reason,'')!=''
        GROUP BY lost_reason ORDER BY count DESC LIMIT 10""", params, as_dict=True)
    return [{"reason": r.reason, "count": r.count or 0} for r in rows]


def _get_lead_source_performance(fd, td, user, user_cond, user_params, project=None, status_filter=None, search=None):
    where, params = _build_lead_where(fd, td, user_cond, user_params, alias="l", project=project, status=status_filter, search=search)
    rows = frappe.db.sql(f"""
        SELECT IFNULL(l.source,'Other') AS source, COUNT(l.name) AS total,
               SUM(CASE WHEN s.type='Won' THEN 1 ELSE 0 END) AS won
        FROM `tabCRM Lead` l LEFT JOIN `tabCRM Deal` d ON d.lead=l.name
        LEFT JOIN `tabCRM Deal Status` s ON d.status=s.name
        {where} GROUP BY l.source ORDER BY total DESC""", params, as_dict=True)
    return [{"source": r.source, "total": r.total or 0, "won": r.won or 0} for r in rows]


def _get_monthly_target(user=None):
    now = frappe.utils.now_datetime()
    start = frappe.utils.get_first_day(now)
    end = frappe.utils.get_last_day(now)
    conds = ["d.closed_date BETWEEN %(start_date)s AND %(end_date)s", "s.type='Won'"]
    params = {"start_date": start, "end_date": end}
    if user:
        if user == "__TEAM__":
            members = _get_team_members_for_leader(frappe.session.user)
            params["team_users"] = tuple(members + [frappe.session.user])
            conds.append("d.deal_owner IN %(team_users)s")
        else:
            params["target_user"] = user
            conds.append("d.deal_owner=%(target_user)s")
    where = "WHERE " + " AND ".join(conds)
    won = frappe.db.sql(f"SELECT COUNT(d.name) FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON d.status=s.name {where}", params)[0][0] or 0
    target = 10
    return {"won_deals": won, "target": target, "percentage": round(won/target*100, 1) if target else 0}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Projects / Inventory Performance Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
@sales_user_only
def get_inventory_dashboard(from_date="", to_date="", user="", project=None):
    project = project.strip() if project and project.strip() else None
    return {
        "project_stats": _get_inventory_project_stats(project),
        "unit_stats":    _get_inventory_unit_stats(project),
        "insights":      _get_inventory_insights(project),
        "performance":   _get_inventory_performance(project),
        "targets":       _get_inventory_targets(project),
        "profits":       _get_inventory_profits(project),
        "reservations":  _get_inventory_reservations(project),
    }


def _get_inventory_project_stats(pf=None):
    filters = {"name": pf} if pf else {}
    try:
        stats = frappe.db.get_list("Real Estate Project", filters=filters, fields=["status", "count(*) as count"], group_by="status")
        total = frappe.db.count("Real Estate Project", filters=filters)
        items = {s.status: s.count for s in stats}
    except Exception:
        return {"total": 0, "available": 0, "sold": 0, "archived": 0}
    return {"total": total, "available": items.get("Available", 0), "sold": items.get("Sold", 0), "archived": items.get("Removed", 0)+items.get("Archived", 0)}


def _get_inventory_unit_stats(pf=None):
    filters = {"project": pf} if pf else {}
    try:
        stats = frappe.db.get_list("Project Unit", filters=filters, fields=["status", "count(*) as count"], group_by="status")
        total = frappe.db.count("Project Unit", filters=filters)
        items = {s.status: s.count for s in stats}
    except Exception:
        return {"total": 0, "available": 0, "sold": 0, "reserved": 0}
    return {"total": total, "available": items.get("Available", 0), "sold": items.get("Sold", 0), "reserved": items.get("Reserved", 0)}


def _get_inventory_insights(pf=None):
    try:
        most = frappe.db.sql("SELECT project, COUNT(*) AS c FROM `tabProject Unit` GROUP BY project ORDER BY c DESC LIMIT 1", as_dict=True)
        dist = frappe.db.sql("SELECT district, COUNT(*) AS c FROM `tabReal Estate Project` WHERE COALESCE(district,'')!='' GROUP BY district ORDER BY c DESC LIMIT 1", as_dict=True)
        f = {"project": pf} if pf else {}
        lo = frappe.db.get_list("Project Unit", filters=f, fields=["unit_name","price"], order_by="price asc", limit=1)
        hi = frappe.db.get_list("Project Unit", filters=f, fields=["unit_name","price"], order_by="price desc", limit=1)
        avg = frappe.db.sql("SELECT AVG(price_per_meter) AS a, COUNT(*) AS c FROM `tabProject Unit` WHERE COALESCE(price_per_meter,0)>0", as_dict=True)
    except Exception:
        return []
    return [
        {"label": "Most units project",   "value": most[0].project if most else "N/A",         "sub": f"{most[0].c} units" if most else ""},
        {"label": "Most active district", "value": dist[0].district if dist else "N/A",         "sub": f"{dist[0].c} projects" if dist else ""},
        {"label": "Highest price unit",   "value": f"{hi[0].price:,.0f}" if hi and hi[0].get('price') else "0", "sub": hi[0].unit_name if hi else ""},
        {"label": "Lowest price unit",    "value": f"{lo[0].price:,.0f}" if lo and lo[0].get('price') else "0", "sub": lo[0].unit_name if lo else ""},
        {"label": "Avg price / m²",       "value": f"{avg[0].a:,.0f}" if avg and avg[0].a else "0", "sub": f"{avg[0].c} units" if avg else ""},
        {"label": "Inventory status",     "value": "Healthy", "sub": "Last updated recently"},
    ]


def _get_inventory_performance(pf=None):
    try:
        projects = frappe.db.sql("SELECT project, COUNT(*) AS total FROM `tabProject Unit` GROUP BY project ORDER BY total DESC LIMIT 3", as_dict=True)
        for p in projects:
            p.sold = frappe.db.count("Project Unit", {"project": p.project, "status": "Sold"})
            p.percent = round((p.sold/p.total)*100) if p.total else 0
        return projects
    except Exception:
        return []


def _get_inventory_targets(pf=None):
    target = 20
    try:
        fd = frappe.utils.get_first_day(frappe.utils.nowdate())
        td = frappe.utils.get_last_day(frappe.utils.nowdate())
        f = {"status": "Sold", "modified": ["between", [fd, td]]}
        if pf: f["project"] = pf
        achieved = frappe.db.count("Project Unit", filters=f)
        colours = ["#86efac","#93c5fd","#c084fc","#60a5fa","#99f6e4"]
        monthly = []
        for i in range(4, -1, -1):
            ref = frappe.utils.add_months(frappe.utils.nowdate(), -i)
            mf = frappe.utils.get_first_day(ref)
            mt = frappe.utils.get_last_day(ref)
            label = frappe.utils.get_datetime(ref).strftime("%b")
            mf2 = {"status": "Sold", "modified": ["between", [mf, mt]]}
            if pf: mf2["project"] = pf
            cnt = frappe.db.count("Project Unit", filters=mf2)
            monthly.append({"month": label, "percent": round((cnt/target)*100) if target else 0, "color": colours[i % len(colours)]})
        return {"target": target, "achieved": achieved, "percent": round((achieved/target)*100) if target else 0, "monthly_data": monthly}
    except Exception:
        return {"target": target, "achieved": 0, "percent": 0, "monthly_data": []}


def _get_inventory_profits(pf=None):
    f = {"project": pf} if pf else {}
    try:
        exp = frappe.db.get_list("Project Unit", filters=f, fields=["sum(price) as t"])
        sol = frappe.db.get_list("Project Unit", filters={**f, "status": "Sold"}, fields=["sum(price) as t"])
        expected = (exp[0].t or 0)/1000
        realized = (sol[0].t or 0)/1000
        diff = max(expected-realized, 0)
    except Exception:
        expected = realized = diff = 0
    return [
        {"type": "Expected",   "value": round(expected), "color": "#86efac"},
        {"type": "Realized",   "value": round(realized), "color": "#93c5fd"},
        {"type": "Difference", "value": round(diff),     "color": "#c084fc"},
    ]


def _get_inventory_reservations(pf=None):
    f = {"project": pf} if pf else {}
    try:
        cur  = frappe.db.count("Reservation", {**f, "status": "Reserved",  "docstatus": 1})
        done = frappe.db.count("Reservation", {**f, "status": "Deal Done", "docstatus": 1})
        canc = frappe.db.count("Reservation", {**f, "docstatus": 2})
    except Exception:
        cur = done = canc = 0
    return [
        {"type": "Current",   "value": cur,  "color": "#93c5fd"},
        {"type": "Completed", "value": done, "color": "#86efac"},
        {"type": "Cancelled", "value": canc, "color": "#fca5a5"},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Tasks Performance Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
@sales_user_only
def get_tasks_dashboard(from_date="", to_date="", user="", project=None):
    roles = frappe.get_roles(frappe.session.user)
    is_sales_user = "Sales User" in roles and "Sales Manager" not in roles and "System Manager" not in roles
    if is_sales_user and not user:
        user = frappe.session.user

    project = project.strip() if project and project.strip() else None

    return {
        "kpis":               _get_task_kpis(from_date, to_date, user, project),
        "status_breakdown":   _get_task_status_breakdown(from_date, to_date, user, project),
        "type_breakdown":     _get_task_type_breakdown(from_date, to_date, user, project),
        "priority_breakdown": _get_task_priority_breakdown(from_date, to_date, user, project),
        "completion_by_user": _get_task_completion_by_user(from_date, to_date, project),
        "overdue_trend":      _get_task_overdue_trend(from_date, to_date, user, project),
        "type_performance":   _get_task_type_performance(from_date, to_date, user, project),
    }


def _task_base_where(fd, td, user=None, project=None, extra_conds=None):
    parts, params = [], {}
    if fd and td:
        parts.append("DATE(t.creation) BETWEEN %(from_date)s AND %(to_date)s")
        params.update(from_date=fd, to_date=td)
    if user:
        parts.append("t.assigned_to = %(task_user)s")
        params["task_user"] = user
    if project:
        parts.append("t.project = %(task_project)s")
        params["task_project"] = project
    if extra_conds:
        parts.extend(extra_conds)
    where = ("WHERE " + " AND ".join(parts)) if parts else ""
    return where, params


def _get_task_kpis(fd, td, user=None, project=None):
    where, params = _task_base_where(fd, td, user, project)
    r = frappe.db.sql(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN t.status='Done' THEN 1 ELSE 0 END) AS done,
            SUM(CASE WHEN t.status='late' OR (t.status NOT IN ('Done','Canceled') AND t.due_date < NOW()) THEN 1 ELSE 0 END) AS late,
            SUM(CASE WHEN t.status='In Progress' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN t.status='Todo' THEN 1 ELSE 0 END) AS todo,
            SUM(CASE WHEN t.status='Canceled' THEN 1 ELSE 0 END) AS canceled
        FROM `tabCRM Task` t {where}""", params, as_dict=True)
    row = r[0] if r else {}
    total = row.total or 0
    done = row.done or 0
    return {
        "total":           total,
        "done":            done,
        "late":            row.late or 0,
        "in_progress":     row.in_progress or 0,
        "todo":            row.todo or 0,
        "canceled":        row.canceled or 0,
        "completion_rate": round((done / total) * 100, 1) if total else 0,
    }


def _get_task_status_breakdown(fd, td, user=None, project=None):
    where, params = _task_base_where(fd, td, user, project)
    rows = frappe.db.sql(f"""
        SELECT t.status, COUNT(*) AS count
        FROM `tabCRM Task` t {where}
        GROUP BY t.status ORDER BY count DESC""", params, as_dict=True)
    status_colours = {
        "Todo": "#93c5fd", "Backlog": "#d1d5db", "In Progress": "#fbbf24",
        "Done": "#34d399", "Canceled": "#9ca3af", "late": "#f87171",
    }
    total = sum(r.count or 0 for r in rows)
    return [
        {"status": r.status, "count": r.count or 0, "color": status_colours.get(r.status, "#94a3b8"),
         "pct": round((r.count or 0) / total * 100, 1) if total else 0}
        for r in rows
    ]


def _get_task_type_breakdown(fd, td, user=None, project=None):
    where, params = _task_base_where(fd, td, user, project)
    rows = frappe.db.sql(f"""
        SELECT t.task_type, COUNT(*) AS count
        FROM `tabCRM Task` t {where}
        GROUP BY t.task_type ORDER BY count DESC""", params, as_dict=True)
    type_colours = {
        "call": "#60a5fa", "property showing": "#34d399", "whatsapp message": "#4ade80",
        "team meeting": "#a78bfa", "lead meeting": "#f472b6", "other": "#94a3b8",
    }
    total = sum(r.count or 0 for r in rows)
    return [
        {"type": r.task_type or "other", "count": r.count or 0,
         "color": type_colours.get(r.task_type or "other", "#94a3b8"),
         "pct": round((r.count or 0) / total * 100, 1) if total else 0}
        for r in rows
    ]


def _get_task_priority_breakdown(fd, td, user=None, project=None):
    where, params = _task_base_where(fd, td, user, project)
    rows = frappe.db.sql(f"""
        SELECT t.priority, COUNT(*) AS count
        FROM `tabCRM Task` t {where}
        GROUP BY t.priority ORDER BY FIELD(t.priority,'High','Medium','Low')""", params, as_dict=True)
    priority_colours = {"High": "#f87171", "Medium": "#fbbf24", "Low": "#34d399"}
    total = sum(r.count or 0 for r in rows)
    return [
        {"priority": r.priority or "Low", "count": r.count or 0,
         "color": priority_colours.get(r.priority or "Low", "#94a3b8"),
         "pct": round((r.count or 0) / total * 100, 1) if total else 0}
        for r in rows
    ]


def _get_task_completion_by_user(fd, td, project=None):
    extra = []
    params = {}
    if fd and td:
        extra = ["DATE(t.creation) BETWEEN %(from_date)s AND %(to_date)s"]
        params.update(from_date=fd, to_date=td)
    if project:
        extra.append("t.project=%(task_project)s")
        params["task_project"] = project
    where = ("WHERE " + " AND ".join(extra)) if extra else ""
    rows = frappe.db.sql(f"""
        SELECT
            t.assigned_to,
            IFNULL(u.full_name, t.assigned_to) AS name,
            COUNT(*) AS total,
            SUM(CASE WHEN t.status='Done' THEN 1 ELSE 0 END) AS done,
            SUM(CASE WHEN t.status='late' OR (t.status NOT IN ('Done','Canceled') AND t.due_date < NOW()) THEN 1 ELSE 0 END) AS late
        FROM `tabCRM Task` t
        LEFT JOIN `tabUser` u ON u.name=t.assigned_to
        {where}
        GROUP BY t.assigned_to ORDER BY total DESC LIMIT 10""", params, as_dict=True)
    return [
        {"user": r.assigned_to, "name": r.name or r.assigned_to, "total": r.total or 0,
         "done": r.done or 0, "late": r.late or 0,
         "completion_rate": round((r.done or 0) / (r.total or 1) * 100, 1)}
        for r in rows
    ]


def _get_task_overdue_trend(fd, td, user=None, project=None):
    if not fd or not td:
        return []
    extra = []
    params = {"from_date": fd, "to_date": td}
    if user:
        extra.append("t.assigned_to=%(task_user)s"); params["task_user"] = user
    if project:
        extra.append("t.project=%(task_project)s"); params["task_project"] = project
    extra_cond = ("AND " + " AND ".join(extra)) if extra else ""
    rows = frappe.db.sql(f"""
        SELECT
            DATE_FORMAT(t.creation,'%%Y-%%m-%%d') AS date,
            COUNT(*) AS total,
            SUM(CASE WHEN t.status='late' OR (t.status NOT IN ('Done','Canceled') AND t.due_date < NOW()) THEN 1 ELSE 0 END) AS overdue
        FROM `tabCRM Task` t
        WHERE DATE(t.creation) BETWEEN %(from_date)s AND %(to_date)s {extra_cond}
        GROUP BY DATE(t.creation) ORDER BY date""", params, as_dict=True)
    return [{"date": r.date, "total": r.total or 0, "overdue": r.overdue or 0} for r in rows]


def _get_task_type_performance(fd, td, user=None, project=None):
    where, params = _task_base_where(fd, td, user, project)
    rows = frappe.db.sql(f"""
        SELECT
            t.task_type,
            COUNT(*) AS total,
            SUM(CASE WHEN t.status='Done' THEN 1 ELSE 0 END) AS done,
            SUM(CASE WHEN t.status='late' OR (t.status NOT IN ('Done','Canceled') AND t.due_date < NOW()) THEN 1 ELSE 0 END) AS late
        FROM `tabCRM Task` t {where}
        GROUP BY t.task_type ORDER BY total DESC""", params, as_dict=True)
    type_colours = {
        "call": "#60a5fa", "property showing": "#34d399", "whatsapp message": "#4ade80",
        "team meeting": "#a78bfa", "lead meeting": "#f472b6", "other": "#94a3b8",
    }
    return [
        {"type": r.task_type or "other", "total": r.total or 0, "done": r.done or 0, "late": r.late or 0,
         "color": type_colours.get(r.task_type or "other", "#94a3b8"),
         "completion_rate": round((r.done or 0) / (r.total or 1) * 100, 1)}
        for r in rows
    ]


@frappe.whitelist()
def test_project_filter(project="", from_date="", to_date=""):
    if not project:
        return {"error": "Project required"}
    if not from_date or not to_date:
        from_date = frappe.utils.get_first_day(frappe.utils.nowdate())
        to_date = frappe.utils.get_last_day(frappe.utils.nowdate())
    p = (project, from_date, to_date)
    total = frappe.db.sql("SELECT COUNT(*) AS c FROM `tabCRM Lead` WHERE project=%s AND creation>=%s AND creation<DATE_ADD(%s,INTERVAL 1 DAY)", p, as_dict=1)[0].c or 0
    dups  = frappe.db.sql("SELECT COUNT(*) AS c FROM `tabCRM Lead` WHERE project=%s AND is_duplicate=1 AND creation>=%s AND creation<DATE_ADD(%s,INTERVAL 1 DAY)", p, as_dict=1)[0].c or 0
    excl  = frappe.db.sql("SELECT COUNT(*) AS c FROM `tabCRM Lead` WHERE project=%s AND COALESCE(is_duplicate,0)=0 AND creation>=%s AND creation<DATE_ADD(%s,INTERVAL 1 DAY)", p, as_dict=1)[0].c or 0
    dash  = get_total_leads(from_date, to_date, "", project).get("value", 0)
    return {"project": project, "total": total, "duplicates": dups, "excluding_dups": excl, "dashboard": dash, "match": excl == dash}
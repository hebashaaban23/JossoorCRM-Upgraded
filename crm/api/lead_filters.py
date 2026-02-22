# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def lead_filter_options():
	"""
	Returns options for Lead filters: status, project, territory, source, etc.
	"""
	return {
		"status": get_status_options(),
		"project": get_project_options(),
		"territory": get_territory_options(),
		"lead_source": get_source_options(),
		"lead_origin": [],
		"lead_type": get_type_options(),
		"last_contact_field": "last_contacted_on",
		"location_field": "territory",
		"has_budget": True,
		"has_space": True,
	}

def get_status_options():
	return frappe.get_all("CRM Lead Status", fields=["name as value", "name as label", "color"], order_by="position")

def get_project_options():
	return frappe.get_all("Real Estate Project", fields=["name as value", "name as label"])

def get_territory_options():
	return frappe.get_all("CRM Territory", fields=["name as value", "name as label"])

def get_source_options():
	return frappe.get_all("CRM Lead Source", fields=["name as value", "name as label"])

def get_type_options():
	# lead_type is a Select field in CRM Lead, but we might have a Lead Type doctype
	if frappe.db.exists("DocType", "CRM Lead Type"):
		return frappe.get_all("CRM Lead Type", fields=["name as value", "name as label"])
	return [
		{"value": "Out Source", "label": "Out Source"},
		{"value": "Company", "label": "Company"}
	]

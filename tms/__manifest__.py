# Copyright 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Transportation Management System (TMS)",
    "summary": "Transportation Management System (TMS)",
    "version": "15.0.1.0.0",
    "category": "Logistic",
    "website": "https://github.com/OCA/tms",
    "author": "Tecnativa, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "external_dependencies": {
        "python": [
            "stdnum",
        ],
    },
    "depends": [
        "base_automation",
        "base_geolocalize",
        "purchase",
        "fleet",
        "sale_timesheet",
        "project_task_default_stage",
        "project_timeline",
        "sale_order_invoicing_finished_task",
        "sale_order_type",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/tms_security.xml",
        "data/ir_sequence_data.xml",
        "data/iso6346.length.csv",
        "data/iso6346.second.size.csv",
        "data/iso6346.type.csv",
        "data/custom_actions_server.xml",
        "data/base_automation.xml",
        "data/tms_data.xml",
        "views/account_invoice_views.xml",
        "views/fleet_vehicle_model_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_view.xml",
        "views/sale_view.xml",
        "views/project_view.xml",
        "views/project_task_view.xml",
        "views/product_view.xml",
        "views/purchase_views.xml",
        "views/tms_equipment_view.xml",
        "views/tms_menu_view.xml",
        "views/tms_package.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tms/static/src/scss/kanban_view.scss",
            "tms/static/src/js/kanban_view.js",
        ],
    },
}

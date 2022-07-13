# Copyright 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "TMS Division",
    "summary": "Division for Transportation Management System (TMS)",
    "version": "13.0.1.0.0",
    "category": "Logistic",
    "website": "https://github.com/OCA/tms",
    "author": "Tecnativa, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "tms",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "views/tms_division.xml",
    ],
}

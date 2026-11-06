# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    gst_code = fields.Char(
        string="GST Code",
        index=True,
        copy=False,
        help="GST matching code for branch assignment (e.g. DL, CH, HR, MH).",
    )

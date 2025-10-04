from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    missing_valuation = fields.Boolean(string="Missing Valuation", default=False)

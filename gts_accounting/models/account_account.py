from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_tds = fields.Boolean(string="Is TDS Account?")
    is_vat = fields.Boolean(string="Is VAT Account?")

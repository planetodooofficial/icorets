from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_tds = fields.Boolean(string="Is TDS Account?")
    is_vat = fields.Boolean(string="Is VAT Account?")
    gstin_unit_id = fields.Many2one('res.partner', string="GSTIN Unit")

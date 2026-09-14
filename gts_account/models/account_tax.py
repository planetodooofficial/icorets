from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    section_name = fields.Many2one('section.tds', string='Section Name')
    exempt_limit = fields.Integer(string='Exempt Limit')
    deductee_type_id = fields.Many2one('account.deductee.type', string='Deductee Type', ondelete='restrict', copy=False)
    is_tds = fields.Boolean(string="Is TDS")
    is_a_default = fields.Boolean(string="Is a Default", default=False)
    gstin_unit_id = fields.Many2one('res.partner', string="GSTIN Unit")

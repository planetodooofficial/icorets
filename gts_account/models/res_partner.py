from odoo import models, fields


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    tds_tax_id = fields.Many2one('account.tax', string="TDS Tax")
    deductee_type_id = fields.Many2one('account.deductee.type', string='Deductee Type', copy=False)
    is_gstin = fields.Boolean(string="Is GSTIN")

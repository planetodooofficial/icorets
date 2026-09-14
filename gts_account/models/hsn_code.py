from odoo import models, fields, api


class AccountHsnCode(models.Model):
    _name = 'hsn.code'
    _rec_name = 'hsnsac_code'
    _description = 'HSN / SAC Code'

    hsnsac_code = fields.Char(string='HSN/SAC Code', required=True)
    description = fields.Char(string='Description')
    type = fields.Selection([
        ('s', 'Sales'),
        ('p', 'Purchase'),
    ], string='Type', required=True)
    taxes_id = fields.Many2one('account.tax', string='Tax', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, copy=False)
    is_active = fields.Boolean(string="Is Active", default=True)

    @api.onchange('type')
    def tax_domain(self):
        if self.type == 's':
            tax_sales = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('company_id', '=', self.company_id.id)])
            if tax_sales:
                return {'domain': {'taxes_id': [('id', 'in', tax_sales.ids)]}}
        elif self.type == 'p':
            tax_purchase = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id)])
            if tax_purchase:
                return {'domain': {'taxes_id': [('id', 'in', tax_purchase.ids)]}}
        return {'domain': {'taxes_id': []}}

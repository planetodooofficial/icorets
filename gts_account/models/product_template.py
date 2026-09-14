from odoo import models, fields, api


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    purchase_hsn = fields.Many2one('hsn.code', string='Purchase HSN', domain="[('type', '=', 'p')]")
    sale_hsn = fields.Many2one('hsn.code', string='Sales HSN', domain="[('type', '=', 's')]")
    sales_hsn_description = fields.Char(string='Sales HSN Description')
    purchase_hsn_description = fields.Char(string='Purchase HSN Description')

    @api.onchange('purchase_hsn')
    def _onchange_purchase_hsn(self):
        if self.purchase_hsn:
            self.purchase_hsn_description = self.purchase_hsn.description
            if self.purchase_hsn.taxes_id:
                self.supplier_taxes_id = [(6, 0, [self.purchase_hsn.taxes_id.id])]

    @api.onchange('sale_hsn')
    def _onchange_sale_hsn(self):
        if self.sale_hsn:
            if hasattr(self, 'l10n_in_hsn_code') and self.sale_hsn.hsnsac_code:
                self.l10n_in_hsn_code = self.sale_hsn.hsnsac_code
            self.sales_hsn_description = self.sale_hsn.description
            if self.sale_hsn.taxes_id:
                self.taxes_id = [(6, 0, [self.sale_hsn.taxes_id.id])]

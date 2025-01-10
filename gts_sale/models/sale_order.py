from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    po_date = fields.Date(string="PO Date")
    po_ex_date = fields.Date(string="PO Expiration Date")

    @api.constrains('client_order_ref')
    def _constraint_po_number(self):
        for rec in self:
            if rec.client_order_ref:
                temp = self.env['sale.order'].search(
                    [('client_order_ref', '=', self.client_order_ref), ('id', '!=', rec.id)])
                if temp:
                    raise UserError(_('Sale order with same PO Number already exist !!!'))
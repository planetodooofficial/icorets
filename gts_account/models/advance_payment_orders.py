from odoo import models, fields


class AdvanceOrder(models.Model):
    _name = 'advance.payment.orders'
    _description = 'Advance Payment Orders'

    sale_id = fields.Many2one('sale.order', string="Sales Order", domain=[('state', '=', 'sale')])
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", domain=[('state', '=', 'purchase')])
    partner_id = fields.Many2one('res.partner', string="Partner")
    payment_terms = fields.Many2one('account.payment.term', string="Payment Terms", readonly=True)
    order_amount = fields.Float(string="Order Amount", readonly=True)
    advance_amount = fields.Float(string="Advance Amount")
    payment_id = fields.Many2one('account.payment', string="Payment", auto_join=True, ondelete='cascade')

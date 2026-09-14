from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentWiz(models.TransientModel):
    _name = "payment.wiz"
    _description = "Register Advance / Partial Payment"

    journal_id = fields.Many2one('account.journal', string="Journal")
    payment_method_id = fields.Many2one('account.payment.method.line', string="Payment Method")
    amount = fields.Float(string="Amount")
    payment_date = fields.Date(string="Payment Date", default=fields.Date.context_today)
    memo = fields.Char(string="Memo")
    so_order_id = fields.Many2one('sale.order', string="Sales Order")
    po_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    so_term_id = fields.Many2one('payments.by.term', string="Sales Term")
    po_term_id = fields.Many2one('po.payments.term', string="Purchase Term")

    @api.onchange('journal_id')
    def get_payment_method(self):
        if self.journal_id:
            payment_type = 'inbound' if self.so_order_id else 'outbound'
            payment_method_lines = self.journal_id._get_available_payment_method_lines(payment_type)
            self.payment_method_id = payment_method_lines[0]._origin.id if payment_method_lines else False

    def create_payment(self):
        self.ensure_one()
        term_id = self.po_term_id or self.so_term_id
        if term_id and self.amount > term_id.value - term_id.amount_received:
            raise UserError(_("Payment amount is greater than partial term amount!"))
        order_id = self.so_order_id or self.po_order_id
        payment_type = 'inbound' if self.so_order_id else 'outbound'
        payment_method_lines = self.journal_id._get_available_payment_method_lines(payment_type)

        payment = self.env['account.payment'].create({
            'partner_id': order_id.partner_id.id,
            'payment_type': payment_type,
            'amount': self.amount,
            'date': self.payment_date,
            'ref': self.memo,
            'journal_id': self.journal_id.id,
            'payment_method_line_id': payment_method_lines[0]._origin.id if payment_method_lines else False,
            'currency_id': order_id.currency_id.id,
            'so_order_id': self.so_order_id.id if self.so_order_id else False,
            'po_order_id': self.po_order_id.id if self.po_order_id else False,
            'so_term_id': self.so_term_id.id if self.so_term_id else False,
            'po_term_id': self.po_term_id.id if self.po_term_id else False,
            'is_advance': True,
            'advance_order_ids': [(0, 0, {
                'sale_id': self.so_order_id.id if self.so_order_id else False,
                'purchase_id': self.po_order_id.id if self.po_order_id else False,
                'partner_id': order_id.partner_id.id,
                'payment_terms': order_id.payment_term_id.id if hasattr(order_id, 'payment_term_id') else False,
                'advance_amount': self.amount,
            })]
        })

        if term_id:
            term_id.amount_received += payment.amount
            term_id.payment_recv_date = self.payment_date
        payment.action_post()

        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': payment.id,
        }

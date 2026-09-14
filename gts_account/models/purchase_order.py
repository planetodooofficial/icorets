from odoo import models, fields, api, _
from datetime import date


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    payments_by_terms = fields.One2many('po.payments.term', 'po_id', string="Payments by Terms")
    to_check = fields.Boolean(string="To Check", tracking=True, copy=False, default=False)
    is_checked = fields.Boolean(string="Checked", tracking=True, copy=False, default=False)
    checker_id = fields.Many2one('res.users', string="Checker")
    gstin_id = fields.Many2one("res.partner", string="GSTIN Unit")
    l10n_in_journal_id = fields.Many2one('account.journal', string="Journal", domain="[('type', '=', 'purchase')]")

    @api.onchange('gstin_id')
    def _onchange_gstin_id(self):
        self.l10n_in_journal_id = False
        return {'domain': {'l10n_in_journal_id': [('type', '=', 'purchase')]}}

    def send_for_checking(self):
        self.ensure_one()
        return {
            'name': _('Send for Checker'),
            'res_model': 'send.checker',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def button_set_checked(self):
        for po in self:
            po.to_check = False
            po.is_checked = True

    def button_confirm(self):
        self.compute_payments_by_terms()
        return super().button_confirm()

    def compute_payments_by_terms(self):
        for order in self:
            if order.payment_term_id:
                order.payments_by_terms.unlink()
                values = []
                payment_terms = order.payment_term_id._compute_terms(
                    date_ref=order.date_order or fields.Date.today(),
                    currency=order.currency_id or order.company_id.currency_id,
                    tax_amount_currency=order.amount_tax,
                    tax_amount=order.amount_tax,
                    untaxed_amount_currency=order.amount_untaxed,
                    untaxed_amount=order.amount_untaxed,
                    company=order.company_id,
                    sign=1
                )
                term_lines = payment_terms.get('line_ids', []) if isinstance(payment_terms, dict) else payment_terms
                total_amount = order.amount_total or (order.amount_untaxed + order.amount_tax)
                percent_sum = 0.0
                for i, term in enumerate(term_lines):
                    line = order.payment_term_id.line_ids[i] if i < len(order.payment_term_id.line_ids) else False
                    term_desc = (line and line.desc) or term.get('desc') or (line and line.value) or ''
                    if line and line.value == 'percent':
                        percent = line.value_amount
                        percent_sum += percent
                    elif line and line.value == 'balance':
                        percent = max(0.0, 100.0 - percent_sum)
                    elif total_amount:
                        percent = round((term.get('company_amount', 0.0) / total_amount) * 100.0, 2)
                    else:
                        percent = term.get('percent', 0.0)
                    values.append((0, 0, {
                        'name': term_desc,
                        'percent': percent or 0.0,
                        'due_date': term.get('date'),
                        'value': term.get('company_amount', 0.0),
                        'po_id': order.id,
                        'company_id': order.company_id.id,
                    }))

                order.payments_by_terms = values


class POPaymentsByTerms(models.Model):
    _name = 'po.payments.term'
    _description = 'Purchase Payments by Term'
    _order = "sequence,id"

    name = fields.Char(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    po_id = fields.Many2one('purchase.order', string="Purchase Order", ondelete='cascade')
    value = fields.Float(string="Amount")
    percent = fields.Float(string="Amount in %")
    due_date = fields.Date(string="Due Date")
    payment_recv_date = fields.Date(string="Payment Date")
    amount_received = fields.Float(string="Amount Paid")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)

    def open_create_payment_wizard(self):
        self.ensure_one()
        res_id = self.env['payment.wiz'].sudo().create({
            'po_term_id': self.id,
            'po_order_id': self.po_id.id,
            'amount': self.value - self.amount_received,
            'payment_date': date.today(),
            'memo': f"Advance Payment for {self.po_id.name or ''}"
        })
        return {
            'name': _('Register Payment'),
            'res_model': 'payment.wiz',
            'view_mode': 'form',
            'target': 'new',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window'
        }

    def view_payments(self):
        self.ensure_one()
        payments = self.env['account.payment'].sudo().search([('po_term_id', '=', self.id)])
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('po_term_id', '=', self.id)],
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id
            })
        return action


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    hsn_id = fields.Many2one(
        'hsn.code',
        string='HSN / SAC Code',
        domain="[('company_id', '=', company_id), ('type', '=', 'p')]"
    )

    @api.onchange('hsn_id')
    def _onchange_hsn_id(self):
        if self.hsn_id and self.hsn_id.taxes_id:
            self.tax_ids = [(6, 0, [self.hsn_id.taxes_id.id])]

    @api.onchange('product_id')
    def _onchange_product_id_hsn(self):
        if self.product_id and self.product_id.purchase_hsn:
            self.hsn_id = self.product_id.purchase_hsn.id

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move=move)
        if self.product_id and self.product_id.purchase_hsn:
            res['hsn_id'] = self.product_id.purchase_hsn.id
        elif self.hsn_id:
            res['hsn_id'] = self.hsn_id.id
        return res

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class PaymentInherit(models.Model):
    _inherit = 'account.payment'

    partial_lines = fields.One2many('partial.line', 'payment_id', string="Partial Lines")
    pending_amt = fields.Float(string="Pending Amount", compute="compute_pending_amt")
    advance_order_ids = fields.One2many('advance.payment.orders', 'payment_id', string="Advance Orders")
    is_advance = fields.Boolean(string="Advance?", default=False)
    remarks = fields.Char(string='Remarks')
    payment_method_name = fields.Char(string='Payment Method Name', related='payment_method_id.name')
    beneficiary_name = fields.Char(string='Beneficiary Name', related='partner_id.name', store=True)
    acc_payee = fields.Boolean(string='Account Payee')
    so_order_id = fields.Many2one('sale.order', string="Sales Order")
    po_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    so_term_id = fields.Many2one('payments.by.term', string="Sales Payment Term")
    po_term_id = fields.Many2one('po.payments.term', string="Purchase Payment Term")
    to_check = fields.Boolean(string="To Check", tracking=True, copy=False, default=False)
    is_checked = fields.Boolean(string="Checked", tracking=True, copy=False, default=False)
    checker_id = fields.Many2one('res.users', string="Checker")
    destination_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Destination Journal',
        domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id), ('id', '!=', journal_id)]",
        check_company=True,
    )
    is_internal_transfer = fields.Boolean(
        string="Internal Transfer",
        readonly=False,
        store=True,
        tracking=True,
        compute="_compute_is_internal_transfer",
    )

    @api.depends('partner_id', 'journal_id', 'destination_journal_id')
    def _compute_is_internal_transfer(self):
        for payment in self:
            payment.is_internal_transfer = bool(
                payment.partner_id
                and payment.partner_id == payment.journal_id.company_id.partner_id
                and payment.destination_journal_id
            )
            if self.env.context.get('is_contra_entry'):
                payment.is_internal_transfer = True

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
        for payment in self:
            payment.to_check = False
            payment.is_checked = True

    def action_draft(self):
        res = super().action_draft()
        for payment in self:
            payment.to_check = False
            payment.is_checked = False
        return res

    @api.onchange('is_advance', 'partner_id')
    def unlink_advances(self):
        self.advance_order_ids.unlink()

    @api.onchange('payment_type')
    def reset_partial_lines(self):
        self.partial_lines = False

    @api.depends('amount', 'partial_lines.amount')
    def compute_pending_amt(self):
        for pay in self:
            amount = pay.amount - sum(pay.partial_lines.mapped('amount'))
            pay.pending_amt = amount

    def action_reconcile_lines(self):
        self.ensure_one()
        acc_type = 'asset_receivable' if self.payment_type == 'inbound' else 'liability_payable'
        payment_move_lines = self.move_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)
        if not payment_move_lines:
            raise ValidationError(_("No receivable/payable line found on the payment."))
        payment_move_line = payment_move_lines[0]
        for rec in self.partial_lines.filtered(lambda x: not x.reconciled_id and x.amount > 0 and x.state == 'against_ref'):
            move_lines = rec.move_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)
            if not move_lines:
                continue
            move_line_id = move_lines[0]
            data = {
                'amount': rec.amount,
                'credit_amount_currency': rec.amount,
                'debit_amount_currency': rec.amount,
                'max_date': datetime.now().date(),
                'debit_move_id': move_line_id.id if rec.move_id.move_type == 'out_invoice' else payment_move_line.id,
                'credit_move_id': payment_move_line.id if rec.move_id.move_type == 'out_invoice' else move_line_id.id,
            }
            reconciled_id = self.env['account.partial.reconcile'].create(data)
            rec.reconciled_id = reconciled_id.id
        payment_move_line._compute_amount_residual()

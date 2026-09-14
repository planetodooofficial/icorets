from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartialLines(models.Model):
    _name = 'partial.line'
    _description = 'Partial Reconciliation Line'

    state = fields.Selection([
        ('against_ref', 'Against Ref'),
        ('new_ref', 'New Ref'),
        ('advance', 'Advance'),
        ('on_account', 'On Account')
    ], string="State")
    entry_id = fields.Many2one('account.move', string="Entry", auto_join=True, domain=[('payment_state', 'in', ('not_paid', 'partial')), ('state', '=', 'posted')])
    payment_line = fields.Many2one('account.move.line', string="Payment Line")
    payment_residual_amt = fields.Float(string="Payment Residual Amount", compute="set_payment_residual_amt", store=True)
    move_id = fields.Many2one('account.move', string="Move")
    move_line = fields.Many2one('account.move.line', string="Invoice/Bill Line")
    payment_id = fields.Many2one('account.payment', string="Payment")
    partner_id = fields.Many2one('res.partner', string="Partner")
    move_amt = fields.Float(string="Move Amount", readonly=True)
    residual_amount = fields.Float(string="Residual Amount", readonly=True)
    amount = fields.Float(string="Amount")
    reconciled_id = fields.Many2one('account.partial.reconcile', string="Reconciliation")
    custom_payment_type = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ], string="Payment Type")
    description = fields.Char(string="Description")
    sale_order_id = fields.Many2one('sale.order', string="Sales Order", domain=[('state', 'in', ('draft', 'sent', 'sale'))])
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order", domain=[('state', 'in', ('draft', 'sent', 'purchase'))])

    @api.depends('payment_line', 'payment_line.amount_residual')
    def set_payment_residual_amt(self):
        for rec in self:
            rec.payment_residual_amt = rec.payment_line and abs(rec.payment_line.amount_residual) or 0.0

    @api.onchange('custom_payment_type')
    def reset_lines(self):
        self.sale_order_id = False
        self.purchase_order_id = False
        self.move_line = False
        self.move_id = False
        self.amount = 0.0

    @api.onchange('move_line')
    def set_move_line_domain(self):
        self.move_id = self.move_line and self.move_line.move_id.id or False
        self.residual_amount = self.move_line and abs(self.move_line.amount_residual) or 0.0
        self.move_amt = self.move_line and (self.move_line.debit + self.move_line.credit) or 0.0

    @api.onchange('sale_order_id')
    def set_sale_order_data(self):
        self.residual_amount = self.move_amt = self.sale_order_id and self.sale_order_id.amount_total or 0.0

    @api.onchange('purchase_order_id')
    def set_purchase_order_data(self):
        self.residual_amount = self.move_amt = self.purchase_order_id and self.purchase_order_id.amount_total or 0.0

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(PartialLines, self).fields_get(allfields, attributes)
        payment_type = self._context.get("default_custom_payment_type") or self._context.get('default_payment_type')
        if payment_type:
            if payment_type == 'inbound':
                domain = "[('move_id.move_type', 'in', ['out_invoice', 'entry']), ('move_id.state', '=', 'posted')," \
                         "('partner_id', '=', partner_id), ('amount_residual', '>', 0),('journal_id.type', 'in', ['general', 'sale'])]"
                name, move_amt = "Invoices", 'Invoice Amount'
            else:
                domain = "[('move_id.move_type', 'in', ['in_invoice', 'entry']), ('move_id.state', '=', 'posted')," \
                         "('partner_id', '=', partner_id), ('amount_residual', '<', 0), ('journal_id.type', 'in', ['general', 'purchase'])]"
                name, move_amt = "Bills", 'Bill Amount'
            if "move_line" in res:
                res["move_line"]["domain"] = domain
                res["move_line"]["string"] = name
            if "move_amt" in res:
                res["move_amt"]["string"] = move_amt
        return res

    @api.onchange('amount')
    def validate_amount(self):
        if self.amount < 0:
            raise ValidationError(_("Negative Amount is not allowed."))
        if self.amount > 0 and self.amount > self.residual_amount and self.state in ('against_ref', 'advance'):
            raise ValidationError(_("Amount should not be greater than Invoice/Bill Residual Amount."))
        elif self.amount > 0 and self.payment_residual_amt and self.amount > self.payment_residual_amt:
            raise ValidationError(_("Amount should not be greater than Payment Residual Amount."))

    @api.ondelete(at_uninstall=False)
    def verify_line_before_unlink(self):
        for rec in self:
            if rec.reconciled_id and rec.payment_id.state == 'posted':
                raise ValidationError(_('You cannot delete reconciled Lines'))

    def button_undo_reconciliation(self):
        for rec in self:
            if rec.reconciled_id:
                rec.reconciled_id.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PartialLines, self).create(vals_list)
        for res in records:
            if res.payment_id and not res.entry_id:
                res.entry_id = res.payment_id.move_id.id
                payment_type = 'asset_receivable' if res.entry_id.custom_payment_type == 'inbound' else 'liability_payable'
                payment_line = res.entry_id.line_ids.filtered(lambda x: x.account_id.account_type == payment_type)
                if len(payment_line) == 1:
                    res.payment_line = payment_line.id
        return records

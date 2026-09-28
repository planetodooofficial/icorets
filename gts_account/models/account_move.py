from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import date, datetime
from odoo.tools import float_is_zero


class AccountMove(models.Model):
    _inherit = 'account.move'

    # POD and Logistics Fields
    pod_document_id = fields.Binary(string="POD Document", attachment=False)
    pod_document_name = fields.Char(string="POD Document Name")
    customer_appointment_date = fields.Date(string="Customer Appointment Date")
    transporter_name = fields.Char(string="Transporter Name")
    lr_number = fields.Char(string="LR Number")
    logistic_number = fields.Char(string="L Number....")
    customer_delivery_number = fields.Char(string="Delivery Status")
    quick_commerce = fields.Char(string="Quick Commerce")
    po_expiry_date = fields.Date(string="PO Expiry Date")
    eta = fields.Char(string="ETA")
    timing = fields.Char(string="Timing")
    appointment = fields.Char(string="Appointment")
    cn_number = fields.Char(string="CN Number")
    dn_number = fields.Char(string="DN Number")
    old_po = fields.Char(string="Old PO")
    reason = fields.Char(string="Reason")
    remarks = fields.Char(string="Remarks")
    asn_no = fields.Char(string="ASN No")
    vin_po_no = fields.Char(string="VIN PO No")
    vin_asn_no = fields.Char(string="VIN ASN No")
    shortage = fields.Char(string="Shortage")
    logistic_charge = fields.Float(string="Logistic Charge", copy=False)
    credit_invoice_ids = fields.Many2many(
        'account.move',
        'credit_invoices_rel',
        'credit_id',
        'invoice_id',
        string='Select Invoice'
    )
    tracking_website = fields.Char(string="Tracking Website")
    without_sale_cogs = fields.Boolean(string="Without Sale Cogs", compute="_compute_without_sale_invoice", store=True)

    # Accounting & Checking / Reconciliation / TDS Fields
    partial_lines = fields.One2many('partial.line', 'entry_id', string="Partial Lines")
    pending_amt = fields.Float(string="Pending Amount", compute="compute_pending_amt")
    custom_payment_type = fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound')], string="Custom Payment Type")
    taxes_id = fields.Many2one('account.tax', copy=False, string="Applicable TDS", domain="[('is_tds', '=', True)]")
    deductee_type_id = fields.Many2one(string="Deductee Type", related='partner_id.deductee_type_id', readonly=True)
    total_invoiced = fields.Float(string="Total Invoiced", compute="compute_total_invoice")
    adv_pay_amt = fields.Float(string="Advance Payment Amount")
    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Payment Method',
        readonly=False,
        store=True,
        copy=False,
        compute='_compute_payment_method_line_id',
        domain="[('id', 'in', available_payment_method_line_ids)]",
    )
    available_payment_method_line_ids = fields.Many2many(
        'account.payment.method.line',
        compute='_compute_payment_method_line_fields'
    )
    is_checked = fields.Boolean(string="Checked", default=False, tracking=True, copy=False)
    to_check = fields.Boolean(string="To Check", default=False, tracking=True, copy=False)
    checker_id = fields.Many2one('res.users', string="Checker")
    gstin_id = fields.Many2one("res.partner", string="GSTIN Unit")

    @api.depends('suitable_journal_ids')
    def _compute_show_journal(self):
        for move in self:
            move.show_journal = len(move.suitable_journal_ids) > 0 or move.move_type == 'entry'

    @api.depends('invoice_line_ids.sale_line_ids')
    def _compute_without_sale_invoice(self):
        for move in self:
            print("----move", move)
            move.without_sale_cogs = bool(move.invoice_line_ids.mapped('sale_line_ids'))

    @api.onchange('credit_invoice_ids')
    def onchange_credit_invoice_ids(self):
        self.with_context(check_move_validity=False)
        self.invoice_line_ids = [(5, 0, 0)]
        line_vals = []
        for credit_invoice in self.credit_invoice_ids:
            for line in credit_invoice.invoice_line_ids:
                vals = {
                    'sequence': line.sequence,
                    'display_type': line.display_type or 'product',
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'account_id': line.account_id.id,
                    'tax_ids': [Command.set(line.tax_ids.ids)],
                }
                line_vals.append(Command.create(vals))
        self.invoice_line_ids = line_vals

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for res in records:
            if res.credit_invoice_ids:
                for line in res.line_ids:
                    if line.display_type == 'product' and line.credit == 0 and line.debit == 0:
                        line.unlink()
                for invoice in res.credit_invoice_ids:
                    invoice.write({'reversal_move_id': [(4, res.id)]})
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.credit_invoice_ids:
            for line in self.line_ids:
                if line.display_type == 'product' and line.credit == 0 and line.debit == 0:
                    line.unlink()
        return res

    @api.onchange("partner_id")
    def _onchange_salesperson(self):
        for move in self:
            if move.partner_id.user_id:
                move.invoice_user_id = move.partner_id.user_id.id

    def compute_total_invoice(self):
        fiscal_year = self.env['account.fiscal.year'].search([], limit=1) if 'account.fiscal.year' in self.env else False
        for move in self:
            domain = [('partner_id', '=', move.partner_id.id), ('move_type', '=', move.move_type), ('state', '=', 'posted')]
            if fiscal_year:
                domain.extend([('invoice_date', '>=', fiscal_year.date_from), ('invoice_date', '<=', fiscal_year.date_to)])
            move.total_invoiced = sum(self.env['account.move'].search(domain).mapped('amount_total'))

    def get_current_financial_year_moves(self):
        self.ensure_one()
        fiscal_year = self.env['account.fiscal.year'].search([], limit=1) if 'account.fiscal.year' in self.env else False
        domain = [('partner_id', '=', self.partner_id.id), ('move_type', '=', self.move_type), ('state', '=', 'posted')]
        if fiscal_year:
            domain.extend([('invoice_date', '>=', fiscal_year.date_from), ('invoice_date', '<=', fiscal_year.date_to)])
        move_ids = self.env['account.move'].search(domain)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', move_ids.ids)]
        }

    @api.onchange('taxes_id')
    def populate_in_line_items(self):
        if self.move_type == 'in_invoice' and self.taxes_id:
            for line in self.invoice_line_ids:
                if line.display_type in ('line_section', 'line_note'):
                    continue
                existing_taxes = line.tax_ids.ids
                if self.taxes_id.id not in existing_taxes:
                    line.tax_ids = [Command.link(self.taxes_id.id)]

    @api.depends('partial_lines.amount', 'adv_pay_amt')
    def compute_pending_amt(self):
        for move in self:
            move.pending_amt = move.adv_pay_amt - sum(move.partial_lines.mapped('amount'))

    def _get_valid_liquidity_accounts(self):
        return (
            self.journal_id.default_account_id.id,
            self.payment_method_line_id.payment_account_id.id,
            self.journal_id.company_id.account_journal_payment_debit_account_id.id,
            self.journal_id.company_id.account_journal_payment_credit_account_id.id,
        )

    @api.onchange('journal_id', 'payment_method_line_id', 'adv_pay_amt')
    def create_move_line(self):
        os_line = self.line_ids.filtered(lambda x: x.is_os_line)
        if self.custom_payment_type == 'inbound' and self.payment_method_line_id:
            account_id = self.payment_method_line_id.payment_account_id or self.journal_id.company_id.account_journal_payment_debit_account_id or self.journal_id.default_account_id
            if account_id:
                if not os_line:
                    self.line_ids = [(0, 0, {'account_id': account_id.id, 'debit': self.adv_pay_amt, 'is_os_line': True, 'partner_id': self.partner_id.id})]
                else:
                    self.update(dict(line_ids=[(1, os_line.id, {'account_id': account_id.id, 'debit': self.adv_pay_amt, 'partner_id': self.partner_id.id})]))
        elif self.custom_payment_type == 'outbound' and self.payment_method_line_id:
            account_id = self.payment_method_line_id.payment_account_id or self.journal_id.company_id.account_journal_payment_credit_account_id or self.journal_id.default_account_id
            if account_id:
                if not os_line:
                    self.line_ids = [(0, 0, {'account_id': account_id.id, 'credit': self.adv_pay_amt, 'is_os_line': True, 'partner_id': self.partner_id.id})]
                else:
                    self.update(dict(line_ids=[(1, os_line.id, {'account_id': account_id.id, 'credit': self.adv_pay_amt, 'partner_id': self.partner_id.id, 'amount_currency': -(self.adv_pay_amt)})]))

    @api.depends('journal_id', 'custom_payment_type')
    def _compute_payment_method_line_id(self):
        for pay in self:
            payment_type = pay.custom_payment_type
            if payment_type and pay.journal_id:
                available_payment_method_lines = pay.journal_id._get_available_payment_method_lines(payment_type)
                if pay.payment_method_line_id in available_payment_method_lines:
                    pay.payment_method_line_id = pay.payment_method_line_id
                elif available_payment_method_lines:
                    pay.payment_method_line_id = available_payment_method_lines[0]._origin
                else:
                    pay.payment_method_line_id = False
            else:
                pay.payment_method_line_id = False

    @api.depends('journal_id', 'custom_payment_type')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            payment_type = pay.custom_payment_type
            if payment_type and pay.journal_id:
                pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(payment_type)
            else:
                pay.available_payment_method_line_ids = False

    def action_reconcile_lines(self):
        self.ensure_one()
        if sum(self.partial_lines.filtered(lambda x: x.reconciled_id).mapped('amount')) == self.adv_pay_amt and self.partial_lines.filtered(lambda x: not x.reconciled_id):
            raise ValidationError(_('You cannot reconcile more Invoices/Bills.'))
        if sum(self.partial_lines.filtered(lambda x: x.reconciled_id).mapped('amount')) == self.adv_pay_amt:
            raise ValidationError(_('You have reconciled all the line items.'))
        if self.partial_lines.filtered(lambda x: x.payment_line.id not in self.line_ids.ids):
            raise ValidationError(_('Incorrect Payment Selected For Reconciliation.'))
        acc_type = 'asset_receivable' if self.custom_payment_type == 'inbound' else 'liability_payable'
        for rec in self.partial_lines.filtered(lambda x: not x.reconciled_id and x.amount > 0 and x.state == 'against_ref'):
            payment_move_line = rec.payment_line
            if abs(payment_move_line.amount_residual) < rec.amount:
                raise ValidationError(_(
                    'You are only allowed to reconcile %s %s for %s',
                    abs(payment_move_line.amount_residual),
                    payment_move_line.currency_id.symbol,
                    rec.move_id.name
                ))
            move_line_id = rec.move_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)[0]
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
        for move in self:
            move.to_check = False
            move.is_checked = True

    def reject(self):
        for move in self:
            move.is_checked = False
            move.to_check = False

    def button_draft(self):
        res = super().button_draft()
        for move in self:
            move.is_checked = False
            move.to_check = False
        return res

    @api.onchange('invoice_line_ids')
    def _onchange_quick_edit_line_ids(self):
        res = super()._onchange_quick_edit_line_ids()
        for line in self.invoice_line_ids:
            if line.product_id:
                move_type = line.move_id.move_type
                if move_type == 'in_invoice' and line.product_id.purchase_hsn:
                    line.hsn_id = line.product_id.purchase_hsn.id
                elif line.product_id.sale_hsn:
                    line.hsn_id = line.product_id.sale_hsn.id
        return res

    @api.onchange('partner_id', 'journal_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.move_type == 'in_invoice' and self.partner_id.tds_tax_id:
            self.taxes_id = self.partner_id.tds_tax_id.id
        return res

    def statement_partner_report(self):
        today = datetime.today()
        if today.month < 4:
            fy_start_year = today.year - 1
        else:
            fy_start_year = today.year

        date_from = date(fy_start_year, 4, 1).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        recipients = self.env['res.partner'].search([('email', '!=', False)])
        report = self.env.ref('account_reports.partner_ledger_report', raise_if_not_found=False)
        if not report:
            return

        report = report.sudo()
        mail_created = []
        for recipient in recipients:
            moves = self.env['account.move.line'].sudo().search([
                ('date', '<=', date_to),
                ('partner_id', '=', recipient.id),
                ('move_id.state', '=', 'posted'),
                ('account_id.account_type', '=', 'asset_receivable')
            ], order='date asc')
            due_amount = sum(moves.mapped('balance'))
            if due_amount > 0:
                body = (
                    "<p>Dear Sir/Madam,</p>\n\n "
                    f"<p>This is a reminder regarding the outstanding payment Due Amount: <b>{'{:,.2f}'.format(due_amount)}</b></p>"
                    "<p>As of today, we have not yet received the payment. Kindly make the payment.</p>"
                    "<p>For your reference, please find the attached Accounts Ledger.</p>"
                    "<br/><br/><br/>"
                    "<p>Note: This is a system generated email. If you have already paid, please share the payment details.</p>"
                )
                options = {
                    'date': {'date_from': date_from, 'date_to': date_to, 'filter': 'custom', 'mode': 'range'},
                    'hierarchy': False,
                    'unfold_all': True,
                    'unfolded': False,
                    'fiscal_position': 'all',
                    'filter_unfold_all': True,
                    'unposted_in_period': True,
                    'partner_ids': [recipient.id],
                    'selected_partner_ids': [recipient.id],
                    'params': {'partner_ids': [recipient.id], 'ignore_session': 'both'}
                }
                new_options = report._get_options(options)
                xlsx_data = report.export_to_xlsx(new_options, response=None)
                attachment = self.env['ir.attachment'].create({
                    'name': 'partner_ledger.xlsx',
                    'type': 'binary',
                    'datas': base64.b64encode(xlsx_data.get('file_content')),
                    'res_model': 'res.partner',
                    'res_id': recipient.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                mail_values = {
                    'subject': "Customer Account Ledger Report",
                    'body_html': body,
                    'email_to': recipient.email,
                    'attachment_ids': [(6, 0, [attachment.id])],
                }
                mail = self.env['mail.mail'].create(mail_values).send()
                mail_created.append(mail)

        if mail_created:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Email Sent.'),
                    'message': _('Mail Sent Successfully'),
                    'sticky': True,
                }
            }

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        lines_vals_list = []
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        for move in self:
            move = move.with_company(move.company_id)
            sale_lines = move.invoice_line_ids.mapped('sale_line_ids')
            if not sale_lines:
                continue
            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            anglo_saxon_price_ctx = move._get_anglo_saxon_price_ctx()

            for line in move.invoice_line_ids:
                if not line._eligible_for_cogs():
                    continue

                accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                sign = -1 if move.move_type == 'out_refund' else 1
                price_unit = line.with_context(anglo_saxon_price_ctx)._stock_account_get_anglo_saxon_price_unit()
                amount_currency = sign * line.quantity * price_unit

                if move.currency_id.is_zero(amount_currency) or float_is_zero(price_unit, precision_digits=price_unit_prec):
                    continue

                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'amount_currency': -amount_currency,
                    'account_id': debit_interim_account.id,
                    'display_type': 'cogs',
                    'tax_ids': [],
                })

                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'amount_currency': amount_currency,
                    'account_id': credit_expense_account.id,
                    'analytic_distribution': line.analytic_distribution,
                    'display_type': 'cogs',
                    'tax_ids': [],
                })
        return lines_vals_list

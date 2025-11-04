from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
import base64
import calendar
from datetime import date, timedelta, datetime
from odoo.tools import float_compare, float_is_zero

class AccountMove(models.Model):
    _inherit = 'account.move'

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
    old_po = fields.Char(string="Old Po")
    reason = fields.Char(string="Reason")
    remarks = fields.Char(string="Remarks")
    asn_no = fields.Char(string="ASN No")
    vin_po_no = fields.Char(string="VIN Po No")
    vin_asn_no = fields.Char(string="VIN ASN No")
    shortage = fields.Char(string="Shortage")
    logistic_charge = fields.Float(string="Logistic Charge", copy=False)

    credit_invoice_ids = fields.Many2many('account.move', 'credit_invoices_rel', 'credit_id', 'invoice_id',
                                          string='Select Invoice')
    tracking_website = fields.Char(string="Tracking Website")

    without_sale_cogs = fields.Boolean(string="Without Sale Cogs", compute="_compute_without_sale_invoice", store=True)

    @api.depends('invoice_line_ids.sale_line_ids')
    def _compute_without_sale_invoice(self):
        for move in self:
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

        print('\n\nline_vals+++++++++++++', line_vals)
        self.invoice_line_ids = line_vals

    @api.model
    def create(self, vals):
        res = super().create(vals)

        if res.credit_invoice_ids:
            for line in res.line_ids:
                if line.display_type == 'product' and line.credit == 0 and line.debit == 0:
                    line.unlink()
            for invoice in res.credit_invoice_ids:
                invoice.update({
                    'reversal_move_id': [(4, res.id)]
                })
        return res

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
            move.invoice_user_id = move.partner_id.user_id.id

    def _cal_customer_due(self, partner_id):
        query = '''
            SELECT SUM(aml.debit) - SUM(aml.credit) AS balance
            FROM account_move_line aml
            JOIN account_account acc ON aml.account_id = acc.id
            WHERE aml.partner_id = %s AND acc.account_type = 'receivable'
        '''
        self._cr.execute(query, (partner_id,))
        result = self._cr.fetchone()
        return result[0] or 0.0

    def statement_partner_report(self):
        subject = "Customer Account Ledger Report"

        today = datetime.today()

        if today.month < 4:
            # Jan, Feb, Mar → financial year started April 1st last year
            fy_start_year = today.year - 1
        else:
            # Apr to Dec → financial year started April 1st this year
            fy_start_year = today.year

        date_from = date(fy_start_year, 4, 1).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        # date_from = '2025-01-01'
        # date_to = '2026-12-31'
        # Get email recipients (you can customize this as needed)
        recipients = self.env['res.partner'].search([('email', '!=', False)])
        report = self.env['account.report'].sudo().browse(self.env.ref('account_reports.partner_ledger_report').id)
        mail_created = []
        for recipient in recipients:

            # move = self.env['account.move'].search([('partner_id', '=', recipient.id), ('move_type', '=', 'out_invoice'),
            #                                         ('invoice_date', '>=', date_from), ('invoice_date', '<=', date_to),
            #                                         ('state', '=', 'posted')])
            move = self.env['account.move.line'].sudo().search([('date', '<=', date_to),
                                                                ('partner_id', '=', recipient.id),
                                                                ('move_id.state', '=', 'posted'),
                                                                ('account_id.account_type', '=', 'asset_receivable')],
                                                               order='date asc')
            due_amount = sum(move.mapped('balance'))
            body = ("<p>Dear Sir/Mam,</p>\n\n "
                    f"<p>This is a reminder regarding the outstanding payment Due Amount:<b>{'{:,.2f}'.format(due_amount)}</b></p>"
                    "<p>As of today, we have not yet received the payment, kindly make the payment.</p>"
                    "<p>For your reference, please find the attached Invoice copy and Accounts Ledger.</p>"
                    "<br/><br/><br/>"
                    "<p>Note:- This is system generated Mail if you are already paid please share the payment details</p>"

                    )
            options = {
                'date': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'filter': 'custom',
                    'mode': 'range', },
                'hierarchy': False,
                'unfold_all': True,
                'unfolded': False,
                'fiscal_position': 'all',
                'filter_unfold_all': True,
                'unposted_in_period': True,
                'partner_ids': [recipient.id],
                'selected_partner_ids': [recipient.id],
                'params': {
                    'partner_ids': [recipient.id],
                    'ignore_session': 'both', }

            }
            if due_amount > 0:
                # new_options = report._get_options(options)
                new_options = report.sudo()._get_options(options)
                xlsx_data = report.sudo().export_to_xlsx(new_options, response=None)
                attachment = self.env['ir.attachment'].create({
                    'name': 'partner_ledger.xlsx',
                    'type': 'binary',
                    'datas': base64.b64encode(xlsx_data.get('file_content')),
                    # 'datas': xlsx_data.get('file_content'),
                    'res_model': 'res.partner',
                    'res_id': recipient.id,
                    'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                mail_values = {
                    'subject': subject,
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

    #Override base function
    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        for move in self:
            # Make the loop multi-company safe when accessing models like product.product
            move = move.with_company(move.company_id)
            # if sale not link with invoice don't create cogs entry
            sale_lines = move.invoice_line_ids.mapped('sale_line_ids')
            if not sale_lines:
                continue
            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            anglo_saxon_price_ctx = move._get_anglo_saxon_price_ctx()

            for line in move.invoice_line_ids:
                # Filter out lines being not eligible for COGS.
                if not line._eligible_for_cogs():
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                # Compute accounting fields.
                sign = -1 if move.move_type == 'out_refund' else 1
                price_unit = line.with_context(anglo_saxon_price_ctx)._stock_account_get_anglo_saxon_price_unit()
                amount_currency = sign * line.quantity * price_unit

                if move.currency_id.is_zero(amount_currency) or float_is_zero(price_unit, precision_digits=price_unit_prec):
                    continue

                # Add interim account line.
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

                # Add expense account line.
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

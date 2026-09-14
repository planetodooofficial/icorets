import base64
from num2words import num2words
from odoo import models, fields, api, _


class AccountMoveInheritClass(models.Model):
    _inherit = 'account.move'

    no_of_cartons = fields.Char('No of Cartons')
    grn_names = fields.Char(string='GRN Names', help='Names of associated GRNs')
    check_amount_in_words = fields.Char(compute='_amt_in_words', string='Amount in Words')
    event = fields.Char('Event')
    type_s = fields.Selection([
        ('sor', 'SOR'),
        ('outwrite', 'Outright'),
        ('sample', 'Sample'),
        ('sp_player', 'Sponsored Player'),
    ])
    cust_code = fields.Char("Code", compute="_compute_cust_code", store=True)
    tot_line_qty = fields.Integer(string="Total Line Qty", compute="_tot_line_qty")

    # Related fields for address
    partner_id_street = fields.Char('Inv Street', related='partner_id.street')
    partner_id_street2 = fields.Char('Inv Street2', related='partner_id.street2')
    partner_id_city = fields.Char('Inv City', related='partner_id.city')
    partner_id_state = fields.Many2one('res.country.state', 'Inv State', related='partner_id.state_id')
    partner_id_zip = fields.Char('Inv Zip', related='partner_id.zip')
    partner_id_country = fields.Many2one('res.country', 'Inv Country', related='partner_id.country_id')

    partner_shipping_id_street = fields.Char('Del Street', related='partner_shipping_id.street')
    partner_shipping_id_street2 = fields.Char('Del Street2', related='partner_shipping_id.street2')
    partner_shipping_id_city = fields.Char('Del City', related='partner_shipping_id.city')
    partner_shipping_id_state = fields.Many2one('res.country.state', 'Del State',
                                                related='partner_shipping_id.state_id')
    partner_shipping_id_zip = fields.Char('Del Zip', related='partner_shipping_id.zip')
    partner_shipping_id_country = fields.Many2one('res.country', 'Del Country',
                                                  related='partner_shipping_id.country_id')

    # new selection field of address for credit note
    shipping_id_credit = fields.Many2one('res.partner', string='Ship To')
    dispatch_partner_id = fields.Many2one('res.partner', string='Dispatch Address')

    def open_update_partner_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Partner Wizard',
            'res_model': 'journal.partner.update.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends('invoice_line_ids.quantity')
    def _tot_line_qty(self):
        for move in self:
            move.tot_line_qty = sum(move.invoice_line_ids.mapped('quantity'))

    # Added default get for false journal
    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveInheritClass, self).default_get(fields_list)
        if res.get('move_type') in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
            res['journal_id'] = False
        return res

    # Onchange for journal through gstin
    @api.onchange('gstin_id')
    def onchange_gstin_id(self):
        domain = []
        if self.move_type == "out_invoice":
            domain = [('type', '=', 'sale')]
            if self.gstin_id and hasattr(self.env['account.journal'], 'l10n_in_gstin_partner_id'):
                domain = [('l10n_in_gstin_partner_id.vat', '=', self.gstin_id.vat), ('type', '=', 'sale')]
                journal_ids = self.env['account.journal'].search([("l10n_in_gstin_partner_id", '=', self.gstin_id.id),
                                                                  ('type', '=', 'sale')])
                self.journal_id = False
                if len(journal_ids) == 1:
                    self.journal_id = journal_ids.id
            else:
                self.journal_id = False
        elif self.move_type == "in_invoice":
            domain = [('type', '=', 'purchase')]
            if self.gstin_id and hasattr(self.env['account.journal'], 'l10n_in_gstin_partner_id'):
                domain = [('l10n_in_gstin_partner_id.vat', '=', self.gstin_id.vat), ('type', '=', 'purchase')]
                journal_ids = self.env['account.journal'].search([("l10n_in_gstin_partner_id", '=', self.gstin_id.id),
                                                                  ('type', '=', 'purchase')])
                self.journal_id = False
                if len(journal_ids) == 1:
                    self.journal_id = journal_ids.id
            else:
                self.journal_id = False
        else:
            if self._context.get('default_custom_payment_type'):
                domain = [('type', '=', 'bank')]
            else:
                domain = [('company_id', '=', self.env.company.id)]

        return {'domain': {'journal_id': domain}}

    @api.depends("partner_id")
    def _compute_cust_code(self):
        for rec in self:
            if rec.partner_id:
                rec.cust_code = rec.partner_id.cust_alias_name

    # Function for amount in indian words
    @api.depends('amount_total')
    def _amt_in_words(self):
        for rec in self:
            rec.check_amount_in_words = num2words(str(rec.amount_total), lang='en_IN').replace(',', '').replace('and',
                                                                                                                '').replace(
                'point', 'and paise').replace('thous', 'thousand')

    def action_invoice_sent(self):
        # OVERRIDE
        rslt = super(AccountMoveInheritClass, self).action_invoice_sent()
        if self.partner_id.user_id:
            rslt['context']['default_partner_cc_ids'] = self.partner_id.user_id.partner_id.ids
        return rslt

    def send_daily_tax_invoice_report(self):
        for invoice in self:
            if invoice.lr_number and invoice.partner_id.email:
                pdf_content = self.env["ir.actions.report"]._render_qweb_pdf('icorets.taxes_invoice_report', invoice.id)[0]
                attachment = self.env['ir.attachment'].create({
                    'name': f'Tax Invoice - {invoice.name}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'mimetype': 'application/pdf'
                })
                # Send email
                mail_values = {
                    'subject': f'Tax Invoice - {invoice.name}',
                    'body_html': f'''<p>Dear LOGY XPRESS,
                                    Here is your invoice <b>{invoice.name}</b> (with reference: <b>{invoice.ref}</b>) amounting in <b>{invoice.amount_total}</b> from {invoice.gstin_id.name}. Please remit the payment as per the payment terms.<br/><br/><br/>
                                    <b>Transporter details<b/><br/>
                                    LR No. {invoice.lr_number}<br/>
                                    Name: {invoice.partner_id.name} <br/>
                                    Tracking website : {invoice.tracking_website} <br/>
                                    Do not hesitate to contact us if you have any questions.</p>''',
                    'email_to': invoice.partner_id.email,
                    'attachment_ids': [(6, 0, [attachment.id])],
                }
                if invoice.partner_id.user_id.partner_id.email:
                    mail_values['email_cc'] = invoice.partner_id.user_id.partner_id.email
                self.env['mail.mail'].create(mail_values).send()


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    tax_amount_line = fields.Monetary(string='Total Amount', readonly=True,
                                      compute="check_tax_amount", currency_field='currency_id')
    myntra_sku_code = fields.Char(string="Myntra SKU Code", copy=False)
    remarks = fields.Text('Remarks')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')
    ean_code = fields.Char(string='Ean Code', related='product_id.barcode')
    size = fields.Char(string='Size', related='product_id.size')
    color = fields.Char(string='Color', related='product_id.color')

    @api.depends('product_id', 'journal_id')
    def _compute_name(self):
        super()._compute_name()
        for line in self:
            if line.product_id:
                product = line.product_id
                if product.default_code:
                    name = f"[{product.default_code}] {product.name}"
                else:
                    name = f"{product.name or ''}"
                if line.journal_id.type == 'sale' and product.description_sale:
                    name += f"\n{product.description_sale}"
                elif line.journal_id.type == 'purchase' and product.description_purchase:
                    name += f"\n{product.description_purchase}"
                line.name = name

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            line.quantity = abs(line.quantity)
            line.price_unit = abs(line.price_unit)
        super()._compute_totals()

    # For updating tax amount
    @api.depends('tax_ids')
    def check_tax_amount(self):
        for rec in self:
            if rec.tax_ids:
                tax_amount_line = 0
                for tax in rec.tax_ids:
                    tax_amount_line += (rec.price_unit * tax.amount) / 100
                rec.tax_amount_line = rec.quantity * tax_amount_line
            else:
                rec.tax_amount_line = 0

    # For getting size
    def fetch_size(self):
        lst = []
        for rec in self:
            if rec.product_id.product_template_attribute_value_ids:
                i = 0
                for size in rec.product_id.product_template_attribute_value_ids:
                    if i % 2 != 0:
                        lst.append(size.name)
                    i += 1
        if len(lst) > 0:
            return lst[0]

    # Fetch Color
    def fetch_color(self):
        lst = []
        for rec in self:
            if rec.product_id.product_template_attribute_value_ids:
                i = 0
                for color in rec.product_id.product_template_attribute_value_ids:
                    if i % 2 == 0:
                        lst.append(color.name)
                    i += 1
        if len(lst) > 0:
            return lst[0]

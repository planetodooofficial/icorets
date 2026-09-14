from odoo import models, fields, api, _
from datetime import date


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    payments_by_terms = fields.One2many('payments.by.term', 'order_id', string="Payments by Terms")
    gstin_id = fields.Many2one("res.partner", string="GSTIN Unit")

    @api.onchange('gstin_id')
    def _onchange_gstin_id(self):
        self.journal_id = False
        if self.gstin_id:
            domain = [('type', '=', 'sale')]
            return {'domain': {'journal_id': domain}}

    def get_fiscal_position(self):
        buyer_state = self.partner_shipping_id.state_id or self.partner_invoice_id.state_id or self.partner_id.state_id
        buyer_country = self.partner_shipping_id.country_id or self.partner_invoice_id.country_id or self.partner_id.country_id
        seller_state = False

        # 1. Check journal_id on sale order
        if self.journal_id:
            if '(MH)' in (self.journal_id.name or '') or ' MH' in (self.journal_id.name or '') or 'MH' in (self.journal_id.code or ''):
                seller_state = self.env['res.country.state'].search([('code', '=', 'MH'), ('country_id.code', '=', 'IN')], limit=1)
            elif '(DL)' in (self.journal_id.name or '') or ' DL' in (self.journal_id.name or '') or 'DL' in (self.journal_id.code or ''):
                seller_state = self.env['res.country.state'].search([('code', '=', 'DL'), ('country_id.code', '=', 'IN')], limit=1)
            elif '(CH)' in (self.journal_id.name or '') or ' CH' in (self.journal_id.name or '') or 'CH' in (self.journal_id.code or ''):
                seller_state = self.env['res.country.state'].search([('code', '=', 'TN'), ('country_id.code', '=', 'IN')], limit=1)
            elif self.journal_id.company_id and self.journal_id.company_id.state_id:
                seller_state = self.journal_id.company_id.state_id
            elif self.journal_id.company_id and self.journal_id.company_id.partner_id.state_id:
                seller_state = self.journal_id.company_id.partner_id.state_id

        # 2. GSTIN Unit on sale order
        if not seller_state and self.gstin_id and self.gstin_id.state_id:
            seller_state = self.gstin_id.state_id

        # 3. Warehouse partner state
        if not seller_state and self.warehouse_id and self.warehouse_id.partner_id.state_id:
            seller_state = self.warehouse_id.partner_id.state_id

        # 4. Company state fallback
        if not seller_state and self.company_id.state_id:
            seller_state = self.company_id.state_id
        if not seller_state and self.company_id.partner_id.state_id:
            seller_state = self.company_id.partner_id.state_id

        fpos = None
        if buyer_country and buyer_country.code != 'IN':
            fpos = self.env['account.fiscal.position'].search([
                ('company_id', 'in', [self.company_id.id, False]),
                ('name', '=ilike', 'Export%')
            ], limit=1)

        is_intra = bool(seller_state and buyer_state and seller_state.id == buyer_state.id)
        if not fpos:
            if is_intra:
                if seller_state and seller_state.code:
                    fpos = self.env['account.fiscal.position'].search([
                        ('company_id', 'in', [self.company_id.id, False]),
                        ('name', '=ilike', f'{seller_state.code}-Intra%')
                    ], limit=1)
                if not fpos:
                    fpos = self.env['account.fiscal.position'].search([
                        ('company_id', 'in', [self.company_id.id, False]),
                        ('name', '=ilike', 'Intra%')
                    ], limit=1)
            else:
                if seller_state and seller_state.code:
                    fpos = self.env['account.fiscal.position'].search([
                        ('company_id', 'in', [self.company_id.id, False]),
                        ('name', '=ilike', f'{seller_state.code}-Inter%')
                    ], limit=1)
                if not fpos:
                    fpos = self.env['account.fiscal.position'].search([
                        ('company_id', 'in', [self.company_id.id, False]),
                        ('name', '=ilike', 'Inter%')
                    ], limit=1)

        if not fpos:
            fpos = self.env['account.fiscal.position'].with_company(self.company_id)._get_fiscal_position(
                self.partner_id, self.partner_shipping_id
            )

        return fpos.id if fpos else False

    @api.onchange('journal_id', 'partner_id', 'partner_shipping_id', 'gstin_id', 'warehouse_id')
    def set_order_line(self):
        fpos_id = self.get_fiscal_position()
        if fpos_id:
            self.fiscal_position_id = fpos_id
        for line in self.order_line:
            if line.product_id:
                taxes = line.product_id.taxes_id._filter_taxes_by_company(line.company_id or self.company_id)
                if self.fiscal_position_id:
                    taxes = self.fiscal_position_id.map_tax(taxes)
                line.tax_ids = taxes

    @api.onchange('payment_term_id')
    def compute_payments_by_terms(self):
        for order in self:
            order.payments_by_terms = False
            values = []
            if order.payment_term_id:
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
                        'order_id': order.id,
                        'company_id': order.company_id.id,
                    }))

                order.payments_by_terms = values


class PaymentsByTerms(models.Model):
    _name = 'payments.by.term'
    _description = 'Sales Payments by Term'
    _order = "sequence,id"

    name = fields.Char(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    order_id = fields.Many2one('sale.order', string="Sales Order", ondelete='cascade')
    value = fields.Float(string="Amount")
    percent = fields.Float(string="Amount in %")
    due_date = fields.Date(string="Due Date")
    payment_recv_date = fields.Date(string="Payment Received Date")
    amount_received = fields.Float(string="Amount Received")
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
            'so_term_id': self.id,
            'so_order_id': self.order_id.id,
            'amount': self.value - self.amount_received,
            'payment_date': date.today(),
            'memo': f"Advance Payment for {self.order_id.name or ''}"
        })
        return {
            'name': _('Register Payment'),
            'res_model': 'payment.wiz',
            'view_mode': 'form',
            'target': 'new',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window',
        }

    def view_payments(self):
        self.ensure_one()
        payments = self.env['account.payment'].sudo().search([('so_term_id', '=', self.id)])
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('so_term_id', '=', self.id)],
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id
            })
        return action


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    hsn_id = fields.Many2one(
        'hsn.code',
        string='HSN / SAC Code',
        domain="[('company_id', '=', company_id), ('type', '=', 's')]"
    )

    @api.onchange('hsn_id')
    def _onchange_hsn_id(self):
        if self.hsn_id and self.hsn_id.taxes_id:
            self.tax_ids = [(6, 0, [self.hsn_id.taxes_id.id])]

    @api.onchange('product_id')
    def _onchange_product_id_hsn(self):
        if self.product_id and self.product_id.sale_hsn:
            self.hsn_id = self.product_id.sale_hsn.id

    def _prepare_invoice_line(self, **optional_values):
        result = super()._prepare_invoice_line(**optional_values)
        if self.product_id and self.product_id.sale_hsn:
            result['hsn_id'] = self.product_id.sale_hsn.id
        elif self.hsn_id:
            result['hsn_id'] = self.hsn_id.id
        return result

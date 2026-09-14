from num2words import num2words
from odoo import models, fields, api, _


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    check_amount_in_words = fields.Char(compute='_amt_in_words', string='Amount in Words')
    location_id = fields.Many2one(
        'stock.location', ' Source Location',
        ondelete='restrict', index=True, check_company=True)
    event = fields.Char('Event')
    l10n_in_journal_id = fields.Many2one('account.journal', string="Journal", related='journal_id', readonly=False, store=True)
    is_fo = fields.Boolean("Is Fo", copy=False, default=False)
    fo_id = fields.Many2one("sale.order", string="FO ID")
    fo_so_count = fields.Integer()
    gstin_id = fields.Many2one('res.partner', 'GSTIN')
    l10n_in_gst_treatment = fields.Selection(related='partner_id.l10n_in_gst_treatment', string="GST Treatment", readonly=False, store=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')

    # Related fields for address
    partner_invoice_id_street = fields.Char('Inv Street', related='partner_invoice_id.street')
    partner_invoice_id_street2 = fields.Char('Inv Street2', related='partner_invoice_id.street2')
    partner_invoice_id_city = fields.Char('Inv City', related='partner_invoice_id.city')
    partner_invoice_id_state = fields.Many2one('res.country.state', 'Inv State', related='partner_invoice_id.state_id')
    partner_invoice_id_zip = fields.Char('Inv Zip', related='partner_invoice_id.zip')
    partner_invoice_id_country = fields.Many2one('res.country', 'Inv Country', related='partner_invoice_id.country_id')

    partner_shipping_id_street = fields.Char('Del Street', related='partner_shipping_id.street')
    partner_shipping_id_street2 = fields.Char('Del Street2', related='partner_shipping_id.street2')
    partner_shipping_id_city = fields.Char('Del City', related='partner_shipping_id.city')
    partner_shipping_id_state = fields.Many2one('res.country.state', 'Del State',
                                                related='partner_shipping_id.state_id')
    partner_shipping_id_zip = fields.Char('Del Zip', related='partner_shipping_id.zip')
    partner_shipping_id_country = fields.Many2one('res.country', 'Del Country',
                                                  related='partner_shipping_id.country_id')
    reason_id = fields.Many2one('reason.reason')
    desc = fields.Char('Description')
    is_short_close = fields.Boolean(store=True)
    closer_date = fields.Datetime()

    @api.depends('amount_total')
    def _amt_in_words(self):
        for rec in self:
            rec.check_amount_in_words = num2words(str(rec.amount_total), lang='en_IN').replace(',', '').replace('and',
                                                                                                                '').replace(
                'point', 'and paise').replace('thous', 'thousand')

    def action_view_fo_so(self):
        search_so = self.env["sale.order"].search([('fo_id', '=', self.id)])
        return {
            'name': _("Sale Orders"),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', search_so.ids)],
        }

    def short_close(self):
        view = self.env.ref('icorets.view_short_close_wizard')
        return {
            'name': 'Short Close',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'short.close',
            'view_id': view.id,
            'target': 'new',
        }

    def short_close_sale_order(self):
        view = self.env.ref('icorets.view_short_close_wizard')
        return {
            'name': 'Short Close',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'short.close',
            'view_id': view.id,
            'target': 'new',
            'context': {
                'sale_order_ids': self.ids
            }
        }

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderInherit, self).default_get(fields)
        active_ids = self.env.context.get('default_forecast_order')
        if active_ids:
            if 'is_fo' in fields:
                res['is_fo'] = True
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])
            if vals.get('name', _("New")) == _("New"):
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['date_order'])
                ) if 'date_order' in vals else None
                if vals.get('is_fo'):
                    vals['name'] = self.env['ir.sequence'].next_by_code('forecast.order',
                                                                        sequence_date=seq_date) or _("New")
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'sale.order', sequence_date=seq_date) or _("New")

        return super().create(vals_list)

    # For checking available quantity
    @api.onchange('location_id')
    def check_quantity(self):
        if self.location_id:
            for rec in self.order_line:
                prd_qty = self.env['stock.quant'].search(
                    [('product_id', '=', rec.product_id.id), ('location_id', '=', self.location_id.id)])
                if rec.product_id:
                    rec.stock_quantity = prd_qty.available_quantity

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderInherit, self)._prepare_invoice()
        invoice_vals['dispatch_partner_id'] = self.warehouse_id.partner_id.id
        invoice_vals['gstin_id'] = self.gstin_id.id
        return invoice_vals

    def action_open_fo_wiz(self):
        fo_line_lst = []

        top_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '1')], limit=1)
        medium_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '2')], limit=1)
        low_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '3')], limit=1)

        for rec in self.order_line:
            if rec.product_id:
                search_top_stock = self.env["stock.quant"].search(
                    [('product_id', '=', rec.product_id.id), ('warehouse_id', '=', top_priority_warehouse.id)],
                    limit=1)
                search_medium_stock = self.env["stock.quant"].search(
                    [('product_id', '=', rec.product_id.id), ('warehouse_id', '=', medium_priority_warehouse.id)],
                    limit=1)
                search_low_stock = self.env["stock.quant"].search(
                    [('product_id', '=', rec.product_id.id), ('warehouse_id', '=', low_priority_warehouse.id)],
                    limit=1)
                fo_line_vals = (0, 0, {
                    'product_id': rec.product_id.id,
                    'demand_qty': rec.product_uom_qty,
                    'top_priority_qty_avail': search_top_stock.available_quantity if search_top_stock.available_quantity > 0 else 0,
                    'medium_priority_qty_avail': search_medium_stock.available_quantity if search_medium_stock.available_quantity > 0 else 0,
                    'low_priority_qty_avail': search_low_stock.available_quantity if search_low_stock.available_quantity > 0 else 0,
                    'top_priority_warehouse': search_top_stock.location_id.id,
                    'medium_priority_warehouse': search_medium_stock.location_id.id,
                    'low_priority_warehouse': search_low_stock.location_id.id,
                    'so_line_id': rec.id,
                })
                fo_line_lst.append(fo_line_vals)
        fo_id = self.env["forecast.order"].create({'forecast_order_ids': fo_line_lst})
        return {
            'name': "FO Lines",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'forecast.order',
            'res_id': fo_id.id,
            'view_id': self.env.ref('icorets.view_forecast_order_wizard_form').id,
            'target': 'new'
        }

    def fo_action_confirm(self):
        top_priority_stock = {}
        medium_priority_stock = {}
        low_priority_stock = {}

        ''' To Get Priority Wise Warehouses '''
        top_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '1')], limit=1)
        medium_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '2')], limit=1)
        low_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '3')], limit=1)

        ''' To Get The Requirement of the Stock Product Wise '''
        stock_requirement = {}

        ''' To get the stock availability for that particular product warehouse wise '''
        for so_line in self.order_line:
            if so_line not in stock_requirement:
                stock_requirement[so_line] = so_line.product_uom_qty
            search_top_stock = self.env["stock.quant"].search(
                [('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', top_priority_warehouse.id)], limit=1)
            search_medium_stock = self.env["stock.quant"].search(
                [('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', medium_priority_warehouse.id)],
                limit=1)
            search_low_stock = self.env["stock.quant"].search(
                [('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', low_priority_warehouse.id)], limit=1)

            if search_top_stock:
                if search_top_stock.available_quantity > 0:
                    if so_line not in top_priority_stock:
                        top_priority_stock[so_line] = search_top_stock.available_quantity
                    else:
                        top_priority_stock[so_line] += search_top_stock.available_quantity

            if search_medium_stock:
                if search_medium_stock.available_quantity > 0:
                    if so_line not in medium_priority_stock:
                        medium_priority_stock[so_line] = search_medium_stock.available_quantity
                    else:
                        medium_priority_stock[so_line] += search_medium_stock.available_quantity

            if search_low_stock:
                if search_low_stock.available_quantity > 0:
                    if so_line not in low_priority_stock:
                        low_priority_stock[so_line] = search_low_stock.available_quantity
                    else:
                        low_priority_stock[so_line] += search_low_stock.available_quantity

        backorder_of_fo_lines = {}
        qty_to_reduce_from_fo_lines = {}

        ''' To create 'so' for top priority warehouse based on the availability in the stock '''
        if len(top_priority_warehouse.ids) > 0:
            top_priority_so_line_lst = []
            for so_line_obj, qty in top_priority_stock.items():
                if stock_requirement[so_line_obj] > 0:
                    prd_qty = 0
                    if qty == stock_requirement[so_line_obj]:
                        prd_qty = stock_requirement[so_line_obj]
                        top_priority_stock[so_line_obj] -= prd_qty
                    elif qty > stock_requirement[so_line_obj]:
                        prd_qty = stock_requirement[so_line_obj]
                        top_priority_stock[so_line_obj] -= prd_qty
                    elif qty < stock_requirement[so_line_obj]:
                        prd_qty = qty
                        top_priority_stock[so_line_obj] -= prd_qty

                        if so_line_obj not in medium_priority_stock and so_line_obj not in low_priority_stock:
                            remaining_prd_qty = stock_requirement[so_line_obj] - prd_qty
                            if remaining_prd_qty > 0:
                                if so_line_obj not in backorder_of_fo_lines:
                                    backorder_of_fo_lines[so_line_obj] = remaining_prd_qty
                                else:
                                    backorder_of_fo_lines[so_line_obj] += remaining_prd_qty

                    ''' To get the order line after stock assigned '''
                    if so_line_obj not in qty_to_reduce_from_fo_lines:
                        qty_to_reduce_from_fo_lines[so_line_obj] = prd_qty
                    else:
                        qty_to_reduce_from_fo_lines[so_line_obj] += prd_qty

                    if so_line_obj in stock_requirement:
                        stock_requirement[so_line_obj] -= prd_qty

                    top_priority_so_line_vals = (0, 0, {
                        'product_id': so_line_obj.product_id.id,
                        'product_template_id': so_line_obj.product_template_id.id,
                        'name': so_line_obj.name,
                        'product_uom_qty': prd_qty,
                        'product_uom_id': so_line_obj.product_uom_id.id,
                        'price_unit': so_line_obj.price_unit,
                        'tax_ids': [(4, tax.id) for tax in so_line_obj.tax_ids] if so_line_obj.tax_ids else False,
                        'discount': so_line_obj.discount,
                        'hsn_id': so_line_obj.hsn_id.id,
                    })
                    top_priority_so_line_lst.append(top_priority_so_line_vals)
            top_priority_so_vals = {
                'is_fo': False,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'warehouse_id': top_priority_warehouse.id,
                'order_line': top_priority_so_line_lst,
            }
            if len(top_priority_so_line_lst) >= 1:
                self.env["sale.order"].create(top_priority_so_vals)

        ''' To create 'so' for medium priority warehouse based on the availability in the stock '''
        if len(medium_priority_warehouse.ids) > 0:
            medium_priority_so_line_lst = []
            for so_line_obj, qty in medium_priority_stock.items():
                if stock_requirement[so_line_obj] > 0:
                    prd_qty = 0
                    if qty == stock_requirement[so_line_obj]:
                        prd_qty = stock_requirement[so_line_obj]
                        medium_priority_stock[so_line_obj] -= prd_qty
                    elif qty > stock_requirement[so_line_obj]:
                        prd_qty = stock_requirement[so_line_obj]
                        medium_priority_stock[so_line_obj] -= prd_qty
                    elif qty < stock_requirement[so_line_obj]:
                        prd_qty = qty
                        medium_priority_stock[so_line_obj] -= prd_qty

                        if so_line_obj not in low_priority_stock:
                            remaining_prd_qty = stock_requirement[so_line_obj] - prd_qty
                            if remaining_prd_qty > 0:
                                if so_line_obj not in backorder_of_fo_lines:
                                    backorder_of_fo_lines[so_line_obj] = remaining_prd_qty
                                else:
                                    backorder_of_fo_lines[so_line_obj] += remaining_prd_qty

                    ''' To get the orderline after stock assigned '''
                    if so_line_obj not in qty_to_reduce_from_fo_lines:
                        qty_to_reduce_from_fo_lines[so_line_obj] = prd_qty
                    else:
                        qty_to_reduce_from_fo_lines[so_line_obj] += prd_qty

                    if so_line_obj in stock_requirement:
                        stock_requirement[so_line_obj] -= prd_qty

                    medium_priority_so_line_vals = (0, 0, {
                        'product_id': so_line_obj.product_id.id,
                        'product_template_id': so_line_obj.product_template_id.id,
                        'name': so_line_obj.name,
                        'product_uom_qty': prd_qty,
                        'product_uom_id': so_line_obj.product_uom_id.id,
                        'price_unit': so_line_obj.price_unit,
                        'tax_ids': [(4, tax.id) for tax in so_line_obj.tax_ids] if so_line_obj.tax_ids else False,
                        'discount': so_line_obj.discount,
                        'hsn_id': so_line_obj.hsn_id.id,
                    })
                    medium_priority_so_line_lst.append(medium_priority_so_line_vals)
            medium_priority_so_vals = {
                'is_fo': False,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'warehouse_id': medium_priority_warehouse.id,
                'order_line': medium_priority_so_line_lst,
            }
            if len(medium_priority_so_line_lst) >= 1:
                self.env["sale.order"].create(medium_priority_so_vals)

        ''' To create 'so' for low priority warehouse based on the availability in the stock '''
        if len(low_priority_warehouse.ids) > 0:
            low_priority_so_line_lst = []
            for so_line_obj, qty in low_priority_stock.items():
                if stock_requirement[so_line_obj] > 0:
                    prd_qty = 0
                    if qty == stock_requirement[so_line_obj]:
                        prd_qty = stock_requirement[so_line_obj]
                        low_priority_stock[so_line_obj] -= prd_qty
                    elif qty > stock_requirement[so_line_obj]:
                        prd_qty = stock_requirement[so_line_obj]
                        low_priority_stock[so_line_obj] -= prd_qty
                    elif qty < stock_requirement[so_line_obj]:
                        prd_qty = qty
                        low_priority_stock[so_line_obj] -= prd_qty

                        remaining_prd_qty = stock_requirement[so_line_obj] - prd_qty
                        if remaining_prd_qty > 0:
                            if so_line_obj not in backorder_of_fo_lines:
                                backorder_of_fo_lines[so_line_obj] = remaining_prd_qty
                            else:
                                backorder_of_fo_lines[so_line_obj] += remaining_prd_qty

                    ''' To get the orderline after stock assigned '''
                    if so_line_obj not in qty_to_reduce_from_fo_lines:
                        qty_to_reduce_from_fo_lines[so_line_obj] = prd_qty
                    else:
                        qty_to_reduce_from_fo_lines[so_line_obj] += prd_qty

                    if so_line_obj in stock_requirement:
                        stock_requirement[so_line_obj] -= prd_qty

                    low_priority_so_line_vals = (0, 0, {
                        'product_id': so_line_obj.product_id.id,
                        'product_template_id': so_line_obj.product_template_id.id,
                        'name': so_line_obj.name,
                        'product_uom_qty': prd_qty,
                        'product_uom_id': so_line_obj.product_uom_id.id,
                        'price_unit': so_line_obj.price_unit,
                        'tax_ids': [(4, tax.id) for tax in so_line_obj.tax_ids] if so_line_obj.tax_ids else False,
                        'discount': so_line_obj.discount,
                        'hsn_id': so_line_obj.hsn_id.id,
                    })
                    low_priority_so_line_lst.append(low_priority_so_line_vals)
            low_priority_so_vals = {
                'is_fo': False,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'warehouse_id': low_priority_warehouse.id,
                'order_line': low_priority_so_line_lst,
            }
            if len(low_priority_so_line_lst) >= 1:
                self.env["sale.order"].create(low_priority_so_vals)

        for fo_line, qty in qty_to_reduce_from_fo_lines.items():
            fo_line.write({"product_uom_qty": qty})

        for so_line, so_line_prd_qty in stock_requirement.items():
            if so_line not in top_priority_stock and so_line not in medium_priority_stock and so_line not in low_priority_stock:
                if so_line not in backorder_of_fo_lines:
                    backorder_of_fo_lines[so_line] = so_line_prd_qty

        if len(backorder_of_fo_lines) >= 1:
            backorder_of_fo_lines_lst = []
            for bo_fo_line, bo_qty in backorder_of_fo_lines.items():
                bo_so_line_vals = (0, 0, {
                    'product_id': bo_fo_line.product_id.id,
                    'product_template_id': bo_fo_line.product_template_id.id,
                    'name': bo_fo_line.name,
                    'product_uom_qty': bo_qty,
                    'product_uom_id': bo_fo_line.product_uom_id.id,
                    'price_unit': bo_fo_line.price_unit,
                    'tax_ids': [(4, tax.id) for tax in bo_fo_line.tax_ids] if bo_fo_line.tax_ids else False,
                    'discount': bo_fo_line.discount,
                    'hsn_id': bo_fo_line.hsn_id.id,
                })
                backorder_of_fo_lines_lst.append(bo_so_line_vals)
            bo_so_vals = {
                'is_fo': True,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'warehouse_id': low_priority_warehouse.id,
                'order_line': backorder_of_fo_lines_lst,
            }
            if len(backorder_of_fo_lines_lst) >= 1:
                self.env["sale.order"].create(bo_so_vals)

        for so_line, so_line_prd_qty in stock_requirement.items():
            if so_line not in top_priority_stock and so_line not in medium_priority_stock and so_line not in low_priority_stock:
                unlink_record = self.order_line.filtered(lambda x: x if x.id == so_line.id else False)
                unlink_record.unlink()
        self.write({'state': 'done'})


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    stock_quantity = fields.Float('Stock Quantity')
    hsn_c = fields.Many2one(string='HSN Code', related='product_id.product_tmpl_id.sale_hsn')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')
    size = fields.Char(string='Size', related='product_id.size')
    color = fields.Char(string='Color', related='product_id.color')
    tax_amount_line = fields.Monetary(string='Total Amount', readonly=True,
                                      compute="check_tax_amount", currency_field='currency_id')
    sale_price_product = fields.Float(string='Product Sale Price', related='product_id.list_price')

    @api.depends('tax_ids')
    def check_tax_amount(self):
        for rec in self:
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    rec.tax_amount_line += (rec.price_unit * tax.amount) / 100
                    rec.tax_amount_line = rec.product_uom_qty * rec.tax_amount_line
            else:
                rec.tax_amount_line = 0

    @api.depends('product_id', 'linked_line_id', 'linked_line_ids')
    def _compute_name(self):
        for line in self:
            if not line.product_id and not line.is_downpayment:
                continue

            if line.is_downpayment:
                line.name = line._get_downpayment_description()
                continue

            product = line.product_id
            if product.default_code:
                name = f"[{product.default_code}] {product.name}"
            else:
                name = f"{product.name or ''}"

            if product.description_sale:
                name += f"\n{product.description_sale}"

            line.name = name

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.product_uom_qty < 0:
                line.product_uom_qty = abs(line.product_uom_qty)
            if line.price_unit < 0:
                line.price_unit = abs(line.price_unit)
        super()._compute_amount()

    def _prepare_invoice_line(self, **optional_values):
        result = super(SaleOrderLineInherit, self)._prepare_invoice_line(**optional_values)
        hsn = self.product_id.product_tmpl_id.sale_hsn
        result['hsn_id'] = hsn.id
        return result

    @api.onchange('product_id')
    def check_quantity(self):
        prd_qty = self.env['stock.quant'].search(
            [('product_id', '=', self.product_id.id), ('location_id', '=', self.order_id.location_id.id)])
        if self.product_id:
            self.stock_quantity = prd_qty.available_quantity

from lxml import etree

from num2words import num2words
from datetime import timedelta
import logging
from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
import datetime
from datetime import datetime
from io import BytesIO
from odoo.addons.iap import jsonrpc
import html2text
from odoo.tools.safe_eval import safe_eval


from odoo.exceptions import ValidationError
from odoo.tools import json, float_round, get_lang, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round



class ProductVariantInherit(models.Model):
    _inherit = "product.product"



    variants_ean_code = fields.Char('EAN Code')
    variant_article_code = fields.Char(string='Article Code')
    variants_asin = fields.Char('ASIN')
    variants_func_spo = fields.Char(related='product_tmpl_id.func_spo', string='Function / Sport')
    variants_gender = fields.Char(related='product_tmpl_id.gender', string='Gender')
    variants_tech_feat = fields.Char(related='product_tmpl_id.tech_feat', string='Technology / Features')
    variants_fsn = fields.Char('FSN')
    variant_cost = fields.Float('Invalid Cost')  # not used
    variant_packaging_cost = fields.Float('Packaging Cost')
    variant_total_cost = fields.Float('Total Cost')
    brand_id_rel = fields.Many2one(related='product_tmpl_id.brand_id', string="Brand")
    color = fields.Char('Color')
    size = fields.Char('Size')
    buin = fields.Char('BUIN')


    # Inherited and removed domain
    product_template_variant_value_ids = fields.Many2many('product.template.attribute.value',
                                                          relation='product_variant_combination',
                                                          string="Variant Values", ondelete='restrict', domain=[])

    # _sql_constraints = [
    #     ('asin_unique', 'unique(variant_asin)', "ASIN code can only be assigned to one variant product !"),
    #     ('ean_code_unique', 'unique(variant_ean_code)', "EAN code can only be assigned to one variant product !"),
    #     ('fsn_unique', 'unique(variant_fsn)', "FSN code can only be assigned to one variant product !"),
    # ]

    def name_get(self):
        return [(record.id, "%s" % (record.default_code if record.default_code else record.name)) for record in self]

    # For updating standard price by sum of cost and packaging cost
    @api.onchange('standard_price', 'variant_packaging_cost')
    def sum_cost(self):
        if self.standard_price and self.variant_packaging_cost:
            self.variant_total_cost = self.standard_price + self.variant_packaging_cost


class ProductInherit(models.Model):
    _inherit = "product.template"

    material = fields.Char('Moc')
    brand_id = fields.Many2one('product.brand', 'Brand')
    occasion = fields.Char('Event')
    style_code = fields.Char('Style Code')
    parent_buin = fields.Char('Parent buin')
    user_defined_miscallaneous1 = fields.Char('User Defined Miscallaneous1')
    user_defined_miscallaneous2 = fields.Char('User Defined Miscallaneous2')
    user_defined_miscallaneous3 = fields.Char('User Defined Miscallaneous3')
    user_defined_miscallaneous4 = fields.Char('User Defined Miscallaneous4')
    user_defined_miscallaneous5 = fields.Char('User Defined Miscallaneous5')
    # technical details

    manufactured_by = fields.Char('Manufactured By')
    marketed_by = fields.Char('Marketed By / Customer Care')
    length = fields.Float('Length (Dimensions)')
    width = fields.Float('width (Dimensions)')
    height = fields.Float('height (Dimensions)')
    weight = fields.Float('Weight (Dimensions)')
    cntry_of_origin = fields.Char('Country of Origin')
    manufacture_year = fields.Date('Manufacture Year')

    func_spo = fields.Char('Function / Sport')
    gender = fields.Char('Gender')
    tech_feat = fields.Char('Technology / Features')

    _sql_constraints = [
        ('buin_unique', 'unique(buin)', "BUIN code can only be assigned to one product !"),
    ]

    def name_get(self):
        return [(record.id, "%s" % (record.default_code if record.default_code else record.name)) for record in self]

    # Added func for hsn
    @api.onchange('sale_hsn')
    def set_hsn(self):
        if self.sale_hsn:
            self.l10n_in_hsn_code = self.sale_hsn.hsnsac_code
            # hsn_codepur = self.env['hsn.codes'].search([('hsnsac_code', '=', self.sale_hsn),('type','=','p')])
            # self.purchase_hsn = hsn_codepur.hsnsac_code
            # end


class ProductBrand(models.Model):
    _name = "product.brand"

    name = fields.Char('Brand Name')


class AccountMoveInheritClass(models.Model):
    _inherit = 'account.move'

    grn_names = fields.Char(string='GRN Names', help='Names of associated GRNs')
    check_amount_in_words = fields.Char(compute='_amt_in_words', string='Amount in Words')
    # warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    # po_no = fields.Char('PO No')
    event = fields.Char('Event')
    type_s = fields.Selection([
        ('sor', 'SOR'),
        ('outwrite', 'Outright'),
        ('sample', 'Sample'),
        ('sp_player', 'Sponsored Player'),

    ])
    cust_code = fields.Char("Code", compute="_compute_cust_code", store=True)
    tot_line_qty = fields.Integer(string="Total Line Qty",compute="_tot_line_qty")

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

    @api.depends('invoice_line_ids.quantity')
    def _tot_line_qty(self):
        for move in self:
            move.tot_line_qty = sum(move.invoice_line_ids.mapped('quantity'))

    # Added default get for false journal
    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveInheritClass, self).default_get(fields_list)
        res['journal_id'] = False
        return res

    # Onchange for journal through gstin
    @api.onchange('gstin_id')
    def onchange_gstin_id(self):
        domain = []
        if self.move_type == "out_invoice":
            domain = [('l10n_in_gstin_partner_id.vat', '=', self.gstin_id.vat), ('type', '=', 'sale')]
            journal_ids = self.env['account.journal'].search([("l10n_in_gstin_partner_id", '=', self.gstin_id.id),
                                                              ('type', '=', 'sale')])
            self.journal_id = False
            if len(journal_ids) == 1:
                self.journal_id = journal_ids.id
        elif self.move_type == "in_invoice":
            domain = [('l10n_in_gstin_partner_id.vat', '=', self.gstin_id.vat), ('type', '=', 'purchase')]
            journal_ids = self.env['account.journal'].search([("l10n_in_gstin_partner_id", '=', self.gstin_id.id),
                                                              ('type', '=', 'purchase')])
            self.journal_id = False
            if len(journal_ids) == 1:
                self.journal_id = journal_ids.id
        else:
            if self._context.get('default_custom_payment_type'):
                domain = [('type', '=', 'bank')]
            else:
                domain = [('company_id', '=', self.env.company.id)]

        # domain.append(('id', 'in', self.suitable_journal_ids.ids))
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
        for line in self:
            if line.display_type == 'payment_term':
                if line.move_id.payment_reference:
                    line.name = line.move_id.payment_reference
                elif not line.name:
                    line.name = ''
                continue
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
            if line.partner_id.lang:
                product = line.product_id.with_context(lang=line.partner_id.lang)
            else:
                product = line.product_id

            values = []
            if product.partner_ref:
                values.append(product.partner_ref)
            if line.journal_id.type == 'sale':
                if product.description_sale:
                    values.append(product.description_sale)
            elif line.journal_id.type == 'purchase':
                if product.description_purchase:
                    values.append(product.description_purchase)
            line.name = '\n'.join(values)

            if line.product_id.display_name:
                if line.product_id.default_code:
                    product_name = f"[{line.product_id.default_code}] {line.product_id.name}"
                    line.name = product_name
                else:
                    product_name = f"{line.product_id.name}"
                    line.name = product_name

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            line.quantity = abs(line.quantity)
            line.price_unit = abs(line.price_unit)
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            subtotal = line.quantity * line_discount_price_unit

            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal

    # For updaing tax amount
    @api.depends('tax_ids')
    def check_tax_amount(self):
        for rec in self:
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    rec.tax_amount_line += (rec.price_unit * tax.amount) / 100
                    rec.tax_amount_line = rec.quantity * rec.tax_amount_line
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


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    # po_no = fields.Char('PO No')
    no_of_cartons = fields.Char('No of Cartons')
    location_id = fields.Many2one(
        'stock.location', ' Source Location',
        ondelete='restrict', index=True, check_company=True)  # removed the required=True
    event = fields.Char('Event')
    l10n_in_journal_id = fields.Many2one('account.journal', string="Journal", default=False, required=True, store=True,
                                         readonly=True,
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    is_fo = fields.Boolean("Is Fo", copy=False, default=False)
    fo_id = fields.Many2one("sale.order", string="FO ID")
    fo_so_count = fields.Integer()
    gstin_id = fields.Many2one('res.partner', 'GSTIN')

    # Related fields for address
    partner_invoice_id_street = fields.Char('Inv Street', related='partner_invoice_id.street')
    partner_invoice_id_street2 = fields.Char('Inv Street2', related='partner_invoice_id.street2')
    partner_invoice_id_city = fields.Char('Inv City', related='partner_invoice_id.city')
    partner_invoice_id_state = fields.Many2one('res.country.state','Inv State', related='partner_invoice_id.state_id')
    partner_invoice_id_zip = fields.Char('Inv Zip', related='partner_invoice_id.zip')
    partner_invoice_id_country = fields.Many2one('res.country','Inv Country', related='partner_invoice_id.country_id')
    
    partner_shipping_id_street = fields.Char('Del Street', related='partner_shipping_id.street')
    partner_shipping_id_street2 = fields.Char('Del Street2', related='partner_shipping_id.street2')
    partner_shipping_id_city = fields.Char('Del City', related='partner_shipping_id.city')
    partner_shipping_id_state = fields.Many2one('res.country.state','Del State', related='partner_shipping_id.state_id')
    partner_shipping_id_zip = fields.Char('Del Zip', related='partner_shipping_id.zip')
    partner_shipping_id_country = fields.Many2one('res.country','Del Country', related='partner_shipping_id.country_id')


    def action_view_fo_so(self):
        search_so = self.env["sale.order"].search([('fo_id', '=', self.id)])
        return {
            'name': _("Sale Orders"),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', search_so.ids)],
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

    # For checking available  quantity
    @api.onchange('location_id')
    def check_quantity(self):
        if self.location_id:
            for rec in self.order_line:
                prd_qty = self.env['stock.quant'].search(
                    [('product_id', '=', rec.product_id.id), ('location_id', '=', self.location_id.id)])
                if rec.product_id:
                    rec.stock_quantity = prd_qty.available_quantity

    # Inherited for warehouse
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderInherit, self)._prepare_invoice()
        invoice_vals['dispatch_partner_id'] = self.warehouse_id.partner_id.id
        # invoice_vals['po_no'] = self.po_no
        invoice_vals['event'] = self.event
        invoice_vals['journal_id'] = self.l10n_in_journal_id.id
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

    ''' This Func is used for creating forecasted orders. '''
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
            search_top_stock = self.env["stock.quant"].search([('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', top_priority_warehouse.id)], limit=1)
            search_medium_stock = self.env["stock.quant"].search([('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', medium_priority_warehouse.id)], limit=1)
            search_low_stock = self.env["stock.quant"].search([('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', low_priority_warehouse.id)], limit=1)

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

                    # if so_line_obj in stock_requirement:
                    #     stock_requirement[so_line_obj] -= prd_qty
                    #
                    # if qty < stock_requirement[so_line_obj]:
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
                    # so_line_obj.product_uom_qty -= prd_qty

                    if so_line_obj in stock_requirement:
                        stock_requirement[so_line_obj] -= prd_qty

                    top_priority_so_line_vals = (0, 0, {
                        'product_id': so_line_obj.product_id.id,
                        'product_template_id': so_line_obj.product_template_id.id,
                        'name': so_line_obj.name,
                        'product_uom_qty': prd_qty,
                        'product_uom': so_line_obj.product_uom.id,
                        'price_unit': so_line_obj.price_unit,
                        'tax_id': [(4, tax_id.id) for tax_id in so_line_obj.tax_id] if so_line_obj.tax_id else False,
                        'discount': so_line_obj.discount,
                        'hsn_id': so_line_obj.hsn_id.id,
                    })
                    top_priority_so_line_lst.append(top_priority_so_line_vals)
            top_priority_so_vals = {
                'is_fo': False,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                # 'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'no_of_cartons': self.no_of_cartons,
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

                    # if so_line_obj in stock_requirement:
                    #     stock_requirement[so_line_obj] -= prd_qty
                    #
                    # if qty < stock_requirement[so_line_obj]:
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
                    # so_line_obj.product_uom_qty -= prd_qty

                    if so_line_obj in stock_requirement:
                        stock_requirement[so_line_obj] -= prd_qty

                    medium_priority_so_line_vals = (0, 0, {
                        'product_id': so_line_obj.product_id.id,
                        'product_template_id': so_line_obj.product_template_id.id,
                        'name': so_line_obj.name,
                        'product_uom_qty': prd_qty,
                        'product_uom': so_line_obj.product_uom.id,
                        'price_unit': so_line_obj.price_unit,
                        'tax_id': [(4, tax_id.id) for tax_id in so_line_obj.tax_id] if so_line_obj.tax_id else False,
                        'discount': so_line_obj.discount,
                        'hsn_id': so_line_obj.hsn_id.id,
                    })
                    medium_priority_so_line_lst.append(medium_priority_so_line_vals)
            medium_priority_so_vals = {
                'is_fo': False,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'no_of_cartons': self.no_of_cartons,
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

                    # if so_line_obj in stock_requirement:
                    #     stock_requirement[so_line_obj] -= prd_qty
                    #
                    # if qty < stock_requirement[so_line_obj]:
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
                    # so_line_obj.product_uom_qty -= prd_qty

                    if so_line_obj in stock_requirement:
                        stock_requirement[so_line_obj] -= prd_qty

                    low_priority_so_line_vals = (0, 0, {
                        'product_id': so_line_obj.product_id.id,
                        'product_template_id': so_line_obj.product_template_id.id,
                        'name': so_line_obj.name,
                        'product_uom_qty': prd_qty,
                        'product_uom': so_line_obj.product_uom.id,
                        'price_unit': so_line_obj.price_unit,
                        'tax_id': [(4, tax_id.id) for tax_id in so_line_obj.tax_id] if so_line_obj.tax_id else False,
                        'discount': so_line_obj.discount,
                        'hsn_id': so_line_obj.hsn_id.id,
                    })
                    low_priority_so_line_lst.append(low_priority_so_line_vals)
            low_priority_so_vals = {
                'is_fo': False,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'no_of_cartons': self.no_of_cartons,
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
                    'product_uom': bo_fo_line.product_uom.id,
                    'price_unit': bo_fo_line.price_unit,
                    'tax_id': [(4, tax_id.id) for tax_id in bo_fo_line.tax_id] if bo_fo_line.tax_id else False,
                    'discount': bo_fo_line.discount,
                    'hsn_id': bo_fo_line.hsn_id.id,
                })
                backorder_of_fo_lines_lst.append(bo_so_line_vals)
            bo_so_vals = {
                'is_fo': True,
                'partner_id': self.partner_id.id,
                'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
                'partner_shipping_id': self.partner_shipping_id.id,
                'partner_shipping_id': self.partner_shipping_id.id,
                'pricelist_id': self.pricelist_id.id,
                'payment_term_id': self.payment_term_id.id,
                'l10n_in_journal_id': self.l10n_in_journal_id.id,
                'event': self.event,
                'no_of_cartons': self.no_of_cartons,
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

    # Function for domain on location according to warehouse
    # @api.model
    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super(SaleOrderInherit, self).get_view(view_id,view_type, **options)
    #     if view_type == 'form':
    #         doc = etree.XML(res['arch'])
    #         domain = f"[('warehouse_id.code', '=', {self.location_id.location_id.name})]"
    #         for node in doc.xpath("//field[@name='location_id']"):
    #             node.set('domain', domain)
    #             test = node.get("modifiers")
    #             modifiers = json.loads(node.get("modifiers"))
    #             modifiers['domain'] = domain
    #             node.set("modifiers", json.dumps(modifiers))
    #         res['arch'] = etree.tostring(doc)
    #     return res

    # @api.onchange('field_id')
    # def onchange_field_id(self):
    #     relation_ids = [x.id for x in self.field_id.relation_ids]
    #     return {'domain': {'relation_id': [('id', 'in', relation_ids)]}}


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    stock_quantity = fields.Float('Stock Quantity')
    hsn_c = fields.Many2one(string='HSN Code', related='product_id.product_tmpl_id.sale_hsn')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')
    size = fields.Char(string='Size', related='product_id.size')
    color = fields.Char(string='Color', related='product_id.color')

    # Inherited for sale order line unit_price
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if line.qty_invoiced > 0:
                continue
            if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
                line.price_unit = 0.0
            else:
                pass
                # price = line.with_company(line.company_id)._get_display_price()
                # line.price_unit = line.product_id._get_tax_included_unit_price(
                #     line.company_id,
                #     line.order_id.currency_id,
                #     line.order_id.date_order,
                #     'sale',
                #     fiscal_position=line.order_id.fiscal_position_id,
                #     product_price_unit=price,
                #     product_currency=line.currency_id
                # )

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            if not line.order_partner_id.is_public:
                line = line.with_context(lang=line.order_partner_id.lang)
            name = line._get_sale_order_line_multiline_description_sale()
            if line.is_downpayment and not line.display_type:
                context = {'lang': line.order_partner_id.lang}
                dp_state = line._get_downpayment_state()
                if dp_state == 'draft':
                    name = _("%(line_description)s (Draft)", line_description=name)
                elif dp_state == 'cancel':
                    name = _("%(line_description)s (Canceled)", line_description=name)
                del context
            line.name = name
            if line.product_id.display_name:
                if line.product_id.default_code:
                    product_name = f"[{line.product_id.default_code}] {line.product_id.name}"
                    line.name = product_name
                else:
                    product_name = f"{line.product_id.name}"
                    line.name = product_name


    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.product_uom_qty < 0:
                line.product_uom_qty = (line.product_uom_qty) * -1
            if line.price_unit < 0:
                line.price_unit = (line.price_unit) * -1
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    # Populating HSN Field data in Invoice line item from product HSN
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

#CREATED FOR SAPAT REQUIREMENT
# class VendorbillWizard(models.TransientModel):
#     _name = "vendorbill.wizard"
#     _description = "Vendor Bill Wizard"
#
#     grn_name = fields.Many2many('stock.picking',"name", string='Select GRN', required=True)
#
#
#     @api.onchange('grn_name')
#     def onchange_grn_name(self):
#         active_purchase_id = self.env['purchase.order'].browse(self.env.context.get('active_ids', []))
#         return {'domain': {'grn_name': [('id', 'in', active_purchase_id.picking_ids.ids)]}}
#
#     def action_create_invoice(self):
#         precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
#         moves = self.env['account.move']
#         AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
#
#         # Group selected GRNs by associated purchase order
#         purchase_orders = {}
#         grn_names = []
#
#         for picking in self.grn_name:
#             if not picking.purchase_id:
#                 raise UserError(_('Selected GRN must be associated with a purchase order.'))
#             if picking.purchase_id not in purchase_orders:
#                 purchase_orders[picking.purchase_id] = []
#             purchase_orders[picking.purchase_id].append(picking)
#             grn_names.append(picking.name)
#
#         # Create vendor bills for each purchase order
#         for purchase_order, grouped_grns in purchase_orders.items():
#             # 1) Prepare invoice vals and clean-up the section lines
#             invoice_vals = self._prepare_invoice(purchase_order, grn_names)
#             sequence = 10
#             pending_section = None
#
#             for picking in grouped_grns:
#                 for line in picking.purchase_id.order_line.filtered(
#                         lambda line: line.product_id in picking.move_ids.product_id):
#                     if line.display_type == 'line_section':
#                         pending_section = line
#                         continue
#                     if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
#                         if pending_section:
#                             line_vals = pending_section._prepare_account_move_line()
#                             line_vals.update({'sequence': sequence})
#                             invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
#                             sequence += 1
#                             pending_section = None
#                         line_vals = line._prepare_account_move_line()
#                         line_vals.update({'sequence': sequence})
#                         invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
#                         sequence += 1
#
#             if invoice_vals['invoice_line_ids']:
#                 # 2) Create the invoice
#                 move = AccountMove.with_company(invoice_vals['company_id']).create(invoice_vals)
#                 moves |= move
#
#                 # 3) Some moves might actually be refunds: convert them if the total amount is negative
#                 # We do this after the moves have been created since we need taxes, etc. to know if the total
#                 # is actually negative or not
#                 if move.currency_id.round(move.amount_total) < 0:
#                     move.action_switch_invoice_into_refund_credit_note()
#
#         if not moves:
#             raise UserError(
#                 _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))
#
#         return self.action_view_invoice(moves)
#
#     def action_view_invoice(self, invoices=False):
#         """This function returns an action that displays existing vendor bills.
#         """
#         if not invoices:
#             invoices = self.env['account.move'].search([('purchase_id', 'in', self.grn_name.purchase_ids.ids)])
#
#         result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
#         # choose the view_mode accordingly
#         if len(invoices) > 1:
#             result['domain'] = [('id', 'in', invoices.ids)]
#         elif len(invoices) == 1:
#             res = self.env.ref('account.view_move_form', False)
#             form_view = [(res and res.id or False, 'form')]
#             if 'views' in result:
#                 result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
#             else:
#                 result['views'] = form_view
#             result['res_id'] = invoices.id
#         else:
#             result = {'type': 'ir.actions.act_window_close'}
#
#         return result
#
#     def _prepare_invoice(self, purchase_order, grn_names):
#         """Prepare the dict of values to create the new invoice for a purchase order.
#         """
#         self.ensure_one()
#         move_type = self._context.get('default_move_type', 'in_invoice')
#
#         partner_invoice = self.env['res.partner'].browse(purchase_order.partner_id.address_get(['invoice'])['invoice'])
#         partner_bank_id = purchase_order.partner_id.commercial_partner_id.bank_ids.filtered_domain(
#             ['|', ('company_id', '=', False), ('company_id', '=', purchase_order.company_id.id)])[:1]
#
#         invoice_vals = {
#             'ref': purchase_order.partner_ref or '',
#             'move_type': move_type,
#             'narration': purchase_order.notes,
#             'currency_id': purchase_order.currency_id.id,
#             'invoice_user_id': purchase_order.user_id and purchase_order.user_id.id or self.env.user.id,
#             'partner_id': partner_invoice.id,
#             'fiscal_position_id': (
#                     purchase_order.fiscal_position_id or purchase_order.fiscal_position_id._get_fiscal_position(
#                 partner_invoice)).id,
#             'payment_reference': purchase_order.partner_ref or '',
#             'partner_bank_id': partner_bank_id.id,
#             'invoice_origin': purchase_order.name,
#             'invoice_payment_term_id': purchase_order.payment_term_id.id,
#             'invoice_line_ids': [],
#             'company_id': purchase_order.company_id.id,
#             'journal_id': purchase_order.l10n_in_journal_id.id,
#             'grn_names': ', '.join(grn_names)
#         }
#         return invoice_vals


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    is_approve = fields.Boolean('Is Approve')

    # Onchange for selecting warehouse
    @api.onchange('picking_type_id')
    def onchange_delivery_name(self):
        for rec in self:
            return {'domain': {'warehouse_id': [('id', '=', rec.picking_type_id.warehouse_id.id)]}}

    #CREATED WIZARD FOR SAPAT REQUIREMENT
    # def open_vendorbill_wizard(self):
    #     # Call the wizard action to open the wizard
    #     return {
    #         'name': 'Vendor Bill Wizard',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'vendorbill.wizard',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('icorets.view_vendorbill_wizard_form').id,
    #         'target': 'new',
    #     }



    # For getting user which used approve button in purchase order in pdf
    def button_approve(self, force=False):
        res = super(PurchaseOrderInherit, self).button_approve()
        self.is_approve = True
        return res

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrderInherit, self)._prepare_invoice()
        invoice_vals['gstin_id'] = self.gstin_id.id
        invoice_vals['journal_id'] = self.l10n_in_journal_id.id
        return invoice_vals


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    tax_amount_line = fields.Monetary(string='Total Amount', readonly=True,
                                      compute="check_tax_amount", currency_field='currency_id')

    remark = fields.Text('Remarks')
    hsn_c = fields.Many2one(string='HSN Code', related='product_id.product_tmpl_id.purchase_hsn')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')
    color = fields.Char(string='Color', related='product_id.color')

    @api.depends('product_qty', 'product_uom')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if line.product_id.default_code:
                product_name = f"[{line.product_id.default_code}] {line.product_id.name}"
                line.name = product_name
            else:
                product_name = f"{line.product_id.name}"
                line.name = product_name
            if not line.product_id or line.invoice_lines:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.taxes_id,
                    line.company_id,
                )
                price_unit = line.product_id.currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order,
                    False
                )
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                               self.env[
                                                                                   'decimal.precision'].precision_get(
                                                                                   'Product Price')))
                continue

            price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                 line.product_id.supplier_taxes_id,
                                                                                 line.taxes_id,
                                                                                 line.company_id) if seller else 0.0
            price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order,
                                                     False)
            price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                      self.env['decimal.precision'].precision_get(
                                                                          'Product Price')))
            line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

            if line.product_id.default_code:
                product_name = f"[{line.product_id.default_code}] {line.product_id.name}"
                line.name = product_name
            else:
                product_name = f"{line.product_id.name}"
                line.name = product_name

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            if line.product_qty < 0:
                line.product_qty = (line.product_qty) * -1
            if line.price_unit < 0:
                line.price_unit = (line.price_unit) * -1
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    # Adding Purchase HSN Code in Bills

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLineInherit, self)._prepare_account_move_line(move)
        hsn = self.product_id.product_tmpl_id.purchase_hsn
        res.update({'hsn_id': hsn.id})
        return res

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

    # For fetching color

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

    # for getting rax amount

    @api.depends('taxes_id')
    def check_tax_amount(self):
        for rec in self:
            if rec.taxes_id:
                for tax in rec.taxes_id:
                    rec.tax_amount_line += (rec.price_unit * tax.amount) / 100
            else:
                rec.tax_amount_line = 0


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, values):
        res = super(StockPickingInherit, self).create(values)
        stock_transfers_search = self.env['sale.order'].search([('name', '=', res.origin)])
        if stock_transfers_search:
            res.location_id = stock_transfers_search.location_id.id
        return res

    # For uploading detailed transfers by importing file
    def update_picking_list_wizard(self):
        return {
            'name': 'Upload File',
            'type': 'ir.actions.act_window',
            'res_model': 'packing.list.manual',
            'view_mode': 'form',
            'view_id': self.env.ref('icorets.view_bag_entry_manual_wizard_form').id,
            'target': 'new',
        }

# Code for populating stock in stock.move.line

class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def create(self, vals_list):
        res = super(StockMoveLineInherit, self).create(vals_list)
        stock_transfers_search = self.env['sale.order'].search([('name', '=', res.origin)])
        if stock_transfers_search:
            res.location_id = res.picking_id.location_id
            print(res.location_id, 'res')
        return res


class InheritApprovalRequest(models.Model):
    _inherit = "approval.request"

    cust_partner_id = fields.Many2one("res.partner")
    vendor_count = fields.Integer("Vendor Count")

    def action_show_contact(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.cust_partner_id.id,
            'name': self.cust_partner_id.name,
            'view_mode': 'form',
            'views': [(False, "form")],
        }

    def action_approve(self, approver=None):
        if self.cust_partner_id:
            self._ensure_can_approve()
            if not isinstance(approver, models.BaseModel):
                approver = self.mapped('approver_ids').filtered(
                    lambda approver: approver.user_id == self.env.user
                )
            approver.write({'status': 'approved'})
            self.sudo()._update_next_approvers('pending', approver, only_next_approver=True)
            self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
            self.cust_partner_id.write({'active': True})


class InheritResPartner(models.Model):
    _inherit = "res.partner"

    # alias_name = fields.Many2one("alias.name", "Alias Name", copy=False)
    cust_alias_name = fields.Char("Alias Name", copy=False)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            args += ['|', '|', ('name', operator, name), ('cust_alias_name', operator, name)]
        return super()._name_search(name, args, operator, limit, name_get_uid)

    @api.depends('cust_alias_name','name')
    def name_get(self):
        return [(record.id, "[%s] %s" % (record.cust_alias_name, record.name)) if record.cust_alias_name else (record.id, "%s" % (record.name)) for record in self]


    # Commented Approval cateory on creating vendor
    # @api.model_create_multi
    # def create(self, vals):
    #     result = super(InheritResPartner, self).create(vals)
    #     active_ids = self.env.context.get('default_supplier_rank')
    #     if active_ids:
    #         result.active = False
    #         approval_category_id = self.env['approval.category'].sudo().search([
    #             ('name', '=', 'Vendor')
    #         ], limit=1)
    #         if not approval_category_id:
    #             raise ValidationError("'Vendor' Approval Category Is Not Created.")
    #
    #         approval_vals = {
    #             'name': "Vendor Approval",
    #             'request_owner_id': self.env.user.id,
    #             'cust_partner_id': result.id,
    #             "category_id": approval_category_id.id,
    #             "vendor_count": 1,
    #         }
    #         data = self.env['approval.request'].create(approval_vals)
    #         data.action_confirm()
    #         print(data)
    #     return result

    # @api.model
    # def default_get(self, fields):
    #     res = super(InheritResPartner, self).default_get(fields)
    #     active_ids = self.env.context.get('default_supplier_rank')
    #     if active_ids:
    #         if 'is_approved' in fields and 'active' in fields:
    #             res['is_approved'] = False
    #             res['active'] = False
    #     else:
    #         if 'is_approved' in fields and 'active' in fields:
    #             res['is_approved'] = True
    #             res['active'] = True
    #     return res

# Created for Packing List
class PackingListManual(models.TransientModel):
    _name = "packing.list.manual"
    _description = "Manual Packing List"

    upload_file = fields.Binary("Upload File", required=True, help="Upload your .csv file here.")
    file_name = fields.Char('File Name')
    alert_notification = fields.Html(
        default="<h6 style='color:red;text-align:center;'>Please Upload .CSV File Only.</h6>", readonly=True)

    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        picking_id = self.env["stock.picking"].browse(active_id)
        excel_data = self.upload_file
        filename = BytesIO(base64.b64decode(excel_data))
        data = pd.read_csv(filename)

        cols_to_check = ['Product', 'Unit of Measure', 'Source Package','Done Quantity']
        empty_column = data[cols_to_check].isnull().any()
        cols_with_null_names = empty_column[empty_column == True].index.tolist()

        if cols_with_null_names:
            raise ValidationError("Empty cells in %s columns." % cols_with_null_names)

        st_move_line_lst = []
        for index, rows in data.iterrows():
            search_product = self.env["product.product"].search([('default_code', '=', rows['Product'])], limit=1)
            if not search_product:
                raise ValidationError(f"Product {rows['Product']} Not Found.")

            search_uom = self.env["uom.uom"].search([('name', '=', rows['Unit of Measure'])], limit=1)
            if not search_uom:
                raise ValidationError(f"Unit of Measure {rows['Unit of Measure']} Not Found.")


            package_obj = self.env['stock.quant.package']
            if rows['Source Package']:
                pck = package_obj.create({'name': rows['Source Package'] + " " + '('+ picking_id.origin +')'})

            st_move_line_vals = (0, 0, {
                'product_id': search_product.id,
                'product_uom_id': search_uom.id,
                'package_id': pck.id,
                'qty_done': rows['Done Quantity'],

            })
            st_move_line_lst.append(st_move_line_vals)
        picking_id.write({'move_line_ids_without_package': st_move_line_lst})

from lxml import etree

from num2words import num2words

from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
import datetime
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tools import json


class ProductVariantInherit(models.Model):
    _inherit = "product.product"

    variant_asin = fields.Char('') #Not used
    variant_fsn = fields.Char('') #Not used
    variant_ean_code = fields.Char('') #Not used

    variants_ean_code = fields.Char('EAN Code')
    variant_article_code = fields.Char('Article Code')
    variants_asin = fields.Char('ASIN')
    variants_fsn = fields.Char('FSN')
    variant_cost = fields.Float('Invalid Cost')  # not used
    variant_packaging_cost = fields.Float('Packaging Cost')
    variant_total_cost = fields.Float('Total Cost')
    brand_id_rel = fields.Many2one(related='product_tmpl_id.brand_id', string="Brand")
    color = fields.Char('Color')
    size = fields.Char('Size')

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
    occasion = fields.Char('Occasion')
    style_code = fields.Char('Style Code')
    buin = fields.Char('BUIN')
    parent_buin = fields.Char('parent_buin')
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
            # end


class ProductBrand(models.Model):
    _name = "product.brand"

    name = fields.Char('Brand Name')


class AccountMoveInheritClass(models.Model):
    _inherit = 'account.move'

    check_amount_in_words = fields.Char(compute='_amt_in_words', string='Amount in Words')
    # warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    po_no = fields.Char('PO No')
    event = fields.Char('Event')
    type_s = fields.Selection([
        ('sor', 'SOR'),
        ('outwrite', 'OutWrite'),

    ])
    cust_partner_alias_id = fields.Many2one("alias.name", "Alias Name", copy=False)

    @api.onchange("cust_partner_alias_id")
    def action_onchange_partner_alias(self):
        if self.cust_partner_alias_id:
            search_partner = self.env["res.partner"].search([('alias_name', '=', self.cust_partner_alias_id.id)], limit=1)
            self.partner_id = search_partner.id

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

    po_no = fields.Char('PO No')
    no_of_cartons = fields.Char('No of Cartons')
    location_id = fields.Many2one(
        'stock.location', ' Source Location',
        ondelete='restrict', index=True, check_company=True)  # removed the required=True
    event = fields.Char('Event')
    l10n_in_journal_id = fields.Many2one('account.journal', string="Journal", default=False, required=True, store=True,
                                         readonly=True,
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    is_fo = fields.Boolean("Is Fo", copy=False, default=False)

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
        invoice_vals['po_no'] = self.po_no
        invoice_vals['event'] = self.event
        invoice_vals['journal_id'] = self.l10n_in_journal_id.id
        return invoice_vals

    def fo_action_confirm(self):
        top_priority_stock = {}
        medium_priority_stock = {}
        low_priority_stock = {}

        top_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '1')], limit=1)
        medium_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '2')], limit=1)
        low_priority_warehouse = self.env["stock.warehouse"].search([('priority', '=', '3')], limit=1)

        for so_line in self.order_line:
            search_top_stock = self.env["stock.quant"].search([('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', top_priority_warehouse.id)], limit=1)
            search_medium_stock = self.env["stock.quant"].search([('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', medium_priority_warehouse.id)], limit=1)
            search_low_stock = self.env["stock.quant"].search([('product_id', '=', so_line.product_id.id), ('warehouse_id', '=', low_priority_warehouse.id)], limit=1)

            if search_top_stock:
                if so_line not in top_priority_stock:
                    top_priority_stock[so_line] = search_top_stock.quantity
                else:
                    top_priority_stock[so_line] += search_top_stock.quantity

            if search_medium_stock:
                if so_line not in medium_priority_stock:
                    medium_priority_stock[so_line] = search_medium_stock.quantity
                else:
                    medium_priority_stock[so_line] += search_medium_stock.quantity

            if search_low_stock:
                if so_line not in low_priority_stock:
                    low_priority_stock[so_line] = search_low_stock.quantity
                else:
                    low_priority_stock[so_line] += search_low_stock.quantity

        backorder_of_fo_lines = {}

        if len(top_priority_warehouse) > 0:
            top_priority_so_line_lst = []
            for so_line_obj, qty in top_priority_stock.items():
                search_top_priority_stock = self.env["stock.quant"].search(
                    [('product_id', '=', so_line_obj.product_id.id), ('warehouse_id', '=', top_priority_warehouse.id)],
                    limit=1)
                prd_qty = 0
                if qty == so_line_obj.product_uom_qty:
                    prd_qty = so_line_obj.product_uom_qty
                    top_priority_stock[so_line_obj] -= prd_qty
                elif qty > so_line_obj.product_uom_qty:
                    prd_qty = so_line_obj.product_uom_qty
                    top_priority_stock[so_line_obj] -= prd_qty
                elif qty < so_line_obj.product_uom_qty:
                    prd_qty = qty
                    top_priority_stock[so_line_obj] -= prd_qty

                if qty < so_line_obj.product_uom_qty:
                    remaining_prd_qty = so_line_obj.product_uom_qty - prd_qty
                    if remaining_prd_qty > 0:
                        if so_line_obj not in backorder_of_fo_lines:
                            backorder_of_fo_lines[so_line_obj] = remaining_prd_qty
                        else:
                            backorder_of_fo_lines[so_line_obj] += remaining_prd_qty
                    so_line_obj.product_uom_qty = prd_qty

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
                'partner_invoice_id': self.partner_invoice_id.id,
                'partner_shipping_id': self.partner_shipping_id.id,
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
        if len(medium_priority_warehouse) > 0:
            medium_priority_so_line_lst = []
            for so_line_obj, qty in medium_priority_stock.items():
                search_medium_priority_stock = self.env["stock.quant"].search(
                    [('product_id', '=', so_line_obj.product_id.id), ('warehouse_id', '=', medium_priority_warehouse.id)],
                    limit=1)
                prd_qty = 0
                if qty == so_line_obj.product_uom_qty:
                    prd_qty = so_line_obj.product_uom_qty
                    medium_priority_stock[so_line_obj] -= prd_qty
                elif qty > so_line_obj.product_uom_qty:
                    prd_qty = so_line_obj.product_uom_qty
                    medium_priority_stock[so_line_obj] -= prd_qty
                elif qty < so_line_obj.product_uom_qty:
                    prd_qty = qty
                    medium_priority_stock[so_line_obj] -= prd_qty

                if qty < so_line_obj.product_uom_qty:
                    remaining_prd_qty = so_line_obj.product_uom_qty - prd_qty
                    if remaining_prd_qty > 0:
                        if so_line_obj not in backorder_of_fo_lines:
                            backorder_of_fo_lines[so_line_obj] = remaining_prd_qty
                        else:
                            backorder_of_fo_lines[so_line_obj] += remaining_prd_qty
                    so_line_obj.product_uom_qty = prd_qty

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
                'partner_invoice_id': self.partner_invoice_id.id,
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
        if len(low_priority_warehouse) > 0:
            low_priority_so_line_lst = []
            for so_line_obj, qty in low_priority_stock.items():
                search_low_priority_stock = self.env["stock.quant"].search(
                    [('product_id', '=', so_line_obj.product_id.id), ('warehouse_id', '=', low_priority_warehouse.id)],
                    limit=1)
                prd_qty = 0
                if qty == so_line_obj.product_uom_qty:
                    prd_qty = so_line_obj.product_uom_qty
                    low_priority_stock[so_line_obj] -= prd_qty
                elif qty > so_line_obj.product_uom_qty:
                    prd_qty = so_line_obj.product_uom_qty
                    low_priority_stock[so_line_obj] -= prd_qty
                elif qty < so_line_obj.product_uom_qty:
                    prd_qty = qty
                    low_priority_stock[so_line_obj] -= prd_qty

                if qty < so_line_obj.product_uom_qty:
                    remaining_prd_qty = so_line_obj.product_uom_qty - prd_qty
                    if remaining_prd_qty > 0:
                        if so_line_obj not in backorder_of_fo_lines:
                            backorder_of_fo_lines[so_line_obj] = remaining_prd_qty
                        else:
                            backorder_of_fo_lines[so_line_obj] += remaining_prd_qty
                    so_line_obj.product_uom_qty = prd_qty

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
                'partner_invoice_id': self.partner_invoice_id.id,
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
                'partner_invoice_id': self.partner_invoice_id.id,
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

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            line.product_uom_qty = abs(line.product_uom_qty)
            line.price_unit = abs(line.price_unit)
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


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    is_approve = fields.Boolean('Is Approve')

    # For getting user which used approve button in purchase order in pdf
    def button_approve(self, force=False):
        res = super(PurchaseOrderInherit, self).button_approve()
        self.is_approve = True
        return res


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    tax_amount_line = fields.Monetary(string='Total Amount', readonly=True,
                                      compute="check_tax_amount", currency_field='currency_id')

    remark = fields.Text('Remarks')
    hsn_c = fields.Many2one(string='HSN Code', related='product_id.product_tmpl_id.purchase_hsn')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            line.product_qty = abs(line.product_qty)
            line.price_unit = abs(line.price_unit)
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

    alias_name = fields.Many2one("alias.name", "Alias Name", copy=False)

    @api.model_create_multi
    def create(self, vals):
        result = super(InheritResPartner, self).create(vals)
        active_ids = self.env.context.get('default_supplier_rank')
        if active_ids:
            result.active = False
            approval_category_id = self.env['approval.category'].sudo().search([
                ('name', '=', 'Vendor')
            ], limit=1)
            if not approval_category_id:
                raise ValidationError("'Vendor' Approval Category Is Not Created.")

            approval_vals = {
                'name': "Vendor Approval",
                'request_owner_id': self.env.user.id,
                'cust_partner_id': result.id,
                "category_id": approval_category_id.id,
                "vendor_count": 1,
            }
            data = self.env['approval.request'].create(approval_vals)
            data.action_confirm()
            print(data)
        return result

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
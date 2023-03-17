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

from odoo.tools import json


class ProductVariantInherit(models.Model):
    _inherit = "product.product"

    variant_ean_code = fields.Char('EAN Code')
    variant_article_code = fields.Char('Article Code')
    variant_asin = fields.Char('ASIN')
    variant_fsn = fields.Char('FSN')
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

    _sql_constraints = [
        ('asin_unique', 'unique(variant_asin)', "ASIN code can only be assigned to one variant product !"),
        ('ean_code_unique', 'unique(variant_ean_code)', "EAN code can only be assigned to one variant product !"),
        ('fsn_unique', 'unique(variant_fsn)', "FSN code can only be assigned to one variant product !"),
    ]

    # For updating standard price by rakng sum of cost(basic) and packaging cost
    @api.onchange('standard_price', 'packaging_cost')
    def sum_cost(self):
        if self.standard_price and self.packaging_cost:
            self.variant_total_cost = self.standard_price + self.packaging_cost


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


class ProductBrand(models.Model):
    _name = "product.brand"

    name = fields.Char('Brand Name')


class AccountMoveInheritClass(models.Model):
    _inherit = 'account.move'

    check_amount_in_words = fields.Char(compute='_amt_in_words', string='Amount in Words')
    # warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    po_no = fields.Char('PO No')
    event = fields.Char('Event')

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
        ondelete='restrict', required=True, index=True, check_company=True)

    # For checking quantity
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
        return invoice_vals

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



class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    stock_quantity = fields.Float('Stock Quantity')
    hsn_c = fields.Many2one(string='HSN Code', related='product_id.product_tmpl_id.sale_hsn')
    article_code = fields.Char(string='Article Code', related='product_id.variant_article_code')

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

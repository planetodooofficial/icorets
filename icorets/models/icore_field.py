from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
import datetime
from datetime import datetime


class ProductVariantInherit(models.Model):
    _inherit = "product.product"

    # For updating standard price by rakng sum of cost(basic) and packaging cost
    @api.onchange('cost', 'packaging_cost')
    def sum_cost(self):
        if self.cost and self.packaging_cost:
            self.standard_price = self.cost + self.packaging_cost


class ProductInherit(models.Model):
    _inherit = "product.template"

    material = fields.Char('Moc')
    color = fields.Char('Color')
    brand_id = fields.Many2one('product.brand', 'Brand')
    occasion = fields.Char('Occasion')
    ean_code = fields.Char('EAN Code')
    style_code = fields.Char('Style Code')
    article_code = fields.Char('Article Code')
    size = fields.Char('Style Code')
    asin = fields.Char('ASIN')
    fsn = fields.Char('FSN')
    buin = fields.Char('BUIN')
    parent_buin = fields.Char('parent_buin')
    user_defined_miscallaneous1 = fields.Char('User Defined Miscallaneous1')
    user_defined_miscallaneous2 = fields.Char('User Defined Miscallaneous2')
    user_defined_miscallaneous3 = fields.Char('User Defined Miscallaneous3')
    user_defined_miscallaneous4 = fields.Char('User Defined Miscallaneous4')
    user_defined_miscallaneous5 = fields.Char('User Defined Miscallaneous5')
    # technical details
    cost = fields.Float('Cost (Basic)')
    packaging_cost = fields.Float('Packaging Cost')
    manufactured_by = fields.Char('Manufactured By')
    marketed_by = fields.Char('Marketed By / Customer Care')
    length = fields.Float('Length (Dimensions)')
    width = fields.Float('width (Dimensions)')
    height = fields.Float('height (Dimensions)')
    weight = fields.Float('Weight (Dimensions)')
    country_of_origin = fields.Char('Country of Origin')
    manufacture_year = fields.Date('Manufacture Year')

    _sql_constraints = [
        ('asin_unique', 'unique(asin)', "ASIN code can only be assigned to one product !"),
        ('ean_code_unique', 'unique(ean_code)', "EAN code can only be assigned to one product !"),
        ('fsn_unique', 'unique(fsn)', "FSN code can only be assigned to one product !"),
        ('buin_unique', 'unique(buin)', "BUIN code can only be assigned to one product !"),
    ]


class ProductBrand(models.Model):
    _name = "product.brand"

    name = fields.Char('Brand Name')

from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
import datetime
from datetime import datetime
from odoo.exceptions import ValidationError, UserError



class ImportAttributes(models.TransientModel):
    _name = 'import.attributes'
    _description = 'Import Attribute Wizard'

    upload_attributes_file = fields.Binary('File')

    def convert_to_df(self):
        csv_data = self.upload_attributes_file
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def import_product(self):
        df = self.convert_to_df()
        data = df.to_dict('index').values()

        lst_data = []

        title = list(map(lambda a: a['Style Code'], data))

        title = list(set(title))
        # print('Print Title : ', title)

        new_data = {}
        for a in title:
            new_data[a] = list(filter(lambda t: t['Style Code'] == a, data))
        # print(new_data)
        created_product = []
        for keys, values in new_data.items():
            print(keys, values)

            # search_product = self.env["product.template"].search([("name", "=", keys)])
            for i in values:
                # Search Taxes
                search_tax_purchase = self.env['account.tax'].search(
                    [('name', '=', i['GST']), ('type_tax_use', '=', 'purchase')])
                search_tax_sale = self.env['account.tax'].search(
                    [('name', '=', i['GST']), ('type_tax_use', '=', 'sale')])

                # #For product Category for subclass (last column)
                search_prod_category = self.env['product.category'].search(
                    [('name', '=', i['SubClass'])], limit=1)

                if not search_prod_category:
                    raise ValidationError(f"'Product Category not available for '{i['SubClass']}")

                # Brand Search
                brand_search = self.env['product.brand'].search([('name','=',i['Brand'])])
                if not brand_search:
                    brand_search = self.env['product.brand'].create({'name': i['Brand']})

                # uom id for product
                search_uom = self.env['uom.uom'].search([('name', '=', i['UoM'])])

                # For attribute
                search_attribute_color = self.env['product.attribute'].search(
                    [('name', '=', 'Color')])  # search color Attribute
                search_attribute_size = self.env['product.attribute'].search(
                    [('name', '=', 'Size')])  # Search Size Attribute

                # For value
                if i['Color']:
                    search_attribute_value_color = self.env['product.attribute.value'].search(
                        [('name', '=', i['Color'])]) # Search Color Attribute value
                    if not search_attribute_value_color:
                        raise ValidationError(_(f"{i['Color']} Color not available"))

                if i['Size']:
                    search_attribute_value_size = self.env['product.attribute.value'].search(
                        [('name', '=', i['Size'])])  # Search Size Attribute value
                    if not search_attribute_value_size:
                        raise ValidationError(_(f"{i['Size']} Size not available"))

                if keys not in created_product:
                    lst = []
                    if i['Color']:

                        prod_line_vals = (0, 0, {
                            'attribute_id': search_attribute_color.id,
                            'value_ids': [(4, search_attribute_value_color.id)],
                        })
                        lst.append(prod_line_vals)
                    if i['Size']:
                        prod_line_vals_s = (0, 0, {
                            'attribute_id': search_attribute_size.id,
                            'value_ids': [(4, search_attribute_value_size.id)],
                        })
                        # lst2.append(lst_vrnt)

                        lst.append(prod_line_vals_s)

                    product_vals = {
                        'name': i['Title'],
                        # 'barcode': i['EAN Code'],
                        'material': i['Material'],
                        'occasion': i['Occasion'],
                        'style_code': i['Style Code'],
                        'l10n_in_hsn_code': i['HSN Code'],
                        'func_spo': i['Function/Sport'],
                        'gender': i['Gender'],
                        'tech_feat': i['Technology/Features'],
                        'uom_id': search_uom.id,
                        'uom_po_id': search_uom.id,
                        'brand_id': brand_search.id,
                        'list_price': i['MRP'],
                        'categ_id': search_prod_category.id,
                        'taxes_id': [(4, search_tax_sale.id)] if search_tax_sale.id else False,
                        'supplier_taxes_id': [(4, search_tax_purchase.id)] if search_tax_purchase.id else False,
                        'detailed_type': 'product',
                        'standard_price': i['Total Cost'],
                        'attribute_line_ids': lst,
                    }
                    print(product_vals)
                    search_product_id = self.env['product.template'].create(product_vals)

                    created_product.append(keys)

                else:
                    search_product = self.env["product.template"].search([("style_code", "=", keys)])
                    for attribute in search_product.attribute_line_ids:
                        if attribute.attribute_id.name == "Color":
                            if i['Color'] not in attribute.value_ids:
                                attribute.value_ids = [(4, search_attribute_value_color.id)]
                        else:
                            if i['Size'] not in attribute.value_ids.ids:
                                attribute.value_ids = [(4, search_attribute_value_size.id)]

class UpdateAttributes(models.TransientModel):
    _name = 'update.attributes'
    _description = 'Update Attribute Wizard'

    upload_attributes_file = fields.Binary('File')

    def convert_to_df(self):
        csv_data = self.upload_attributes_file
        file_obj = TemporaryFile('wb+')
        csv_data = base64.decodebytes(csv_data)
        file_obj.write(csv_data)
        file_obj.seek(0)
        return pd.read_csv(file_obj).fillna(False)

    def update_variants(self):

        csv_data = base64.b64decode(self.upload_attributes_file)
        csv_data = csv_data.decode('utf-8').split('\n')

        # Assuming the first row contains the header
        header = csv_data[0].split(',')
        csv_reader = csv.DictReader(csv_data[1:], fieldnames=header)

        for row in csv_reader:
            internal_ref = row['SKU Code']
            color = row['Color']
            size = row['Size']
            title = row['Title']
            stylecode = row['Style Code']
            ean = row['EAN Code']
            article = row['Article Code']
            fsn = row['FSN']
            asin = row['ASIN']

            product_template = self.env['product.product'].search([('name', '=', title), ('style_code', '=', stylecode),
                ('product_template_attribute_value_ids.name', '=', size),
                ('product_template_attribute_value_ids.name', '=', color)
            ], limit=1)

            product_template_color = self.env['product.product'].search([('name', '=', title), ('style_code', '=', stylecode),
                                                                   ('product_template_attribute_value_ids.name', '=',
                                                                    color)
                                                                   ], limit=1)
            product_template_size = self.env['product.product'].search([('name', '=', title), ('style_code', '=', stylecode),
                                                                   ('product_template_attribute_value_ids.name', '=',
                                                                    size),
                                                                   ], limit=1)

            if product_template:
                for product_variant in product_template:
                    product_variant.update({'default_code': internal_ref})
                    product_variant.update({'barcode': ean})
                    if asin:
                        product_variant.update({'variants_asin': asin})
                    if fsn:
                        product_variant.update({'variants_fsn': fsn})
                    product_variant.update({'variant_article_code': article})
            elif product_template_size:
                for product_variant in product_template_size:
                    product_variant.update({'default_code': internal_ref})
                    product_variant.update({'barcode': ean})
                    if asin:
                        product_variant.update({'variants_asin': asin})
                    if fsn:
                        product_variant.update({'variants_fsn': fsn})
                    product_variant.update({'variant_article_code': article})
            elif product_template_color:
                for product_variant in product_template_color:
                    product_variant.update({'default_code': internal_ref})
                    product_variant.update({'barcode': ean})
                    if asin:
                        product_variant.update({'variants_asin': asin})
                    if fsn:
                        product_variant.update({'variants_fsn': fsn})
                    product_variant.update({'variant_article_code': article})







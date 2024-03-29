from odoo import models, api, fields, _
import base64
import csv
import io
from tempfile import TemporaryFile
import pandas as pd
import datetime
from datetime import datetime


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
        # print(data)
        # b = []  # b is list of dictionary with data of each row
        # for rec in data.values():
        #     data = {}
        #     for i, j in rec.items():
        #         if j is not False:
        #             data[i] = j
        #     b.append(data)
        # c = []  # c is list of column names with data  of each row
        # list = []
        # line_items = []
        # line_items1 = []
        # line_attrs = []
        # line_attrs_s = []

        # for rec in b:
        #     attribute_color = rec.get('Color', False)
        #     attribute_size = rec.get('Size', False)
        #     prod_name = rec.get('Title', False)
        #     style_code = rec.get('Style Code', False)
        #     brand = rec.get('Brand', False)
        #     ean_code = rec.get('EAN Code', False)
        #     material = rec.get('Material', False)
        #     occasion = rec.get('Occasion', False)
        #     mrp = rec.get('MRP', False)
        #
        #     keys_list = [key for key, val in rec.items() if val]
        #     c.append(keys_list)
        # list = c[-1]

        # For attribute Color
        # search_att_color = self.env['product.attribute'].search([('name', '=', 'Color')])
        # att_list = search_att_color.value_ids.mapped('name')
        # if attribute_color not in att_list:
        #     if attribute_color:
        #         # if search_att_color:
        #         #     if attribute_color:
        #         add_attribute = (0, 0, {
        #             'name': attribute_color
        #         })
        #         line_items.append(add_attribute)
        #         search_att_color.write({'value_ids': line_items})
        #         line_items = []
        #         print(attribute_color)
        #
        # # For attribute Size
        # search_att_size = self.env['product.attribute'].search([('name', '=', 'Size')])
        # att_list1 = search_att_size.value_ids.mapped('name')
        # if attribute_size not in att_list1:
        #     if attribute_size:
        #         # if search_att_size:
        #         #     if attribute_size:
        #         add_attribute_size = (0, 0, {
        #             'name': attribute_size
        #         })
        #         line_items1.append(add_attribute_size)
        #
        #         search_att_size.write({'value_ids': line_items1})
        #         line_items1 = []
        #         print(attribute_size)

        # For prod name

        # prod_name_search = self.env['product.template'].search(
        #     [('name', '=', prod_name)])  # search internal reference
        #
        # search_attribute_color = self.env['product.attribute'].search(
        #     [('name', '=', 'Color')])  # search color Attribute
        # search_attribute_value_color = self.env['product.attribute.value'].search(
        #     [('name', '=', attribute_color)])  # Search Color Attribute value
        #
        # search_attribute_size = self.env['product.attribute'].search(
        #     [('name', '=', 'Size')])  # search Size Attribute
        # search_attribute_value_size = self.env['product.attribute.value'].search(
        #     [('name', '=', attribute_size)])  # Search Size Attribute value
        #
        # if not prod_name_search:  # create product if not created
        #     prod_attrs = (0, 0, {
        #         'attribute_id': search_attribute_color.id,
        #         'value_ids': search_attribute_value_color,
        #     })
        #     line_attrs.append(prod_attrs)
        #
        #     product_vals = {
        #         'name': prod_name,
        #         'default_code': style_code,
        #         'brand': brand,
        #         'ean_code': ean_code,
        #         'material': material,
        #         'occasion': occasion,
        #         'standard_price': mrp,
        #         'attribute_line_ids': line_attrs,
        #     }
        #     prod_name_search = self.env['product.template'].create(product_vals)
        #
        #     # if not prod_name_search.attribute_line_ids:
        #
        #     # prod_name_search.write({'attribute_line_ids': line_attrs})
        #
        # else:
        #     for a in prod_name_search.attribute_line_ids:
        #         print(a.attribute_id,'attribute',search_attribute_value_color,'search color')
        #         if a.attribute_id == search_attribute_color:
        #             a.value_ids = [(4, search_attribute_value_color.id)]

        lst_data = []

        title = list(map(lambda a: a['Title'], data))

        title = list(set(title))
        # print('Print Title : ', title)

        new_data = {}
        for a in title:
            new_data[a] = list(filter(lambda t: t['Title'] == a, data))
        # print(new_data)
        created_product = []
        for keys, values in new_data.items():
            # print(keys, values)

            # search_product = self.env["product.template"].search([("name", "=", keys)])
            for i in values:
                #For product Category
                search_prod_category = self.env['product.category'].search(
                    [('name', '=', i['Category']),('parent_id', '=' , 'All')])
                if not search_prod_category:
                    search_parent_category = self.env['product.category'].search([('name', '=', 'All')])
                    search_prod_category = self.env['product.category'].create(
                        {'name': i['Category'],
                         'parent_id': search_parent_category.id}
                    )
                brand_search = self.env['product.brand'].search([('name','=',i['Brand'])])
                if not brand_search:
                    brand_search = self.env['product.brand'].create({'name': i['Brand']})

                # For attribute
                search_attribute_color = self.env['product.attribute'].search(
                    [('name', '=', 'Color')])  # search color Attribute
                search_attribute_size = self.env['product.attribute'].search(
                    [('name', '=', 'Size')])  # Search Size Attribute

                # For value
                search_attribute_value_color = self.env['product.attribute.value'].search(
                    [('name', '=', i['Color'])]) # Search Color Attribute value
                if not search_attribute_value_color:
                    search_attribute_value_color = self.env['product.attribute.value'].create(
                        {'name': i['Color']}
                    )
                search_attribute_value_size = self.env['product.attribute.value'].search(
                    [('name', '=', i['Size'])])  # Search Size Attribute value
                if not search_attribute_value_size:
                    search_attribute_value_size = self.env['product.attribute.value'].create(
                        {'name': i['Size']}
                    )
                if keys not in created_product:
                    # if not self.env["product.template"].search([("name", "=", keys)]):
                    lst = []
                    if i['Color'] or i['Size']:

                        prod_line_vals = (0, 0, {
                            'attribute_id': search_attribute_color.id,
                            'value_ids': [(4, search_attribute_value_color.id)],
                        })

                        prod_line_vals_s = (0, 0, {
                            'attribute_id': search_attribute_size.id,
                            'value_ids': [(4, search_attribute_value_size.id)],
                        })
                        # lst2.append(lst_vrnt)
                        lst.append(prod_line_vals)
                        lst.append(prod_line_vals_s)

                    product_vals = {
                        'name': i['Title'],
                        'ean_code': i['EAN Code'],
                        'material': i['Material'],
                        'occasion': i['Occasion'],
                        'article_code': i['Article Code'],
                        'style_code': i['Style Code'],
                        'cost': i['Cost'],
                        'l10n_in_hsn_code': i['HSN Code'],
                        'packaging_cost': i['Packaging Cost'],
                        'asin': i['ASIN'],
                        'fsn': i['FSN'],
                        'brand_id': brand_search.id,
                        'list_price': i['MRP'],
                        'detailed_type': 'product',
                        'standard_price': i['Total Cost'],
                        'categ_id': search_prod_category.id,
                        'attribute_line_ids': lst,
                    }
                    search_product_id = self.env['product.template'].create(product_vals)

                    created_product.append(keys)

                else:
                    search_product = self.env["product.template"].search([("name", "=", keys)])
                    for attribute in search_product.attribute_line_ids:
                        if attribute.attribute_id.name == "Color":
                            if i['Color'] not in attribute.value_ids:
                                attribute.value_ids = [(4, search_attribute_value_color.id)]
                        else:
                            if i['Size'] not in attribute.value_ids:
                                attribute.value_ids = [(4, search_attribute_value_size.id)]






from odoo import api, models, fields, _
import pandas as pd
from io import BytesIO

class StockVariantReport(models.AbstractModel):
    _name = "report.icorets.stock_variant_excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, report):
        print("generate_xlsx_report is working")
        worksheet = workbook.add_worksheet("Report")
        product_list = self.search_product(report)

        header_report = workbook.add_worksheet("Header Report")
        search_attributes = self.env['product.attribute'].search([('name', '=', 'Size')])
        attribute_list = [att.name for att in search_attributes.value_ids]

        static_columns = ['Brand', 'Category 3', 'Style Code', 'Article Code', 'Colour']
        dynamic_columns = static_columns + attribute_list

        # Write the column headers
        for col_num, column_name in enumerate(dynamic_columns):
            worksheet.write(0, col_num, column_name.replace('_', ' ').title())

        data = []

        for product_id in product_list:
            product = self.env['product.product'].browse(product_id)
            colour = ''
            size = ''
            qty_available = product.qty_available or 0
            for attribute in product.product_template_attribute_value_ids:
                if attribute.attribute_id.is_colour:
                    colour = attribute.name
                if attribute.attribute_id.is_size:
                    size = attribute.name

            if not colour:
                continue

            product_data = {
                'Brand': product.brand_id_rel.name or '',
                'Category 3': product.categ_id.name or '',
                'Style Code': product.style_code or '',
                'Article Code': product.variant_article_code or '',
                'Colour': colour or ''
            }

            # Ensure to initialize size columns with 0
            for attr in attribute_list:
                product_data[attr] = 0

            # Set the quantity for the respective size
            if size:
                product_data[size] = qty_available

            data.append(product_data)

        # Create a DataFrame from the data list
        df = pd.DataFrame(data)

        # Group by 'Brand', 'Category 3', 'Style Code', 'Article Code', 'Colour' and aggregate the size quantities
        df = df.groupby(['Brand', 'Category 3', 'Style Code', 'Article Code', 'Colour'], as_index=False).sum()

        # Write the DataFrame back to the worksheet
        for r, row_data in enumerate(df.values):
            for c, cell_data in enumerate(row_data):
                worksheet.write(r + 1, c, cell_data)




    def search_product(self, report_data):
        product_list = []

        all_data = {}
        # Date Filter

        if report_data.product_category:
            category = report_data.product_category.ids
        else:
            all_category = self.env['product.category'].search([])
            category = all_category.ids
        search_product = self.env['product.product'].search([('categ_id.id','in', category)])
        # search_product = self.env['product.product'].search([('style_code','=','HT3434')])
        for rec in search_product:
            product_list.append(rec.id)
        return product_list



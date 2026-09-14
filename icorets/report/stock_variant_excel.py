from odoo import api, models, fields, _
import pandas as pd
from io import BytesIO

class StockVariantReport(models.AbstractModel):
    _name = "report.icorets.stock_variant_excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, report):
        worksheet = workbook.add_worksheet("Report")
        product_list = self.search_product(report)

        search_attributes = self.env['product.attribute'].search([('is_size', '=', True)])
        attribute_list = list(dict.fromkeys(att.name for att in search_attributes.value_ids if att.name))

        static_columns = ['Brand', 'Category 3', 'Style Code', 'Article Code', 'MRP', 'Colour']
        dynamic_columns = static_columns + attribute_list

        # Write the column headers
        for col_num, column_name in enumerate(dynamic_columns):
            worksheet.write(0, col_num, column_name.replace('_', ' ').title())

        data_rows = []

        for product_id in product_list:
            product = self.env['product.product'].browse(product_id)
            colour = ''
            size = ''
            qty_available = product.qty_available or 0.0
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
                'MRP': product.lst_price or 0.0,
                'Colour': colour or ''
            }

            # Ensure to initialize size columns with 0
            for attr in attribute_list:
                product_data[attr] = 0.0

            # Set the quantity for the respective size
            if size and size in product_data:
                product_data[size] = qty_available

            data_rows.append(product_data)

        # Create a DataFrame from the data list
        df = pd.DataFrame(data_rows, columns=dynamic_columns)

        if not df.empty:
            # Group by static columns and aggregate the size quantities
            if attribute_list:
                df = df.groupby(static_columns, as_index=False)[attribute_list].sum()
            else:
                df = df.drop_duplicates(subset=static_columns)

            # Write the DataFrame back to the worksheet
            for r, row_data in enumerate(df.values):
                for c, cell_data in enumerate(row_data):
                    worksheet.write(r + 1, c, cell_data)

    def search_product(self, report_data):
        if report_data.product_category:
            category = report_data.product_category.ids
        else:
            all_category = self.env['product.category'].search([])
            category = all_category.ids
        search_products = self.env['product.product'].search([('categ_id.id', 'in', category)])
        return search_products.ids




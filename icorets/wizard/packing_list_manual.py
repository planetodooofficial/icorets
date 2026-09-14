import base64
from datetime import datetime
from io import BytesIO
import pandas as pd

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PackingListManual(models.TransientModel):
    _name = "packing.list.manual"
    _description = "Manual Packing List"

    upload_file = fields.Binary("Upload File", required=True, help="Upload your .xlsx file here.")
    file_name = fields.Char('File Name')
    alert_notification = fields.Html(
        default="<h6 style='color:red;text-align:center;'>Please Upload Excel File Only.</h6>", readonly=True)

    def action_confirm(self):
        create_date = datetime.now()
        active_id = self.env.context.get('active_id')
        picking_id = self.env["stock.picking"].browse(active_id)

        # Check if the file is in Excel format
        if not self.file_name or not self.file_name.lower().endswith(('.xls', '.xlsx')):
            raise ValidationError("Invalid file format. Please upload a .xls or .xlsx file.")

        excel_data = self.upload_file
        filename = BytesIO(base64.b64decode(excel_data))

        # Read the Excel file
        data = pd.read_excel(filename)

        cols_to_check = ['SKU', 'Destination Location', 'Packed Qty']
        empty_column = data[cols_to_check].isnull().any()
        cols_with_null_names = empty_column[empty_column == True].index.tolist()

        if cols_with_null_names:
            raise ValidationError("Empty cells in %s columns." % cols_with_null_names)

        for index, rows in data.iterrows():
            if rows['Destination Location'] == '0' or not rows['Destination Location']:
                continue

            search_product = self.env["product.product"].search([('default_code', '=', rows['SKU'])], limit=1)

            if not search_product:
                raise ValidationError(f"Product {rows['SKU']} Not Found.")

            create_date_str = create_date.strftime("%d/%m/%Y")
            destination_package_name = str(picking_id.origin) + '-' + str(create_date_str) + '-' + str(
                rows['Destination Location'])

            existing_package = self.env['stock.quant.package'].search([('name', '=', destination_package_name)],
                                                                      limit=1)

            if existing_package:
                package = existing_package
            else:
                package_obj = self.env['stock.quant.package']
                package_vals = {'name': destination_package_name}
                package = package_obj.create(package_vals)

            new_move_line_vals = {
                'product_id': search_product.id,
                'qty_done': rows['Packed Qty'],
                'result_package_id': package.id
            }
            picking_id.update({'move_line_ids_without_package': [(0, 0, new_move_line_vals)]})

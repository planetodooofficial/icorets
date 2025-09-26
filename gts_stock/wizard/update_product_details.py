from odoo import models, fields, api, _
import base64
import io
import openpyxl
import csv
from odoo.exceptions import UserError


class UpdateProductDetails(models.Model):
    _name = "update.product.details"
    _description = "Update Product Details"

    upload_file = fields.Binary("Upload File", required=True)
    file_name = fields.Char("File Name")

    def action_update_products(self):
        """Read uploaded Excel file (sku, cost) and update product.product"""
        if not self.upload_file:
            raise UserError(_("Please upload a file."))

        try:
            # Decode file
            file_data = base64.b64decode(self.upload_file)
            file_stream = io.BytesIO(file_data)

            # Load Excel workbook
            workbook = openpyxl.load_workbook(file_stream, data_only=True)
            sheet = workbook.active  # First sheet

            updated, not_found = 0, []

            # Assuming header row: sku | cost
            for row in sheet.iter_rows(min_row=2, values_only=True):
                sku, cost = row[0], row[1]
                if not sku or not cost:
                    continue
                product = self.env["product.product"].search([("default_code", "=", str(sku))], limit=1)
                if product:
                    product.sudo().write({"standard_price": float(cost)})
                    updated += 1
                else:
                    not_found.append(str(sku))

            message = f"{updated} products updated."
            if not_found:
                message += f" Not found SKUs: {', '.join(not_found)}"
            return {
                "effect": {
                    "fadeout": "slow",
                    "message": message,
                    "type": "rainbow_man",
                }
            }

        except Exception as e:
            raise UserError(_("File format error: %s") % str(e))
# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from datetime import datetime
from io import BytesIO
import xlsxwriter


class SaleOrder(models.Model):
    _inherit = 'purchase.order'

    excel_file = fields.Binary('Download report Excel', attachment=True, readonly=True)
    file_name = fields.Char('Excel File', size=64)

    def generate_excel(self):
        filename = "Purchase Order"

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        font_size_10 = workbook.add_format({
            'font_name': 'KacstBook',
            'font_size': 12,
            'border': 1
        })
        date_format = workbook.add_format({
            'num_format': 'dd-mm-yyyy',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1
        })
        table_header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'bg_color': '#f5eb67',
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
        })
        table_cell_format_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
        })
        table_cell_format_right = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
        })

        sheet = workbook.add_worksheet('data')
        sheet.set_column(6, 6, 60)

        headers = [
            ['Vendor Name', 25],
            ['PO NUMBER', 18],
            ['DATE', 15],
            ['Order Lines/Product', 25],
            ['Order Lines/Article Code', 25],
            ['Order Lines/Size', 20],
            ['Order Lines/Description', 30],
            ['Order Lines/Price Unit', 30],
            ['Order Lines/Taxes', 25],
            ['Order Lines/Quantity', 20],
            ['Order Lines/Received Quantity', 28],
            ['Order Lines/Invoiced Quantity', 28],
            ['Status', 28]
        ]

        for index, val in enumerate(headers):
            sheet.set_column(index, index, val[1])
            sheet.write(0, index, val[0], table_header_format)

        row = 1
        for purchase in self:
            for line in purchase.order_line:
                col = 0
                sheet.write(row, col, line.order_id.partner_id.name or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.order_id.name or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.order_id.date_order.date() if line.order_id.date_order else '', date_format)
                col += 1
                sheet.write(row, col, line.product_id.name or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.product_id.default_code or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, getattr(line.product_id, 'size', '') or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.name or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.price_unit or 0.0, table_cell_format_right)
                col += 1
                tax_ids = ', '.join(line.taxes_id.mapped('name'))
                sheet.write(row, col, tax_ids or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.product_qty or 0.0, table_cell_format_right)
                col += 1
                sheet.write(row, col, line.qty_received or 0.0, table_cell_format_right)
                col += 1
                sheet.write(row, col, line.qty_invoiced or 0.0, table_cell_format_right)
                col += 1
                sheet.write(row, col, line.order_id.state or '', table_cell_format_left)
                row += 1

        workbook.close()
        output.seek(0)

        file_name = f"{filename}_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
        self.write({
            'file_name': file_name,
            'excel_file': base64.encodebytes(output.getvalue())
        })

        return {
            'type': 'ir.actions.act_url',
            'name': filename,
            'url': '/web/content/purchase.order/%s/excel_file?download=true' % self[0].id,
            'target': 'new'
        }
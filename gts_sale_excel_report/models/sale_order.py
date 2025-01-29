# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from datetime import datetime
from io import BytesIO
import xlsxwriter


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    excel_file = fields.Binary('Download report Excel', attachment=True, readonly=True)
    file_name = fields.Char('Excel File', size=64)

    def generate_excel(self):
        filename = "Sales Order"

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        font_size_10 = workbook.add_format({
            'font_name': 'KacstBook',
            'font_size': 12,
            'border': 1
        })
        date_format = workbook.add_format(
            {'num_format': 'dd-mm-yyyy', 'align': 'right',
             'valign': 'vright', 'border': 1})
        table_header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'bg_color': '#ed1b0c',
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
        })
        table_cell_format_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'left',
            'valign': 'vleft',
        })
        table_cell_format_right = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'right',
            'valign': 'vright',
        })

        sheet = workbook.add_worksheet('data')
        # sheet.set_column(0, 10, 20)
        # [sheet.set_row(idx, 20) for idx in range(10)]
        # sheet.set_row(3, 60)
        # sheet.set_row(4, 60)
        sheet.set_column(6, 6, 60)
        company = self.env.company
        sheet.write('A3', company.name, font_size_10)

        headers = [
            ['Customer', 25],
            ['Creation Date', 15],
            ['Order Reference', 18],
            ['PO Date', 15],
            ['PO Expiration Date', 20],
            ['Customer Reference', 20],
            ['Order Lines/Product', 25],
            ['Order Lines/Article Code', 25],
            ['Order Lines/Size', 20],
            ['Order Lines/Description', 30],
            ['Order Lines/Product/Sales Price', 30],
            ['Order Lines/Taxes', 25],
            ['Order Lines/Quantity', 20],
            ['Order Lines/Delivery Quantity', 28],
            ['Order Lines/Invoiced Quantity', 28]
        ]

        for index, val in enumerate(headers):
            sheet.set_column(index, index, val[1])
            sheet.write(0, index, val[0], table_header_format)

        row = 1
        for sale in self:
            for line in sale.order_line:
                col = 0
                sheet.write(row, col, line.order_id.partner_id.name, table_cell_format_left)
                col += 1
                sheet.write(row, col, line.order_id.create_date, date_format)
                col += 1
                sheet.write(row, col, line.order_id.name, table_cell_format_left)
                col += 1
                sheet.write(row, col, line.order_id.po_date or None, date_format)
                col += 1
                sheet.write(row, col, line.order_id.po_ex_date or None, date_format)
                col += 1
                sheet.write(row, col, line.order_id.client_order_ref or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.product_id.name, table_cell_format_left)
                col += 1
                sheet.write(row, col, line.product_id.default_code, table_cell_format_left)
                col += 1
                sheet.write(row, col, line.size or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.name, table_cell_format_left)
                col += 1
                sheet.write(row, col, line.product_id.list_price, table_cell_format_right)
                col += 1
                tax_ids = ', '.join([tax['name'] for tax in line.tax_id])
                sheet.write(row, col, tax_ids or '', table_cell_format_left)
                col += 1
                sheet.write(row, col, line.product_uom_qty, table_cell_format_right)
                col += 1
                sheet.write(row, col, line.qty_delivered, table_cell_format_right)
                col += 1
                sheet.write(row, col, line.qty_invoiced, table_cell_format_right)

                row += 1

        workbook.close()
        output.seek(0)

        self.write({'file_name': filename + str(datetime.today().strftime('%Y-%m-%d')) + '.xlsx'})
        self.excel_file = base64.encodebytes(output.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'name': filename,
            'url': '/web/content/sale.order/%s/excel_file?download=true' % self[0].id,
            'target': 'new'
        }

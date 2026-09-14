from odoo import models


class SaleOrderReport(models.AbstractModel):
    _name = "report.icorets.saleorder_report_xls"
    _inherit = "report.report_xlsx.abstract"
    _description = "Sale Order XLSX Report"

    def generate_xlsx_report(self, workbook, data, lines):
        bold = workbook.add_format(
            {'font_size': 11, 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7', 'font': 'Calibri Light',
             'text_wrap': True, 'border': 1})
        bold_red = workbook.add_format(
            {'font_size': 11, 'color': '#FF0000', 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7',
             'font': 'Calibri Light',
             'text_wrap': True, 'border': 1})
        sheet = workbook.add_worksheet('Location Summary')
        sheet.set_column(0, 0, 20)
        sheet.set_column(0, 1, 25)
        sheet.set_column(0, 2, 25)
        sheet.set_column(0, 3, 25)
        sheet.set_column(0, 4, 25)
        sheet.set_column(0, 5, 25)
        sheet.set_column(0, 6, 25)
        sheet.set_column(0, 7, 25)
        sheet.set_column(0, 8, 25)
        sheet.set_column(0, 9, 25)
        sheet.set_column(0, 10, 25)
        sheet.set_column(0, 11, 25)
        sheet.set_column(0, 12, 25)
        sheet.set_column(0, 13, 25)
        sheet.set_column(0, 14, 25)
        sheet.set_column(0, 15, 25)
        sheet.set_column(0, 16, 25)
        sheet.set_column(0, 17, 25)
        sheet.set_column(0, 18, 25)
        sheet.set_column(0, 19, 25)
        sheet.set_column(0, 20, 25)
        sheet.set_column(0, 21, 17)
        sheet.set_column(0, 22, 17)
        sheet.set_column(0, 23, 17)
        sheet.set_column(0, 24, 17)
        sheet.set_column(0, 25, 25)
        sheet.set_column(0, 26, 25)
        sheet.set_column(0, 27, 25)
        sheet.set_column(0, 28, 25)
        sheet.set_column(0, 29, 25)

        # **************************************************
        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'ASIN', bold)
        sheet.write(0, 2, 'FSN', bold)
        sheet.write(0, 3, 'SKU', bold)
        sheet.write(0, 4, 'Description', bold)
        sheet.write(0, 5, 'Article Code', bold)
        sheet.write(0, 6, 'Barcode', bold)
        sheet.write(0, 7, 'Color', bold)
        sheet.write(0, 8, 'Size', bold)
        sheet.write(0, 9, 'MRP', bold)
        sheet.write(0, 10, 'Quantity', bold)
        sheet.write(0, 11, 'Invoiced Quantity', bold)
        sheet.write(0, 12, 'Balance to Pack', bold)
        sheet.write(0, 13, 'Packed Qty', bold)
        sheet.write(0, 14, 'Destination Location', bold)

        sheet.freeze_panes(1, 0)

        row = 1
        col = 0

        sale_order = self.env['sale.order'].search([])

        for record in sale_order:
            if record.name == lines.origin:
                for rec in record.order_line:
                    sheet.write(row, col, str(rec.product_id.brand_id_rel.name))
                    sheet.write(row, col + 1, rec.product_id.variants_asin)
                    sheet.write(row, col + 2, rec.product_id.variants_fsn)
                    sheet.write(row, col + 3, rec.product_id.default_code)
                    sheet.write(row, col + 4, rec.name)
                    sheet.write(row, col + 5, rec.article_code)
                    sheet.write(row, col + 6, rec.product_id.barcode)
                    sheet.write(row, col + 7, rec.product_id.color)
                    sheet.write(row, col + 8, rec.product_id.size)
                    sheet.write(row, col + 9, rec.product_id.lst_price)
                    sheet.write(row, col + 10, rec.product_uom_qty)
                    sheet.write(row, col + 11, rec.qty_invoiced)
                    row += 1

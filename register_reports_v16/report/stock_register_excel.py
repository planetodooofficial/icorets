from odoo import api, models, fields, _


class StockRegisterReport(models.AbstractModel):
    _name = "report.register_reports_v16.stock_register_excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, report):
        print("generate_xlsx_report is working")
        worksheet = workbook.add_worksheet("Report")
        move_line_list = self.search_po(report)
        move_list = self.search_po(report)
        move_line_list = move_line_list[0]
        move_list = move_list[1]
        header_report = workbook.add_worksheet("Header Report")

        worksheet.set_column("A:A", 10)

        worksheet.set_column("B:B", 10)

        worksheet.write("A1", "Brand")
        worksheet.write("B1", "Category 1")
        worksheet.write("C1", "Category 2")
        worksheet.write("D1", "Category 3")
        worksheet.write("E1", "Function Sport")
        worksheet.write("F1", "Gender")
        worksheet.write("G1", "Title")
        worksheet.write("H1", "Composition / Material")
        worksheet.write("I1", "Technology / Features")
        worksheet.write("J1", "Event")
        worksheet.write("K1", "HSN Code")
        worksheet.write("L1", "Style Code")
        worksheet.write("M1", "Article Code")
        worksheet.write("N1", "SKU")
        worksheet.write("O1", "EAN Code")
        worksheet.write("P1", "ASIN")
        worksheet.write("Q1", "FSIN")
        worksheet.write("R1", "Colour")
        worksheet.write("S1", "Size")
        # worksheet.write("Q1", "Untaxed Amount")
        worksheet.write("T1", "MRP")
        worksheet.write("U1", "GST")
        worksheet.write("V1", "Opening Stock")
        worksheet.write("W1", "Closing Stock")


        row = 1



    def search_po(self, report_data):
        po_line_list = []
        # Domains for filtering according to fields in form view
        move_line_list = []
        move_list = []
        # Date Filter
        if report_data.to_date and report_data.from_date:
            # IN stock
            in_stock_moves = self.env['stock.move'].search([
                ('location_id.usage', '=', 'supplier'),
                ('location_dest_id.usage', '=', 'internal'),
                ('state', '=', 'done'),
                ('date', '>=', report_data.from_date),('date', '<=', report_data.to_date)
            ])
            quantities_in_by_product = in_stock_moves.read_group(
                [('id', 'in', in_stock_moves.ids)], ['product_id', 'product_qty'], ['product_id']
            )

            total_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in quantities_in_by_product}
            print(total_quantities_by_product)

            # Out Stock

            out_stock_moves = self.env['stock.move'].search([
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'customer'),
                ('state', '=', 'done'),
                ('date', '>=', report_data.from_date),('date', '<=', report_data.to_date)
            ])

            # Get the quantities of each product_id
            quantities_out_by_product = out_stock_moves.read_group(
                [('id', 'in', out_stock_moves.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_out_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in quantities_out_by_product}

        #     Opening Stock

            opening_moves = self.env['stock.move'].search([
                    ('location_id.usage', '!=', 'internal'),
                    ('location_dest_id.usage', '=', 'internal'),
                    ('state', '=', 'done'),
                    ('date', '<', report_data.from_date)])

            quantities_opening_by_product = opening_moves.read_group(
                [('id', 'in', opening_moves.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_opening_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                               quantities_opening_by_product}




        return move_line_list, move_list



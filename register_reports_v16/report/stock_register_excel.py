from odoo import api, models, fields, _


class StockRegisterReport(models.AbstractModel):
    _name = "report.register_reports_v16.stock_register_excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, report):
        print("generate_xlsx_report is working")
        worksheet = workbook.add_worksheet("Report")
        move_line_list = self.search_po(report)

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
        worksheet.write("V1", "IHO Opening Stock")
        worksheet.write("W1", "Bhiwandi Opening Stock")
        worksheet.write("X1", "Delhi Opening Stock")
        worksheet.write("Y1", "Total Opening Stock Qty")
        worksheet.write("Z1", "Total Purchase Qty")
        worksheet.write("Z1", "Total Purchase Qty")
        worksheet.write("AA1", "Purchase Returns Qty")
        worksheet.write("AB1", "Total Sales Qty")
        worksheet.write("AC1", "Sales Returns Qty")

        row = 1

        for rec in move_line_list:
            search_product = self.env['product.product'].search([('id', '=', rec)])
            worksheet.write(row, 0, search_product.brand_id_rel.name or ' ', )
            worksheet.write(row, 1, search_product.categ_id.parent_id.parent_id.name or ' ', )
            worksheet.write(row, 2, search_product.categ_id.parent_id.name or ' ', )
            worksheet.write(row, 3, search_product.categ_id.name or ' ', )
            worksheet.write(row, 4, search_product.variants_func_spo or ' ', )
            worksheet.write(row, 5, search_product.gender or ' ', )
            worksheet.write(row, 6, search_product.name or ' ', )
            worksheet.write(row, 7, search_product.default_code or ' ', )
            worksheet.write(row, 8, search_product.material or ' ', )
            worksheet.write(row, 9, search_product.variants_tech_feat or ' ', )
            worksheet.write(row, 10, search_product.occasion or ' ', )
            worksheet.write(row, 11, search_product.l10n_in_hsn_code or search_product.sale_hsn.hsnsac_code or ' ', )
            worksheet.write(row, 12, search_product.style_code or ' ', )
            worksheet.write(row, 13, search_product.variant_article_code or ' ', )
            worksheet.write(row, 14, search_product.barcode or ' ', )
            worksheet.write(row, 15, search_product.variants_asin or ' ', )
            worksheet.write(row, 16, search_product.variants_fsn or ' ', )
            worksheet.write(row, 17, search_product.color or ' ', )
            worksheet.write(row, 18, search_product.size or ' ', )
            worksheet.write(row, 19, search_product.lst_price or ' ', )
            worksheet.write(row, 20, ''.join(
                [str(x) for x in search_product.taxes_id.name]) if search_product.taxes_id else '' or ' ', )
            worksheet.write(row, 21, move_line_list[rec][2] or ' ', )
            worksheet.write(row, 22, ' ', )
            worksheet.write(row, 23, ' ', )
            worksheet.write(row, 24, ' ', )
            worksheet.write(row, 25, move_line_list[rec][0] or ' ', )
            row = row + 1

    def search_po(self, report_data):
        po_line_list = []
        # Domains for filtering according to fields in form view
        move_line_list = []
        move_list = []
        all_data = {}
        # Date Filter
        if report_data.to_date and report_data.from_date:
            # IN stock
            in_stock_moves = self.env['stock.move'].search([
                ('location_id.usage', '=', 'supplier'),
                ('location_dest_id.usage', '=', 'internal'),
                ('state', '=', 'done'),
                ('date', '>=', report_data.from_date), ('date', '<=', report_data.to_date)
            ])
            quantities_in_by_product = in_stock_moves.read_group(
                [('id', 'in', in_stock_moves.ids)], ['product_id', 'product_qty'], ['product_id']
            )

            total_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                           quantities_in_by_product}

            # Out Stock

            out_stock_moves = self.env['stock.move'].search([
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'customer'),
                ('state', '=', 'done'),
                ('date', '>=', report_data.from_date), ('date', '<=', report_data.to_date)
            ])

            # Get the quantities of each product_id
            quantities_out_by_product = out_stock_moves.read_group(
                [('id', 'in', out_stock_moves.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_out_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                               quantities_out_by_product}

            #     Opening Stock mum

            search_mumbai = self.env['stock.warehouse'].search([('name','=','Mumbai')])

            opening_moves_in_mumbai = self.env['stock.move'].search(['|',
                ('location_id.warehouse_id', '=', False),  # Check if warehouse is not set
                ('location_id.warehouse_id.id', '!=', search_mumbai.id),
                ('location_dest_id.warehouse_id.id','=',search_mumbai.id),
                ('state', '=', 'done'),
                ('date', '<', report_data.from_date)])

            # print(opening_moves_in_mumbai)

            quantities_opening_in_mum_by_product = opening_moves_in_mumbai.read_group(
                [('id', 'in', opening_moves_in_mumbai.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_opening_in_mum_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                                   quantities_opening_in_mum_by_product}



            opening_moves_out_mumbai = self.env['stock.move'].search(['|',
                ('location_dest_id.warehouse_id','=',False),
                ('location_dest_id.warehouse_id.id', '!=',search_mumbai.id),
                ('location_id.warehouse_id', '=', search_mumbai.id),
                ('location_dest_id.usage', '!=', 'internal'),
                ('state', '=', 'done'),
                ('date', '<', report_data.from_date)])

            quantities_opening_out_mum_by_product = opening_moves_out_mumbai.read_group(
                [('id', 'in', opening_moves_out_mumbai.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_opening_out_mum_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                                          quantities_opening_out_mum_by_product}

            mumbai_opening = {k: total_opening_in_mum_quantities_by_product.get(k, 0) - total_opening_out_mum_quantities_by_product.get(k, 0) for k in set(total_opening_in_mum_quantities_by_product) | set(total_opening_out_mum_quantities_by_product)}

            # bhiwandi opening

            opening_moves_in_bhiwandi = self.env['stock.move'].search([
                ('location_id.usage', '!=', 'internal'),
                ('location_dest_id.usage', '=', 'internal'),
                ('warehouse_id.name', '=', 'Bhiwandi'),
                ('state', '=', 'done'),
                ('date', '<', report_data.from_date)])

            quantities_opening_in_bhiwandi_by_product = opening_moves_in_mumbai.read_group(
                [('id', 'in', opening_moves_in_bhiwandi.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_opening_in_bhiwandi_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                                          quantities_opening_in_bhiwandi_by_product}

            opening_moves_out_bhiwandi = self.env['stock.move'].search([
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '!=', 'internal'),
                ('warehouse_id.name', '=', 'Bhiwandi'),
                ('state', '=', 'done'),
                ('date', '<', report_data.from_date)])

            quantities_opening_out_bhiwandi_by_product = opening_moves_out_mumbai.read_group(
                [('id', 'in', opening_moves_out_mumbai.ids)], ['product_id', 'product_qty'], ['product_id']
            )
            total_opening_out_bhiwandi_quantities_by_product = {data['product_id'][0]: data['product_qty'] for data in
                                                           quantities_opening_out_bhiwandi_by_product}

            bhiwandi_opening = {k: total_opening_in_bhiwandi_quantities_by_product.get(k,
                                                                                0) - total_opening_out_bhiwandi_quantities_by_product.get(
                k, 0) for k in set(total_opening_in_bhiwandi_quantities_by_product) | set(
                total_opening_out_bhiwandi_quantities_by_product)}

            all_keys = set().union(total_quantities_by_product, total_out_quantities_by_product,
                                   mumbai_opening,bhiwandi_opening)

            # Initialize dictionary e

            # Populate values for each key in dictionary e
            for key in all_keys:
                all_data[key] = [total_quantities_by_product.get(key, 0), total_out_quantities_by_product.get(key, 0),
                                 mumbai_opening.get(key, 0),bhiwandi_opening.get(key,0)]

        return all_data

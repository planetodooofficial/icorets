from odoo import api, models, fields, _
import string


class StockRegisterReport(models.AbstractModel):
    _name = "report.gts_icore_reports.stock_location_wise_excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, report):
        print("generate_xlsx_report is working")
        worksheet = workbook.add_worksheet("Report")
        # header_report = workbook.add_worksheet("Header Report")
        worksheet.set_column("A:A", 10)

        worksheet.set_column("B:B", 10)
        style_header1 = workbook.add_format({
            'bold': 1,
            'border': 1,
            'bg_color': '#dadce0',
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'})

        number_format = workbook.add_format({'num_format': '#,###.00', 'bold': 0,
            'border': 1, 'align': 'right',})

        # List of all headers extracted from the image
        headers1 = [
            "Brand", "Category 1", "Category 2", "Category 3", "Function Sport",
            "Gender", "Age group", "Title", "Marketplace Tittle", "Composition / Material", "Technology / Features",
            "Event", "HSN Code", "Style Code", "Article Code", "SKU", "EAN Code", "ASIN",
            "FSIN", "Myntra", "AJIO", "Fancode", "Swiggy",
            "Bigbasket", "Blinkit", "Zepto", "Colour", "Size", "MRP", "GST",

        ]
        company = self.env.company
        location_domain = [('company_id', '=', company.id), ('usage', 'in', ['internal', 'inventory', 'supplier',
                                                                             'customer'])]
        locations = self.env['stock.location'].search(location_domain)
        # print("----locations....", locations)
        # Write headers to the first row dynamically

        header_col = 0
        for col_num, header in enumerate(headers1):
            worksheet.write(0, col_num, header, style_header1)
            # print("col_num...", col_num)
            header_col += 1
        # print("--header_col-", header_col)
        for location in locations:
            # print("......--location.complete_name", location)
            worksheet.write(0, header_col, 'Opening ' + location.complete_name, style_header1)
            header_col += 1

        headers3 = ["Total Qty Opening",
                    'Purchase', 'Purchase Return', "Total Purchase", "Average P Rate (Excl GST)",
                    "Average P Rate (Inc GST)", "Total Purchase Value(Excl GST)", "Total Purchase Value(Inc GST)",

                    'Sales', 'Sales Return', "Total Sales", "Average Sales Rate (Excl GST)",
                    "Average Sales Rate (Inc GST)", "Total Sales Value(Excl GST)", "Total Sales Value(Inc GST)",
                    ]
        for col_num, header in enumerate(headers3):
            worksheet.write(0, header_col, header, style_header1)
            header_col += 1

        # Closing Location Headers
        for location in locations:
            # print("......--location.complete_name", location)
            worksheet.write(0, header_col, 'Closing ' + location.complete_name, style_header1)
            header_col += 1

        headers4 = ["Total Qty Closing", "Closing Stock Value(Excluding Taxes)",
                                         "Sales Quotation Qty", "Confirmed SO Qty(Not Invoiced)",
                    "Free To Use",

                    "PO Receipt Pending(GRN)", "PO Receipt Pending(Bills)", "Average Rate (Excl GST)",
                    "Total Value(Excl GST)", "To Replenish", "Google Drive Link"]

        for col_num, header in enumerate(headers4):
            worksheet.write(0, header_col, header, style_header1)
            header_col += 1

        # for col_num in range(50):  # 26 columns (A-Z)
        #     col_letter = chr(65 + col_num)  # Convert number to letter (A, B, C, ...)
        #     worksheet.set_column(f'{col_letter}:{col_letter}', 30)
        worksheet.set_row(0, 50)
        data = self.get_report_data(report, locations)
        # Header Columns ---> [
        #     "Brand", "Category 1", "Category 2", "Category 3", "Function Sport",
        #     "Gender", "Age group", "Title", "Marketplace Tittle", "Composition / Material", "Technology / Features",
        #     "Event", "HSN Code", "Style Code", "Article Code", "SKU", "EAN Code", "ASIN",
        #     "FSIN", "Myntra", "AJIO", "Fancode", "Swiggy",
        #     "Bigbasket", "Blinkit", "Zepto", "Colour", "Size", "MRP", "GST",
        #
        # ]
        row = 1
        cols = list(string.ascii_uppercase)
        # cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
        #         'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM',
        #         'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ', 'BA', 'BB', 'BC', 'BD',
        #         'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU',
        #         'BV', 'BW', 'BX', 'BY', 'BZ', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CI', 'CJ', 'CK', 'CL',
        #         'CM', 'CN', 'CO', 'CP', 'CQ', 'CR', 'CS', 'CT', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DA', 'DB', 'DC',
        #         'DD', 'DE', 'DF', 'DG', 'DH', 'DI', 'DJ', 'DK', 'DL', 'DM', 'DN', 'DO', 'DP', 'DQ', 'DR', 'DS', 'DT',
        #         'DU', 'DV', 'DW', 'DX', 'DY', 'DZ']
        # Generate columns from AA to DZ
        for first in string.ascii_uppercase:
            for second in string.ascii_uppercase:
                col1 = first + second
                cols.append(col1)
                if col1 == 'DZ':
                    break  # Stop once we reach 'DZ'
            if col1 == 'DZ':
                break  # Exit outer loop too
        for rec in data:
            # print("---data----", data[rec][10])
            # print("-----rec...", rec)
            search_product = self.env['product.product'].browse(rec)
            worksheet.write(row, 0, search_product.brand_id_rel.name)
            worksheet.write(row, 1, search_product.categ_id.parent_id.parent_id.name or ' ', )
            worksheet.write(row, 2, search_product.categ_id.parent_id.name or ' ', )
            worksheet.write(row, 3, search_product.categ_id.name or ' ', )
            worksheet.write(row, 4, search_product.variants_func_spo or ' ', )
            worksheet.write(row, 5, search_product.gender or ' ', )
            worksheet.write(row, 6, search_product.age_group or ' ', )
            worksheet.write(row, 7, search_product.name or ' ', )
            worksheet.write(row, 8, search_product.market_place_tittle or ' ', )
            worksheet.write(row, 9, search_product.material, )
            worksheet.write(row, 10, search_product.variants_tech_feat or ' ', )
            worksheet.write(row, 11, search_product.occasion or ' ', )
            worksheet.write(row, 12, search_product.l10n_in_hsn_code or search_product.sale_hsn.hsnsac_code or ' ', )
            worksheet.write(row, 13, search_product.style_code or ' ', )
            worksheet.write(row, 14, search_product.variant_article_code or ' ', )
            worksheet.write(row, 15, search_product.default_code or ' ', )
            worksheet.write(row, 16, search_product.variants_ean_code or ' ', )
            worksheet.write(row, 17, search_product.variants_asin or ' ', )
            worksheet.write(row, 18, search_product.variants_fsn or ' ', )

            worksheet.write(row, 19, search_product.myntra or ' ', )
            worksheet.write(row, 20, search_product.ajio or ' ', )
            worksheet.write(row, 21, search_product.fancode or ' ', )
            worksheet.write(row, 22, search_product.swiggy or ' ', )
            worksheet.write(row, 23, search_product.bigbasket or ' ', )
            worksheet.write(row, 24, search_product.blinkit or ' ', )
            worksheet.write(row, 25, search_product.zepto or ' ', )
            worksheet.write(row, 26, search_product.color or ' ', )
            worksheet.write(row, 27, search_product.size or ' ', )
            worksheet.write(row, 28, search_product.lst_price or ' ', )
            worksheet.write(row, 29, ''.join(
                [str(x) for x in search_product.taxes_id.name]) if search_product.taxes_id else '' or ' ', )
            col = 30
            total_qty = 0
            for location in locations:
                loc_qty_available = search_product.with_context(
                    {'location': location.id, 'to_date': report.from_date}).qty_available
                worksheet.write(row, col, loc_qty_available or 0, number_format)
                if not location.usage == 'inventory':
                    total_qty += loc_qty_available
                col += 1
            worksheet.write(row, col, total_qty or 0, number_format)
            col += 1

            # purchase
            worksheet.write(row, col, data[rec][12] or 0, number_format)
            col += 1

            # purchase return
            worksheet.write(row, col, data[rec][1] or 0, number_format)
            col += 1
            worksheet.write(row, col, f'=IFERROR({cols[col - 2]}{row + 1}-{cols[col - 1]}{row + 1}, 0)' or 0, number_format)
            col += 1

            # Avg Purchase Unit Exl
            if isinstance(data[rec][2], list):
                worksheet.write(row, col, data[rec][2][1] / data[rec][2][0] or 0, number_format)
                col += 1
            else:
                worksheet.write(row, col, data[rec][2] or 0, number_format)
                col += 1

            # Avg Purchase Unit Inc
            if isinstance(data[rec][2], list):
                worksheet.write(row, col, data[rec][2][2] / data[rec][2][0] or 0, number_format)
                col += 1
            else:
                worksheet.write(row, col, data[rec][2] or 0, number_format)
                col += 1
            worksheet.write(row, col, f'=IFERROR({cols[col - 3]}{row + 1}*{cols[col - 2]}{row + 1}, 0)' or 0, number_format)
            col += 1
            worksheet.write(row, col, f'=IFERROR({cols[col - 4]}{row + 1}*{cols[col - 2]}{row + 1}, 0)' or 0, number_format)
            col += 1

            # sales section
            worksheet.write(row, col, data[rec][11] or 0, number_format)
            col += 1

            # sales return
            worksheet.write(row, col, data[rec][4] or 0, number_format)
            col += 1

            worksheet.write(row, col, f'=IFERROR({cols[col-2]}{row + 1}-{cols[col-1]}{row + 1}, 0)' or 0, number_format)
            col += 1
            # Avg sales Unit Exl
            if isinstance(data[rec][5], list):
                worksheet.write(row, col, data[rec][5][1] / data[rec][5][0] or 0, number_format)
                col += 1
            else:
                worksheet.write(row, col, data[rec][5] or 0, number_format)
                col += 1

            # Avg sales Unit Inc
            if isinstance(data[rec][5], list):
                worksheet.write(row, col, data[rec][5][2] / data[rec][5][0] or 0, number_format)
                col += 1
            else:
                worksheet.write(row, col, data[rec][5] or 0, number_format)
                col += 1
            worksheet.write(row, col, f'=IFERROR({cols[col-3]}{row + 1}*{cols[col - 2]}{row + 1}, 0)' or 0, number_format)
            col += 1
            worksheet.write(row, col, f'=IFERROR({cols[col-4]}{row + 1}*{cols[col - 2]}{row + 1}, 0)' or 0, number_format)
            col += 1

            # location wise closing stock value
            total_closing_qty = 0
            for location in locations:
                loc_closing_qty_available = search_product.with_context(
                    {'location': location.id, 'to_date': report.to_date}).qty_available
                worksheet.write(row, col, loc_closing_qty_available or 0, number_format)
                if not location.usage == 'inventory':
                    total_closing_qty += loc_closing_qty_available
                col += 1

            worksheet.write(row, col, total_closing_qty or 0, number_format)
            col += 1
            # Closing Stock Value(Excluding Taxes)
            worksheet.write(row, col, 0 or 0, number_format)
            col += 1

            worksheet.write(row, col, data[rec][7] or 0, number_format)
            col += 1
            #Todo: Confirmed SO Qty(Not Invoiced)
            worksheet.write(row, col, data[rec][6] or 0, number_format)
            col += 1

            # free to use
            worksheet.write(row, col, 0, number_format)
            col += 1

            worksheet.write(row, col, data[rec][8], number_format)
            col += 1
            #todo: PO Receipt Pending(Bills)
            worksheet.write(row, col, data[rec][9], number_format)
            col += 1
            if isinstance(data[rec][10], list):
                if data[rec][10][1] != 0 and data[rec][10][0] != 0:
                    worksheet.write(row, col, data[rec][10][1]/data[rec][10][0], number_format)
                    col += 1
                else:
                    worksheet.write(row, col, 0, number_format)
                    col += 1
                if data[rec][10][2] != 0 and data[rec][10][0] != 0:
                    worksheet.write(row, col, data[rec][10][2]/data[rec][10][0], number_format)
                    col += 1
                else:
                    worksheet.write(row, col, 0, number_format)
                    col += 1
            else:
                worksheet.write(row, col, 0, number_format)
                col += 1
                worksheet.write(row, col, 0, number_format)
                col += 1
            worksheet.write(row, col, 0, number_format)
            col += 1
            worksheet.write(row, col, search_product.google_drive_link, )
            col += 1

            row += 1


        # print("---data---", data)

    def get_report_data(self, report_data, locations):
        print("get_report_data is working")
        # Implement your custom logic to fetch data from the database
        # For this example, we are assuming that the data is stored in a variable called 'data'
        all_data = {}
        if report_data.to_date and report_data.from_date:
            stock_moves = self.env['stock.move']
            if report_data.product_category:
                category = report_data.product_category.ids
            else:
                all_category = self.env['product.category'].search([])
                category = all_category.ids
            # products = self.env['product.product'].search([('categ_id', 'in', category), ('id', '=', 21286)])
            product_domain = ('product_id', 'in', [39935, 47653, 47700, 40037])
            sale_line_confirm = self.env['sale.order.line'].search(
                [('product_id.categ_id.id', 'in', category),
                 ('order_id.date_order', '>=', report_data.from_date),
                 ('order_id.date_order', '<=', report_data.to_date),
                 ('state', 'in', ['sale', 'done'])
                 ])
            # sale_line_confirm_qty = sum(sale_line_confirm.mapped("product_uom_qty"))
            sale_line_confirm_qty = sale_line_confirm.read_group([('id', 'in', sale_line_confirm.ids)],
                                                                 ['product_id', 'qty_to_invoice'],
                                                                 ['product_id'])
            sale_line_confirm_qty_by_product = {data['product_id'][0]: data['qty_to_invoice'] for data in
                                                sale_line_confirm_qty}

            #Todo: Sales Done For current
            sale_line_done_confirm_qty = sale_line_confirm.read_group([('id', 'in', sale_line_confirm.ids)],
                                                                 ['product_id', 'qty_delivered'],
                                                                 ['product_id'])
            sale_line_done_qty_by_product = {data['product_id'][0]: data['qty_delivered'] for data in
                                                sale_line_done_confirm_qty}

            # sale quotation quantities by product

            sale_line_quotation = self.env['sale.order.line'].search(
                [('product_id.categ_id.id', 'in', category),
                 ('order_id.date_order', '>=',
                  report_data.from_date),
                 ('order_id.date_order', '<=',
                  report_data.to_date),
                 ('state', 'in', ['draft', 'sent'])
                 ])

            sale_line_quotation_qty = sale_line_quotation.read_group([('id', 'in', sale_line_quotation.ids)],
                                                                     ['product_id', 'product_uom_qty'],
                                                                     ['product_id'])
            sale_line_quotation_qty_by_product = {data['product_id'][0]: data['product_uom_qty'] for data in
                                                  sale_line_quotation_qty}


            # Purchase Receipt Pending Quantity
            receipts = stock_moves.search(
                [('product_id.categ_id.id', 'in', category), ('state', '!=', 'done'),
                 ('purchase_line_id', '!=', False),
                 ('date', '>=', report_data.from_date),
                 ('date', '<=', report_data.to_date),
                 ])
            purchase_receipt_pending_qty = receipts.read_group([('id', 'in', receipts.ids)],
                                                               ['product_id', 'product_uom_qty'],
                                                               ['product_id'])
            purchase_receipt_pending_qty_by_product = {data['product_id'][0]: data['product_uom_qty'] for data in
                                                       purchase_receipt_pending_qty}

            # purchase qty
            purchase_bills = self.env['account.move.line'].search([('product_id.categ_id.id', 'in', category),
                                                                   ('parent_state', '=', 'posted'),
                                                                   ('date', '>=', report_data.from_date),
                                                                   ('date', '<=', report_data.to_date),
                                                                   ('move_type', '=', 'in_invoice')
                                                                   ])
            purchase_bills_qty = purchase_bills.read_group([('id', 'in', purchase_bills.ids)],
                                                           ['product_id', 'quantity', 'price_subtotal'],
                                                           ['product_id'])
            purchase_bills_qty_by_product = {data['product_id'][0]: data['quantity'] for data in
                                             purchase_bills_qty}
            #Todo : Purchase qty and bills
            purchase_pending_bills = self.env['purchase.order.line'].search(
                [('product_id.categ_id.id', 'in', category),
                 ('order_id.date_order', '>=',
                  report_data.from_date),
                 ('order_id.date_order', '<=',
                  report_data.to_date),
                 ('state', 'in', ['done', 'purchase'])
                 ])
            po_pending_bills = purchase_pending_bills.read_group([('id', 'in', purchase_pending_bills.ids)],
                                                           ['product_id', 'qty_to_invoice',],
                                                           ['product_id'])
            po_pending_bills_qty_by_product = {data['product_id'][0]: data['qty_to_invoice'] for data in
                                             po_pending_bills}

            #Todo : Purchase Done For Current
            po_done_qty = purchase_pending_bills.read_group([('id', 'in', purchase_pending_bills.ids)],
                                                                 ['product_id', 'qty_received', ],
                                                                 ['product_id'])
            po_done_qty_by_product = {data['product_id'][0]: data['qty_received'] for data in
                                               po_done_qty}

            # purchase debit notes qty
            purchase_debit_notes = self.env['account.move.line'].search([('product_id.categ_id.id', 'in', category),
                                                                         ('parent_state', '=', 'posted'),
                                                                         ('date', '>=', report_data.from_date),
                                                                         ('date', '<=', report_data.to_date),
                                                                         ('move_type', '=', '	in_refund')
                                                                         ])
            purchase_debit_qty = purchase_debit_notes.read_group([('id', 'in', purchase_debit_notes.ids)],
                                                                 ['product_id', 'quantity', 'price_subtotal'],
                                                                 ['product_id'])
            purchase_debit_qty_by_product = {data['product_id'][0]: data['quantity'] for data in
                                             purchase_debit_qty}

            purchase_bills_debit_notes = self.env['account.move.line'].search(
                [('product_id.categ_id.id', 'in', category),
                 ('parent_state', '=', 'posted'),
                 ('date', '>=', report_data.from_date),
                 ('date', '<=', report_data.to_date),
                 ('move_type', 'in', ['in_invoice', 'in_refund'])
                 ])

            purchase_bills_debit_qty = purchase_bills_debit_notes.read_group(
                [('id', 'in', purchase_bills_debit_notes.ids)],
                ['product_id', 'quantity', 'price_subtotal', 'price_total'],
                ['product_id'])
            purchase_bills_debit_by_product = {data['product_id'][0]: [data['quantity'], data['price_subtotal'],
                                                                       data['price_total']] for data in
                                               purchase_bills_debit_qty}

            # Todo: This part of invoice sales

            sales_inv = self.env['account.move.line'].search([('product_id.categ_id.id', 'in', category),
                                                              ('parent_state', '=', 'posted'),
                                                              ('date', '>=', report_data.from_date),
                                                              ('date', '<=', report_data.to_date),
                                                              ('move_type', '=', 'in_invoice')
                                                              ])
            sales_inv_qty = sales_inv.read_group([('id', 'in', sales_inv.ids)],
                                                 ['product_id', 'quantity', 'price_subtotal'],
                                                 ['product_id'])
            sales_inv_qty_by_product = {data['product_id'][0]: data['quantity'] for data in
                                        sales_inv_qty}

            # sales debit notes qty return
            sales_credit_notes = self.env['account.move.line'].search([('product_id.categ_id.id', 'in', category),
                                                                       ('parent_state', '=', 'posted'),
                                                                       ('date', '>=', report_data.from_date),
                                                                       ('date', '<=', report_data.to_date),
                                                                       ('move_type', '=', '	in_refund')
                                                                       ])
            sales_credit_qty = sales_credit_notes.read_group([('id', 'in', sales_credit_notes.ids)],
                                                             ['product_id', 'quantity', 'price_subtotal'],
                                                             ['product_id'])
            sales_credit_qty_by_product = {data['product_id'][0]: data['quantity'] for data in
                                           sales_credit_qty}

            # sale invoice and credit notes entry
            sales_inv_credit_notes = self.env['account.move.line'].search(
                [('product_id.categ_id.id', 'in', category),
                 ('parent_state', '=', 'posted'),
                 ('date', '>=', report_data.from_date),
                 ('date', '<=', report_data.to_date),
                 ('move_type', 'in', ['in_invoice', 'in_refund'])
                 ])

            sales_inv_credit_qty = sales_inv_credit_notes.read_group(
                [('id', 'in', sales_inv_credit_notes.ids)],
                ['product_id', 'quantity', 'price_subtotal', 'price_total'],
                ['product_id'])
            sales_inv_credit_by_product = {data['product_id'][0]: [data['quantity'], data['price_subtotal'],
                                                                   data['price_total']] for data in
                                           sales_inv_credit_qty}

            valuations = self.env['stock.valuation.layer'].search(
                [('product_id.categ_id.id', 'in', category),
                 ('create_date', '>=', report_data.from_date),
                 ('create_date', '<=', report_data.to_date),
                 ])

            # valuations_qty = valuations.read_group(
            #     [('id', 'in', valuations.ids)],
            #     ['product_id', 'quantity', 'unit_cost', 'value'],
            #     ['product_id'])
            # print("----valuations_qty-----", valuations_qty)
            valuation_by_product = {
                svl_pro.id: [
                    abs(sum(valuations.filtered(lambda svl: svl.product_id.id == svl_pro.id).mapped('quantity'))),
                    abs(sum(valuations.filtered(lambda svl: svl.product_id.id == svl_pro.id).mapped('unit_cost'))),
                    abs(sum(valuations.filtered(lambda svl: svl.product_id.id == svl_pro.id).mapped('value')))
                ]
                for svl_pro in valuations.mapped('product_id')
            }



            # final dictinry
            all_keys = set().union(purchase_bills_qty_by_product, purchase_debit_qty_by_product,
                                   purchase_bills_debit_by_product,

                                   sales_inv_qty_by_product, sales_credit_qty_by_product, sales_inv_credit_by_product,

                                   sale_line_confirm_qty_by_product, sale_line_quotation_qty_by_product,
                                   purchase_receipt_pending_qty_by_product, valuation_by_product,
                                   sale_line_done_qty_by_product, po_done_qty_by_product)
            # print("---all_keys", all_keys)
            for key in all_keys:
                all_data[key] = [purchase_bills_qty_by_product.get(key, 0), purchase_debit_qty_by_product.get(key, 0),
                                 purchase_bills_debit_by_product.get(key, 0),

                                 sales_inv_qty_by_product.get(key, 0), sales_credit_qty_by_product.get(key, 0),
                                 sales_inv_credit_by_product.get(key, 0),

                                 sale_line_confirm_qty_by_product.get(key, 0),
                                 sale_line_quotation_qty_by_product.get(key, 0),

                                 purchase_receipt_pending_qty_by_product.get(key, 0),
                                 po_pending_bills_qty_by_product.get(key, 0), valuation_by_product.get(key, 0),

                                 sale_line_done_qty_by_product.get(key, 0), po_done_qty_by_product.get(key, 0),
                                 ]
            # print("----all_data", all_data)

        return all_data

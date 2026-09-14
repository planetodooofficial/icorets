import io
from io import BytesIO
import json
import pandas as pd
import xlsxwriter
from odoo.http import content_disposition, request, Controller
from odoo import http
import ast


class DownloadReport(Controller):
    font = "Arial"

    @staticmethod
    def compute_taxes(invoice_line):
        tax_val = dict()
        for tax in invoice_line.tax_ids:
            taxes = tax.compute_all(invoice_line.price_unit, invoice_line.currency_id, invoice_line.quantity,
                                    product=invoice_line.product_id, partner=invoice_line.partner_id)
            for tx in taxes.get('taxes', []):
                name = tx.get('name')
                amount = tx.get('amount')
                if name:
                    tax_val.update({name: amount})
        return tax_val

    @staticmethod
    def get_tax_group_dict(taxes):
        res = {}
        if not taxes or not isinstance(taxes, dict):
            return res
        if 'subtotals' in taxes:
            for sub in taxes.get('subtotals', []):
                for tg in sub.get('tax_groups', []):
                    name = tg.get('group_name') or tg.get('tax_group_name')
                    amt = tg.get('tax_amount') if 'tax_amount' in tg else tg.get('tax_group_amount', 0.0)
                    if name:
                        res[f"Total {name}"] = amt
        elif 'groups_by_subtotal' in taxes:
            for sub_name, tg_list in taxes.get('groups_by_subtotal', {}).items():
                if isinstance(tg_list, list):
                    for tg in tg_list:
                        name = tg.get('tax_group_name') or tg.get('group_name')
                        amt = tg.get('tax_group_amount') if 'tax_group_amount' in tg else tg.get('tax_amount', 0.0)
                        if name:
                            res[f"Total {name}"] = amt
        return res

    @staticmethod
    def get_purchase_tax_amount(move):
        taxes = move.tax_totals or {}
        amt_tax = 0.0
        found = False
        if 'subtotals' in taxes:
            for sub in taxes.get('subtotals', []):
                for tg in sub.get('tax_groups', []):
                    name = tg.get('group_name') or tg.get('tax_group_name') or ''
                    amt = tg.get('tax_amount') if 'tax_amount' in tg else tg.get('tax_group_amount', 0.0)
                    if name not in ["TDS", "TCS"]:
                        amt_tax += amt
                        found = True
        elif 'groups_by_subtotal' in taxes:
            for sub_name, tg_list in taxes.get('groups_by_subtotal', {}).items():
                if isinstance(tg_list, list):
                    for tg in tg_list:
                        name = tg.get('tax_group_name') or tg.get('group_name') or ''
                        amt = tg.get('tax_group_amount') if 'tax_group_amount' in tg else tg.get('tax_amount', 0.0)
                        if name not in ["TDS", "TCS"]:
                            amt_tax += amt
                            found = True
        if not found:
            amt_tax = move.amount_tax
        return amt_tax

    @staticmethod
    def get_move_amounts(move):
        taxes = move.tax_totals or {}
        un_tax_amt = taxes.get('base_amount') if 'base_amount' in taxes else taxes.get('amount_untaxed', move.amount_untaxed)
        total_amt = taxes.get('total_amount') if 'total_amount' in taxes else taxes.get('amount_total', move.amount_total)
        return (un_tax_amt or 0.0), (total_amt or 0.0)

    @staticmethod
    def get_company_details(company_id):
        comp = request.env['res.company'].browse(int(company_id))
        return comp.name or ''

    # styles
    @staticmethod
    def title_format(workbook):
        return workbook.add_format({
            'font_size': 14,
            'font': DownloadReport.font,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'})

    @staticmethod
    def txt_font(workbook):
        return workbook.add_format({'bold': 1, 'bg_color': '#ccccff', })

    @staticmethod
    def txt_font2(workbook):
        return workbook.add_format({'bg_color': '#ccccff', })

    @staticmethod
    def txt_font3(workbook):
        return workbook.add_format({'bold': 1, })

    @staticmethod
    def no_data_found():
        fp = io.BytesIO(b'No Data Found')
        with open('no_data_found.txt', 'wb') as f:
            f.write(fp.getbuffer())
        out = fp.getvalue()
        pdfhttpheaders = [('Content-Type', 'application/octet-stream'),
                          ('Content-Disposition', content_disposition(f"No Data Found.txt"))]
        return request.make_response(out, headers=pdfhttpheaders)

    @staticmethod
    def decorate_worksheet(worksheet, df):
        columns = df.columns
        max_width = 50
        for pos, col in enumerate(columns):
            max_str = max(df[col].apply(str).str.len()) + 5
            col_name_len = len(col) + 5
            col_size = max_width if max_str > max_width else col_name_len if max_str < col_name_len else max_str
            worksheet.set_column(pos, pos, col_size)
        worksheet.freeze_panes(2, 0)

    @staticmethod
    def dataframe_operations(data, sheet_name, writer):
        if data:
            df = pd.DataFrame(data)
            sort_column = df.columns[0]
            nan_value = float("NaN")
            df.replace("", nan_value, inplace=True)
            df.dropna(how='all', axis=1, inplace=True)
            df.sort_values(by=sort_column, inplace=True)
            df.loc['Column_Total'] = df.sum(numeric_only=True, axis=0)
            df.to_excel(writer, index=False, startrow=1, sheet_name=sheet_name)
            DownloadReport.decorate_worksheet(writer.sheets[sheet_name], df)
        else:
            df = pd.DataFrame()
            df.to_excel(writer, index=False, startrow=1, sheet_name=sheet_name)

    @staticmethod
    def create_summary_sheet(writer):
        workbook = writer.book
        summary_sheet = workbook.add_worksheet('Summary')
        return summary_sheet

    @staticmethod
    def detail_sales_register(start_date, end_date, invoice_data, company_id, *args, **kwargs):
        fp = BytesIO()
        writer = pd.ExcelWriter(fp, engine='xlsxwriter')
        summary_sheet = DownloadReport.create_summary_sheet(writer)

        def get_detailed_sales_data(invoices, sheet_name):
            data_rows = []
            gst_data = {}

            def convert_curr(amount, move):
                if move.currency_id and move.company_id.currency_id and move.currency_id != move.company_id.currency_id:
                    date = move.invoice_date or move.date
                    return move.currency_id._convert(amount, move.company_id.currency_id, move.company_id, date)
                return amount

            for invoice_line in invoices.invoice_line_ids.filtered(
                    lambda line: line.display_type not in ['line_section', 'line_note']):
                taxes = invoice_line.move_id.tax_totals or {}
                pod_status = 'POD Received' if invoice_line.move_id.pod_document_id else 'POD Not Received'
                un_tax_amt, total_amt = DownloadReport.get_move_amounts(invoice_line.move_id)

                product = invoice_line.product_id
                uom_name = invoice_line.product_uom_id.name or (product.uom_id.name if product else '')
                categ_1 = product.categ_id.parent_id.parent_id.name if (product and product.categ_id and product.categ_id.parent_id and product.categ_id.parent_id.parent_id) else ''
                categ_2 = product.categ_id.parent_id.name if (product and product.categ_id and product.categ_id.parent_id) else ''
                categ_3 = product.categ_id.name if (product and product.categ_id) else ''

                po_number = invoice_line.move_id.ref if invoice_line.move_id.move_type != 'out_refund' else (invoice_line.move_id.reversed_entry_id.ref if invoice_line.move_id.reversed_entry_id else '')

                data = {'Invoice NO': invoice_line.move_id.name or '',
                        'Invoice Date': invoice_line.move_id.date,
                        'Salesperson': invoice_line.move_id.invoice_user_id.name or '',
                        'Customer': invoice_line.move_id.partner_id.name or '',
                        'City': invoice_line.move_id.partner_id.city or '',
                        'State': invoice_line.move_id.partner_id.state_id.name or '',
                        'Pin': invoice_line.move_id.partner_id.zip or '',
                        'GST NO': invoice_line.partner_id.vat or '',
                        'Analytic': invoice_line.analytic_distribution or '',
                        'Product': product.name if product else '',
                        'MRP': product.list_price if product else 0.0,
                        'Article Code': invoice_line.article_code or '',
                        'SO Number': invoice_line.move_id.invoice_origin or '',
                        'PO Number': po_number or '',
                        'SKU': product.default_code if product else '',
                        'EAN': product.barcode if product else '',
                        'Brand': product.brand_id.name if (product and hasattr(product, 'brand_id') and product.brand_id) else '',
                        'UOM': uom_name,
                        'Size': product.size if (product and hasattr(product, 'size')) else '',
                        'Color': product.color if (product and hasattr(product, 'color')) else '',
                        'Category 1': categ_1,
                        'Category 2': categ_2,
                        'Category 3': categ_3,
                        'Account': invoice_line.account_id.display_name or '',
                        'Journal': invoice_line.move_id.journal_id.name or '',
                        'Quantity': invoice_line.quantity,
                        'GRN Qty': ' ',
                        'Shortage': invoice_line.move_id.shortage or ' ',
                        'Transporter': invoice_line.move_id.transporter_name or ' ',
                        'POD Status': pod_status or ' ',
                        'Remarks': invoice_line.move_id.remarks or ' ',
                        'Unit Price': invoice_line.price_unit,
                        'Discount': invoice_line.discount,
                        'Price Subtotal': invoice_line.price_subtotal,
                        'Taxes': ','.join(map(lambda x: (x.description or x.name), invoice_line.tax_ids)),
                        'Bill Net Amt': convert_curr(invoice_line.price_unit * invoice_line.quantity, invoice_line.move_id),
                        'Price Total': invoice_line.price_total,
                        'Invoice Untaxed Amt': convert_curr(un_tax_amt, invoice_line.move_id),
                        'Invoice Tax Amount': convert_curr(getattr(invoice_line, 'tax_amount_line', 0.0), invoice_line.move_id),
                        'Invoice Total Amt': convert_curr(total_amt, invoice_line.move_id),
                        'Payment Ref': invoice_line.move_id.payment_reference or ' ',
                        'Customer Appointment Date': invoice_line.move_id.customer_appointment_date or False,
                        'LR Number': invoice_line.move_id.lr_number or '',
                        'Logistic Charge': invoice_line.move_id.logistic_charge or '',
                        'Delivery Status': invoice_line.move_id.customer_delivery_number or '',
                        'Quick Commerce': invoice_line.move_id.quick_commerce or ' ',
                        'No of Box': invoice_line.move_id.no_of_cartons or ' ',
                        'Ship From': invoice_line.company_id.name or ' ',
                        'Ship To': invoice_line.move_id.partner_shipping_id.name or ' ',
                        'PO Expiry Date': invoice_line.move_id.po_expiry_date or False,
                        'ETA': invoice_line.move_id.eta or ' ',
                        'Timing': invoice_line.move_id.timing or ' ',
                        'Appointment ID': invoice_line.move_id.appointment or ' ',
                        'CN': invoice_line.move_id.cn_number or ' ',
                        'DN': invoice_line.move_id.dn_number or ' ',
                        'Old Po': invoice_line.move_id.old_po or ' ',
                        'Reason': invoice_line.move_id.reason or ' ',
                        'ASN No': invoice_line.move_id.asn_no or ' ',
                        'VIN PO No': invoice_line.move_id.vin_po_no or ' ',
                        'VIN ASN No': invoice_line.move_id.vin_asn_no or ' ',
                        'COST Price': product.standard_price if product else 0.0,
                        }
                data.update(DownloadReport.get_tax_group_dict(taxes))
                data.update(DownloadReport.compute_taxes(invoice_line))

                data_rows.append(data)
            DownloadReport.dataframe_operations(data_rows, sheet_name, writer)
            return gst_data

        gst_data = get_detailed_sales_data(invoice_data.filtered(lambda x: x.move_type == "out_invoice"),
                                           'Sales Register')
        gst_data1 = get_detailed_sales_data(invoice_data.filtered(lambda x: x.move_type == "out_refund"),
                                            'Sales Return')

        total_gst_op = sum(gst_data.values())

        workbook = writer.book
        title_format = DownloadReport.title_format(workbook)
        txt_font = DownloadReport.txt_font(workbook)
        txt_font2 = DownloadReport.txt_font2(workbook)

        summary_sheet.write('A1', 'Report: Detailed Sales and Detail Register Report', title_format)
        summary_sheet.write('A2', f"Company Name: {DownloadReport.get_company_details(company_id)}")
        summary_sheet.write('A3', f"GST CALCULATION FOR: {start_date} to {end_date}")
        summary_sheet.write('A5', f"GST OUTPUT", txt_font)
        summary_sheet.write('A16', f"GST OUTPUT TOTAL", txt_font)
        summary_sheet.write('B16', total_gst_op, txt_font)
        summary_sheet.write('A22', f"GST INPUT", txt_font)
        summary_sheet.write('A30', f" Less: - Set - off  c / f of GST", txt_font)
        summary_sheet.write('A37', f" Less:- Reverse Charge & Joint Charge Paid", txt_font)
        summary_sheet.write('A45', f" Total GST Payable", txt_font)
        summary_sheet.write('A47', f" Reverse charge and Joint charge Payable ", txt_font)
        summary_sheet.write('A52', f" Total Reverse charge and Joint charge Payable", txt_font)

        key_col = 7
        val_col = 7
        for key, value in gst_data.items():
            summary_sheet.write('A' + str(key_col), key, txt_font2)
            summary_sheet.write('B' + str(val_col), round(value), txt_font2)
            key_col += 1
            val_col += 1

        writer.close()
        out = fp.getvalue()
        pdfhttpheaders = [('Content-Type', 'application/octet-stream'),
                          ('Content-Disposition', content_disposition(f"Detail Sales and Return Register Report.xlsx"))]
        return request.make_response(out, headers=pdfhttpheaders)

    @staticmethod
    def sales_register(start_date, end_date, invoice_data, company_id, *args, **kwargs):
        fp = BytesIO()
        writer = pd.ExcelWriter(fp, engine='xlsxwriter')
        summary_sheet = DownloadReport.create_summary_sheet(writer)

        def get_sales_data(invoices, sheet_name):
            gst_data = {}
            data_rows = list()
            for invoice in invoices:
                un_tax_amt, total_amt = DownloadReport.get_move_amounts(invoice)
                irn = invoice.l10n_in_transaction_id.irn if hasattr(invoice, 'l10n_in_transaction_id') and invoice.l10n_in_transaction_id else ""
                data = {'Invoice NO': invoice.name or '',
                        'Invoice Date': invoice.date,
                        'LR Number': invoice.lr_number if invoice.lr_number else ' ',
                        'IRN': irn,
                        'Salesperson': invoice.invoice_user_id.name or '',
                        'Customer': invoice.partner_id.name or '',
                        'GST NO': invoice.partner_id.vat or '',
                        'Untaxed Amt': un_tax_amt,
                        'Tax Amount': invoice.amount_tax,
                        'Total Amt': total_amt
                        }
                for line in invoice.line_ids:
                    account_name = line.account_id.name
                    if not account_name:
                        continue
                    if 'gst' in account_name.lower():
                        if account_name not in gst_data:
                            gst_data[account_name] = line.debit + line.credit
                        else:
                            gst_data[account_name] += line.debit + line.credit
                    if account_name not in data:
                        data[account_name] = line.debit + line.credit
                    else:
                        data[account_name] += line.debit + line.credit
                    if line.analytic_distribution:
                        analytic_ids = [int(x) for x in line.analytic_distribution.keys() if str(x).isdigit()] if isinstance(line.analytic_distribution, dict) else [int(x) for x in list(line.analytic_distribution) if str(x).isdigit()]
                        if analytic_ids:
                            analytic_account = request.env['account.analytic.account'].sudo().browse(analytic_ids[0])
                            data['Analytic'] = analytic_account.name or ''

                data_rows.append(data)
            DownloadReport.dataframe_operations(data_rows, sheet_name, writer)
            return gst_data

        gst_data = get_sales_data(invoice_data.filtered(lambda x: x.move_type == "out_invoice"), 'Sales Register')
        gst_data1 = get_sales_data(invoice_data.filtered(lambda x: x.move_type == "out_refund"), 'Sales Return')
        total_gst_op = sum(gst_data.values())

        workbook = writer.book
        title_format = DownloadReport.title_format(workbook)
        txt_font = DownloadReport.txt_font(workbook)
        txt_font2 = DownloadReport.txt_font2(workbook)
        txt_font3 = DownloadReport.txt_font3(workbook)

        summary_sheet.write('A1', 'Report: Sales and Return Register', title_format)
        summary_sheet.write('A2', f"Company Name: {DownloadReport.get_company_details(company_id)}")
        summary_sheet.write('A3', f"GST CALCULATION FOR: {start_date} to {end_date}")
        summary_sheet.write('A5', f"GST OUTPUT", txt_font)
        summary_sheet.write('A16', f"GST OUTPUT TOTAL", txt_font)
        summary_sheet.write('B16', total_gst_op, txt_font)
        summary_sheet.write('A22', f"GST INPUT", txt_font)
        summary_sheet.write('A30', f" Less: - Set - off  c / f of GST", txt_font)
        summary_sheet.write('A37', f" Less:- Reverse Charge & Joint Charge Paid", txt_font)
        summary_sheet.write('A45', f" Total GST Payable", txt_font)
        summary_sheet.write('A47', f" Reverse charge and Joint charge Payable ", txt_font)
        summary_sheet.write('A52', f" Total Reverse charge and Joint charge Payable", txt_font)

        key_col = 7
        val_col = 7
        for key, value in gst_data.items():
            summary_sheet.write('A' + str(key_col), key, txt_font2)
            summary_sheet.write('B' + str(val_col), value, txt_font2)
            key_col += 1
            val_col += 1

        writer.close()
        out = fp.getvalue()
        pdfhttpheaders = [('Content-Type', 'application/octet-stream'),
                          ('Content-Disposition', content_disposition(f"Sales and Return Register Report.xlsx"))]
        return request.make_response(out, headers=pdfhttpheaders)

    @http.route(['/download/reports'], type='http', auth='user')
    def portal_my_quotes(self, *args, **kwargs):
        report_for, start_date, end_date, company_id, move_type, journal_id = request.params.get('report_for'), \
            request.params.get('start_date'), \
            request.params.get('end_date'), \
            request.params.get('company_id'), \
            request.params.get('move_type'), \
            request.params.get('journal_id')
        domain = [('state', '=', 'posted'), ('date', '>=', start_date),
                  ('date', '<=', end_date), ('company_id', '=', int(company_id))]
        if move_type == "sales":
            domain.append(('move_type', 'in', ['out_invoice', 'out_refund']))
        else:
            domain.append(('move_type', 'in', ['in_invoice', 'in_refund']))
        if journal_id and journal_id != "False":
            domain.append(('journal_id', 'in', ast.literal_eval(journal_id)))
        invoices = request.env['account.move'].search(domain)

        if not invoices:
            return self.no_data_found()
        return getattr(self, report_for)(start_date, end_date, invoices, company_id)

    # Purchase Register
    @staticmethod
    def detail_purchase_register(start_date, end_date, invoice_data, company_id, *args, **kwargs):
        fp = BytesIO()
        writer = pd.ExcelWriter(fp, engine='xlsxwriter')
        summary_sheet = DownloadReport.create_summary_sheet(writer)

        def get_detail_bills_data(invoices, sheet_name):
            data_rows = list()
            gst_data = {}

            def convert_curr(amount, move):
                if move.currency_id and move.company_id.currency_id and move.currency_id != move.company_id.currency_id:
                    date = move.invoice_date or move.date
                    return move.currency_id._convert(amount, move.company_id.currency_id, move.company_id, date)
                return amount

            for invoice_line in invoices.invoice_line_ids.filtered(
                    lambda line: line.display_type not in ['line_section', 'line_note']):
                taxes = invoice_line.move_id.tax_totals or {}
                amt_tax = DownloadReport.get_purchase_tax_amount(invoice_line.move_id)
                un_tax_amt, _ = DownloadReport.get_move_amounts(invoice_line.move_id)
                final_total = un_tax_amt + amt_tax

                product = invoice_line.product_id
                uom_name = invoice_line.product_uom_id.name or (product.uom_id.name if product else '')
                categ_1 = product.categ_id.parent_id.parent_id.name if (product and product.categ_id and product.categ_id.parent_id and product.categ_id.parent_id.parent_id) else ''
                categ_2 = product.categ_id.parent_id.name if (product and product.categ_id and product.categ_id.parent_id) else ''
                categ_3 = product.categ_id.name if (product and product.categ_id) else ''

                data = {'Bill NO': invoice_line.move_id.name or '',
                        "Bill Reference": invoice_line.move_id.ref or '',
                        'Accounting Date': invoice_line.move_id.date,
                        "Bill Date": invoice_line.move_id.invoice_date,
                        'Purchase Representative': invoice_line.move_id.invoice_user_id.name or '',
                        'Vendor': invoice_line.move_id.partner_id.name or '',
                        'City': invoice_line.move_id.partner_id.city or '',
                        'State': invoice_line.move_id.partner_id.state_id.name or '',
                        'Pin': invoice_line.move_id.partner_id.zip or '',
                        'GST NO': invoice_line.partner_id.vat or '',
                        'Product': product.name if product else '',
                        'MRP': product.list_price if product else 0.0,
                        'Article Code': invoice_line.article_code or '',
                        'PO Number': invoice_line.move_id.invoice_origin or '',
                        'SKU': product.default_code if product else '',
                        'EAN': product.barcode if product else '',
                        'Brand': product.brand_id.name if (product and hasattr(product, 'brand_id') and product.brand_id) else '',
                        'UOM': uom_name,
                        'Size': product.size if (product and hasattr(product, 'size')) else '',
                        'Color': product.color if (product and hasattr(product, 'color')) else '',
                        'Category 1': categ_1,
                        'Category 2': categ_2,
                        'Category 3': categ_3,
                        'Account': invoice_line.account_id.display_name or '',
                        'Journal': invoice_line.move_id.journal_id.name or '',
                        'Quantity': invoice_line.quantity,
                        'Unit Price': invoice_line.price_unit,
                        'Discount': invoice_line.discount,
                        'Price Subtotal': invoice_line.price_subtotal,
                        'Taxes': ','.join(map(lambda x: (x.description or x.name), invoice_line.tax_ids)),
                        'Bill Net Amt': convert_curr(invoice_line.price_unit * invoice_line.quantity, invoice_line.move_id),
                        'Bill Untaxed Amt': convert_curr(un_tax_amt, invoice_line.move_id),
                        'Bill Tax Amount': convert_curr(getattr(invoice_line, 'tax_amount_line', 0.0), invoice_line.move_id),
                        'Bill Total Amt': convert_curr(final_total, invoice_line.move_id)}

                if invoice_line.analytic_distribution:
                    analytic_ids = [int(x) for x in invoice_line.analytic_distribution.keys() if str(x).isdigit()] if isinstance(invoice_line.analytic_distribution, dict) else [int(x) for x in list(invoice_line.analytic_distribution) if str(x).isdigit()]
                    if analytic_ids:
                        analytic_account = request.env['account.analytic.account'].sudo().browse(analytic_ids[0])
                        data['Analytic'] = analytic_account.name or ''
                data.update(DownloadReport.get_tax_group_dict(taxes))
                data.update(DownloadReport.compute_taxes(invoice_line))

                data_rows.append(data)
            DownloadReport.dataframe_operations(data_rows, sheet_name, writer)
            return gst_data

        gst_data = get_detail_bills_data(invoice_data.filtered(lambda x: x.move_type == 'in_invoice'),
                                         'Purchase Register')
        gst_data1 = get_detail_bills_data(invoice_data.filtered(lambda x: x.move_type == 'in_refund'),
                                          'Purchase Return')

        total_gst_op = sum(gst_data.values())
        workbook = writer.book
        title_format = DownloadReport.title_format(workbook)
        txt_font = DownloadReport.txt_font(workbook)
        txt_font2 = DownloadReport.txt_font2(workbook)
        txt_font3 = DownloadReport.txt_font3(workbook)

        summary_sheet.write('A1', 'Report: Detailed Purchase and Return Register', title_format)
        summary_sheet.write('A2', f"Company Name: {DownloadReport.get_company_details(company_id)}")
        summary_sheet.write('A3', f"GST CALCULATION FOR: {start_date} to {end_date}")
        summary_sheet.write('A5', f"GST OUTPUT", txt_font)
        summary_sheet.write('A18', f"GST OUTPUT TOTAL", txt_font)
        summary_sheet.write('B18', total_gst_op, txt_font)
        summary_sheet.write('A22', f"GST INPUT", txt_font)
        summary_sheet.write('A30', f" Less: - Set - off  c / f of GST", txt_font)
        summary_sheet.write('A37', f" Less:- Reverse Charge & Joint Charge Paid", txt_font)
        summary_sheet.write('A45', f" Total GST Payable", txt_font)
        summary_sheet.write('A47', f" Reverse charge and Joint charge Payable ", txt_font)
        summary_sheet.write('A52', f" Total Reverse charge and Joint charge Payable", txt_font)

        key_col = 7
        val_col = 7
        for key, value in gst_data.items():
            summary_sheet.write('A' + str(key_col), key, txt_font2)
            summary_sheet.write('B' + str(val_col), value, txt_font2)
            key_col += 1
            val_col += 1
        writer.close()
        out = fp.getvalue()
        pdfhttpheaders = [('Content-Type', 'application/octet-stream'),
                          ('Content-Disposition', content_disposition(f"Detail Purchase Register Report.xlsx"))]
        return request.make_response(out, headers=pdfhttpheaders)

    @staticmethod
    def purchase_register(start_date, end_date, invoice_data, company_id, *args, **kwargs):
        fp = BytesIO()
        writer = pd.ExcelWriter(fp, engine='xlsxwriter')
        summary_sheet = DownloadReport.create_summary_sheet(writer)

        def get_bills_data(invoices, sheet_name):
            data_rows = list()
            gst_data = {}
            for invoice in invoices:
                amt_tax = DownloadReport.get_purchase_tax_amount(invoice)
                un_tax_amt, _ = DownloadReport.get_move_amounts(invoice)
                final_total = un_tax_amt + amt_tax
                data = {'Bill NO': invoice.name or '', "Bill Reference": invoice.ref or '',
                        'Accounting Date': invoice.date, 'Bill Date': invoice.invoice_date,
                        'Purchase Representative': invoice.invoice_user_id.name or '',
                        'Vendor': invoice.partner_id.name or '', 'GST NO': invoice.partner_id.vat or '',
                        'Untaxed Amt': un_tax_amt, 'Tax Amount': amt_tax, 'Total Amt': final_total}
                for line in invoice.line_ids:
                    account_name = line.account_id.name
                    if not account_name:
                        continue
                    if 'gst' in account_name.lower():
                        if account_name not in gst_data:
                            gst_data[account_name] = line.debit + line.credit
                        else:
                            gst_data[account_name] += line.debit + line.credit
                    if account_name not in data:
                        data[account_name] = line.debit + line.credit
                    else:
                        data[account_name] += line.debit + line.credit

                    if line.analytic_distribution:
                        analytic_ids = [int(x) for x in line.analytic_distribution.keys() if str(x).isdigit()] if isinstance(line.analytic_distribution, dict) else [int(x) for x in list(line.analytic_distribution) if str(x).isdigit()]
                        if analytic_ids:
                            analytic_account = request.env['account.analytic.account'].sudo().browse(analytic_ids[0])
                            data['Analytic'] = analytic_account.name or ''
                data_rows.append(data)
            DownloadReport.dataframe_operations(data_rows, sheet_name, writer)
            return gst_data

        gst_data = get_bills_data(invoice_data.filtered(lambda x: x.move_type == 'in_invoice'), 'Purchase Register')
        gst_data1 = get_bills_data(invoice_data.filtered(lambda x: x.move_type == 'in_refund'), 'Purchase Returns')

        total_gst_op = sum(gst_data.values())
        workbook = writer.book
        title_format = DownloadReport.title_format(workbook)
        txt_font = DownloadReport.txt_font(workbook)
        txt_font2 = DownloadReport.txt_font2(workbook)
        txt_font3 = DownloadReport.txt_font3(workbook)
        summary_sheet.write('A1', 'Report: Purchase Register', title_format)
        summary_sheet.write('A2', f"Company Name: {DownloadReport.get_company_details(company_id)}")
        summary_sheet.write('A3', f"GST CALCULATION FOR: {start_date} to {end_date}")
        summary_sheet.write('A5', f"GST OUTPUT", txt_font)
        summary_sheet.write('A18', f"GST OUTPUT TOTAL", txt_font)
        summary_sheet.write('B18', total_gst_op, txt_font)
        summary_sheet.write('A22', f"GST INPUT", txt_font)
        summary_sheet.write('A30', f" Less: - Set - off  c / f of GST", txt_font)
        summary_sheet.write('A37', f" Less:- Reverse Charge & Joint Charge Paid", txt_font)
        summary_sheet.write('A45', f" Total GST Payable", txt_font)
        summary_sheet.write('A47', f" Reverse charge and Joint charge Payable ", txt_font)
        summary_sheet.write('A52', f" Total Reverse charge and Joint charge Payable", txt_font)

        key_col = 7
        val_col = 7
        for key, value in gst_data.items():
            summary_sheet.write('A' + str(key_col), key, txt_font2)
            summary_sheet.write('B' + str(val_col), value, txt_font2)
            key_col += 1
            val_col += 1

        writer.close()
        out = fp.getvalue()
        pdfhttpheaders = [('Content-Type', 'application/octet-stream'),
                          ('Content-Disposition', content_disposition(f"Purchase Register Report.xlsx"))]
        return request.make_response(out, headers=pdfhttpheaders)

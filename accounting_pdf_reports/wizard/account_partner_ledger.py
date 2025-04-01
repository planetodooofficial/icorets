# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import base64
from odoo.exceptions import UserError

import calendar
import io
from PyPDF2 import PdfFileMerger, PdfFileReader
from datetime import date, timedelta, datetime
import base64
from datetime import datetime
from io import BytesIO
import xlsxwriter

from odoo.tools import get_lang


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.partner.report"
    _description = "Account Partner Ledger"

    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on "
                                          "report if the currency differs from "
                                          "the company currency.")
    reconciled = fields.Boolean('Reconciled Entries')
    include_narration = fields.Boolean(string="Include Narration")
    partners = fields.Selection([('customer', 'Customer'), ('vendor', 'Vendor')], string="Partner Type")

    file_data = fields.Binary('File')

    def _get_report_data(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'include_narration': self.include_narration,
                             'amount_currency': self.amount_currency})
        return data

    @api.model
    def default_get(self, fields_list):
        res = super(AccountPartnerLedger, self).default_get(fields_list)
        current_year_start = datetime(datetime.today().year, 8, 1).strftime('%Y-%m-%d')
        res["date_from"] = current_year_start
        # Set date_to to today's date
        today = datetime.today().strftime('%Y-%m-%d')
        res["date_to"] = today

        return res

    def _print_report(self, data):
        data = self._get_report_data(data)
        # calling report Partner Ledger PDF Report
        print('data+++++++++++++++++++++++++++', data)
        res = self.env.ref('accounting_pdf_reports.action_report_partnerledger').with_context(portrait=True). \
            report_action(self, data=data)

        return res

    def get_date_range(self, data):
        start_date = data.get('form', {}).get('date_from')
        end_date = data.get('form', {}).get('date_to')
        return start_date, end_date

    def remove_duplicate(self, list_):
        seen = {}
        for index, value in enumerate(list_):
            if value not in seen:
                seen[value] = index

        result = []
        for index, value in enumerate(list_):
            if seen[value] == index:
                result.append(value)

        return result

    def get_partner_parent_child(self, list_):
        fetched_partner_list = self.env['res.partner'].browse(list_)

        parent_child_map = {}
        standalone_partners = []

        for partner in fetched_partner_list:
            # parent_id = partner.parent_id.id if partner.parent_id else None
            res_partner_custom = self.env['res.partner.custom'].search([('custom_partner_id', '=', partner.id)])
            if res_partner_custom:
                parent_id = res_partner_custom.custom_parent_id.id if res_partner_custom.custom_parent_id else None
            else:
                parent_id = False

            if parent_id:
                if parent_id not in parent_child_map:
                    parent_child_map[parent_id] = []
                parent_child_map[parent_id].append(partner.id)
            else:
                standalone_partners.append(partner.id)

        sorted_partners = []

        for parent_id in sorted(parent_child_map.keys()):
            sorted_partners.append(parent_id)

            children = sorted(parent_child_map[parent_id])
            sorted_partners.extend(children)

        sorted_partners.extend(sorted(standalone_partners))
        return sorted_partners

    @api.model
    def _get_report_values(self, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['liability_payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['asset_receivable', 'liability_payable']

        self.env.cr.execute("""
                SELECT a.id
                FROM account_account a
                WHERE a.account_type IN %s
                AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
                SELECT DISTINCT "account_move_line".partner_id
                FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
                WHERE "account_move_line".partner_id IS NOT NULL
                    AND "account_move_line".account_id = account.id
                    AND am.id = "account_move_line".move_id
                    AND am.state IN %s
                    AND "account_move_line".account_id IN %s
                    AND NOT account.deprecated
                    AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id'] for res in
                           self.env.cr.dictfetchall()]
        partner_ids = self.get_partner_parent_child(partner_ids)
        partner_ids = self.remove_duplicate(partner_ids)
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        return partners

    # working26march
    def download_report(self, data):
        start_date, end_date = self.get_date_range(data)

        file_pointer = BytesIO()
        workbook = xlsxwriter.Workbook(file_pointer)
        worksheet = workbook.add_worksheet('Sheet 1')
        bold = workbook.add_format({'bold': True})
        style_header = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter'})
        # style_header.set_text_wrap()
        style_header.set_font_size(9)

        style_header_parent = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#00ff00'
        })

        style_header_child = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4db8ff'
        })

        style_header_partner_detail = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
            # 'bg_color': '#999999'
        })
        date_format = workbook.add_format({'num_format': 'd/m/yyyy',
                                           'align': 'center',
                                           'valign': 'vcenter'})

        style_value_partner_detail = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'center',
            # 'valign': 'vcenter',
        })
        style_value_partner_detail.set_text_wrap()

        style_value_amount_partner_detail = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'right',
        })

        style_total_partner_detail = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'center',
            'valign': 'vcenter',
        })
        style_total_amount_partner_detail = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'right',
            'valign': 'vcenter',
        })

        row = 0
        col = 0

        header_content = '''\n{name} \nPeriod : {start} To {end}'''.format(start=start_date, end=end_date,
                                                                           name='Ledger')
        worksheet.set_row(0, 60)
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 45)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 5, 15)
        worksheet.set_column(6, 6, 15)
        worksheet.set_column(7, 7, 15)

        worksheet.merge_range(row, col, row, col + 5, header_content, style_header)

        row = 3
        col = 0

        # line_data_list = self.env['report.accounting_pdf_reports.report_partnerledger']._get_report_values('', data=data)
        partners = self._get_report_values(data)
        for partner in partners:
            is_parent = partner.check_parent()
            if is_parent:
                if partner.shop_sales_channel_id.name:
                    worksheet.write(row, col, partner.shop_sales_channel_id.name or '', style_header_parent)
                    row += 1
                worksheet.write(row, col, partner.name or '', style_header_parent)
                row += 1
                if partner.cust_alias_name:
                    worksheet.write(row, col, partner.cust_alias_name or '', style_header_parent)
                    row += 1
            if not is_parent:
                if partner.shop_sales_channel_id.name:
                    worksheet.write(row, col, partner.shop_sales_channel_id.name or '', style_header_child)
                    row += 1
                worksheet.write(row, col, partner.name or '', style_header_child)
                row += 1
                if partner.cust_alias_name:
                    worksheet.write(row, col, partner.cust_alias_name or '', style_header_child)
                    row += 1

                worksheet.write(row, col, 'Contact Phone:', style_header_partner_detail)
                worksheet.write(row, col + 1, 'Contact Email:', style_header_partner_detail)
                worksheet.write(row, col + 2, 'Sales Person:', style_header_partner_detail)
                worksheet.write(row, col + 3, 'Is Customer:', style_header_partner_detail)
                worksheet.write(row, col + 4, 'Is Vendor:', style_header_partner_detail)
                row += 1

                worksheet.write(row, col, partner.phone or '', style_value_partner_detail)
                worksheet.write(row, col + 1, partner.email or '', style_value_partner_detail)
                worksheet.write(row, col + 2, partner.user_id.name or '', style_value_partner_detail)
                worksheet.write(row, col + 3, True if partner.is_customer else '', style_value_partner_detail)
                worksheet.write(row, col + 4, True if partner.is_supplier else '', style_value_partner_detail)
                row += 1

                worksheet.write(row, col, 'Date', style_header_partner_detail)
                worksheet.write(row, col + 1, 'Payment Terms', style_header_partner_detail)
                worksheet.write(row, col + 2, 'narration', style_header_partner_detail)
                worksheet.write(row, col + 3, 'Debit', style_header_partner_detail)
                worksheet.write(row, col + 4, 'Credit', style_header_partner_detail)
                worksheet.write(row, col + 5, 'Balance', style_header_partner_detail)
                row += 1

                line_data_list = self.env['report.accounting_pdf_reports.report_partnerledger']._lines(data, partner)
                debit_total = 0
                credit_total = 0
                balance_total = 0
                for line_data in line_data_list:
                    debit_total += line_data.get('debit')
                    credit_total += line_data.get('credit')
                    balance_total += line_data.get('progress')

                    worksheet.write(row, col, line_data.get('date'), date_format)
                    worksheet.write(row, col + 1, line_data.get('payment_term'), style_value_partner_detail)
                    worksheet.write(row, col + 2, line_data.get('displayed_name'), style_value_partner_detail)
                    worksheet.write(row, col + 3, f"{line_data.get('debit', 0):,.2f}",
                                    style_value_amount_partner_detail)
                    worksheet.write(row, col + 4, f"{line_data.get('credit', 0):,.2f}",
                                    style_value_amount_partner_detail)
                    worksheet.write(row, col + 5, f"{line_data.get('progress', 0):,.2f}",
                                    style_value_amount_partner_detail)
                    row += 1

                worksheet.write(row, col, 'Total:', style_total_partner_detail)
                worksheet.write(row, col + 1, '', style_total_partner_detail)
                worksheet.write(row, col + 2, '', style_total_partner_detail)
                worksheet.write(row, col + 3, f"{debit_total:,.2f}", style_total_amount_partner_detail)
                worksheet.write(row, col + 4, f"{credit_total:,.2f}", style_total_amount_partner_detail)
                worksheet.write(row, col + 5, f"{balance_total:,.2f}",
                                style_total_amount_partner_detail)
                row += 2

        workbook.close()
        file_pointer.seek(0)

        file_data = file_pointer.read()
        attachment = self.env['ir.attachment'].create({
            'name': 'partner_ledger.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })
        file_pointer.close()

        return attachment

    def _print_report_xslx(self, data):
        data = self._get_report_data(data)
        # res = self.env.ref('accounting_pdf_reports.action_report_partnerledger_xlsx').report_action(self, data=data)
        attachment = self.download_report(data)
        return attachment

    def vendor_balance_confirmation_pdf(self):
        today = date.today()
        pdf_content, _1 = self.env['ir.actions.report']._render_qweb_pdf(
            'accounting_pdf_reports.report_vendor_balance_confirmation', res_ids=self.partner_ids.ids)
        # pdf_content2 = self.check_report()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        result_selection = 'customer_supplier'
        if self.partners == 'customer':
            result_selection = 'customer'
        else:
            result_selection = 'supplier'
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        data['from_date'] = self.date_from
        data['date_to'] = self.date_to
        data = self._get_report_data(data)
        data['form']['result_selection'] = result_selection
        pdf_content2, _2 = self.env['ir.actions.report']._render_qweb_pdf(
            'accounting_pdf_reports.action_report_partnerledger', res_ids=self.partner_ids.ids, data=data)
        pdf_1_reader = PdfFileReader(io.BytesIO(pdf_content))
        pdf_2_reader = PdfFileReader(io.BytesIO(pdf_content2))
        # Merge PDFs
        merger = PdfFileMerger()
        merger.append(pdf_1_reader)
        # merger.append(pdf_2_reader)

        # Save the merged PDF
        merged_pdf = io.BytesIO()
        merger.write(merged_pdf)
        merger.close()
        merged_pdf = merged_pdf.getvalue()
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'vendor_balance_confirmation.pdf',
            'type': 'binary',
            'datas': base64.b64encode(merged_pdf),
            'res_model': 'res.partner',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        # Trigger download
        url = '/web/content/%d/%s' % (attachment.id, attachment.name)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

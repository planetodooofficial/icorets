from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models


class PartnerXlsx(models.AbstractModel):
    _name = 'report.gts_account.account_move_line_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'TDS XLSX Report'

    def generate_xlsx_report(self, workbook, data, lines):
        search_domain = [('tax_line_id.is_tds', '=', True), ('move_id.state', '=', 'posted')]
        if lines.from_date:
            search_domain.append(('date', '>=', lines.from_date))
        if lines.end_date:
            search_domain.append(('date', '<=', lines.end_date))

        account_lines = self.env['account.move.line'].search(search_domain)
        bold = workbook.add_format({
            'font_size': 11,
            'valign': 'vcenter',
            'bold': True,
            'bg_color': '#b7b7b7',
            'font': 'Calibri Light',
            'text_wrap': True,
            'border': 1
        })
        sheet = workbook.add_worksheet('Detailed TDS Report')
        for col_idx in range(21):
            sheet.set_column(col_idx, col_idx, 22)

        # Header for Detailed TDS Report
        sheet.write(0, 0, 'Party Code', bold)
        sheet.write(0, 1, 'Party Description', bold)
        sheet.write(0, 2, 'Party Company', bold)
        sheet.write(0, 3, 'Party PAN', bold)
        sheet.write(0, 4, 'TDS Tax Code', bold)
        sheet.write(0, 5, 'TDS Tax code Description', bold)
        sheet.write(0, 6, 'TDS Percentage', bold)
        sheet.write(0, 7, 'TDS Account Code', bold)
        sheet.write(0, 8, 'TDS Account Description', bold)
        sheet.write(0, 9, 'Voucher Type', bold)
        sheet.write(0, 10, 'Voucher Number', bold)
        sheet.write(0, 11, 'Voucher Date', bold)
        sheet.write(0, 12, 'Transaction Amount', bold)
        sheet.write(0, 13, 'Gross Assessable Amount', bold)
        sheet.write(0, 14, 'TDS Amount', bold)
        sheet.write(0, 15, 'Voucher Status', bold)
        sheet.write(0, 16, 'Document Reference Number', bold)
        sheet.write(0, 17, 'Document Date', bold)
        sheet.write(0, 18, 'Ledger Account Code', bold)
        sheet.write(0, 19, 'Ledger Account Desc', bold)
        sheet.write(0, 20, 'Narration', bold)

        sheet1 = workbook.add_worksheet('Summary of TDS Report')
        for col_idx in range(8):
            sheet1.set_column(col_idx, col_idx, 22)

        # Header for Summary report
        sheet1.write(0, 0, 'TDS Tax Code', bold)
        sheet1.write(0, 1, 'TDS Tax code Description', bold)
        sheet1.write(0, 2, 'TDS Percentage', bold)
        sheet1.write(0, 3, 'TDS Account Code', bold)
        sheet1.write(0, 4, 'TDS Account Description', bold)
        sheet1.write(0, 5, 'Transaction Amount', bold)
        sheet1.write(0, 6, 'Gross Assessable Amount', bold)
        sheet1.write(0, 7, 'TDS Amount', bold)

        row = 1
        col = 0
        totaltax = 0.0
        tax_fields = {}

        for line in account_lines:
            date_str = line.move_id.date.strftime(DEFAULT_SERVER_DATE_FORMAT) if line.move_id.date else ''
            amt_tax = abs(line.balance)
            totaltax += amt_tax

            section_key = line.tax_line_id.section_name.name or line.tax_line_id.name or 'Other'
            if section_key not in tax_fields:
                tax_fields[section_key] = {
                    'name': section_key,
                    'tax_total': amt_tax,
                    'untaxed_amount': line.move_id.amount_untaxed,
                    'total_amount': line.move_id.amount_total,
                    'ledger_name': line.account_id.name,
                    'ledger_code': line.account_id.code,
                    'account_name': line.name,
                    'tax_percent': f"{line.tax_line_id.amount}%" if line.tax_line_id.is_tds else ' ',
                }
            else:
                tax_fields[section_key]['tax_total'] += amt_tax
                tax_fields[section_key]['untaxed_amount'] += line.move_id.amount_untaxed
                tax_fields[section_key]['total_amount'] += line.move_id.amount_total

            sheet.write(row, col, line.partner_id.ref or ' ')
            sheet.write(row, col + 1, line.partner_id.name or ' ')
            sheet.write(row, col + 2, line.company_id.name or ' ')
            sheet.write(row, col + 3, str(line.partner_id.vat)[2:12] if line.partner_id.vat and len(line.partner_id.vat) >= 12 else (line.partner_id.vat or ' '))
            sheet.write(row, col + 4, line.tax_line_id.section_name.name if line.tax_line_id.is_tds and line.tax_line_id.section_name else (line.tax_line_id.name or ' '))
            sheet.write(row, col + 5, line.name or ' ')
            sheet.write(row, col + 6, f"{line.tax_line_id.amount}%" if line.tax_line_id.is_tds else ' ')
            sheet.write(row, col + 7, line.account_id.code or ' ')
            sheet.write(row, col + 8, line.account_id.name or ' ')
            sheet.write(row, col + 9, line.move_id.journal_id.name or ' ')
            sheet.write(row, col + 10, line.move_id.name or ' ')
            sheet.write(row, col + 11, date_str)
            sheet.write(row, col + 12, line.move_id.amount_untaxed or 0.0)
            sheet.write(row, col + 13, line.move_id.amount_total or 0.0)
            sheet.write(row, col + 14, amt_tax)
            sheet.write(row, col + 15, line.move_id.state or ' ')
            sheet.write(row, col + 16, line.move_id.ref or ' ')
            sheet.write(row, col + 17, str(line.move_id.invoice_date or ''))
            sheet.write(row, col + 18, line.account_id.code or ' ')
            sheet.write(row, col + 19, line.account_id.name or ' ')
            sheet.write(row, col + 20, line.move_id.narration or ' ')
            row += 1

        row += 1
        sheet.write(row, col, 'Total', bold)
        sheet.write(row, col + 14, totaltax, bold)

        # Summary sheet population
        s_row = 1
        total_untax = 0.0
        total_tax2 = 0.0
        total_amt = 0.0

        for item in tax_fields.values():
            sheet1.write(s_row, col, item['name'] or '')
            sheet1.write(s_row, col + 1, item['ledger_name'] or ' ')
            sheet1.write(s_row, col + 2, item['tax_percent'] or ' ')
            sheet1.write(s_row, col + 3, item['ledger_code'] or ' ')
            sheet1.write(s_row, col + 4, item['account_name'] or ' ')
            sheet1.write(s_row, col + 5, item['untaxed_amount'] or 0.0)
            sheet1.write(s_row, col + 6, item['total_amount'] or 0.0)
            sheet1.write(s_row, col + 7, item['tax_total'] or 0.0)
            s_row += 1
            total_untax += item['untaxed_amount']
            total_tax2 += item['tax_total']
            total_amt += item['total_amount']

        s_row += 1
        sheet1.write(s_row, col, 'Total', bold)
        sheet1.write(s_row, col + 5, total_untax, bold)
        sheet1.write(s_row, col + 6, total_amt, bold)
        sheet1.write(s_row, col + 7, total_tax2, bold)

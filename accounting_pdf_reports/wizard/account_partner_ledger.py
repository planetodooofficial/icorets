# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import calendar
import io
# from PyPDF2 import PdfMerger, PdfReader
from PyPDF2 import PdfFileMerger, PdfFileReader
from datetime import date, timedelta, datetime

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
        res = self.env.ref('accounting_pdf_reports.action_report_partnerledger').with_context(portrait=True).\
            report_action(self, data=data)

        return res

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

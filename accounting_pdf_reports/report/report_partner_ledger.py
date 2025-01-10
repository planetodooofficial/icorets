# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _lines(self, data, partner):
        full_account = []
        currency = self.env['res.currency']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        print("---query_get_data", query_get_data)
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        sum = 0.0
        # s_date = '2024/01/01'
        if data.get('from_date'):
            params1 = [partner.id, tuple(data['computed']['account_ids']), data.get('from_date'), self.env.company.id, tuple(data['form'].get('journal_ids'))]
            query = ('''select sum(debit) as debit, sum(credit) as credit, sum(debit-credit) as balance from account_move_line 
                     where partner_id = %s and parent_state = 'posted' \
             and account_id in %s and date < %s and company_id = %s and journal_id in %s ''')
            self.env.cr.execute(query, tuple(params1))
            res1 = self.env.cr.dictfetchall()
            # if res1 and res1[0]:
            for r in res1:
                if r['debit'] or r['credit'] or r['balance']:
                    r['date'] = ''
                    # r['bdl_number'] = ''
                    r['displayed_name'] = 'Opening Balance as on ' + str(data.get('from_date'))
                    balance = r['balance']
                    r['debit'] = r['debit']
                    r['credit'] = r['credit']
                    r['payment_term'] = ''
                    if balance:
                        sum += balance
                    r['progress'] = sum
                    r['currency_id'] = currency.browse(r.get('currency_id'))
                    r['include_narration'] = False if data['form']['include_narration'] else False
                    full_account.append(r)

        query = """
            SELECT "account_move_line".id, "account_move_line".date, partner.name as narration, j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref, m.name as move_name,
             m.invoice_payment_term_id,"account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code
            FROM """ + query_get_data[0] + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            LEFT JOIN res_users use ON (m.create_uid=use.id)
            LEFT JOIN res_partner partner ON (use.partner_id=partner.id)
            WHERE "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + """
                ORDER BY "account_move_line".date"""
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        print("----res", res)
        # sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            # print("rrr..", r)
            r['date'] = r['date']
            # r['bdl_number'] = r['bdl_number']
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            r['payment_term'] = (
                self.env['account.payment.term'].browse(r.get('invoice_payment_term_id')).name
                if r.get('invoice_payment_term_id')
                else ''
            )
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id'))
            r['include_narration'] = data['form']['include_narration'] if data['form']['include_narration'] else False
            full_account.append(r)
            # print("full_account", full_account)
        return full_account

    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        contexts = data['form'].get('used_context', {})
        contexts.update({
            'date_from': False,
            # 'date_to': False,
        })
        query_get_data = self.env['account.move.line'].with_context(contexts)._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        params = [partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        # if data.get('from_date') and data.get('date_to'):
        #     print("...query_get_data[0]", query_get_data[0])
        #     print("...query_get_data[1]", query_get_data[1])
        #     query_get_data = tuple([query_get_data[0].replace('''("account_move_line"."date" <= %s) AND ''', 'sasaa'), query_get_data[1].replace('''("account_move_line"."date" >= %s) AND ''', 'wwqwwq')])
        #     print("inside from and date", query_get_data)
        #     # del params[3]
        #     # del params[3]
        # elif data.get('from_date'):
        #     query_get_data = tuple([query_get_data[0],
        #                             query_get_data[1].replace('''("account_move_line"."date" >= %s) AND ''', '')])
        #     print("query_get_data...", query_get_data)
        #     del params[3]

        query = """SELECT sum(""" + field + """)
                FROM """ + query_get_data[0] + """, account_move AS m
                WHERE "account_move_line".partner_id = %s
                    AND m.id = "account_move_line".move_id
                    AND m.state IN %s
                    AND account_id IN %s
                    AND """ + query_get_data[1]
        # print ("query======sum==========", query_get_data[1], reconcile_clause)
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
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
            print("partner_ids...", partner_ids)
        else:
            partner_ids = [res['partner_id'] for res in
                           self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }
# posted', 17, ('line_section', 'line_note'), 'cancel', (17,)
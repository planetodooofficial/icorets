# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import models, fields, _
from odoo.tools.misc import format_date


class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group,
                                   level_shift=0):
        if aml_query_result['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move.line'

        columns = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_expr_label = column['expression_label']

            col_value = None
            currency = False

            if col_expr_label == 'ref':
                col_value = self._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name'])
            elif col_expr_label == 'balance':
                col_value = aml_query_result.get('balance', 0.0) if column['column_group_key'] == aml_query_result['column_group_key'] else None
                if col_value is not None:
                    col_value += init_bal_by_col_group[column['column_group_key']]
            elif col_expr_label == 'amount_currency':
                col_value = aml_query_result.get('amount_currency') if column['column_group_key'] == aml_query_result['column_group_key'] else None
                if col_value is not None:
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    if currency == self.env.company.currency_id:
                        col_value = ''
            elif col_expr_label == 'tds':
                move_line = self.env['account.move.line'].browse(aml_query_result.get('id'))
                debit_tds = sum(move_line.move_id.line_ids.filtered(lambda x: getattr(x.account_id, 'is_tds', False)).mapped('debit'))
                credit_tds = sum(move_line.move_id.line_ids.filtered(lambda x: getattr(x.account_id, 'is_tds', False)).mapped('credit'))
                col_value = debit_tds if debit_tds > 0 else credit_tds
                currency = self.env['res.currency'].browse(aml_query_result.get('currency_id')) or self.env.company.currency_id
            elif col_expr_label == 'vat':
                move_line = self.env['account.move.line'].browse(aml_query_result.get('id'))
                debit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: getattr(x.account_id, 'is_vat', False)).mapped('debit'))
                credit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: getattr(x.account_id, 'is_vat', False)).mapped('credit'))
                col_value = debit_vat if debit_vat > 0 else credit_vat
                currency = self.env['res.currency'].browse(aml_query_result.get('currency_id')) or self.env.company.currency_id
            elif col_expr_label in ('is_customer', 'is_vendor', 'salesperson', 'credit_days', 'credit_limit'):
                col_value = ''
            elif col_expr_label in aml_query_result:
                col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None

            if col_value is None:
                columns.append(report._build_column_dict(None, None))
            else:
                columns.append(report._build_column_dict(col_value, column, options=options, currency=currency))

        return {
            'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id, markup=aml_query_result['partial_id']),
            'parent_id': partner_line_id,
            'name': self._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name']),
            'columns': columns,
            'caret_options': caret_type,
            'level': 3 + level_shift,
            'is_draft': aml_query_result['parent_state'] == 'draft',
            'no_followup': aml_query_result['no_followup'],
        }

    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: {
                total: 0.0
                for total in ['debit', 'credit', 'amount', 'balance', 'vat', 'tds']
            }
            for column_group_key in options['column_groups']
        }

        partners_results = self._query_partners(report, options)

        search_filter = options.get('filter_search_bar', '')
        accept_unknown_in_filter = search_filter.lower() in self._get_no_partner_line_label().lower()
        for partner, results in partners_results:
            if options.get('export_mode') == 'print' and search_filter and not partner and not accept_unknown_in_filter:
                continue

            partner_values = defaultdict(dict)
            for column_group_key in options['column_groups']:
                partner_sum = results.get(column_group_key, {})

                partner_values[column_group_key]['debit'] = partner_sum.get('debit', 0.0)
                partner_values[column_group_key]['credit'] = partner_sum.get('credit', 0.0)
                partner_values[column_group_key]['amount'] = partner_sum.get('amount', 0.0)
                partner_values[column_group_key]['balance'] = partner_sum.get('balance', 0.0)
                partner_values[column_group_key]['amount_currency'] = partner_sum.get('amount_currency')
                partner_values[column_group_key]['currency_id'] = partner_sum.get('currency_id')

                partner_values[column_group_key]['is_customer'] = 'Yes' if partner and getattr(partner, 'is_customer', False) else ''
                partner_values[column_group_key]['is_vendor'] = 'Yes' if partner and getattr(partner, 'is_supplier', False) else ''
                partner_values[column_group_key]['salesperson'] = partner.user_id.name if partner and partner.user_id else ''
                payment_term_id = partner.with_company(self.env.company).property_payment_term_id if partner else False
                partner_values[column_group_key]['credit_days'] = payment_term_id.name if payment_term_id else ''
                partner_values[column_group_key]['credit_limit'] = str(partner.credit_limit) if partner and getattr(partner, 'credit_limit', False) else ''
                partner_values[column_group_key]['vat'] = partner_sum.get('vat', 0.0)
                partner_values[column_group_key]['tds'] = partner_sum.get('tds', 0.0)

                totals_by_column_group[column_group_key]['debit'] += partner_values[column_group_key]['debit']
                totals_by_column_group[column_group_key]['credit'] += partner_values[column_group_key]['credit']
                totals_by_column_group[column_group_key]['amount'] += partner_values[column_group_key]['amount']
                totals_by_column_group[column_group_key]['balance'] += partner_values[column_group_key]['balance']

            lines.append(self._get_report_line_partners(options, partner, partner_values, level_shift=level_shift))

        return lines, totals_by_column_group

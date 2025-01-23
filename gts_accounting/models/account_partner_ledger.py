# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json

from odoo import models, _, fields
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import format_date, get_lang

from datetime import timedelta
from collections import defaultdict


class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'
    # _inherit = 'account.report.custom.handler'
    # _description = 'Partner Ledger Custom Handler'

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        if aml_query_result['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move.line'

        columns = []
        report = self.env['account.report']
        for column in options['columns']:
            col_expr_label = column['expression_label']

            if col_expr_label == 'ref':
                col_value = report._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name'])
            else:
                if col_expr_label == 'tds':
                    col_value = 'tds' if column['column_group_key'] == aml_query_result[
                        'column_group_key'] else None
                elif col_expr_label == 'vat':
                    col_value = 'vat' if column['column_group_key'] == aml_query_result[
                        'column_group_key'] else None
                else:
                    col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None

            if col_value is None:
                columns.append({})
            else:
                col_class = 'number'

                if col_expr_label == 'date_maturity':
                    formatted_value = format_date(self.env, fields.Date.from_string(col_value))
                    col_class = 'date'
                elif col_expr_label == 'amount_currency':
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    formatted_value = report.format_value(col_value, currency=currency, figure_type=column['figure_type'])
                elif col_expr_label == 'tds':
                    move_line = self.env['account.move.line'].browse(aml_query_result.get('id'))
                    credit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: x.account_id.is_tds).mapped('credit'))
                    amount = credit_vat
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    formatted_value = report.format_value(amount, currency=currency, figure_type=column['figure_type'])
                elif col_expr_label == 'vat':
                    move_line = self.env['account.move.line'].browse(aml_query_result.get('id'))
                    debit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: x.account_id.is_vat).mapped('debit'))
                    amount = debit_vat
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    formatted_value = report.format_value(amount, currency=currency, figure_type=column['figure_type'])
                elif col_expr_label == 'balance':
                    col_value += init_bal_by_col_group[column['column_group_key']]
                    formatted_value = report.format_value(col_value, figure_type=column['figure_type'], blank_if_zero=column['blank_if_zero'])
                else:
                    if col_expr_label == 'ref':
                        col_class = 'o_account_report_line_ellipsis'
                    elif col_expr_label not in ('debit', 'credit'):
                        col_class = ''
                    formatted_value = report.format_value(col_value, figure_type=column['figure_type'])

                columns.append({
                    'name': formatted_value,
                    'no_format': col_value,
                    'class': col_class,
                })

        return {
            'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id),
            'parent_id': partner_line_id,
            'name': format_date(self.env, aml_query_result['date']),
            'class': 'text-muted' if aml_query_result['key'] == 'indirectly_linked_aml' else 'text',  # do not format as date to prevent text centering
            'columns': columns,
            'caret_options': caret_type,
            'level': 4 + level_shift,
        }
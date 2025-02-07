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

    # partner_ledgeropen
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
                    debit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: x.account_id.is_tds).mapped('debit'))
                    credit_vat = sum(
                        move_line.move_id.line_ids.filtered(lambda x: x.account_id.is_tds).mapped('credit'))
                    if debit_vat > 0:
                        amount = debit_vat
                    else:
                        amount = credit_vat
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    formatted_value = report.format_value(amount, currency=currency, figure_type=column['figure_type'])
                elif col_expr_label == 'vat':
                    move_line = self.env['account.move.line'].browse(aml_query_result.get('id'))
                    debit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: x.account_id.is_vat).mapped('debit'))
                    credit_vat = sum(move_line.move_id.line_ids.filtered(lambda x: x.account_id.is_vat).mapped('credit'))
                    if debit_vat > 0:
                        amount = debit_vat
                    else:
                        amount = credit_vat
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

    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: {
                total: 0.0
                for total in ['debit', 'credit', 'balance', 'vat', 'tds']
            }
            for column_group_key in options['column_groups']
        }

        search_filter = options.get('filter_search_bar') or ''
        accept_unknown_in_filter = search_filter.lower() in self._get_no_partner_line_label().lower()
        for partner, results in self._query_partners(options):
            print('results++++++++++++++++++++++=', results)
            if self.env.context.get('print_mode') and search_filter and not partner and not accept_unknown_in_filter:
                # When printing and searching for a specific partner, make it so we only show its lines, not the 'Unknown Partner' one, that would be
                # shown in case a misc entry with no partner was reconciled with one of the target partner's entries.
                continue

            partner_values = defaultdict(dict)
            for column_group_key in options['column_groups']:
                partner_sum = results.get(column_group_key, {})

                partner_values[column_group_key]['debit'] = partner_sum.get('debit', 0.0)
                partner_values[column_group_key]['credit'] = partner_sum.get('credit', 0.0)
                partner_values[column_group_key]['balance'] = partner_sum.get('balance', 0.0)
                partner_values[column_group_key]['vat'] = partner_sum.get('vat', 0.0)
                partner_values[column_group_key]['tds'] = partner_sum.get('tds', 0.0)

                totals_by_column_group[column_group_key]['debit'] += partner_values[column_group_key]['debit']
                totals_by_column_group[column_group_key]['credit'] += partner_values[column_group_key]['credit']
                totals_by_column_group[column_group_key]['balance'] += partner_values[column_group_key]['balance']
                totals_by_column_group[column_group_key]['vat'] += partner_values[column_group_key]['vat']
                totals_by_column_group[column_group_key]['tds'] += partner_values[column_group_key]['tds']

            lines.append(self._get_report_line_partners(options, partner, partner_values, level_shift=level_shift))

        return lines, totals_by_column_group

    def _query_partners(self, options):
        """ Executes the queries and performs all the computation.
        :return:        A list of tuple (partner, column_group_values) sorted by the table's model _order:
                        - partner is a res.parter record.
                        - column_group_values is a dict(column_group_key, fetched_values), where
                            - column_group_key is a string identifying a column group, like in options['column_groups']
                            - fetched_values is a dictionary containing:
                                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        """
        # partner_ledgeropen
        def assign_sum(row):
            fields_to_assign = ['balance', 'debit', 'credit', 'vat', 'tds']
            if any(not company_currency.is_zero(row[field]) for field in fields_to_assign):
                groupby_partners.setdefault(row['groupby'], defaultdict(lambda: defaultdict(float)))
                for field in fields_to_assign:
                    groupby_partners[row['groupby']][row['column_group_key']][field] += row[field]


        company_currency = self.env.company.currency_id

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options)

        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            assign_sum(res)

        # Correct the sums per partner, for the lines without partner reconciled with a line having a partner
        query, params = self._get_sums_without_partner(options)

        self._cr.execute(query, params)
        totals = {}
        for total_field in ['debit', 'credit', 'balance', 'vat', 'tds']:
            totals[total_field] = {col_group_key: 0 for col_group_key in options['column_groups']}

        for row in self._cr.dictfetchall():
            totals['debit'][row['column_group_key']] += row['debit']
            totals['credit'][row['column_group_key']] += row['credit']
            totals['balance'][row['column_group_key']] += row['balance']
            totals['vat'][row['column_group_key']] += row['vat']
            totals['tds'][row['column_group_key']] += row['tds']

            if row['groupby'] not in groupby_partners:
                continue

            assign_sum(row)

        if None in groupby_partners:
            # Debit/credit are inverted for the unknown partner as the computation is made regarding the balance of the known partner
            for column_group_key in options['column_groups']:
                groupby_partners[None][column_group_key]['debit'] += totals['credit'][column_group_key]
                groupby_partners[None][column_group_key]['credit'] += totals['debit'][column_group_key]
                groupby_partners[None][column_group_key]['balance'] -= totals['balance'][column_group_key]
                groupby_partners[None][column_group_key]['vat'] -= totals['vat'][column_group_key]
                groupby_partners[None][column_group_key]['tds'] -= totals['tds'][column_group_key]


        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        if groupby_partners:
            # Note a search is done instead of a browse to preserve the table ordering.
            partners = self.env['res.partner'].with_context(active_test=False, prefetch_fields=False).search([('id', 'in', list(groupby_partners.keys()))])
        else:
            partners = []

        # Add 'Partner Unknown' if needed
        if None in groupby_partners.keys():
            partners = [p for p in partners] + [None]

        return [(partner, groupby_partners[partner.id if partner else None]) for partner in partners]

    def _get_query_sums(self, options):
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all partners.
        - sums for the initial balances.
        - VAT amounts from related move lines (using credit or debit for tax)
        :param options:             The report options.
        :return:                    (query, params)
        """
        params = []
        queries = []
        report = self.env.ref('account_reports.partner_ledger_report')

        # Create the currency table.
        ct_query = self.env['res.currency']._get_query_currency_table(options)
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(column_group_options, 'normal')
            params.append(column_group_key)
            params += where_params

            print('\n\n\nct_query++++++++++++++++++', ct_query)

            queries.append(f"""
                SELECT
                    account_move_line.partner_id                                                          AS groupby,
                    %s                                                                                    AS column_group_key,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    COALESCE(
                        SUM(
                            ROUND(
                                CASE
                                    WHEN acc.is_vat = true THEN
                                        CASE
                                            WHEN aml_vat_tds.credit > 0 THEN aml_vat_tds.credit * currency_table.rate
                                            WHEN aml_vat_tds.credit = 0 THEN aml_vat_tds.debit * currency_table.rate
                                            ELSE 0
                                        END
                                    ELSE 0
                                END,
                                currency_table.precision
                            )
                        ),
                        0
                    ) AS vat,
                    COALESCE(
                        SUM(
                            ROUND(
                                CASE
                                    WHEN acc.is_tds = true THEN
                                        CASE
                                            WHEN aml_vat_tds.credit > 0 THEN aml_vat_tds.credit * currency_table.rate
                                            WHEN aml_vat_tds.credit = 0 THEN aml_vat_tds.debit * currency_table.rate
                                            ELSE 0
                                        END
                                    ELSE 0
                                END,
                                currency_table.precision
                            )
                        ),
                        0
                    ) AS tds
                FROM {tables}

                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id

                LEFT JOIN account_move am ON account_move_line.move_id = am.id
                
                LEFT JOIN account_move_line aml_vat_tds ON aml_vat_tds.move_id = am.id
                LEFT JOIN account_account acc ON aml_vat_tds.account_id = acc.id


                WHERE {where_clause}

                GROUP BY account_move_line.partner_id
            """)

        return ' UNION ALL '.join(queries), params

    def _get_sums_without_partner(self, options):
        """ Get the sum of lines without partner reconciled with a line with a partner, grouped by partner. Those lines
        should be considered as belonging to the partner for the reconciled amount as it may clear some of the partner
        invoice/bill and they have to be accounted in the partner balance."""
        queries = []
        params = []
        report = self.env.ref('account_reports.partner_ledger_report')
        ct_query = self.env['res.currency']._get_query_currency_table(options)
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(column_group_options, 'normal')
            params += [
                column_group_key,
                column_group_options['date']['date_to'],
                *where_params,
            ]
            queries.append(f"""
                SELECT
                    %s                                                                                                    AS column_group_key,
                    aml_with_partner.partner_id                                                                           AS groupby,
                    COALESCE(SUM(CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE ROUND(
                            partial.amount * currency_table.rate, currency_table.precision) END), 0)                      AS debit,
                    COALESCE(SUM(CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE ROUND(
                            partial.amount * currency_table.rate, currency_table.precision) END), 0)                      AS credit,
                    COALESCE(SUM(- sign(aml_with_partner.balance) * ROUND(
                            partial.amount * currency_table.rate, currency_table.precision)), 0)                          AS balance,
                    COALESCE(
                        SUM(
                            ROUND(
                                CASE
                                    WHEN acc.is_vat = true THEN
                                        CASE
                                            WHEN aml_vat_tds.credit > 0 THEN aml_vat_tds.credit * currency_table.rate
                                            WHEN aml_vat_tds.credit = 0 THEN aml_vat_tds.debit * currency_table.rate
                                            ELSE 0
                                        END
                                    ELSE 0
                                END,
                                currency_table.precision
                            )
                        ),
                        0
                    ) AS vat,
                    COALESCE(
                        SUM(
                            ROUND(
                                CASE
                                    WHEN acc.is_tds = true THEN
                                        CASE
                                            WHEN aml_vat_tds.credit > 0 THEN aml_vat_tds.credit * currency_table.rate
                                            WHEN aml_vat_tds.credit = 0 THEN aml_vat_tds.debit * currency_table.rate
                                            ELSE 0
                                        END
                                    ELSE 0
                                END,
                                currency_table.precision
                            )
                        ),
                        0
                    ) AS tds
                FROM {tables}
                JOIN account_partial_reconcile partial
                    ON account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id
                JOIN account_move_line aml_with_partner ON
                    (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND aml_with_partner.partner_id IS NOT NULL
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id

                LEFT JOIN account_move am ON account_move_line.move_id = am.id
                LEFT JOIN account_move_line aml_vat_tds ON aml_vat_tds.move_id = am.id
                LEFT JOIN account_account acc ON aml_vat_tds.account_id = acc.id

                WHERE partial.max_date <= %s AND {where_clause}
                    AND account_move_line.partner_id IS NULL
                GROUP BY aml_with_partner.partner_id
            """)

        return " UNION ALL ".join(queries), params
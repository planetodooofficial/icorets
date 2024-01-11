from odoo import models, api, fields, _
from odoo.tools.misc import format_date, get_lang


class AliasName(models.Model):
    _name = "alias.name"
    _rec_name = "name"

    name = fields.Char("Name", copy=False)


# Inherited for alias name in partner ledger partner
class PartnerLedgerCustomHandlerInherit(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _get_report_line_partners(self, options, partner, partner_values, level_shift=0):
        company_currency = self.env.company.currency_id
        unfold_all = (self._context.get('print_mode') and not options.get('unfolded_lines')) or options.get(
            'unfold_all')

        unfoldable = False
        column_values = []
        report = self.env['account.report']
        for column in options['columns']:
            col_expr_label = column['expression_label']
            value = partner_values[column['column_group_key']].get(col_expr_label)

            if col_expr_label in {'debit', 'credit', 'balance'}:
                formatted_value = report.format_value(value, figure_type=column['figure_type'],
                                                      blank_if_zero=column['blank_if_zero'])
            else:
                formatted_value = report.format_value(value,
                                                      figure_type=column['figure_type']) if value is not None else value

            unfoldable = unfoldable or (col_expr_label in ('debit', 'credit') and not company_currency.is_zero(value))

            column_values.append({
                'name': formatted_value,
                'no_format': value,
                'class': 'number'
            })

        line_id = report._get_generic_line_id('res.partner', partner.id) if partner else report._get_generic_line_id(
            'res.partner', None, markup='no_partner')

        return {
            'id': line_id,
            'name': partner is not None and (partner.name + ' - ' + str(
                partner.cust_alias_name) if partner.cust_alias_name else partner.name or '')[
                                            :128] or self._get_no_partner_line_label(),
            'columns': column_values,
            'level': 2 + level_shift,
            'trust': partner.trust if partner else None,
            'unfoldable': unfoldable,
            'unfolded': line_id in options['unfolded_lines'] or unfold_all,
            'expand_function': '_report_expand_unfoldable_line_partner_ledger',
        }
#For adding new column in partner ledger

    # def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
    #     if aml_query_result['payment_id']:
    #         caret_type = 'account.payment'
    #     else:
    #         caret_type = 'account.move.line'
    #
    #     columns = []
    #     report = self.env['account.report']
    #     for column in options['columns']:
    #         col_expr_label = column['expression_label']
    #
    #         #added
    #         if col_expr_label == 'alias_name':
    #             col_value = aml_query_result['alias_name'] if column['column_group_key'] == aml_query_result[
    #                 'column_group_key'] else None
    #
    #         elif col_expr_label == 'ref':
    #             col_value = report._format_aml_name(aml_query_result['name'], aml_query_result['ref'], aml_query_result['move_name'])
    #         else:
    #             col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None
    #
    #         if col_value is None:
    #             columns.append({})
    #         else:
    #             col_class = 'number'
    #
    #             if col_expr_label == 'date_maturity':
    #                 formatted_value = format_date(self.env, fields.Date.from_string(col_value))
    #                 col_class = 'date'
    #             elif col_expr_label == 'amount_currency':
    #                 currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
    #                 formatted_value = report.format_value(col_value, currency=currency, figure_type=column['figure_type'])
    #             elif col_expr_label == 'balance':
    #                 col_value += init_bal_by_col_group[column['column_group_key']]
    #                 formatted_value = report.format_value(col_value, figure_type=column['figure_type'], blank_if_zero=column['blank_if_zero'])
    #             else:
    #                 if col_expr_label == 'ref':
    #                     col_class = 'o_account_report_line_ellipsis'
    #                 elif col_expr_label not in ('debit', 'credit'):
    #                     col_class = ''
    #                 formatted_value = report.format_value(col_value, figure_type=column['figure_type'])
    #
    #             columns.append({
    #                 'name': formatted_value,
    #                 'no_format': col_value,
    #                 'class': col_class,
    #             })
    #
    #     return {
    #         'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id),
    #         'parent_id': partner_line_id,
    #         'name': format_date(self.env, aml_query_result['date']),
    #         'class': 'text-muted' if aml_query_result['key'] == 'indirectly_linked_aml' else 'text',  # do not format as date to prevent text centering
    #         'columns': columns,
    #         'caret_options': caret_type,
    #         'level': 4 + level_shift,
    #     }
    #
    # def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
    #     rslt = {partner_id: [] for partner_id in partner_ids}
    #
    #     partner_ids_wo_none = [x for x in partner_ids if x]
    #     directly_linked_aml_partner_clauses = []
    #     directly_linked_aml_partner_params = []
    #     indirectly_linked_aml_partner_params = []
    #     indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IS NOT NULL'
    #     if None in partner_ids:
    #         directly_linked_aml_partner_clauses.append('account_move_line.partner_id IS NULL')
    #     if partner_ids_wo_none:
    #         directly_linked_aml_partner_clauses.append('account_move_line.partner_id IN %s')
    #         directly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
    #         indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IN %s'
    #         indirectly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
    #     directly_linked_aml_partner_clause = '(' + ' OR '.join(directly_linked_aml_partner_clauses) + ')'
    #
    #     ct_query = self.env['res.currency']._get_query_currency_table(options)
    #     queries = []
    #     all_params = []
    #     lang = self.env.lang or get_lang(self.env).code
    #     journal_name = f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')" if \
    #         self.pool['account.journal'].name.translate else 'journal.name'
    #     account_name = f"COALESCE(account.name->>'{lang}', account.name->>'en_US')" if \
    #         self.pool['account.account'].name.translate else 'account.name'
    #     report = self.env.ref('account_reports.partner_ledger_report')
    #     for column_group_key, group_options in report._split_options_per_column_group(options).items():
    #         tables, where_clause, where_params = report._query_get(group_options, 'strict_range')
    #
    #         all_params += [
    #             column_group_key,
    #             *where_params,
    #             *directly_linked_aml_partner_params,
    #             column_group_key,
    #             *indirectly_linked_aml_partner_params,
    #             *where_params,
    #             group_options['date']['date_from'],
    #             group_options['date']['date_to'],
    #         ]
    #
    #         # For the move lines directly linked to this partner
    #         queries.append(f'''
    #             SELECT
    #                 account_move_line.id,
    #                 account_move_line.date,
    #                 account_move_line.date_maturity,
    #                 account_move_line.name,
    #                 account_move_line.ref,
    #                 account_move_line.company_id,
    #                 account_move_line.account_id,
    #                 account_move_line.payment_id,
    #                 account_move_line.partner_id,
    #                 partner.cust_alias_name AS alias_name,
    #                 account_move_line.currency_id,
    #                 account_move_line.amount_currency,
    #                 account_move_line.matching_number,
    #                 ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
    #                 ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
    #                 ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
    #                 account_move.name                                                                AS move_name,
    #                 account_move.move_type                                                           AS move_type,
    #                 account.code                                                                     AS account_code,
    #                 {account_name}                                                                   AS account_name,
    #                 journal.code                                                                     AS journal_code,
    #                 {journal_name}                                                                   AS journal_name,
    #                 %s                                                                               AS column_group_key,
    #                 'directly_linked_aml'                                                            AS key
    #             FROM {tables}
    #             JOIN account_move ON account_move.id = account_move_line.move_id
    #             LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
    #             LEFT JOIN res_company company               ON company.id = account_move_line.company_id
    #             LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
    #             LEFT JOIN account_account account           ON account.id = account_move_line.account_id
    #             LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
    #             WHERE {where_clause} AND {directly_linked_aml_partner_clause}
    #             ORDER BY account_move_line.date, account_move_line.id
    #         ''')
    #
    #         # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
    #         queries.append(f'''
    #             SELECT
    #                 account_move_line.id,
    #                 account_move_line.date,
    #                 account_move_line.date_maturity,
    #                 account_move_line.name,
    #                 account_move_line.ref,
    #                 account_move_line.company_id,
    #                 account_move_line.account_id,
    #                 account_move_line.payment_id,
    #                 aml_with_partner.partner_id,
    #                 partner.cust_alias_name AS alias_name,
    #                 account_move_line.currency_id,
    #                 account_move_line.amount_currency,
    #                 account_move_line.matching_number,
    #                 CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE ROUND(
    #                     partial.amount * currency_table.rate, currency_table.precision
    #                 ) END                                                                               AS debit,
    #                 CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE ROUND(
    #                     partial.amount * currency_table.rate, currency_table.precision
    #                 ) END                                                                               AS credit,
    #                 - sign(aml_with_partner.balance) * ROUND(
    #                     partial.amount * currency_table.rate, currency_table.precision
    #                 )                                                                                   AS balance,
    #                 account_move.name                                                                   AS move_name,
    #                 account_move.move_type                                                              AS move_type,
    #                 account.code                                                                        AS account_code,
    #                 {account_name}                                                                      AS account_name,
    #                 journal.code                                                                        AS journal_code,
    #                 {journal_name}                                                                      AS journal_name,
    #                 %s                                                                                  AS column_group_key,
    #                 'indirectly_linked_aml'                                                             AS key
    #             FROM {tables}
    #                 LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
    #                 LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id,
    #
    #                 account_partial_reconcile partial,
    #                 account_move,
    #                 account_move_line aml_with_partner,
    #                 account_journal journal,
    #                 account_account account
    #             WHERE
    #                 (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
    #                 AND account_move_line.partner_id IS NULL
    #                 AND account_move.id = account_move_line.move_id
    #                 AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
    #                 AND {indirectly_linked_aml_partner_clause}
    #                 AND journal.id = account_move_line.journal_id
    #                 AND account.id = account_move_line.account_id
    #                 AND {where_clause}
    #                 AND partial.max_date BETWEEN %s AND %s
    #             ORDER BY account_move_line.date, account_move_line.id
    #         ''')
    #
    #     query = '(' + ') UNION ALL ('.join(queries) + ')'
    #
    #     if offset:
    #         query += ' OFFSET %s '
    #         all_params.append(offset)
    #
    #     if limit:
    #         query += ' LIMIT %s '
    #         all_params.append(limit)
    #
    #     self._cr.execute(query, all_params)
    #     for aml_result in self._cr.dictfetchall():
    #         if aml_result['key'] == 'indirectly_linked_aml':
    #
    #             # Append the line to the partner found through the reconciliation.
    #             if aml_result['partner_id'] in rslt:
    #                 rslt[aml_result['partner_id']].append(aml_result)
    #
    #             # Balance it with an additional line in the Unknown Partner section but having reversed amounts.
    #             if None in rslt:
    #                 rslt[None].append({
    #                     **aml_result,
    #                     'debit': aml_result['credit'],
    #                     'credit': aml_result['debit'],
    #                     'balance': -aml_result['balance'],
    #                 })
    #         else:
    #             rslt[aml_result['partner_id']].append(aml_result)
    #
    #     return rslt
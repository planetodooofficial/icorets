# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountingCommonPartnerReport(models.TransientModel):
    _name = 'account.common.partner.report'
    _inherit = "account.common.report"
    _description = 'Account Common Partner Report'

    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='customer')
    partner_ids = fields.Many2many('res.partner', string='Partners')

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

    def get_partner_if_none(self, data):
        data['computed'] = {}

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
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
                            SELECT DISTINCT "account_move_line".partner_id
                            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
                            WHERE "account_move_line".partner_id IS NOT NULL
                                AND "account_move_line".account_id = account.id
                                AND am.id = "account_move_line".move_id
                                AND am.state IN %s
                                AND "account_move_line".account_id IN %s
                                AND NOT account.deprecated
                                AND """ + query_get_data[1]
        # AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))

        partner_ids = [res['partner_id'] for res in
                       self.env.cr.dictfetchall()]

        return partner_ids

    def pre_print_report(self, data):
        data['form'].update(self.read(['result_selection'])[0])

        if self.partner_ids.ids:
            partner_record = self.get_partner_parent_child(self.partner_ids.ids)
        else:
            partner_ids = self.get_partner_if_none(data)
            partner_record = self.get_partner_parent_child(partner_ids)

        data['form'].update({'partner_ids': partner_record})
        return data

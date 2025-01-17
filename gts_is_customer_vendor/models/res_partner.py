# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is Customer?', tracking=True,
                                 help="Check this box if this contact is a customer. It can be selected in sales orders.")
    is_supplier = fields.Boolean(string='Is Vendor?', tracking=True,
                                 help="Check this box if this contact is a vendor. It can be selected in purchase orders.")
    is_expense = fields.Boolean(string='Is Expense?', tracking=True,
                                 help="Check this box if this contact is a Expense.")
    is_salary = fields.Boolean(string='Is Salary?', tracking=True,
                                 help="Check this box if this contact is a Salary.")
    is_advanced = fields.Boolean(string='Is Advanced?', tracking=True,
                                 help="Check this box if this contact is a Advanced.")


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('partner_id')
    def onchange_partner(self):
        for val in self:
            if val.move_id.move_type == 'entry' and val.partner_id:
                if val.partner_id.is_customer:
                    val.account_id = val.partner_id.property_account_receivable_id and \
                                     val.partner_id.property_account_receivable_id.id
                if val.partner_id.is_supplier:
                    val.account_id = val.partner_id.property_account_payable_id and \
                                     val.partner_id.property_account_payable_id.id
from odoo import models, fields


class AccountDeducteeType(models.Model):
    _name = 'account.deductee.type'
    _description = 'Deductee Type'

    name = fields.Char(string='Type', required=True)

    _sql_constraints = [
        ('type_uniq', 'unique(name)', 'Type should be Unique')
    ]

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class AccountDeducteeType(models.Model):
    _name = 'account.deductee.type'
    _description = 'Deductee Type'

    name = fields.Char(string='Type', required=True)

    @api.constrains('name')
    def _check_type_uniq(self):
        for rec in self:
            if rec.name:
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('name', '=', rec.name),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_('Type should be Unique'))

from odoo import models, api, fields, _


class AliasName(models.Model):
    _name = "alias.name"
    _rec_name = "name"

    name = fields.Char("Name", copy=False)

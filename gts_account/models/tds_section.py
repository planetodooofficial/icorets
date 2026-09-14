from odoo import models, fields


class SectionTDS(models.Model):
    _name = 'section.tds'
    _description = 'TDS Section'

    name = fields.Char(string="Name", required=True)

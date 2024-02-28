import json

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InheritPicking(models.Model):
    _inherit = 'stock.picking'

    dump_sequence = fields.Char(string='Sequence')


from odoo import models, fields, api, _
import json
import requests

from odoo.exceptions import UserError


class SaleChannelReport(models.TransientModel):
    _name = 'sale.channel.report'
    _description = 'Sale Channel Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    channel_id = fields.Many2many('shop.sales.channel', string='Channel')

    def btn_generate_xlsx_report(self):
        pass
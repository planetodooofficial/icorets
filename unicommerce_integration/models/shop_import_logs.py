from odoo import api, fields, models, _


class ShopImportLogs(models.Model):
    _name = 'shop.import.logs'
    _description = 'Shop Import Logs'
    _order = 'id desc'

    name = fields.Char('Name')
    shop_id = fields.Many2one('shop.instance', 'Shop Name')
    message = fields.Text('Message')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    count = fields.Integer('Count')
    state = fields.Selection([('success', 'Success'), ('exception', 'Exception')], string="Request State")
    operation_performed = fields.Char('Operation Performed')
    error_message = fields.Text('Error Message')

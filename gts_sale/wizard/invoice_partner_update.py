from csv import DictReader
from odoo import models, fields, api, _
from io import BytesIO
import base64
from datetime import datetime, date
import pandas as pd


class InvoicePartnerUpdate(models.TransientModel):
    _name = "invoice.partner.update"

    file = fields.Binary("File")
    file_name = fields.Char("File Name")

    def action_upload(self):
        self.ensure_one()
        excel_data = base64.b64decode(self.file)

        excel_file = BytesIO(excel_data)

        sheets = pd.ExcelFile(excel_file)
        df = sheets.parse(sheets.sheet_names[0])
        for index, row in df.iterrows():
            if row[0] == 'Number':
                continue
            account_move = self.env['account.move'].search(
                [('name', '=', row[0]), ('company_id', '=', self.env.company.id)], limit=1)
            if not account_move:
                continue
            partner = self.env['res.partner'].search([('name', 'like', row[1])], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': row[1]})
            if partner:
                sql_query = "update account_move set partner_id=%d, partner_shipping_id=%d where id=%d;" % (
                    partner.id, partner.id, account_move.id)
                self._cr.execute(sql_query)

                account_move._compute_invoice_partner_display_info()
                # partner onchange in invoice not working due to posted invoices

                sale_order = self.env['sale.order'].search([('invoice_ids', '=', account_move.id)])
                if sale_order:
                    sql_query_sale = "update sale_order set partner_id=%d, partner_invoice_id=%d, partner_shipping_id=%d where id=%d;" % (
                        partner.id, partner.id, partner.id, sale_order.id)
                    self._cr.execute(sql_query_sale)

                    picking = self.env['stock.picking'].search([('sale_id', '=', sale_order.id)])
                    if picking:
                        sql_query_picking = "update stock_picking set partner_id=%d where id=%d;" % (
                            partner.id, picking.id)
                        self._cr.execute(sql_query_picking)

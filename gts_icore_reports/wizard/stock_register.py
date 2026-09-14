from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64


class StockRegister(models.TransientModel):
    _name = 'stock.register'
    _description = "Stock Register Wizard"
    _rec_name = 'date'

    date = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.today)
    product_category = fields.Many2one('product.category', string='Product Category')
    report = fields.Binary(string='Report File')
    report_name = fields.Char(string='Report Filename')

    def get_product_details(self, product_id):
        prod_id = self.env['product.product'].browse(product_id)
        return (
            prod_id.name or '',
            prod_id.default_code or '',
            prod_id.categ_id.name or '',
            prod_id.uom_id.name or '',
            round(prod_id.standard_price or 0.0, 2)
        )

    def action_download_report(self):
        query_params = {
            'date': self.date,
            'end_date': self.end_date,
            'company_id': self.env.company.id,
        }

        category_condition = ""
        if self.product_category:
            category_condition = " AND prod_cat.id = %(category_id)s"
            query_params['category_id'] = self.product_category.id

        opening_query = f"""
            SELECT prod_prod.id AS product_id,
                (CASE 
                    WHEN (source_loc.usage = 'internal' AND dest_loc.usage != 'internal' AND st_move.date < %(date)s) THEN -SUM(COALESCE(st_move.quantity, st_move.product_uom_qty))
                    WHEN (source_loc.usage != 'internal' AND dest_loc.usage = 'internal' AND st_move.date < %(date)s) THEN SUM(COALESCE(st_move.quantity, st_move.product_uom_qty))
                    ELSE 0 
                END) AS opening_stock,
                (CASE 
                    WHEN (source_loc.usage != 'internal' AND dest_loc.usage = 'internal' AND st_move.date BETWEEN %(date)s AND %(end_date)s) THEN SUM(COALESCE(st_move.quantity, st_move.product_uom_qty))
                    ELSE 0
                END) AS inward_quantity,
                (CASE 
                    WHEN (source_loc.usage = 'internal' AND dest_loc.usage != 'internal' AND st_move.date BETWEEN %(date)s AND %(end_date)s) THEN SUM(COALESCE(st_move.quantity, st_move.product_uom_qty))
                    ELSE 0
                END) AS outward_quantity,
                st_move.origin,
                st_pick.partner_id,
                lot.name AS lot_id
            FROM stock_move AS st_move
            JOIN product_product AS prod_prod ON st_move.product_id = prod_prod.id
            JOIN product_template AS prod_tmpl ON prod_prod.product_tmpl_id = prod_tmpl.id
            JOIN stock_location AS source_loc ON st_move.location_id = source_loc.id
            JOIN stock_location AS dest_loc ON st_move.location_dest_id = dest_loc.id
            JOIN product_category AS prod_cat ON prod_tmpl.categ_id = prod_cat.id
            LEFT JOIN stock_move_line AS move_line ON st_move.id = move_line.move_id
            LEFT JOIN stock_picking AS st_pick ON st_move.picking_id = st_pick.id
            LEFT JOIN stock_lot AS lot ON move_line.lot_id = lot.id
            WHERE st_move.state = 'done' 
              AND st_move.company_id = %(company_id)s
              {category_condition}
            GROUP BY prod_prod.id, lot.name, source_loc.id, dest_loc.id, st_move.date, st_move.origin, st_pick.partner_id
        """

        self._cr.execute(opening_query, query_params)
        stock_moves = self.env.cr.dictfetchall()

        if not stock_moves:
            raise UserError(_("No stock move data found for the selected dates and category."))

        df = pd.DataFrame(stock_moves)

        product_details = []
        for row in df.itertuples():
            product_details.append(self.get_product_details(row.product_id))

        product_details_df = pd.DataFrame(
            product_details,
            columns=['product_name', 'internal_reference', 'categ_id', 'UOM', 'price_unit']
        )
        df = pd.concat([df, product_details_df], axis=1).fillna(False)
        df['Lot No'] = df['lot_id']

        # Fetch partner names
        partner_ids = [pid for pid in df['partner_id'].unique().tolist() if pid]
        partners = self.env['res.partner'].browse(partner_ids)
        partner_dict = {p.id: p.name for p in partners}
        df['Contact'] = df['partner_id'].map(partner_dict).fillna('')

        agg_functions = {
            'product_name': 'first',
            'Lot No': 'first',
            'internal_reference': 'first',
            'categ_id': 'first',
            'UOM': 'first',
            'price_unit': 'first',
            'opening_stock': 'sum',
            'inward_quantity': 'sum',
            'outward_quantity': 'sum',
            'origin': 'first',
            'Contact': 'first',
        }

        try:
            df = df.groupby(df['product_id']).aggregate(agg_functions)
        except KeyError:
            raise UserError(_("Could not aggregate stock register data."))

        df['closing_stock'] = (df['opening_stock'] + df['inward_quantity']) - df['outward_quantity']
        df['closing_amt'] = df['closing_stock'] * df['price_unit']
        df['opening_amt'] = df['opening_stock'] * df['price_unit']
        df['inward_amt'] = df['inward_quantity'] * df['price_unit']
        df['outward_amt'] = df['outward_quantity'] * df['price_unit']

        df.columns = (
            'Product Name', 'Lot No', 'Internal Reference', 'Product Category', 'UOM', 'Cost Price',
            'Opening Stock', 'Inward Quantity', 'Outward Quantity', 'Origin', 'Contact',
            'Closing Stock', 'Closing Price', 'Opening Amount', 'Inward Amount', 'Outward Amount'
        )
        df = df[[
            'Product Name', 'Lot No', 'Internal Reference', 'Product Category', 'UOM',
            'Cost Price', 'Opening Stock', 'Opening Amount', 'Inward Quantity', 'Inward Amount',
            'Outward Quantity', 'Outward Amount', 'Closing Stock', 'Closing Price', 'Origin', 'Contact'
        ]]

        fp = io.BytesIO()
        df.to_excel(fp, index=False)
        self.report = base64.encodebytes(fp.getvalue())
        self.report_name = f"Stock_Register_Report_{self.date.strftime('%d-%m-%Y')}_{self.end_date.strftime('%d-%m-%Y')}.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=stock.register&download=true&field=report&id={self.id}&filename={self.report_name}',
            'target': 'new',
            'nodestroy': False,
        }

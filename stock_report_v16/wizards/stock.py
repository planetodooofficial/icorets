from odoo import models, fields, api, _
import pandas as pd
import io
import base64

from odoo.exceptions import UserError


class StockRegister(models.TransientModel):
    _name = 'stock.register'
    _description = "Stock Register Class"
    _rec_name = 'date'

    date = fields.Date(required=1)
    end_date = fields.Date(required=1)
    product_category = fields.Many2one('product.category', string='Product Category')
    report = fields.Binary()
    report_name = fields.Char()

    def get_product_details(self, product_id):
        prod_id = self.env['product.product'].browse(product_id)
        return prod_id.name, prod_id.default_code, prod_id.categ_id.name, prod_id.uom_id.name, round(
            prod_id.standard_price, 2)

    # def action_download_report(self):
    #     opening_query = """select prod_prod.id as product_id,
    #      (case
    #         when (source_loc.usage = 'internal' and dest_loc.usage != 'internal' and st_move.date < %(date)s) THEN -sum(st_move.product_uom_qty)
    #         when (source_loc.usage != 'internal' and dest_loc.usage = 'internal' and st_move.date < %(date)s) THEN sum(st_move.product_uom_qty)
    #         ELSE 0 END) AS opening_stock,
    #      (case
    #            when(source_loc.usage != 'internal' and dest_loc.usage = 'internal' and st_move.date between %(date)s and %(end_date)s) THEN sum(st_move.product_uom_qty) END) AS inward_quantity,
    #       (case when (source_loc.usage = 'internal' and dest_loc.usage != 'internal' and st_move.date between %(date)s and %(end_date)s) THEN sum(st_move.product_uom_qty) END) AS outward_quantity
    #      from stock_move as st_move
    #      join product_product prod_prod on st_move.product_id = prod_prod.id
    #      join product_template prod_tmpl on prod_prod.product_tmpl_id = prod_tmpl.id
    #      join stock_location source_loc on st_move.location_id = source_loc.id
    #      join stock_location dest_loc on st_move.location_dest_id = dest_loc.id
    #      join product_category prod_cat on prod_tmpl.categ_id = prod_cat.id
    #      where st_move.state = 'done'
    #      and st_move.company_id = %(company_id)s
    #      """
    #
    #     if self.product_category:
    #         opening_query += "and prod_cat.id =" + str(self.product_category.id)
    #
    #     opening_query += "group by (prod_prod.id, source_loc.id, dest_loc.id, st_move.date, st_move.origin ,st_pick.partner_id);"
    #
    #     morgify_query = self.env.cr.mogrify(opening_query, {'date': self.date, 'end_date': self.end_date,
    #                                                         'company_id': self.env.company.id}).decode(
    #         self.env.cr.connection.encoding)
    #     self._cr.execute(morgify_query)
    #     stock_moves = self.env.cr.dictfetchall()
    #     df = pd.DataFrame(stock_moves)
    #     product_details = []
    #     for row in df.itertuples():
    #         product_details.append(self.get_product_details(row.product_id))
    #     product_details_df = pd.DataFrame(product_details,
    #                                       columns=['product_name', 'internal_reference', 'categ_id', 'UOM',
    #                                                'price_unit'])
    #     df = pd.concat([df, product_details_df], axis=1)
    #
    #     agg_functions = {'product_name': 'first', 'internal_reference': 'first', 'categ_id': 'first', 'UOM': 'first',
    #                      'price_unit': 'first',
    #                      'opening_stock': 'sum', 'inward_quantity': 'sum', 'outward_quantity': 'sum'}
    #     try:
    #         df = df.groupby(df['product_id']).aggregate(agg_functions)
    #     except KeyError:
    #         raise UserError(_('No Product Found for "%s" Category' % self.product_category.name))
    #
    #     # df[['opening_stock', 'inward_quantity', 'outward_quantity', 'closing_stock', 'closing_amt','opening_amt','inward_amt','outward_amt']] = list(map(self.get_summation_amount, df['unit_weight'], df['price_unit'], df['opening_stock'], df['inward_quantity'], df['outward_quantity']))
    #     # df[['closing_stock', 'closing_amt','opening_amt','inward_amt','outward_amt']] = list(map(self.get_summation_amount, df['price_unit'], df['opening_stock'], df['inward_quantity'], df['outward_quantity']))
    #     df['closing_stock'] = (df['opening_stock'] + df['inward_quantity']) - df['outward_quantity']
    #     df['closing_amt'] = df['closing_stock'] * df['price_unit']
    #     df['opening_amt'] = df['opening_stock'] * df['price_unit']
    #     df['inward_amt'] = df['inward_quantity'] * df['price_unit']
    #     df['outward_amt'] = df['outward_quantity'] * df['price_unit']
    #
    #     df.columns = ('Product Name', 'Internal Reference', 'Product Category', 'UOM', 'Cost Price', 'Opening Stock',
    #                   'Inward Quantity',
    #                   'Outward Quantity', 'Closing Stock', 'Closing Price', 'Opening Amount', 'Inward Amount',
    #                   'Outward Amount', 'Origin', 'Contact')
    #     df = df[['Product Name', 'Internal Reference', 'Product Category', 'UOM',
    #              'Cost Price', 'Opening Stock', 'Opening Amount',
    #              'Inward Quantity', 'Inward Amount', 'Outward Quantity', 'Outward Amount',
    #              'Closing Stock', 'Closing Price']]
    #     fp = io.BytesIO()
    #     df.to_excel(fp, index=False)
    #     self.report = base64.encodebytes(fp.getvalue())
    #     self.report_name = "Test.xlsx"
    #     return {'type': 'ir.actions.act_url',
    #             'url': 'web/content/?model=stock.register&download=true&field=report&id={}&fillename={}'.format(self.id,
    #                                                                                                             self.report_name),
    #             'target': 'new', 'nodestroy': False}

    def action_download_report(self):
        opening_query = """select prod_prod.id as product_id,
         (case 
            when (source_loc.usage = 'internal' and dest_loc.usage != 'internal' and st_move.date < %(date)s) THEN -sum(st_move.product_uom_qty)
            when (source_loc.usage != 'internal' and dest_loc.usage = 'internal' and st_move.date < %(date)s) THEN sum(st_move.product_uom_qty)
            ELSE 0 END) AS opening_stock,
         (case 
               when(source_loc.usage != 'internal' and dest_loc.usage = 'internal' and st_move.date between %(date)s and %(end_date)s) THEN sum(st_move.product_uom_qty) END) AS inward_quantity,
          (case when (source_loc.usage = 'internal' and dest_loc.usage != 'internal' and st_move.date between %(date)s and %(end_date)s) THEN sum(st_move.product_uom_qty) END) AS outward_quantity,
          st_move.origin,
          st_pick.partner_id,
          lot.name as lot_id
                    
         from stock_move as st_move
         join product_product prod_prod on st_move.product_id = prod_prod.id
         join product_template prod_tmpl on prod_prod.product_tmpl_id = prod_tmpl.id
         join stock_location source_loc on st_move.location_id = source_loc.id
         join stock_location dest_loc on st_move.location_dest_id = dest_loc.id
         join product_category prod_cat on prod_tmpl.categ_id = prod_cat.id
         left join stock_move_line as move_line ON st_move.id = move_line.move_id
         left join stock_picking st_pick on st_move.picking_id = st_pick.id
         left join stock_lot as lot ON move_line.lot_id = lot.id
         
         where st_move.state = 'done' 
         and st_move.company_id = %(company_id)s
         """

        if self.product_category:
            opening_query += "and prod_cat.id =" + str(self.product_category.id)

        opening_query += "group by (prod_prod.id, lot.name, source_loc.id, dest_loc.id, st_move.date, st_move.origin, st_pick.partner_id);"

        morgify_query = self.env.cr.mogrify(opening_query, {'date': self.date, 'end_date': self.end_date,
                                                            'company_id': self.env.company.id}).decode(
            self.env.cr.connection.encoding)

        print(morgify_query)

        self._cr.execute(morgify_query)
        stock_moves = self.env.cr.dictfetchall()
        df = pd.DataFrame(stock_moves)
        print("fetch all",df)
        product_details = []
        for row in df.itertuples():
            product_details.append(self.get_product_details(row.product_id))
        product_details_df = pd.DataFrame(product_details,
                                          columns=['product_name', 'internal_reference', 'categ_id', 'UOM',
                                                   'price_unit'])
        df = pd.concat([df, product_details_df], axis=1).fillna(False)
        df['Lot No'] = df['lot_id']
        print("product_details_df",product_details_df)
        # Fetch partner names
        partner_ids = df['partner_id'].unique().tolist()
        partners = self.env['res.partner'].browse(partner_ids)
        partner_names = partners.mapped('name')
        partner_dict = dict(zip(partner_ids, partner_names))
        df['Contact'] = df['partner_id'].map(partner_dict)

        agg_functions = {'product_name': 'first', 'Lot No': 'first', 'internal_reference': 'first', 'categ_id': 'first', 'UOM': 'first',
                         'price_unit': 'first',
                         'opening_stock': 'sum', 'inward_quantity': 'sum', 'outward_quantity': 'sum',
                         'origin': 'first', 'Contact': 'first'}
        # try:
        df = df.groupby(df['product_id']).aggregate(agg_functions)
        # except KeyError:
        #     raise UserError(_('No Product Found for "%s" Category' % self.product_category.name))

        df['closing_stock'] = (df['opening_stock'] + df['inward_quantity']) - df['outward_quantity']
        df['closing_amt'] = df['closing_stock'] * df['price_unit']
        df['opening_amt'] = df['opening_stock'] * df['price_unit']
        df['inward_amt'] = df['inward_quantity'] * df['price_unit']
        df['outward_amt'] = df['outward_quantity'] * df['price_unit']

        df.columns = ('Product Name', 'Lot No', 'Internal Reference', 'Product Category', 'UOM', 'Cost Price', 'Opening Stock',
                      'Inward Quantity', 'Outward Quantity', 'Origin', 'Contact', 'Closing Stock', 'Closing Price',
                      'Opening Amount', 'Inward Amount', 'Outward Amount')
        df = df[['Product Name', 'Lot No', 'Internal Reference', 'Product Category', 'UOM',
                 'Cost Price', 'Opening Stock', 'Opening Amount', 'Inward Quantity', 'Inward Amount',
                 'Outward Quantity',
                 'Outward Amount', 'Closing Stock', 'Closing Price', 'Origin', 'Contact']]
        fp = io.BytesIO()
        df.to_excel(fp, index=False)
        self.report = base64.encodebytes(fp.getvalue())
        self.report_name = "Stock_Register_Report_" + str(self.date.strftime('%d/%m/%Y')) + "-" + str(self.end_date.strftime('%d/%m/%Y')) + ".xlsx"
        return {'type': 'ir.actions.act_url',
                'url': 'web/content/?model=stock.register&download=true&field=report&id={}&filename={}'.format(self.id,
                                                                                                                self.report_name),
                'target': 'new', 'nodestroy': False}

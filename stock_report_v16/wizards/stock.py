from odoo import models, fields, api, _
import pandas as pd
import io
import base64


class StockRegister(models.TransientModel):
    _name = 'stock.register'
    _description = "Stock Register Class"
    _rec_name = 'date'

    date = fields.Date(required=1)
    end_date = fields.Date(required=1)
    product_category = fields.Many2one('product.category', string='Product Category')
    accounting_category = fields.Many2one('accounting.category', string='Accounting Category')
    report = fields.Binary()
    report_name = fields.Char()

    def get_product_details(self, product_id):
        prod_id = self.env['product.product'].browse(product_id)
        return prod_id.name, prod_id.default_code,prod_id.categ_id.name,prod_id.accounting_category.name, prod_id.uom_id.name, prod_id.unit_weight,prod_id.avg_comp_cost, round(prod_id.standard_price, 2)
        # return prod_id.name, prod_id.default_code,prod_id.categ_id.name,prod_id.accounting_category.name, prod_id.uom_id.name, prod_id.unit_weight,prod_id.avg_comp_cost, prod_id.avg_comp_cost > 0 and round(prod_id.avg_comp_cost, 2) or round(prod_id.standard_price, 2)


    # @staticmethod
    # def get_summation_amount(unit_weight=0, price_unit=0, opening_qty=0, inward_qty=0, outward_qty=0):
    #     if unit_weight > 0:
    #         opening_price_mm = opening_qty * price_unit
    #         inward_price_mm = opening_qty * price_unit
    #         outward_price_mm = opening_qty * price_unit
    #         opening_qty *= unit_weight
    #         inward_qty *= unit_weight
    #         outward_qty *= unit_weight
    #
    #     closing_qty = (opening_qty + inward_qty) - outward_qty
    #     closing_price = closing_qty * price_unit
    #     opening_price = opening_qty * price_unit
    #     inward_price = inward_qty * price_unit
    #     outward_price = outward_qty * price_unit
    #     return price_unit, opening_qty, inward_qty, outward_qty, closing_qty, round(closing_price, 2), round(opening_price, 2), round(inward_price, 2), round(outward_price, 2)

    # @staticmethod
    # def get_summation_amount(price_unit=0, opening_qty=0, inward_qty=0, outward_qty=0):
    #     closing_qty = (opening_qty + inward_qty) - outward_qty
    #     closing_price = closing_qty * price_unit
    #     opening_price = opening_qty * price_unit
    #     inward_price = inward_qty * price_unit
    #     outward_price = outward_qty * price_unit
    #     return closing_qty, round(closing_price, 2), round(opening_price, 2), round(inward_price, 2), round(outward_price, 2)

    def action_download_report(self):
        opening_query = """select prod_prod.id as product_id,
         (case 
            when (source_loc.usage = 'internal' and dest_loc.usage != 'internal' and st_move.date < %(date)s) THEN -sum(st_move.product_uom_qty)
            when (source_loc.usage != 'internal' and dest_loc.usage = 'internal' and st_move.date < %(date)s) THEN sum(st_move.product_uom_qty)
            ELSE 0 END) AS opening_stock,
         (case 
               when(source_loc.usage != 'internal' and dest_loc.usage = 'internal' and st_move.date between %(date)s and %(end_date)s) THEN sum(st_move.product_uom_qty) END) AS inward_quantity,
          (case when (source_loc.usage = 'internal' and dest_loc.usage != 'internal' and st_move.date between %(date)s and %(end_date)s) THEN sum(st_move.product_uom_qty) END) AS outward_quantity
         from stock_move as st_move
         join product_product prod_prod on st_move.product_id = prod_prod.id
         join product_template prod_tmpl on prod_prod.product_tmpl_id = prod_tmpl.id
         join stock_location source_loc on st_move.location_id = source_loc.id
         join stock_location dest_loc on st_move.location_dest_id = dest_loc.id
         join product_category prod_cat on prod_tmpl.categ_id = prod_cat.id
         join accounting_category acc_cat on prod_tmpl.accounting_category = acc_cat.id
         where st_move.state = 'done' 
         and st_move.company_id = %(company_id)s
         """

        if self.product_category:
            opening_query += "and prod_cat.id =" + str(self.product_category.id)
        if self.accounting_category:
            opening_query += "and acc_cat.id =" + str(self.accounting_category.id)
        opening_query += "group by (prod_prod.id, source_loc.id, dest_loc.id, st_move.date);"

        # and prod_cat.id = %(product_category)s
        #  and acc_cat.id = %(accounting_category)s

        morgify_query = self.env.cr.mogrify(opening_query, {'date': self.date, 'end_date': self.end_date,
                                                            'company_id': self.env.company.id}).decode(self.env.cr.connection.encoding)
        self._cr.execute(morgify_query)
        stock_moves = self.env.cr.dictfetchall()
        df = pd.DataFrame(stock_moves)
        # df[['product_name', 'internal_reference', 'UOM','unit_weight', 'price_unit']] = list(map(self.get_product_details, df['product_id']))
        # df.loc[:, ['product_name', 'internal_reference', 'UOM','unit_weight','comp_cost','categ_id', 'price_unit']] = list(map(self.get_product_details, df['product_id']))
        product_details = []
        for row in df.itertuples():
            product_details.append(self.get_product_details(row.product_id))
        product_details_df = pd.DataFrame(product_details,
                                          columns=['product_name', 'internal_reference', 'categ_id','accounting_category','UOM','unit_weight','comp_cost',
                                                   'price_unit'])
        df = pd.concat([df, product_details_df], axis=1)


        agg_functions = {'product_name': 'first', 'internal_reference': 'first','categ_id': 'first','accounting_category':'first', 'UOM': 'first','unit_weight':'first','price_unit': 'first','comp_cost':'first',
                         'opening_stock': 'sum', 'inward_quantity': 'sum', 'outward_quantity': 'sum'}
        df = df.groupby(df['product_id']).aggregate(agg_functions)

        # df[['opening_stock', 'inward_quantity', 'outward_quantity', 'closing_stock', 'closing_amt','opening_amt','inward_amt','outward_amt']] = list(map(self.get_summation_amount, df['unit_weight'], df['price_unit'], df['opening_stock'], df['inward_quantity'], df['outward_quantity']))
        # df[['closing_stock', 'closing_amt','opening_amt','inward_amt','outward_amt']] = list(map(self.get_summation_amount, df['price_unit'], df['opening_stock'], df['inward_quantity'], df['outward_quantity']))
        df['closing_stock'] = (df['opening_stock'] + df['inward_quantity']) - df['outward_quantity']
        df['closing_amt'] = df['closing_stock'] * df['price_unit']
        df['opening_amt'] = df['opening_stock'] * df['price_unit']
        df['inward_amt'] = df['inward_quantity'] * df['price_unit']
        df['outward_amt'] = df['outward_quantity'] * df['price_unit']
        df.loc[df['unit_weight'] > 0, 'Opening Stock KG'] = df.loc[df['unit_weight'] > 0, 'unit_weight'] * df.loc[df['unit_weight'] > 0, 'opening_stock']
        df.loc[df['unit_weight'] > 0, 'Inward Stock KG'] = df.loc[df['unit_weight'] > 0, 'unit_weight'] * df.loc[df['unit_weight'] > 0, 'inward_quantity']
        df.loc[df['unit_weight'] > 0, 'Outward Stock KG'] = df.loc[df['unit_weight'] > 0, 'unit_weight'] * df.loc[df['unit_weight'] > 0, 'outward_quantity']
        df.loc[df['unit_weight'] > 0, 'Closing Stock KG'] = df.loc[df['unit_weight'] > 0, 'unit_weight'] * df.loc[df['unit_weight'] > 0, 'closing_stock']
        # df.loc[df['unit_weight']> 0, 'Cost Price KG'] = df.loc[df['unit_weight'] > 0, 'opening_amt'] / df.loc[df['unit_weight'] > 0, 'Opening Stock KG']
        df.loc[(df['unit_weight'] > 0) & (df['Opening Stock KG'] != 0), 'Cost Price KG'] = df.loc[(df['unit_weight'] > 0) & (df['Opening Stock KG'] != 0), 'opening_amt'] / df.loc[(df[
                                                                                                       'unit_weight'] > 0) & (df['Opening Stock KG'] != 0), 'Opening Stock KG']
        df.columns = ('Product Name', 'Internal Reference','Product Category','Accounting Category', 'UOM', 'Unit Weight', 'Cost Price','Avg Comp Cost', 'Opening Stock', 'Inward Quantity',
                      'Outward Quantity', 'Closing Stock', 'Closing Price', 'Opening Amount', 'Inward Amount', 'Outward Amount',
                      'Opening Stock KG','Inward Stock KG','Outward Stock KG','Closing Stock KG','Cost Price KG')
        df = df[['Product Name', 'Internal Reference','Product Category','Accounting Category', 'UOM', 'Unit Weight',
                 'Cost Price','Avg Comp Cost', 'Cost Price KG', 'Opening Stock','Opening Stock KG','Opening Amount',
                 'Inward Quantity','Inward Stock KG','Inward Amount','Outward Quantity', 'Outward Stock KG','Outward Amount',
                 'Closing Stock', 'Closing Price','Closing Stock KG']]
        fp = io.BytesIO()
        df.to_excel(fp, index=False)
        self.report = base64.encodebytes(fp.getvalue())
        self.report_name = "Test.xlsx"
        return {'type': 'ir.actions.act_url', 'url': 'web/content/?model=stock.register&download=true&field=report&id={}&fillename={}'.format(self.id, self.report_name),
                'target': 'new', 'nodestroy': False}




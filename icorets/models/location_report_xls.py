import datetime
from odoo import api, models, fields, _


class LocationReportWizard(models.TransientModel):
    _name = 'locations.report'

    def location_report_xlsx(self):
        return self.env.ref('icorets.location_report_action_xls').report_action(self)

    # def location_report_xlsx_qtn(self):
    #     return self.env.ref('icorets.location_report_action_xls_qtn').report_action(self)

class LocationReport(models.AbstractModel):
    _name = "report.icorets.location_report_xls"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        bold = workbook.add_format(
            {'font_size': 11, 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7', 'font': 'Calibri Light',
             'text_wrap': True, 'border': 1})
        bold_red = workbook.add_format(
            {'font_size': 11, 'color': '#FF0000', 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7',
             'font': 'Calibri Light',
             'text_wrap': True, 'border': 1})
        sheet = workbook.add_worksheet('Location Summary')
        sheet.set_column(0, 0, 20)
        sheet.set_column(0, 1, 25)
        sheet.set_column(0, 2, 25)
        sheet.set_column(0, 3, 25)
        sheet.set_column(0, 4, 25)
        sheet.set_column(0, 5, 25)
        sheet.set_column(0, 6, 25)
        sheet.set_column(0, 7, 25)
        sheet.set_column(0, 8, 25)
        sheet.set_column(0, 9, 25)
        sheet.set_column(0, 10, 25)
        sheet.set_column(0, 11, 25)
        sheet.set_column(0, 12, 25)
        sheet.set_column(0, 13, 25)
        sheet.set_column(0, 14, 25)
        sheet.set_column(0, 15, 25)
        sheet.set_column(0, 16, 25)
        sheet.set_column(0, 17, 25)
        sheet.set_column(0, 18, 25)
        sheet.set_column(0, 19, 25)
        sheet.set_column(0, 20, 25)
        sheet.set_column(0, 21, 17)
        sheet.set_column(0, 22, 17)
        sheet.set_column(0, 23, 17)
        sheet.set_column(0, 24, 17)
        sheet.set_column(0, 25, 25)
        sheet.set_column(0, 26, 25)
        sheet.set_column(0, 27, 25)
        sheet.set_column(0, 28, 25)
        sheet.set_column(0, 29, 25)
        sheet.set_column(0, 30, 25)
        sheet.set_column(0, 31, 25)
        sheet.set_column(0, 32, 25)
        sheet.set_column(0, 33, 25)
        sheet.set_column(0, 34, 25)
        sheet.set_column(0, 35, 25)
        sheet.set_column(0, 36, 25)
        sheet.set_column(0, 37, 25)
        sheet.set_column(0, 38, 25)
        sheet.set_column(0, 39, 25)
        sheet.set_column(0, 40, 25)
        sheet.set_column(0, 41, 25)
        sheet.set_column(0, 42, 25)
        sheet.set_column(0, 43, 25)
        sheet.set_column(0, 44, 25)
        sheet.set_column(0, 45, 25)

        # **************************************************
        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'Category 1', bold)
        sheet.write(0, 2, 'Category 2', bold)
        sheet.write(0, 3, 'Category 3', bold)
        sheet.write(0, 4, 'Function Sport', bold)
        sheet.write(0, 5, 'Gender', bold)
        sheet.write(0, 6, 'Age group', bold)
        sheet.write(0, 7, 'Title', bold)
        sheet.write(0, 8, 'Composition / Material', bold)
        sheet.write(0, 9, 'Technology / Features', bold)
        sheet.write(0, 10, 'Event', bold)
        sheet.write(0, 11, 'HSN Code', bold)
        sheet.write(0, 12, 'Style Code', bold)
        sheet.write(0, 13, 'Article Code', bold)
        sheet.write(0, 14, 'SKU', bold)
        sheet.write(0, 15, 'EAN Code', bold)
        sheet.write(0, 16, 'ASIN', bold)
        sheet.write(0, 17, 'FSIN', bold)
        sheet.write(0, 18, 'Myntra', bold)
        sheet.write(0, 19, 'AJIO', bold)
        sheet.write(0, 20, 'Fancode', bold)
        sheet.write(0, 21, 'Swiggy', bold)
        sheet.write(0, 22, 'Bigbasket', bold)
        sheet.write(0, 23, 'Blinkit', bold)
        sheet.write(0, 24, 'Zepto', bold)
        sheet.write(0, 25, 'Colour', bold)
        sheet.write(0, 26, 'Size', bold)
        sheet.write(0, 27, 'MRP', bold)
        sheet.write(0, 28, 'GST', bold)
        sheet.write(0, 29, 'IHO Stock', bold)
        sheet.write(0, 30, 'Bhiwandi Stock', bold)
        sheet.write(0, 31, 'Delhi Stock', bold)
        sheet.write(0, 32, 'Total Qty', bold)
        sheet.write(0, 33, 'Quotation Qty', bold)
        sheet.write(0, 34, 'Confirmed SO qty', bold)
        sheet.write(0, 35, 'FREE TO USE', bold)
        sheet.write(0, 36, 'PO Receipt Pending', bold)
        sheet.write(0, 37, 'To Replenish', bold)
        sheet.write(0, 38, 'Product Net Weight (gms)', bold)
        sheet.write(0, 39, 'Product Length (cm)', bold)
        sheet.write(0, 40, 'Product Breadth (cm)', bold)
        sheet.write(0, 41, 'Product Height (cm)', bold)
        sheet.write(0, 42, 'Package Gross Weight (gms)', bold)
        sheet.write(0, 43, 'Package Length (cm)', bold)
        sheet.write(0, 44, 'Package Breadth (cm)', bold)
        sheet.write(0, 45, 'Package Height (cm)', bold)
        # sheet.write(0, 30, '(Onhand + incoming) - outgoing', bold)
        # sheet.write(0, 31, '(Onhand + incoming) - outgoing(With_Qtn)', bold)
        sheet.freeze_panes(1, 0)

        row = 1
        col = 0
        product_data = {}

        products = self.env['product.product'].search([])

        for product in products:
            product_id = product.id

            product_data[product_id] = {
                'Brand': product.brand_id_rel.name or '',
                'Category 1': product.categ_id.parent_id.parent_id.name or '',
                'Category 2': product.categ_id.parent_id.name or '',
                'Category 3': product.categ_id.name or '',
                'Function Sport': product.variants_func_spo or '',
                'Gender': product.gender or '',
                'Title': product.name or '',
                'SKU Code': product.default_code or '',
                'Composition / Material': product.material or '',
                'Technology / Features': product.variants_tech_feat or '',
                'Event': product.occasion or '',
                'HSN Code': product.l10n_in_hsn_code or product.sale_hsn.hsnsac_code or '',
                'Style Code': product.style_code or '',
                'Article Code': product.variant_article_code or '',
                'EAN Code': product.barcode or '',
                'ASIN': product.variants_asin or '',
                'FSIN': product.variants_fsn or '',
                'Myntra': product.myntra or '',
                'AJIO': product.ajio or '',
                'Fancode': product.fancode or '',
                'Swiggy': product.swiggy or '',
                'Bigbasket': product.bigbasket or '',
                'Blinkit': product.blinkit or '',
                'Zepto': product.zepto or '',
                'Colour': product.color or '',
                'Size': product.size or '',
                'MRP': product.lst_price or '',
                'GST': ''.join([str(x) for x in product.taxes_id.name]) if product.taxes_id else '',
                'IHO Stock': '',
                'Bhiwandi Stock': '',
                'Delhi Stock': '',
                'Total': product.qty_available or '',
                'To Replenish': 0,
                '(Onhand + incoming) - outgoing': product.virtual_available or '',
                '(Onhand + incoming) - outgoing(With_Qtn)': 0,
                'Quotation Qty': 0,
                'Confirmed SO qty': 0, # Initialize reserved quantity to 0
                'FREE TO USE': 0,
                'PO Receipt Pending': 0,
                'Age group': product.age_group or '',
                'Product Net Weight (gms)': product.product_net_weight or '',
                'Product Length (cm)': product.product_dimension1 or '',
                'Product Breadth (cm)': product.product_dimension2 or '',
                'Product Height (cm)': product.product_dimension3 or '',
                'Package Length (cm)': product.package_dimension1 or '',
                'Package Breadth (cm)': product.package_dimension2 or '',
                'Package Height (cm)': product.package_dimension3 or '',
                'Package Gross Weight (gms)': product.package_weight or '',

            }

            stock_quants = product.stock_quant_ids.filtered(lambda q: q.location_id.usage == 'internal')

            for quant in stock_quants:
                if quant.location_id.location_id.name == 'IHO':
                    product_data[product_id]['IHO Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BHW':
                    product_data[product_id]['Bhiwandi Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DEL':
                    product_data[product_id]['Delhi Stock'] = quant.quantity

            #Find quotations related to the product

            quotation_orders = self.env['sale.order'].search(
                [('order_line.product_id', '=', product_id), ('state', '=', 'draft'), ('state', '!=', 'cancel')])
            qty_to_deliver_qtn = sum(
                order_line.product_uom_qty - order_line.qty_delivered for order in quotation_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)
            # Update 'Quotation Qty'
            product_data[product_id]['Quotation Qty'] = qty_to_deliver_qtn


            # Find sales orders related to the product
            sale_orders = self.env['sale.order'].search([('order_line.product_id', '=', product_id), ('state', 'not in', ['draft', 'cancel', 'sent'])])
            # Calculate 'Qty to Deliver' based on confirmed sales order quantities
            qty_to_deliver = sum(
                order_line.product_uom_qty - order_line.qty_delivered for order in sale_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)
            # Update 'Reserved Qty'
            product_data[product_id]['Confirmed SO qty'] = qty_to_deliver

            # Update 'FREE TO USE'
            free_to_use = 0
            # product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver
            if product.qty_available < qty_to_deliver:
                product_data[product_id]['FREE TO USE'] = 0
            else:
                product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver
                free_to_use = product.qty_available - qty_to_deliver


            # Fetch purchase orders related to the product
            purchase_orders = self.env['purchase.order'].search([('order_line.product_id', '=', product_id), ('state', 'not in', ['draft','to approve', 'cancel', 'sent'])])

            # Calculate 'Ordered - Received' based on unprocessed purchase order quantities
            order_pending_qty = sum(
                order_line.product_qty - order_line.qty_received for order in purchase_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)

            # Update 'Ordered - Received'
            product_data[product_id]['PO Receipt Pending'] = order_pending_qty

            if free_to_use > 0:
                product_data[product_id]['To Replenish'] = 0
            else:
                replenish_qty = qty_to_deliver - product.qty_available
                product_data[product_id]['To Replenish'] = replenish_qty - order_pending_qty
                if product_data[product_id]['To Replenish'] < 0:
                    product_data[product_id]['To Replenish'] = 0


            quotation_orders = self.env['sale.order'].search(
                [('order_line.product_id', '=', product_id), ('state', '=', 'draft'),('state', '!=', 'cancel')])

            # Calculate outgoing quantity based on sale orders and quotation orders
            quotation_outgoing_qty = sum(
                order_line.product_uom_qty for order in quotation_orders for order_line in order.order_line
                if order_line.product_id.id == product_id)

            # Total outgoing quantity
            outgoing_qty = product.outgoing_qty + quotation_outgoing_qty

            incoming_qty = product.incoming_qty
            onhand_incoming_minus_outgoing = product.qty_available + incoming_qty - outgoing_qty

            # Update '(Onhand + incoming) - outgoing'
            product_data[product_id]['(Onhand + incoming) - outgoing(With_Qtn)'] = onhand_incoming_minus_outgoing


        # Write data to the sheet
        for product_id, data in sorted(product_data.items(), key=lambda x: (x[1]['Brand'].lower(), x[1]['Category 1'].lower(), x[1]['Category 2'].lower(), x[1]['Category 3'].lower())):
            print(data,'dataa')
            sheet.write(row, col, data['Brand'])
            sheet.write(row, col + 1, data['Category 1'])
            sheet.write(row, col + 2, data['Category 2'])
            sheet.write(row, col + 3, data['Category 3'])
            sheet.write(row, col + 4, data['Function Sport'])
            sheet.write(row, col + 5, data['Gender'])
            sheet.write(row, col + 6, data['Age group'])
            sheet.write(row, col + 7, data['Title'])
            sheet.write(row, col + 8, data['Composition / Material'])
            sheet.write(row, col + 9, data['Technology / Features'])
            sheet.write(row, col + 10, data['Event'])
            sheet.write(row, col + 11, data['HSN Code'])
            sheet.write(row, col + 12, data['Style Code'])
            sheet.write(row, col + 13, data['Article Code'])
            sheet.write(row, col + 14, data['SKU Code'])
            sheet.write(row, col + 15, data['EAN Code'])
            sheet.write(row, col + 16, data['ASIN'])
            sheet.write(row, col + 17, data['FSIN'])
            sheet.write(row, col + 18, data['Myntra'])
            sheet.write(row, col + 19, data['AJIO'])
            sheet.write(row, col + 20, data['Fancode'])
            sheet.write(row, col + 21, data['Swiggy'])
            sheet.write(row, col + 22, data['Bigbasket'])
            sheet.write(row, col + 23, data['Blinkit'])
            sheet.write(row, col + 24, data['Zepto'])
            sheet.write(row, col + 25, data['Colour'])
            sheet.write(row, col + 26, data['Size'])
            sheet.write(row, col + 27, data['MRP'])
            sheet.write(row, col + 28, data['GST'])
            sheet.write(row, col + 29, data['IHO Stock'])
            sheet.write(row, col + 30, data['Bhiwandi Stock'])
            sheet.write(row, col + 31, data['Delhi Stock'])
            sheet.write(row, col + 32, data['Total'])
            sheet.write(row, col + 33, data['Quotation Qty'])
            sheet.write(row, col + 34, data['Confirmed SO qty'])
            sheet.write(row, col + 35, data['FREE TO USE'])
            sheet.write(row, col + 36, data['PO Receipt Pending'])
            sheet.write(row, col + 37, data['To Replenish'])
            sheet.write(row, col + 38, data['Product Net Weight (gms)'])
            sheet.write(row, col + 39, data['Product Length (cm)'])
            sheet.write(row, col + 40, data['Product Breadth (cm)'])
            sheet.write(row, col + 41, data['Product Height (cm)'])
            sheet.write(row, col + 42, data['Package Gross Weight (gms)'])
            sheet.write(row, col + 43, data['Package Length (cm)'])
            sheet.write(row, col + 44, data['Package Breadth (cm)'])
            sheet.write(row, col + 45, data['Package Height (cm)'])
            # sheet.write(row, col +30, data['(Onhand + incoming) - outgoing'])
            # sheet.write(row, col + 31, data['(Onhand + incoming) - outgoing(With_Qtn)'])

            row += 1



# class LocationReportQtn(models.AbstractModel):
#     _name = "report.icorets.location_report_xlsx_qtn"
#     _inherit = "report.report_xlsx.abstract"
#
#     def generate_xlsx_report(self, workbook, data, lines):
#         bold = workbook.add_format(
#             {'font_size': 11, 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7', 'font': 'Calibri Light',
#              'text_wrap': True, 'border': 1})
#         bold_red = workbook.add_format(
#             {'font_size': 11, 'color': '#FF0000', 'align': 'vcenter', 'bold': True, 'bg_color': '#b7b7b7',
#              'font': 'Calibri Light',
#              'text_wrap': True, 'border': 1})
#         sheet = workbook.add_worksheet('Location Summary')
#         sheet.set_column(0, 0, 20)
#         sheet.set_column(0, 1, 25)
#         sheet.set_column(0, 2, 25)
#         sheet.set_column(0, 3, 25)
#         sheet.set_column(0, 4, 25)
#         sheet.set_column(0, 5, 25)
#         sheet.set_column(0, 6, 25)
#         sheet.set_column(0, 7, 25)
#         sheet.set_column(0, 8, 25)
#         sheet.set_column(0, 9, 25)
#         sheet.set_column(0, 10, 25)
#         sheet.set_column(0, 11, 25)
#         sheet.set_column(0, 12, 25)
#         sheet.set_column(0, 13, 25)
#         sheet.set_column(0, 14, 25)
#         sheet.set_column(0, 15, 25)
#         sheet.set_column(0, 16, 25)
#         sheet.set_column(0, 17, 25)
#         sheet.set_column(0, 18, 25)
#         sheet.set_column(0, 19, 25)
#         sheet.set_column(0, 20, 25)
#         sheet.set_column(0, 21, 17)
#         sheet.set_column(0, 22, 17)
#         sheet.set_column(0, 23, 17)
#         sheet.set_column(0, 24, 17)
#         sheet.set_column(0, 25, 25)
#         sheet.set_column(0, 26, 25)
#         sheet.set_column(0, 27, 25)
#         sheet.set_column(0, 28, 25)
#
#         # **************************************************
#         sheet.write(0, 0, 'Brand', bold)
#         sheet.write(0, 1, 'Category 1', bold)
#         sheet.write(0, 2, 'Category 2', bold)
#         sheet.write(0, 3, 'Category 3', bold)
#         sheet.write(0, 4, 'Function Sport', bold)
#         sheet.write(0, 5, 'Gender', bold)
#         sheet.write(0, 6, 'Title', bold)
#         sheet.write(0, 7, 'Composition / Material', bold)
#         sheet.write(0, 8, 'Technology / Features', bold)
#         sheet.write(0, 9, 'Event', bold)
#         sheet.write(0, 10, 'HSN Code', bold)
#         sheet.write(0, 11, 'Style Code', bold)
#         sheet.write(0, 12, 'Article Code', bold)
#         sheet.write(0, 13, 'SKU', bold)
#         sheet.write(0, 14, 'EAN Code', bold)
#         sheet.write(0, 15, 'ASIN', bold)
#         sheet.write(0, 16, 'FSIN', bold)
#         sheet.write(0, 17, 'Colour', bold)
#         sheet.write(0, 18, 'Size', bold)
#         sheet.write(0, 19, 'MRP', bold)
#         sheet.write(0, 20, 'GST', bold)
#         sheet.write(0, 21, 'IHO Stock', bold)
#         sheet.write(0, 22, 'Bhiwandi Stock', bold)
#         sheet.write(0, 23, 'Delhi Stock', bold)
#         sheet.write(0, 24, 'Total Qty', bold)
#         sheet.write(0, 25, 'Reserved Qty', bold)
#         sheet.write(0, 26, 'FREE TO USE', bold)
#         sheet.write(0, 27, 'PO Receipt Pending', bold)
#         sheet.write(0, 28, '(Onhand + incoming) - outgoing', bold)
#         sheet.freeze_panes(1, 0)
#
#         row = 1
#         col = 0
#         product_data = {}
#
#         products = self.env['product.product'].search([])
#
#         for product in products:
#             product_id = product.id
#
#             product_data[product_id] = {
#                 'Brand': product.brand_id_rel.name or '',
#                 'Category 1': product.categ_id.parent_id.parent_id.name or '',
#                 'Category 2': product.categ_id.parent_id.name or '',
#                 'Category 3': product.categ_id.name or '',
#                 'Function Sport': product.variants_func_spo or '',
#                 'Gender': product.gender or '',
#                 'Title': product.name or '',
#                 'SKU Code': product.default_code or '',
#                 'Composition / Material': product.material or '',
#                 'Technology / Features': product.variants_tech_feat or '',
#                 'Event': product.occasion or '',
#                 'HSN Code': product.l10n_in_hsn_code or product.sale_hsn.hsnsac_code or '',
#                 'Style Code': product.style_code or '',
#                 'Article Code': product.variant_article_code or '',
#                 'EAN Code': product.barcode or '',
#                 'ASIN': product.variants_asin or '',
#                 'FSIN': product.variants_fsn or '',
#                 'Colour': product.color or '',
#                 'Size': product.size or '',
#                 'MRP': product.lst_price or '',
#                 'GST': ''.join([str(x) for x in product.taxes_id.name]) if product.taxes_id else '',
#                 'IHO Stock': '',
#                 'Bhiwandi Stock': '',
#                 'Delhi Stock': '',
#                 'Total': product.qty_available or '',
#                 '(Onhand + incoming) - outgoing': 0,
#                 # '(Onhand + incoming) - outgoing': product.virtual_available or '',
#                 'Reserved Qty': 0, # Initialize reserved quantity to 0
#                 'FREE TO USE': 0,
#                 'PO Receipt Pending': 0
#             }
#
#             # Fill in stock quantities based on location
#             # stock_quants = self.env['stock.quant'].search([('product_id', '=', product_id), ('location_id.usage', '=', 'internal')])
#
#
#             stock_quants = product.stock_quant_ids.filtered(lambda q: q.location_id.usage == 'internal')
#
#             for quant in stock_quants:
#                 if quant.location_id.location_id.name == 'IHO':
#                     product_data[product_id]['IHO Stock'] = quant.quantity
#                 elif quant.location_id.location_id.name == 'BHW':
#                     product_data[product_id]['Bhiwandi Stock'] = quant.quantity
#                 elif quant.location_id.location_id.name == 'DEL':
#                     product_data[product_id]['Delhi Stock'] = quant.quantity
#
# # *********************************************
#
#             incoming_qty = product.incoming_qty
#             outgoing_qty = product.outgoing_qty
#
#             # Fetch sale orders related to the product
#             sale_orders = self.env['sale.order'].search(
#                 [('order_line.product_id', '=', product_id), ('state', '=', 'sale')])
#             # Fetch quotation orders related to the product
#             quotation_orders = self.env['sale.order'].search(
#                 [('order_line.product_id', '=', product_id), ('state', '=', 'draft'),('state', '!=', 'cancel')])
#
#             # Calculate outgoing quantity based on sale orders and quotation orders
#             quotation_outgoing_qty = sum(
#                 order_line.product_uom_qty for order in quotation_orders for order_line in order.order_line
#                 if order_line.product_id.id == product_id)
#
#             # Total outgoing quantity
#             outgoing_qty = product.outgoing_qty + quotation_outgoing_qty
#
#             onhand_incoming_minus_outgoing = product.qty_available + incoming_qty - outgoing_qty
#
#             # Update '(Onhand + incoming) - outgoing'
#             product_data[product_id]['(Onhand + incoming) - outgoing'] = onhand_incoming_minus_outgoing
#
#
#         # ***************************************
#             # Find sales orders related to the product
#             sale_orders = self.env['sale.order'].search([('order_line.product_id', '=', product_id), ])
#             # Calculate 'Qty to Deliver' based on unprocessed sales order quantities
#             qty_to_deliver = sum(
#                 order_line.product_uom_qty - order_line.qty_delivered for order in sale_orders for order_line in
#                 order.order_line
#                 if order_line.product_id.id == product_id)
#             # Update 'Reserved Qty'
#             product_data[product_id]['Reserved Qty'] = qty_to_deliver
#
#             # Update 'FREE TO USE'
#             product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver
# # ************************************************
#             # Fetch purchase orders related to the product
#             purchase_orders = self.env['purchase.order'].search([('order_line.product_id', '=', product_id)])
#
#             # Calculate 'Ordered - Received' based on unprocessed purchase order quantities
#             ordered_received_qty = sum(
#                 order_line.product_qty - order_line.qty_received for order in purchase_orders for order_line in
#                 order.order_line
#                 if order_line.product_id.id == product_id)
#
#             # Update 'Ordered - Received'
#             product_data[product_id]['PO Receipt Pending'] = ordered_received_qty
#
#
#         # Write data to the sheet
#         for product_id, data in sorted(product_data.items(), key=lambda x: (x[1]['Brand'].lower(), x[1]['Category 1'].lower(), x[1]['Category 2'].lower(), x[1]['Category 3'].lower())):
#             sheet.write(row, col, data['Brand'])
#             sheet.write(row, col + 1, data['Category 1'])
#             sheet.write(row, col + 2, data['Category 2'])
#             sheet.write(row, col + 3, data['Category 3'])
#             sheet.write(row, col + 4, data['Function Sport'])
#             sheet.write(row, col + 5, data['Gender'])
#             sheet.write(row, col + 6, data['Title'])
#             sheet.write(row, col + 7, data['Composition / Material'])
#             sheet.write(row, col + 8, data['Technology / Features'])
#             sheet.write(row, col + 9, data['Event'])
#             sheet.write(row, col + 10, data['HSN Code'])
#             sheet.write(row, col + 11, data['Style Code'])
#             sheet.write(row, col + 12, data['Article Code'])
#             sheet.write(row, col + 13, data['SKU Code'])
#             sheet.write(row, col + 14, data['EAN Code'])
#             sheet.write(row, col + 15, data['ASIN'])
#             sheet.write(row, col + 16, data['FSIN'])
#             sheet.write(row, col + 17, data['Colour'])
#             sheet.write(row, col + 18, data['Size'])
#             sheet.write(row, col + 19, data['MRP'])
#             sheet.write(row, col + 20, data['GST'])
#             sheet.write(row, col + 21, data['IHO Stock'])
#             sheet.write(row, col + 22, data['Bhiwandi Stock'])
#             sheet.write(row, col + 23, data['Delhi Stock'])
#             sheet.write(row, col + 24, data['Total'])
#             sheet.write(row, col + 25, data['Reserved Qty'])
#             sheet.write(row, col + 26, data['FREE TO USE'])
#             sheet.write(row, col + 27, data['PO Receipt Pending'])
#             sheet.write(row, col + 28, data['(Onhand + incoming) - outgoing'])
#
#             row += 1




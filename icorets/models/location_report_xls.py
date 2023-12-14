import datetime
from odoo import api, models, fields, _


class LocationReportWizard(models.TransientModel):
    _name = 'locations.report'

    def location_report_xlsx(self):
        return self.env.ref('icorets.location_report_action_xls').report_action(self)

    def location_report_xlsx_qtn(self):
        return self.env.ref('icorets.location_report_action_xls_qtn').report_action(self)

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

        # **************************************************
        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'Category 1', bold)
        sheet.write(0, 2, 'Category 2', bold)
        sheet.write(0, 3, 'Category 3', bold)
        sheet.write(0, 4, 'Function Sport', bold)
        sheet.write(0, 5, 'Gender', bold)
        sheet.write(0, 6, 'Title', bold)
        sheet.write(0, 7, 'Composition / Material', bold)
        sheet.write(0, 8, 'Technology / Features', bold)
        sheet.write(0, 9, 'Event', bold)
        sheet.write(0, 10, 'HSN Code', bold)
        sheet.write(0, 11, 'Style Code', bold)
        sheet.write(0, 12, 'Article Code', bold)
        sheet.write(0, 13, 'SKU', bold)
        sheet.write(0, 14, 'EAN Code', bold)
        sheet.write(0, 15, 'ASIN', bold)
        sheet.write(0, 16, 'FSIN', bold)
        sheet.write(0, 17, 'Colour', bold)
        sheet.write(0, 18, 'Size', bold)
        sheet.write(0, 19, 'MRP', bold)
        sheet.write(0, 20, 'GST', bold)
        sheet.write(0, 21, 'IHO Stock', bold)
        sheet.write(0, 22, 'Bhiwandi Stock', bold)
        sheet.write(0, 23, 'Delhi Stock', bold)
        sheet.write(0, 24, 'Total Qty', bold)
        sheet.write(0, 25, 'Reserved Qty', bold)
        sheet.write(0, 26, 'FREE TO USE', bold)
        sheet.write(0, 27, 'PO Receipt Pending', bold)
        sheet.write(0, 28, '(Onhand + incoming) - outgoing', bold)
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
                'Colour': product.color or '',
                'Size': product.size or '',
                'MRP': product.lst_price or '',
                'GST': ''.join([str(x) for x in product.taxes_id.name]) if product.taxes_id else '',
                'IHO Stock': '',
                'Bhiwandi Stock': '',
                'Delhi Stock': '',
                'Total': product.qty_available or '',
                '(Onhand + incoming) - outgoing': product.virtual_available or '',
                'Reserved Qty': 0, # Initialize reserved quantity to 0
                'FREE TO USE': 0,
                'PO Receipt Pending': 0
            }

            # Fill in stock quantities based on location
            # stock_quants = self.env['stock.quant'].search([('product_id', '=', product_id), ('location_id.usage', '=', 'internal')])


            stock_quants = product.stock_quant_ids.filtered(lambda q: q.location_id.usage == 'internal')

            for quant in stock_quants:
                if quant.location_id.location_id.name == 'IHO':
                    product_data[product_id]['IHO Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BHW':
                    product_data[product_id]['Bhiwandi Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DEL':
                    product_data[product_id]['Delhi Stock'] = quant.quantity

            # Find sales orders related to the product
            sale_orders = self.env['sale.order'].search([('order_line.product_id', '=', product_id), ('state', 'not in', ['draft', 'cancel', 'sent'])])
            # Calculate 'Qty to Deliver' based on unprocessed sales order quantities
            qty_to_deliver = sum(
                order_line.product_uom_qty - order_line.qty_delivered for order in sale_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)
            # Update 'Reserved Qty'
            product_data[product_id]['Reserved Qty'] = qty_to_deliver

            # Update 'FREE TO USE'
            product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver

            # Fetch purchase orders related to the product
            purchase_orders = self.env['purchase.order'].search([('order_line.product_id', '=', product_id), ('state', 'not in', ['draft','to approve', 'cancel', 'sent'])])

            # Calculate 'Ordered - Received' based on unprocessed purchase order quantities
            ordered_received_qty = sum(
                order_line.product_qty - order_line.qty_received for order in purchase_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)

            # Update 'Ordered - Received'
            product_data[product_id]['PO Receipt Pending'] = ordered_received_qty


        # Write data to the sheet
        for product_id, data in sorted(product_data.items(), key=lambda x: (x[1]['Brand'].lower(), x[1]['Category 1'].lower(), x[1]['Category 2'].lower(), x[1]['Category 3'].lower())):
            sheet.write(row, col, data['Brand'])
            sheet.write(row, col + 1, data['Category 1'])
            sheet.write(row, col + 2, data['Category 2'])
            sheet.write(row, col + 3, data['Category 3'])
            sheet.write(row, col + 4, data['Function Sport'])
            sheet.write(row, col + 5, data['Gender'])
            sheet.write(row, col + 6, data['Title'])
            sheet.write(row, col + 7, data['Composition / Material'])
            sheet.write(row, col + 8, data['Technology / Features'])
            sheet.write(row, col + 9, data['Event'])
            sheet.write(row, col + 10, data['HSN Code'])
            sheet.write(row, col + 11, data['Style Code'])
            sheet.write(row, col + 12, data['Article Code'])
            sheet.write(row, col + 13, data['SKU Code'])
            sheet.write(row, col + 14, data['EAN Code'])
            sheet.write(row, col + 15, data['ASIN'])
            sheet.write(row, col + 16, data['FSIN'])
            sheet.write(row, col + 17, data['Colour'])
            sheet.write(row, col + 18, data['Size'])
            sheet.write(row, col + 19, data['MRP'])
            sheet.write(row, col + 20, data['GST'])
            sheet.write(row, col + 21, data['IHO Stock'])
            sheet.write(row, col + 22, data['Bhiwandi Stock'])
            sheet.write(row, col + 23, data['Delhi Stock'])
            sheet.write(row, col + 24, data['Total'])
            sheet.write(row, col + 25, data['Reserved Qty'])
            sheet.write(row, col + 26, data['FREE TO USE'])
            sheet.write(row, col + 27, data['PO Receipt Pending'])
            sheet.write(row, col + 28, data['(Onhand + incoming) - outgoing'])

            row += 1



class LocationReportQtn(models.AbstractModel):
    _name = "report.icorets.location_report_xlsx_qtn"
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

        # **************************************************
        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'Category 1', bold)
        sheet.write(0, 2, 'Category 2', bold)
        sheet.write(0, 3, 'Category 3', bold)
        sheet.write(0, 4, 'Function Sport', bold)
        sheet.write(0, 5, 'Gender', bold)
        sheet.write(0, 6, 'Title', bold)
        sheet.write(0, 7, 'Composition / Material', bold)
        sheet.write(0, 8, 'Technology / Features', bold)
        sheet.write(0, 9, 'Event', bold)
        sheet.write(0, 10, 'HSN Code', bold)
        sheet.write(0, 11, 'Style Code', bold)
        sheet.write(0, 12, 'Article Code', bold)
        sheet.write(0, 13, 'SKU', bold)
        sheet.write(0, 14, 'EAN Code', bold)
        sheet.write(0, 15, 'ASIN', bold)
        sheet.write(0, 16, 'FSIN', bold)
        sheet.write(0, 17, 'Colour', bold)
        sheet.write(0, 18, 'Size', bold)
        sheet.write(0, 19, 'MRP', bold)
        sheet.write(0, 20, 'GST', bold)
        sheet.write(0, 21, 'IHO Stock', bold)
        sheet.write(0, 22, 'Bhiwandi Stock', bold)
        sheet.write(0, 23, 'Delhi Stock', bold)
        sheet.write(0, 24, 'Total Qty', bold)
        sheet.write(0, 25, 'Reserved Qty', bold)
        sheet.write(0, 26, 'FREE TO USE', bold)
        sheet.write(0, 27, 'PO Receipt Pending', bold)
        sheet.write(0, 28, '(Onhand + incoming) - outgoing', bold)
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
                'Colour': product.color or '',
                'Size': product.size or '',
                'MRP': product.lst_price or '',
                'GST': ''.join([str(x) for x in product.taxes_id.name]) if product.taxes_id else '',
                'IHO Stock': '',
                'Bhiwandi Stock': '',
                'Delhi Stock': '',
                'Total': product.qty_available or '',
                '(Onhand + incoming) - outgoing': 0,
                # '(Onhand + incoming) - outgoing': product.virtual_available or '',
                'Reserved Qty': 0, # Initialize reserved quantity to 0
                'FREE TO USE': 0,
                'PO Receipt Pending': 0
            }

            # Fill in stock quantities based on location
            # stock_quants = self.env['stock.quant'].search([('product_id', '=', product_id), ('location_id.usage', '=', 'internal')])


            stock_quants = product.stock_quant_ids.filtered(lambda q: q.location_id.usage == 'internal')

            for quant in stock_quants:
                if quant.location_id.location_id.name == 'IHO':
                    product_data[product_id]['IHO Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BHW':
                    product_data[product_id]['Bhiwandi Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DEL':
                    product_data[product_id]['Delhi Stock'] = quant.quantity

# *********************************************

            incoming_qty = product.incoming_qty
            outgoing_qty = product.outgoing_qty

            # Fetch sale orders related to the product
            sale_orders = self.env['sale.order'].search(
                [('order_line.product_id', '=', product_id), ('state', '=', 'sale')])
            # Fetch quotation orders related to the product
            quotation_orders = self.env['sale.order'].search(
                [('order_line.product_id', '=', product_id), ('state', '=', 'draft'),('state', '!=', 'cancel')])

            # Calculate outgoing quantity based on sale orders and quotation orders
            qty_sum = sum(order_line.product_uom_qty for order in quotation_orders for order_line in order.order_line
                            if order_line.product_id.id == product_id)
            outgoing_qty = (qty_sum + (product.virtual_available))

            onhand_incoming_minus_outgoing = product.qty_available + incoming_qty - outgoing_qty

            # Update '(Onhand + incoming) - outgoing'
            product_data[product_id]['(Onhand + incoming) - outgoing'] = onhand_incoming_minus_outgoing


        # ***************************************
            # Find sales orders related to the product
            sale_orders = self.env['sale.order'].search([('order_line.product_id', '=', product_id), ])
            # Calculate 'Qty to Deliver' based on unprocessed sales order quantities
            qty_to_deliver = sum(
                order_line.product_uom_qty - order_line.qty_delivered for order in sale_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)
            # Update 'Reserved Qty'
            product_data[product_id]['Reserved Qty'] = qty_to_deliver

            # Update 'FREE TO USE'
            product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver
# ************************************************
            # Fetch purchase orders related to the product
            purchase_orders = self.env['purchase.order'].search([('order_line.product_id', '=', product_id)])

            # Calculate 'Ordered - Received' based on unprocessed purchase order quantities
            ordered_received_qty = sum(
                order_line.product_qty - order_line.qty_received for order in purchase_orders for order_line in
                order.order_line
                if order_line.product_id.id == product_id)

            # Update 'Ordered - Received'
            product_data[product_id]['PO Receipt Pending'] = ordered_received_qty


        # Write data to the sheet
        for product_id, data in sorted(product_data.items(), key=lambda x: (x[1]['Brand'].lower(), x[1]['Category 1'].lower(), x[1]['Category 2'].lower(), x[1]['Category 3'].lower())):
            sheet.write(row, col, data['Brand'])
            sheet.write(row, col + 1, data['Category 1'])
            sheet.write(row, col + 2, data['Category 2'])
            sheet.write(row, col + 3, data['Category 3'])
            sheet.write(row, col + 4, data['Function Sport'])
            sheet.write(row, col + 5, data['Gender'])
            sheet.write(row, col + 6, data['Title'])
            sheet.write(row, col + 7, data['Composition / Material'])
            sheet.write(row, col + 8, data['Technology / Features'])
            sheet.write(row, col + 9, data['Event'])
            sheet.write(row, col + 10, data['HSN Code'])
            sheet.write(row, col + 11, data['Style Code'])
            sheet.write(row, col + 12, data['Article Code'])
            sheet.write(row, col + 13, data['SKU Code'])
            sheet.write(row, col + 14, data['EAN Code'])
            sheet.write(row, col + 15, data['ASIN'])
            sheet.write(row, col + 16, data['FSIN'])
            sheet.write(row, col + 17, data['Colour'])
            sheet.write(row, col + 18, data['Size'])
            sheet.write(row, col + 19, data['MRP'])
            sheet.write(row, col + 20, data['GST'])
            sheet.write(row, col + 21, data['IHO Stock'])
            sheet.write(row, col + 22, data['Bhiwandi Stock'])
            sheet.write(row, col + 23, data['Delhi Stock'])
            sheet.write(row, col + 24, data['Total'])
            sheet.write(row, col + 25, data['Reserved Qty'])
            sheet.write(row, col + 26, data['FREE TO USE'])
            sheet.write(row, col + 27, data['PO Receipt Pending'])
            sheet.write(row, col + 28, data['(Onhand + incoming) - outgoing'])

            row += 1




import base64
from datetime import datetime
from io import BytesIO
import xlsxwriter
from odoo import api, fields, models, _


class LocationReportWizard(models.TransientModel):
    _name = 'locations.report'
    _description = 'Location Report'

    excel_file = fields.Binary('Download report Excel', attachment=True, readonly=True)
    file_name = fields.Char('Excel File', size=64)

    from_date = fields.Date(string='From Date', default=fields.Date.today)
    to_date = fields.Date(string='To Date', default=fields.Date.today)

    def location_report_xlsx(self):
        filename = "Location Summary"
        file_pointer = BytesIO()
        workbook = xlsxwriter.Workbook(file_pointer)
        bold = workbook.add_format({
            'font_size': 11,
            'align': 'vcenter',
            'bold': True,
            'bg_color': '#b7b7b7',
            'font': 'Calibri Light',
            'text_wrap': True,
            'border': 1
        })
        bold_red = workbook.add_format({
            'font_size': 11,
            'color': '#FF0000',
            'align': 'vcenter',
            'bold': True,
            'bg_color': '#b7b7b7',
            'font': 'Calibri Light',
            'text_wrap': True,
            'border': 1
        })
        sheet = workbook.add_worksheet('Location Summary')
        sheet.set_column(0, 0, 20)
        for i in range(1, 21):
            sheet.set_column(0, i, 25)
        for i in range(21, 25):
            sheet.set_column(0, i, 17)
        for i in range(25, 62):
            sheet.set_column(0, i, 25)

        # Header Columns
        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'Creation Date', bold)
        sheet.write(0, 2, 'Category 1', bold)
        sheet.write(0, 3, 'Category 2', bold)
        sheet.write(0, 4, 'Category 3', bold)
        sheet.write(0, 5, 'Function Sport', bold)
        sheet.write(0, 6, 'Gender', bold)
        sheet.write(0, 7, 'Age group', bold)
        sheet.write(0, 8, 'Title', bold)
        sheet.write(0, 9, 'Marketplace Tittle', bold)
        sheet.write(0, 10, 'Composition / Material', bold)
        sheet.write(0, 11, 'Technology / Features', bold)
        sheet.write(0, 12, 'Event', bold)
        sheet.write(0, 13, 'HSN Code', bold)
        sheet.write(0, 14, 'Style Code', bold)
        sheet.write(0, 15, 'Article Code', bold)
        sheet.write(0, 16, 'SKU', bold)
        sheet.write(0, 17, 'EAN Code', bold)
        sheet.write(0, 18, 'ASIN', bold)
        sheet.write(0, 19, 'FSIN', bold)
        sheet.write(0, 20, 'Myntra', bold)
        sheet.write(0, 21, 'AJIO', bold)
        sheet.write(0, 22, 'Fancode', bold)
        sheet.write(0, 23, 'Swiggy', bold)
        sheet.write(0, 24, 'Bigbasket', bold)
        sheet.write(0, 25, 'Blinkit', bold)
        sheet.write(0, 26, 'Zepto', bold)
        sheet.write(0, 27, 'Colour', bold)
        sheet.write(0, 28, 'Size', bold)
        sheet.write(0, 29, 'MRP', bold)
        sheet.write(0, 30, 'COST Price', bold)
        sheet.write(0, 31, 'GST', bold)
        sheet.write(0, 32, 'IHO Stock', bold)
        sheet.write(0, 33, 'Bhiwandi Stock', bold)
        sheet.write(0, 34, 'Delhi Stock', bold)
        sheet.write(0, 35, 'Available Qty', bold)
        sheet.write(0, 36, 'BHU Stock', bold)
        sheet.write(0, 37, 'DHASA Stock', bold)
        sheet.write(0, 38, 'ELM Stock', bold)
        sheet.write(0, 39, 'JSP Stock', bold)
        sheet.write(0, 40, 'JWD Stock', bold)
        sheet.write(0, 41, 'RCP Stock', bold)
        sheet.write(0, 42, 'UPW Stock', bold)
        sheet.write(0, 43, 'BWMIS Stock', bold)
        sheet.write(0, 44, 'Customer Location', bold)
        sheet.write(0, 45, 'Vendor Location', bold)
        sheet.write(0, 46, 'Virtual Locations/Inventory adjustment', bold)
        sheet.write(0, 47, 'Damage/Stock', bold)
        sheet.write(0, 48, 'Virtual Locations/Production', bold)
        sheet.write(0, 49, 'Total Qty', bold)
        sheet.write(0, 50, 'Quotation Qty', bold)
        sheet.write(0, 51, 'Confirmed SO qty', bold)
        sheet.write(0, 52, 'FREE TO USE', bold)
        sheet.write(0, 53, 'PO Receipt Pending', bold)
        sheet.write(0, 54, 'To Replenish', bold)
        sheet.write(0, 55, 'Bullet Point 1', bold)
        sheet.write(0, 56, 'Bullet Point 2', bold)
        sheet.write(0, 57, 'Bullet Point 3', bold)
        sheet.write(0, 58, 'Bullet Point 4', bold)
        sheet.write(0, 59, 'Bullet Point 5', bold)
        sheet.write(0, 60, 'Keyword', bold)
        sheet.write(0, 61, 'Description', bold)
        sheet.write(0, 62, 'Google Drive Link', bold)
        sheet.write(0, 63, 'Drop Box Link', bold)
        sheet.write(0, 64, 'Country of Origin', bold)
        sheet.write(0, 65, 'Product Net Weight (gms)', bold)
        sheet.write(0, 66, 'Product Length (cm)', bold)
        sheet.write(0, 67, 'Product Breadth (cm)', bold)
        sheet.write(0, 68, 'Product Height (cm)', bold)
        sheet.write(0, 69, 'Package Gross Weight (gms)', bold)
        sheet.write(0, 70, 'Package Length (cm)', bold)
        sheet.write(0, 71, 'Package Breadth (cm)', bold)
        sheet.write(0, 72, 'Package Height (cm)', bold)
        sheet.write(0, 73, 'Opening Stock', bold)
        sheet.write(0, 74, 'Purchase', bold)
        sheet.write(0, 75, 'Purchase Return', bold)
        sheet.write(0, 76, 'Net Purchase', bold)
        sheet.write(0, 77, 'Sales', bold)
        sheet.write(0, 78, 'Sales Return', bold)
        sheet.write(0, 79, 'Net Sales', bold)
        sheet.write(0, 80, 'Closing Stock', bold)
        sheet.write(0, 81, 'Pending SOs customers', bold)
        sheet.write(0, 82, 'Pending POs vendors', bold)
        sheet.freeze_panes(1, 0)

        row = 1
        col = 0
        product_data = {}

        products = self.env['product.product'].search([])

        for product in products:
            product_id = product.id

            product_data[product_id] = {
                'Brand': product.brand_id_rel.name or '',
                'Creation Date': product.product_tmpl_id.create_date.strftime('%d/%m/%Y') if product.product_tmpl_id.create_date else '',
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
                'COST Price': product.standard_price or '',
                'GST': ''.join([str(x) for x in product.taxes_id.name]) if product.taxes_id else '',
                'IHO Stock': '',
                'Bhiwandi Stock': '',
                'Delhi Stock': '',
                'Available Qty': 0,
                'BHU Stock': '',
                'DHASA Stock': '',
                'ELM Stock': '',
                'JSP Stock': '',
                'JWD Stock': '',
                'RCP Stock': '',
                'UPW Stock': '',
                'BWMIS Stock': '',
                'CH Stock': '',
                'Customer Location': '',
                'Vendor Location': '',
                'Virtual Locations/Inventory adjustment': '',
                'Damage/Stock': '',
                'Virtual Locations/Production': '',
                'Total': product.qty_available or '',
                'To Replenish': 0,
                '(Onhand + incoming) - outgoing': product.virtual_available or '',
                '(Onhand + incoming) - outgoing(With_Qtn)': 0,
                'Quotation Qty': 0,
                'Confirmed SO qty': 0,
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
                'Marketplace Tittle': product.market_place_tittle or '',
                'Bullet Point 1': product.bullet_point_1 or '',
                'Bullet Point 2': product.bullet_point_2 or '',
                'Bullet Point 3': product.bullet_point_3 or '',
                'Bullet Point 4': product.bullet_point_4 or '',
                'Bullet Point 5': product.bullet_point_5 or '',
                'Keyword': '',
                'Description': product.description or '',
                'Google Drive Link': product.google_drive_link or '',
                'Drop Box Link': product.drop_box_link or '',
                'Country of Origin': product.country_origin or '',
            }

            stock_quants = product.stock_quant_ids.filtered(lambda q: q.location_id.usage != 'view')

            for quant in stock_quants:
                if quant.location_id.location_id.name == 'IHO':
                    product_data[product_id]['IHO Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BHW':
                    product_data[product_id]['Bhiwandi Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DEL':
                    product_data[product_id]['Delhi Stock'] = quant.quantity
                    product_data[product_id]['Available Qty'] = quant.quantity - quant.reserved_quantity
                elif quant.location_id.location_id.name == 'BHU':
                    product_data[product_id]['BHU Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DHASA':
                    product_data[product_id]['DHASA Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'ELM':
                    product_data[product_id]['ELM Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'JSP':
                    product_data[product_id]['JSP Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'JWD':
                    product_data[product_id]['JWD Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'RCP':
                    product_data[product_id]['RCP Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'UPW':
                    product_data[product_id]['UPW Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BWMIS':
                    product_data[product_id]['BWMIS Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'CH':
                    product_data[product_id]['CH Stock'] = quant.quantity
                elif quant.location_id.name == 'Customers':
                    product_data[product_id]['Customer Location'] = quant.quantity
                elif quant.location_id.name == 'Vendors':
                    product_data[product_id]['Vendor Location'] = quant.quantity
                elif quant.location_id.name == 'Inventory adjustment':
                    product_data[product_id]['Virtual Locations/Inventory adjustment'] = quant.quantity
                elif quant.location_id.name == 'Scrap':
                    product_data[product_id]['Damage/Stock'] = quant.quantity
                elif quant.location_id.name == 'Production':
                    product_data[product_id]['Virtual Locations/Production'] = quant.quantity

            # Quotations related to the product
            self.env.cr.execute("""
                select sum(line.product_uom_qty - line.qty_delivered) 
                from sale_order_line as line
                join sale_order so on line.order_id = so.id
                where so.state = 'draft' and line.product_id = %s
                and so.is_short_close is not true
            """, (product_id,))
            qty_to_deliver_qtn_data = self.env.cr.dictfetchall()
            qty_to_deliver_qtn = qty_to_deliver_qtn_data[0].get('sum') if qty_to_deliver_qtn_data[0].get('sum') is not None else 0
            product_data[product_id]['Quotation Qty'] = qty_to_deliver_qtn

            # Sales orders related to the product
            self.env.cr.execute("""
                select sum(line.product_uom_qty - line.qty_delivered) 
                from sale_order_line as line
                join sale_order so on line.order_id = so.id
                where so.state not in ('draft', 'cancel', 'sent') and line.product_id = %s 
                and so.is_short_close is not true
            """, (product_id,))
            qty_to_deliver_data = self.env.cr.dictfetchall()
            qty_to_deliver = qty_to_deliver_data[0].get('sum') if qty_to_deliver_data[0].get('sum') is not None else 0
            product_data[product_id]['Confirmed SO qty'] = qty_to_deliver

            # Free to use
            free_to_use = 0
            if product.qty_available < qty_to_deliver:
                product_data[product_id]['FREE TO USE'] = 0
            else:
                product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver
                free_to_use = product.qty_available - qty_to_deliver

            # Purchase orders related to the product
            self.env.cr.execute("""
                select sum(line.product_qty - line.qty_received) 
                from purchase_order_line as line
                join purchase_order as po on line.order_id = po.id
                where po.state not in ('draft', 'to approve', 'cancel', 'sent') and line.product_id = %s
                and po.is_short_close is not true
            """, (product_id,))
            order_pending_qty_data = self.env.cr.dictfetchall()
            order_pending_qty = order_pending_qty_data[0].get('sum') if order_pending_qty_data[0].get('sum') is not None else 0
            product_data[product_id]['PO Receipt Pending'] = order_pending_qty

            if free_to_use > 0:
                product_data[product_id]['To Replenish'] = 0
            else:
                replenish_qty = qty_to_deliver - product.qty_available
                product_data[product_id]['To Replenish'] = replenish_qty - order_pending_qty
                if product_data[product_id]['To Replenish'] < 0:
                    product_data[product_id]['To Replenish'] = 0

            # Quotation outgoing quantity
            self.env.cr.execute("""
                select sum(line.product_uom_qty) 
                from sale_order_line as line
                join sale_order so on line.order_id = so.id
                where so.state in ('draft') and line.product_id = %s
                and so.is_short_close is not true
            """, (product_id,))
            quotation_outgoing_qty_data = self.env.cr.dictfetchall()
            quotation_outgoing_qty = quotation_outgoing_qty_data[0].get('sum') if quotation_outgoing_qty_data[0].get('sum') is not None else 0

            outgoing_qty = product.outgoing_qty + quotation_outgoing_qty
            incoming_qty = product.incoming_qty
            onhand_incoming_minus_outgoing = product.qty_available + incoming_qty - outgoing_qty
            product_data[product_id]['(Onhand + incoming) - outgoing(With_Qtn)'] = onhand_incoming_minus_outgoing

            # Opening stock
            opening_stock = product.with_context({'to_date': self.from_date}).qty_available
            product_data[product_id]['Opening Stock'] = opening_stock

            # Stock moves
            domain = [
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'supplier'),
                ('location_dest_id.usage', '=', 'internal'),
                ('picking_id.date_done', '>=', self.from_date),
                ('picking_id.date_done', '<=', self.to_date),
                ('picking_id.state', '=', 'done'),
            ]
            purchase_qty = sum(self.env['stock.move'].search(domain).mapped('quantity'))
            product_data[product_id]['Purchase'] = purchase_qty

            domain = [
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'supplier'),
                ('picking_id.date_done', '>=', self.from_date),
                ('picking_id.date_done', '<=', self.to_date),
                ('picking_id.state', '=', 'done'),
            ]
            purchase_return_qty = sum(self.env['stock.move'].search(domain).mapped('quantity'))
            product_data[product_id]['Purchase Return'] = purchase_return_qty
            product_data[product_id]['Net Purchase'] = purchase_qty - purchase_return_qty

            domain = [
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'customer'),
                ('picking_id.date_done', '>=', self.from_date),
                ('picking_id.date_done', '<=', self.to_date),
                ('picking_id.state', '=', 'done'),
            ]
            sales_qty = sum(self.env['stock.move'].search(domain).mapped('quantity'))
            product_data[product_id]['Sales'] = sales_qty

            domain = [
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'customer'),
                ('location_dest_id.usage', '=', 'internal'),
                ('picking_id.date_done', '>=', self.from_date),
                ('picking_id.date_done', '<=', self.to_date),
                ('picking_id.state', '=', 'done'),
            ]
            sales_return_qty = sum(self.env['stock.move'].search(domain).mapped('quantity'))
            product_data[product_id]['Sales Return'] = sales_return_qty
            product_data[product_id]['Net Sales'] = sales_qty - sales_return_qty

            closing_stock = product.with_context({'to_date': self.to_date}).qty_available
            product_data[product_id]['Closing Stock'] = closing_stock

            # Pending SOs / POs
            self.env.cr.execute("""
                select sum(line.product_uom_qty - line.qty_delivered) 
                from sale_order_line as line
                join sale_order as so on line.order_id = so.id
                where so.state not in ('draft', 'cancel', 'sent') and line.product_id = %s
                and so.is_short_close is not true
            """, (product_id,))
            pending_so_data = self.env.cr.dictfetchall()
            pending_so = pending_so_data[0].get('sum') if pending_so_data[0].get('sum') is not None else 0
            product_data[product_id]['Pending SOs customers'] = pending_so

            self.env.cr.execute("""
                select sum(line.product_qty - line.qty_received) 
                from purchase_order_line as line
                join purchase_order as po on line.order_id = po.id
                where po.state in ('purchase', 'done') and line.product_id = %s
                and po.is_short_close is not true
            """, (product_id,))
            pending_po_data = self.env.cr.dictfetchall()
            pending_po = pending_po_data[0].get('sum') if pending_po_data[0].get('sum') is not None else 0
            product_data[product_id]['Pending POs vendors'] = pending_po

        # Write data to the sheet
        for product_id, data in sorted(product_data.items(), key=lambda x: (
                x[1]['Brand'].lower(), x[1]['Category 1'].lower(), x[1]['Category 2'].lower(),
                x[1]['Category 3'].lower())):
            sheet.write(row, col, data['Brand'])
            sheet.write(row, col + 1, data['Creation Date'])
            sheet.write(row, col + 2, data['Category 1'])
            sheet.write(row, col + 3, data['Category 2'])
            sheet.write(row, col + 4, data['Category 3'])
            sheet.write(row, col + 5, data['Function Sport'])
            sheet.write(row, col + 6, data['Gender'])
            sheet.write(row, col + 7, data['Age group'])
            sheet.write(row, col + 8, data['Title'])
            sheet.write(row, col + 9, data['Marketplace Tittle'])
            sheet.write(row, col + 10, data['Composition / Material'])
            sheet.write(row, col + 11, data['Technology / Features'])
            sheet.write(row, col + 12, data['Event'])
            sheet.write(row, col + 13, data['HSN Code'])
            sheet.write(row, col + 14, data['Style Code'])
            sheet.write(row, col + 15, data['Article Code'])
            sheet.write(row, col + 16, data['SKU Code'])
            sheet.write(row, col + 17, data['EAN Code'])
            sheet.write(row, col + 18, data['ASIN'])
            sheet.write(row, col + 19, data['FSIN'])
            sheet.write(row, col + 20, data['Myntra'])
            sheet.write(row, col + 21, data['AJIO'])
            sheet.write(row, col + 22, data['Fancode'])
            sheet.write(row, col + 23, data['Swiggy'])
            sheet.write(row, col + 24, data['Bigbasket'])
            sheet.write(row, col + 25, data['Blinkit'])
            sheet.write(row, col + 26, data['Zepto'])
            sheet.write(row, col + 27, data['Colour'])
            sheet.write(row, col + 28, data['Size'])
            sheet.write(row, col + 29, data['MRP'])
            sheet.write(row, col + 30, data['COST Price'])
            sheet.write(row, col + 31, data['GST'])
            sheet.write(row, col + 32, data['IHO Stock'])
            sheet.write(row, col + 33, data['Bhiwandi Stock'])
            sheet.write(row, col + 34, data['Delhi Stock'])
            sheet.write(row, col + 35, data['Available Qty'])
            sheet.write(row, col + 36, data['BHU Stock'])
            sheet.write(row, col + 37, data['DHASA Stock'])
            sheet.write(row, col + 38, data['ELM Stock'])
            sheet.write(row, col + 39, data['JSP Stock'])
            sheet.write(row, col + 40, data['JWD Stock'])
            sheet.write(row, col + 41, data['RCP Stock'])
            sheet.write(row, col + 42, data['UPW Stock'])
            sheet.write(row, col + 43, data['BWMIS Stock'])
            sheet.write(row, col + 44, data['Customer Location'])
            sheet.write(row, col + 45, data['Vendor Location'])
            sheet.write(row, col + 46, data['Virtual Locations/Inventory adjustment'])
            sheet.write(row, col + 47, data['Damage/Stock'])
            sheet.write(row, col + 48, data['Virtual Locations/Production'])
            sheet.write(row, col + 49, data['Total'])
            sheet.write(row, col + 50, data['Quotation Qty'])
            sheet.write(row, col + 51, data['Confirmed SO qty'])
            sheet.write(row, col + 52, data['FREE TO USE'])
            sheet.write(row, col + 53, data['PO Receipt Pending'])
            sheet.write(row, col + 54, data['To Replenish'])
            sheet.write(row, col + 55, data['Bullet Point 1'])
            sheet.write(row, col + 56, data['Bullet Point 2'])
            sheet.write(row, col + 57, data['Bullet Point 3'])
            sheet.write(row, col + 58, data['Bullet Point 4'])
            sheet.write(row, col + 59, data['Bullet Point 5'])
            sheet.write(row, col + 60, data['Keyword'])
            sheet.write(row, col + 61, data['Description'])
            sheet.write(row, col + 62, data['Google Drive Link'])
            sheet.write(row, col + 63, data['Drop Box Link'])
            sheet.write(row, col + 64, data['Country of Origin'])
            sheet.write(row, col + 65, data['Product Net Weight (gms)'])
            sheet.write(row, col + 66, data['Product Length (cm)'])
            sheet.write(row, col + 67, data['Product Breadth (cm)'])
            sheet.write(row, col + 68, data['Product Height (cm)'])
            sheet.write(row, col + 69, data['Package Gross Weight (gms)'])
            sheet.write(row, col + 70, data['Package Length (cm)'])
            sheet.write(row, col + 71, data['Package Breadth (cm)'])
            sheet.write(row, col + 72, data['Package Height (cm)'])
            sheet.write(row, col + 73, data['Opening Stock'])
            sheet.write(row, col + 74, data['Purchase'])
            sheet.write(row, col + 75, data['Purchase Return'])
            sheet.write(row, col + 76, data['Net Purchase'])
            sheet.write(row, col + 77, data['Sales'])
            sheet.write(row, col + 78, data['Sales Return'])
            sheet.write(row, col + 79, data['Net Sales'])
            sheet.write(row, col + 80, data['Closing Stock'])
            sheet.write(row, col + 81, data['Pending SOs customers'])
            sheet.write(row, col + 82, data['Pending POs vendors'])

            row += 1

        workbook.close()
        file_pointer.seek(0)

        self.write({'file_name': filename + str(datetime.today().strftime('%Y-%m-%d')) + '.xlsx'})
        self.excel_file = base64.encodebytes(file_pointer.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'name': filename,
            'url': '/web/content/locations.report/%s/excel_file?download=true&filename_field=file_name' % self[0].id,
            'target': 'new'
        }


class LocationReport(models.AbstractModel):
    _name = "report.icorets.location_report_xls"
    _inherit = "report.report_xlsx.abstract"
    _description = "Location Report XLSX Abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        bold = workbook.add_format({
            'font_size': 11,
            'align': 'vcenter',
            'bold': True,
            'bg_color': '#b7b7b7',
            'font': 'Calibri Light',
            'text_wrap': True,
            'border': 1
        })
        sheet = workbook.add_worksheet('Location Summary')
        sheet.set_column(0, 0, 20)
        for i in range(1, 21):
            sheet.set_column(0, i, 25)
        for i in range(21, 25):
            sheet.set_column(0, i, 17)
        for i in range(25, 62):
            sheet.set_column(0, i, 25)

        sheet.write(0, 0, 'Brand', bold)
        sheet.write(0, 1, 'Creation Date', bold)
        sheet.write(0, 2, 'Category 1', bold)
        sheet.write(0, 3, 'Category 2', bold)
        sheet.write(0, 4, 'Category 3', bold)
        sheet.write(0, 5, 'Function Sport', bold)
        sheet.write(0, 6, 'Gender', bold)
        sheet.write(0, 7, 'Age group', bold)
        sheet.write(0, 8, 'Title', bold)
        sheet.write(0, 9, 'Marketplace Tittle', bold)
        sheet.write(0, 10, 'Composition / Material', bold)
        sheet.write(0, 11, 'Technology / Features', bold)
        sheet.write(0, 12, 'Event', bold)
        sheet.write(0, 13, 'HSN Code', bold)
        sheet.write(0, 14, 'Style Code', bold)
        sheet.write(0, 15, 'Article Code', bold)
        sheet.write(0, 16, 'SKU', bold)
        sheet.write(0, 17, 'EAN Code', bold)
        sheet.write(0, 18, 'ASIN', bold)
        sheet.write(0, 19, 'FSIN', bold)
        sheet.write(0, 20, 'Myntra', bold)
        sheet.write(0, 21, 'AJIO', bold)
        sheet.write(0, 22, 'Fancode', bold)
        sheet.write(0, 23, 'Swiggy', bold)
        sheet.write(0, 24, 'Bigbasket', bold)
        sheet.write(0, 25, 'Blinkit', bold)
        sheet.write(0, 26, 'Zepto', bold)
        sheet.write(0, 27, 'Colour', bold)
        sheet.write(0, 28, 'Size', bold)
        sheet.write(0, 29, 'MRP', bold)
        sheet.write(0, 30, 'COST Price', bold)
        sheet.write(0, 31, 'GST', bold)
        sheet.write(0, 32, 'IHO Stock', bold)
        sheet.write(0, 33, 'Bhiwandi Stock', bold)
        sheet.write(0, 34, 'Delhi Stock', bold)
        sheet.write(0, 35, 'Available Qty', bold)
        sheet.write(0, 36, 'BHU Stock', bold)
        sheet.write(0, 37, 'DHASA Stock', bold)
        sheet.write(0, 38, 'ELM Stock', bold)
        sheet.write(0, 39, 'JSP Stock', bold)
        sheet.write(0, 40, 'JWD Stock', bold)
        sheet.write(0, 41, 'RCP Stock', bold)
        sheet.write(0, 42, 'UPW Stock', bold)
        sheet.write(0, 43, 'BWMIS Stock', bold)
        sheet.write(0, 44, 'CH Stock', bold)
        sheet.write(0, 45, 'Customer Location', bold)
        sheet.write(0, 46, 'Vendor Location', bold)
        sheet.write(0, 47, 'Virtual Locations/Inventory adjustment', bold)
        sheet.write(0, 48, 'Virtual Locations/Scrap', bold)
        sheet.write(0, 49, 'Virtual Locations/Production', bold)
        sheet.write(0, 50, 'Total Qty', bold)
        sheet.write(0, 51, 'Quotation Qty', bold)
        sheet.write(0, 52, 'Confirmed SO qty', bold)
        sheet.write(0, 53, 'FREE TO USE', bold)
        sheet.write(0, 54, 'PO Receipt Pending', bold)
        sheet.write(0, 55, 'To Replenish', bold)
        sheet.write(0, 56, 'Bullet Point 1', bold)
        sheet.write(0, 57, 'Bullet Point 2', bold)
        sheet.write(0, 58, 'Bullet Point 3', bold)
        sheet.write(0, 59, 'Bullet Point 4', bold)
        sheet.write(0, 60, 'Bullet Point 5', bold)
        sheet.write(0, 61, 'Keyword', bold)
        sheet.write(0, 62, 'Description', bold)
        sheet.write(0, 63, 'Google Drive Link', bold)
        sheet.write(0, 64, 'Drop Box Link', bold)
        sheet.write(0, 65, 'Country of Origin', bold)
        sheet.write(0, 66, 'Product Net Weight (gms)', bold)
        sheet.write(0, 67, 'Product Length (cm)', bold)
        sheet.write(0, 68, 'Product Breadth (cm)', bold)
        sheet.write(0, 69, 'Product Height (cm)', bold)
        sheet.write(0, 70, 'Package Gross Weight (gms)', bold)
        sheet.write(0, 71, 'Package Length (cm)', bold)
        sheet.write(0, 72, 'Package Breadth (cm)', bold)
        sheet.write(0, 73, 'Package Height (cm)', bold)
        sheet.freeze_panes(1, 0)

        row = 1
        col = 0
        product_data = {}

        products = self.env['product.product'].search([])

        for product in products:
            product_id = product.id

            product_data[product_id] = {
                'Brand': product.brand_id_rel.name or '',
                'Creation Date': product.product_tmpl_id.create_date.strftime('%d/%m/%Y') if product.product_tmpl_id.create_date else '',
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
                'COST Price': product.standard_price or '',
                'GST': ''.join([str(x) for x in product.taxes_id.name]) if product.taxes_id else '',
                'IHO Stock': '',
                'Bhiwandi Stock': '',
                'Delhi Stock': '',
                'Available Qty': 0,
                'BHU Stock': '',
                'DHASA Stock': '',
                'ELM Stock': '',
                'JSP Stock': '',
                'JWD Stock': '',
                'RCP Stock': '',
                'UPW Stock': '',
                'BWMIS Stock': '',
                'CH Stock': '',
                'Customer Location': '',
                'Vendor Location': '',
                'Virtual Locations/Inventory adjustment': '',
                'Virtual Locations/Scrap': '',
                'Virtual Locations/Production': '',
                'Total': product.qty_available or '',
                'To Replenish': 0,
                '(Onhand + incoming) - outgoing': product.virtual_available or '',
                '(Onhand + incoming) - outgoing(With_Qtn)': 0,
                'Quotation Qty': 0,
                'Confirmed SO qty': 0,
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
                'Marketplace Tittle': product.market_place_tittle or '',
                'Bullet Point 1': product.bullet_point_1 or '',
                'Bullet Point 2': product.bullet_point_2 or '',
                'Bullet Point 3': product.bullet_point_3 or '',
                'Bullet Point 4': product.bullet_point_4 or '',
                'Bullet Point 5': product.bullet_point_5 or '',
                'Keyword': '',
                'Description': product.description or '',
                'Google Drive Link': product.google_drive_link or '',
                'Drop Box Link': product.drop_box_link or '',
                'Country of Origin': product.country_origin or '',
            }

            stock_quants = product.stock_quant_ids.filtered(lambda q: q.location_id.usage != 'view')

            for quant in stock_quants:
                if quant.location_id.location_id.name == 'IHO':
                    product_data[product_id]['IHO Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BHW':
                    product_data[product_id]['Bhiwandi Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DEL':
                    product_data[product_id]['Delhi Stock'] = quant.quantity
                    product_data[product_id]['Available Qty'] = quant.quantity - quant.reserved_quantity
                elif quant.location_id.location_id.name == 'BHU':
                    product_data[product_id]['BHU Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'DHASA':
                    product_data[product_id]['DHASA Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'ELM':
                    product_data[product_id]['ELM Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'JSP':
                    product_data[product_id]['JSP Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'JWD':
                    product_data[product_id]['JWD Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'RCP':
                    product_data[product_id]['RCP Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'UPW':
                    product_data[product_id]['UPW Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'BWMIS':
                    product_data[product_id]['BWMIS Stock'] = quant.quantity
                elif quant.location_id.location_id.name == 'CH':
                    product_data[product_id]['CH Stock'] = quant.quantity
                elif quant.location_id.name == 'Customers':
                    product_data[product_id]['Customer Location'] = quant.quantity
                elif quant.location_id.name == 'Vendors':
                    product_data[product_id]['Vendor Location'] = quant.quantity
                elif quant.location_id.name == 'Inventory adjustment':
                    product_data[product_id]['Virtual Locations/Inventory adjustment'] = quant.quantity
                elif quant.location_id.name == 'Scrap':
                    product_data[product_id]['Virtual Locations/Scrap'] = quant.quantity
                elif quant.location_id.name == 'Production':
                    product_data[product_id]['Virtual Locations/Production'] = quant.quantity

            # Quotations related to the product
            self.env.cr.execute("""
                select sum(line.product_uom_qty - line.qty_delivered) 
                from sale_order_line as line
                join sale_order so on line.order_id = so.id
                where so.state = 'draft' and line.product_id = %s
                and so.is_short_close is not true
            """, (product_id,))
            qty_to_deliver_qtn_data = self.env.cr.dictfetchall()
            qty_to_deliver_qtn = qty_to_deliver_qtn_data[0].get('sum') if qty_to_deliver_qtn_data[0].get('sum') is not None else 0
            product_data[product_id]['Quotation Qty'] = qty_to_deliver_qtn

            # Sales orders related to the product
            self.env.cr.execute("""
                select sum(line.product_uom_qty - line.qty_delivered) 
                from sale_order_line as line
                join sale_order so on line.order_id = so.id
                where so.state not in ('draft', 'cancel', 'sent') and line.product_id = %s 
                and so.is_short_close is not true
            """, (product_id,))
            qty_to_deliver_data = self.env.cr.dictfetchall()
            qty_to_deliver = qty_to_deliver_data[0].get('sum') if qty_to_deliver_data[0].get('sum') is not None else 0
            product_data[product_id]['Confirmed SO qty'] = qty_to_deliver

            # Free to use
            free_to_use = 0
            if product.qty_available < qty_to_deliver:
                product_data[product_id]['FREE TO USE'] = 0
            else:
                product_data[product_id]['FREE TO USE'] = product.qty_available - qty_to_deliver
                free_to_use = product.qty_available - qty_to_deliver

            # Purchase orders related to the product
            self.env.cr.execute("""
                select sum(line.product_qty - line.qty_received) 
                from purchase_order_line as line
                join purchase_order po on line.order_id = po.id
                where po.state not in ('draft', 'to approve', 'cancel', 'sent') and line.product_id = %s
                and po.is_short_close is not true
            """, (product_id,))
            order_pending_data = self.env.cr.dictfetchall()
            order_pending_qty = order_pending_data[0].get('sum') if order_pending_data[0].get('sum') is not None else 0
            product_data[product_id]['PO Receipt Pending'] = order_pending_qty

            if free_to_use > 0:
                product_data[product_id]['To Replenish'] = 0
            else:
                replenish_qty = qty_to_deliver - product.qty_available
                product_data[product_id]['To Replenish'] = replenish_qty - order_pending_qty
                if product_data[product_id]['To Replenish'] < 0:
                    product_data[product_id]['To Replenish'] = 0

            # Quotation outgoing quantity
            self.env.cr.execute("""
                select sum(line.product_uom_qty) 
                from sale_order_line as line
                join sale_order so on line.order_id = so.id
                where so.state = 'draft' and line.product_id = %s
                and so.is_short_close is not true
            """, (product_id,))
            quotation_outgoing_data = self.env.cr.dictfetchall()
            quotation_outgoing_qty = quotation_outgoing_data[0].get('sum') if quotation_outgoing_data[0].get('sum') is not None else 0

            outgoing_qty = product.outgoing_qty + quotation_outgoing_qty
            incoming_qty = product.incoming_qty
            onhand_incoming_minus_outgoing = product.qty_available + incoming_qty - outgoing_qty
            product_data[product_id]['(Onhand + incoming) - outgoing(With_Qtn)'] = onhand_incoming_minus_outgoing

        # Write data to the sheet
        for product_id, data in sorted(product_data.items(), key=lambda x: (
                x[1]['Brand'].lower(), x[1]['Category 1'].lower(), x[1]['Category 2'].lower(),
                x[1]['Category 3'].lower())):
            sheet.write(row, col, data['Brand'])
            sheet.write(row, col + 1, data['Creation Date'])
            sheet.write(row, col + 2, data['Category 1'])
            sheet.write(row, col + 3, data['Category 2'])
            sheet.write(row, col + 4, data['Category 3'])
            sheet.write(row, col + 5, data['Function Sport'])
            sheet.write(row, col + 6, data['Gender'])
            sheet.write(row, col + 7, data['Age group'])
            sheet.write(row, col + 8, data['Title'])
            sheet.write(row, col + 9, data['Marketplace Tittle'])
            sheet.write(row, col + 10, data['Composition / Material'])
            sheet.write(row, col + 11, data['Technology / Features'])
            sheet.write(row, col + 12, data['Event'])
            sheet.write(row, col + 13, data['HSN Code'])
            sheet.write(row, col + 14, data['Style Code'])
            sheet.write(row, col + 15, data['Article Code'])
            sheet.write(row, col + 16, data['SKU Code'])
            sheet.write(row, col + 17, data['EAN Code'])
            sheet.write(row, col + 18, data['ASIN'])
            sheet.write(row, col + 19, data['FSIN'])
            sheet.write(row, col + 20, data['Myntra'])
            sheet.write(row, col + 21, data['AJIO'])
            sheet.write(row, col + 22, data['Fancode'])
            sheet.write(row, col + 23, data['Swiggy'])
            sheet.write(row, col + 24, data['Bigbasket'])
            sheet.write(row, col + 25, data['Blinkit'])
            sheet.write(row, col + 26, data['Zepto'])
            sheet.write(row, col + 27, data['Colour'])
            sheet.write(row, col + 28, data['Size'])
            sheet.write(row, col + 29, data['MRP'])
            sheet.write(row, col + 30, data['COST Price'])
            sheet.write(row, col + 31, data['GST'])
            sheet.write(row, col + 32, data['IHO Stock'])
            sheet.write(row, col + 33, data['Bhiwandi Stock'])
            sheet.write(row, col + 34, data['Delhi Stock'])
            sheet.write(row, col + 35, data['Available Qty'])
            sheet.write(row, col + 36, data['BHU Stock'])
            sheet.write(row, col + 37, data['DHASA Stock'])
            sheet.write(row, col + 38, data['ELM Stock'])
            sheet.write(row, col + 39, data['JSP Stock'])
            sheet.write(row, col + 40, data['JWD Stock'])
            sheet.write(row, col + 41, data['RCP Stock'])
            sheet.write(row, col + 42, data['UPW Stock'])
            sheet.write(row, col + 43, data['BWMIS Stock'])
            sheet.write(row, col + 44, data['CH Stock'])
            sheet.write(row, col + 45, data['Customer Location'])
            sheet.write(row, col + 46, data['Vendor Location'])
            sheet.write(row, col + 47, data['Virtual Locations/Inventory adjustment'])
            sheet.write(row, col + 48, data['Virtual Locations/Scrap'])
            sheet.write(row, col + 49, data['Virtual Locations/Production'])
            sheet.write(row, col + 50, data['Total'])
            sheet.write(row, col + 51, data['Quotation Qty'])
            sheet.write(row, col + 52, data['Confirmed SO qty'])
            sheet.write(row, col + 53, data['FREE TO USE'])
            sheet.write(row, col + 54, data['PO Receipt Pending'])
            sheet.write(row, col + 55, data['To Replenish'])
            sheet.write(row, col + 56, data['Bullet Point 1'])
            sheet.write(row, col + 57, data['Bullet Point 2'])
            sheet.write(row, col + 58, data['Bullet Point 3'])
            sheet.write(row, col + 59, data['Bullet Point 4'])
            sheet.write(row, col + 60, data['Bullet Point 5'])
            sheet.write(row, col + 61, data['Keyword'])
            sheet.write(row, col + 62, data['Description'])
            sheet.write(row, col + 63, data['Google Drive Link'])
            sheet.write(row, col + 64, data['Drop Box Link'])
            sheet.write(row, col + 65, data['Country of Origin'])
            sheet.write(row, col + 66, data['Product Net Weight (gms)'])
            sheet.write(row, col + 67, data['Product Length (cm)'])
            sheet.write(row, col + 68, data['Product Breadth (cm)'])
            sheet.write(row, col + 69, data['Product Height (cm)'])
            sheet.write(row, col + 70, data['Package Gross Weight (gms)'])
            sheet.write(row, col + 71, data['Package Length (cm)'])
            sheet.write(row, col + 72, data['Package Breadth (cm)'])
            sheet.write(row, col + 73, data['Package Height (cm)'])

            row += 1

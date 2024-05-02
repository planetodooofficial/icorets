from datetime import datetime
import json

import requests

from odoo import models, fields, api, _
from requests import get, post

from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)


class ShopInstance(models.Model):
    _name = 'shop.instance'
    _description = 'Shop Instance'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    shop_url = fields.Char(string='Shop URL', required=True, tracking=True)
    username = fields.Char(string='User Name/Email', required=True, tracking=True)
    auth_bearer = fields.Char(string='Auth Bearer', readonly=True)
    password = fields.Char(string="Password", required=True, tracking=True)
    active = fields.Boolean(string="Active")
    last_import_date = fields.Datetime(string='Last Update Datetime', readonly=True)
    shop_import_logs_ids = fields.One2many('shop.import.logs', 'shop_id', string='Shop Import Logs')
    update_time = fields.Integer(string='Update Time (in minutes)', default=30)

    def generate_token(self):
        """ Generate The Auth Token For The Shop Instance """
        start_date = fields.Datetime.now()
        params = {
            "grant_type": "password",
            "client_id": "my-trusted-client",
            "username": self.username,
            "password": self.password,
        }
        url = self.shop_url + "/oauth/token?"
        fetch_token = get(url=url, params=params)
        if fetch_token.status_code != 200:
            self.generate_exception_log(message=fetch_token.json(), start_date=start_date,
                                        end_date=fields.Datetime.now(), count=1, state='exception')
            raise UserError(_(fetch_token.json()))
        elif fetch_token.status_code == 200:
            token = fetch_token.json()["access_token"]
            self.auth_bearer = "bearer " + token
            self.generate_success_log("Successfully Fetched The Auth Token", start_date=start_date,
                                      end_date=fields.Datetime.now(), count=1, state='success')
            self.last_import_date = fields.Datetime.now()
            return True

    def get_orders(self):
        """ Get The Orders Code From The Shop Instance """
        start_date = fields.Datetime.now()
        try:
            url = self.shop_url + "/services/rest/v1/oms/saleOrder/search"
            headers = {
                'Authorization': self.auth_bearer,
                'Content-Type': 'application/json',
                'Facility': 'karan'
            }
            data = {
                "updatedSinceInMinutes": self.update_time,
            }
            fetch_orders = post(url=url, headers=headers, data=json.dumps(data))
            if fetch_orders.status_code != 200:
                self.generate_exception_log(message=fetch_orders.json(), start_date=start_date,
                                            end_date=fields.Datetime.now(), count=1, state='exception')
                raise UserError(_(fetch_orders.json().get("errors", [])[0]["message"]))
            elif fetch_orders.status_code == 200:
                orders_list = fetch_orders.json()
                if orders_list.get("errors", []):
                    raise UserError(_(orders_list.get("errors", [])[0]["message"]))
                orders_list = self.get_order_list(orders_list)
                if orders_list:
                    searched_orders = self.search_orders(sale_order_codes=orders_list)
                    order_count, updated_order = self.create_orders(orders=searched_orders)
                    if len(order_count) > 0:
                        self.generate_success_log(message="Successfully Fetched The Orders",
                                                  start_date=start_date,
                                                  end_date=fields.Datetime.now(), count=len(order_count),
                                                  state='success', operation_performed='Fetching Orders')
                    if len(updated_order) > 0:
                        # self.create_returns()
                        self.generate_success_log(message="Successfully Updated The Orders",
                                                  start_date=start_date,
                                                  end_date=fields.Datetime.now(), count=len(updated_order),
                                                  state='success', operation_performed='Updated Orders')
                self.last_import_date = fields.Datetime.now()
        except Exception as e:
            self.generate_exception_log(message=e, start_date=start_date,
                                        operation_performed='Fetching Orders',
                                        end_date=fields.Datetime.now(), count=1, state='exception')
            raise UserError(_(e))

    @staticmethod
    def get_order_list(api_response):
        matching_orders = [order for order in api_response.get("elements", []) if order["status"] == "COMPLETE"]
        return matching_orders

    def search_orders(self, sale_order_codes):
        """ Get The Orders Details From The Shop Instance """
        start_date = fields.Datetime.now()
        url = self.shop_url + "/services/rest/v1/oms/saleorder/get"
        headers = {
            'Authorization': self.auth_bearer,
            'Content-Type': 'application/json',
            'Facility': 'karan'
        }
        search_orders = []
        for code in sale_order_codes:
            data = {
                "code": code.get("code")
            }
            fetch_orders = post(url=url, headers=headers, data=json.dumps(data))
            if fetch_orders.status_code != 200:
                self.generate_exception_log(message=fetch_orders.json(), start_date=start_date,
                                            end_date=fields.Datetime.now(), count=1, state='exception')
                raise UserError(_(fetch_orders.json()))
            elif fetch_orders.status_code == 200:
                orders = fetch_orders.json()
                search_orders.append(orders['saleOrderDTO'])
        return search_orders

    def create_orders(self, orders):
        """ Create The Orders From The Shop Instance """
        unicommerce_order_obj = self.env['unicommerce.orders']
        incoming_order_codes = [order['code'] for order in orders]
        # Search for existing orders based on their codes
        existing_orders = unicommerce_order_obj.search([('code', 'in', incoming_order_codes)])
        unicommerce_orders = []
        new_orders = []
        update_orders = []
        for order in orders:
            if order['code'] in existing_orders.mapped('code'):
                # check whether the return dictionary is there and it's status is completed
                if order['returns']:
                    for return_order in order['returns']:
                        if return_order['statusCode'] in ['COMPLETE', 'RETURNED']:
                            update_orders.append(order)
            else:
                new_orders.append(order)
        for order in new_orders:
            # Create New Unicommerce Order
            get_shipping_address_id = order['saleOrderItems'][0]['shippingAddressId']
            get_shipping_address = [address for address in order['addresses'] if
                                    address['id'] == str(get_shipping_address_id)]
            sales_channel_id = self.env['shop.sales.channel'].search([('name', '=', order['source'])], limit=1)
            shipping_packages = order.get('shippingPackages', [])

            # date related to the orders
            shipping_date = shipping_packages[0].get('dispatched', '') if shipping_packages else False
            invoice_date = shipping_packages[0].get('invoiceDate', '') if shipping_packages else False
            invoice_no = shipping_packages[0].get('invoiceCode', '') if shipping_packages else False
            order_lines = self.prepare_lines(order['saleOrderItems'], sales_channel_id)
            # prepare the order dictionary
            unicommerce_order_vals = {
                'code': order['code'],
                'displayOrderCode': order['displayOrderCode'],
                'invoice_no': invoice_no,
                'shipping_date': datetime.utcfromtimestamp(shipping_date // 1000) if shipping_date else False,
                'invoice_date': datetime.utcfromtimestamp(invoice_date // 1000) if invoice_date else False,
                'channel': order['channel'],
                'source': order['source'],
                'sales_channel_id': sales_channel_id.id,
                'shop_instance_id': sales_channel_id.shop_instance_id.id,
                'displayOrderDateTime': datetime.utcfromtimestamp(order['displayOrderDateTime'] // 1000),
                'status': order['status'],
                'created': datetime.utcfromtimestamp(order['created'] // 1000),
                'updated': datetime.utcfromtimestamp(order['updated'] // 1000),
                'fulfillmentTat': datetime.utcfromtimestamp(order['fulfillmentTat'] // 1000),
                'notificationEmail': order['notificationEmail'],
                'notificationMobile': order['notificationMobile'],
                'customerGSTIN': order['customerGSTIN'],
                'channelProcessingTime': datetime.utcfromtimestamp(order['channelProcessingTime'] // 1000),
                'cod': order['cod'],
                'thirdPartyShipping': order['thirdPartyShipping'],
                'priority': order['priority'],
                'currencyCode': order['currencyCode'],
                'customerCode': order['customerCode'],
                'billing_name': order['billingAddress']['name'],
                'billing_addressLine1': order['billingAddress']['addressLine1'],
                'billing_addressLine2': order['billingAddress']['addressLine2'],
                'billing_city': order['billingAddress']['city'],
                'billing_district': order['billingAddress']['district'],
                'billing_state': order['billingAddress']['state'],
                'billing_country': order['billingAddress']['country'],
                'billing_pincode': order['billingAddress']['pincode'],
                'billing_phone': order['billingAddress']['phone'],
                'billing_email': order['billingAddress']['email'],
                'shipping_name': order['addresses'][0]['name'],
                'shipping_addressLine1': get_shipping_address[0]['addressLine1'],
                'shipping_addressLine2': get_shipping_address[0]['addressLine2'],
                'shipping_city': get_shipping_address[0]['city'],
                'shipping_district': get_shipping_address[0]['district'],
                'shipping_state': get_shipping_address[0]['state'],
                'shipping_country': get_shipping_address[0]['country'],
                'shipping_pincode': get_shipping_address[0]['pincode'],
                'shipping_phone': get_shipping_address[0]['phone'],
                'shipping_email': get_shipping_address[0]['email'],
                'order_data_json': json.dumps(order, indent=2),
                'order_state': 'exception' if self.has_exception(order_lines) else 'draft',
                'order_line': order_lines,
            }
            unicommerce_orders.append(unicommerce_order_vals)
        orders = unicommerce_order_obj.create(unicommerce_orders)
        for order in update_orders:
            order_id = unicommerce_order_obj.search([('code', '=', order['code'])])
            if order_id:
                order_id.write(
                    {'is_return': True, 'order_data_json': json.dumps(order, indent=2), 'return_state': 'draft'})
                order_data = json.loads(order_id.order_data_json)
                order_id.write({'return_invoice_no': order_data['returns'][0]['returnInvoiceCode']})
                for line in order_data['returns'][0]['returnItems']:
                    return_line = order_id.order_line.filtered(
                        lambda r: r.product_id.default_code == line['itemSku'] and r.is_returned is False)
                    if return_line:
                        return_line.write({'return_status': True})
        return orders, update_orders

    def prepare_lines(self, lines, shop_channel_id=False):
        """Prepare Lines data for the api product lines"""
        product_obj = self.env['product.product']
        prepared_lines = []
        missing_products = []
        shipping_product_id = self.env['product.product'].search([('default_code', '=', 'SHIPPING_CHARGES')]).id
        if not shipping_product_id:
            raise UserError(
                _("Shipping Charges Product Not Found! Please Create a Product with Default Code `SHIPPING_CHARGE`"))
        tax_obj = self.env['account.tax']
        for order_line in lines:
            product = product_obj.search([('default_code', '=', order_line['itemSku'])])
            tax = False
            if order_line['totalIntegratedGst']:
                tax = order_line['integratedGstPercentage']
            elif order_line['totalStateGst']:
                tax = order_line['stateGstPercentage'] + order_line['centralGstPercentage']
            search_tax = tax_obj.search([('amount', '=', int(tax)), ('is_a_default', '=', True),
                                         ('type_tax_use', '=', 'sale'),
                                         ('company_id', '=', shop_channel_id.company_id.id),
                                         ('tax_group_id.name', '=', 'GST')])
            if order_line['shippingCharges']:
                # append a shipping line with the unit price of the shipping
                shipping_line = {
                    'product_id': shipping_product_id,
                    'selling_price_without_taxes_and_discount': order_line['shippingCharges'] / (
                            1 + (search_tax.amount / 100)),
                    'tax_id': search_tax.id if search_tax else False,
                }
                prepared_lines.append((0, 0, shipping_line))
            unicommerce_order_line_vals = {
                'product_id': product.id,
                'shipping_package_code': order_line.get('shippingPackageCode', ''),
                'shipping_package_status': order_line.get('shippingPackageStatus', ''),
                'facility_code': order_line.get('facilityCode', ''),
                'facility_name': order_line.get('facilityName', ''),
                'alternate_facility_code': order_line.get('alternateFacilityCode', ''),
                'reverse_pickup_code': order_line.get('reversePickupCode', ''),
                'shipping_address_id': order_line.get('shippingAddressId', ''),
                'packet_number': order_line.get('packetNumber', ''),
                'combination_identifier': order_line.get('combinationIdentifier', ''),
                'combination_description': order_line.get('combinationDescription', ''),
                'type': order_line.get('type', ''),
                'item': order_line.get('item', ''),
                'shipping_method_code': order_line.get('shippingMethodCode', ''),
                'item_name': order_line.get('itemName', ''),
                'item_sku': order_line.get('itemSku', ''),
                'seller_sku_code': order_line.get('sellerSkuCode', ''),
                'channel_product_id': order_line.get('channelProductId', ''),
                'image_url': order_line.get('imageUrl', ''),
                'status_code': order_line.get('statusCode', ''),
                'code': order_line.get('code', ''),
                'shelf_code': order_line.get('shelfCode', ''),
                'total_price': order_line.get('totalPrice', ''),
                'selling_price': order_line.get('sellingPrice', ''),
                'shipping_charges': order_line.get('shippingCharges', ''),
                'shipping_method_charges': order_line.get('shippingMethodCharges', ''),
                'cash_on_delivery_charges': order_line.get('cashOnDeliveryCharges', ''),
                'prepaid_amount': order_line.get('prepaidAmount', ''),
                'voucher_code': order_line.get('voucherCode', ''),
                'voucher_value': order_line.get('voucherValue', ''),
                'store_credit': order_line.get('storeCredit', ''),
                'discount': order_line.get('discount', ''),
                'gift_wrap': order_line.get('giftWrap', ''),
                'gift_wrap_charges': order_line.get('giftWrapCharges', ''),
                'tax_percentage': order_line.get('taxPercentage', ''),
                'gift_message': order_line.get('giftMessage', ''),
                'cancellable': order_line.get('cancellable', 'False'),
                'edit_address': order_line.get('editAddress', 'False'),
                'reverse_pickable': order_line.get('reversePickable', 'False'),
                'packet_configurable': order_line.get('packetConfigurable', 'False'),
                'created': order_line.get('created', ''),
                'updated': order_line.get('updated', ''),
                'on_hold': order_line.get('onHold', 'False'),
                'sale_order_item_alternate_id': order_line.get('saleOrderItemAlternateId'),
                'cancellation_reason': order_line.get('cancellationReason'),
                'cancelled_by_seller': order_line.get('cancelledBySeller'),
                'page_url': order_line.get('pageUrl'),
                'color': order_line.get('color'),
                'brand': order_line.get('brand'),
                'size': order_line.get('size'),
                'replacement_sale_order_code': order_line.get('replacementSaleOrderCode'),
                'bundle_sku_code': order_line.get('bundleSkuCode'),
                'custom_field_values': order_line.get('customFieldValues'),
                'item_detail_field_dto_list': order_line.get('itemDetailFieldDTOList'),
                'hsn_code': order_line.get('hsnCode'),
                'total_integrated_gst': order_line.get('totalIntegratedGst'),
                'integrated_gst_percentage': order_line.get('integratedGstPercentage'),
                'total_union_territory_gst': order_line.get('totalUnionTerritoryGst'),
                'union_territory_gst_percentage': order_line.get('unionTerritoryGstPercentage'),
                'total_state_gst': order_line.get('totalStateGst'),
                'state_gst_percentage': order_line.get('stateGstPercentage'),
                'total_central_gst': order_line.get('totalCentralGst'),
                'central_gst_percentage': order_line.get('centralGstPercentage'),
                'max_retail_price': order_line.get('maxRetailPrice'),
                'selling_price_without_taxes_and_discount': order_line.get('sellingPriceWithoutTaxesAndDiscount'),
                'batch_dto': order_line.get('batchDTO'),
                'shipping_charge_tax_percentage': order_line.get('shippingChargeTaxPercentage'),
                'tcs': order_line.get('tcs'),
                'uc_batch_code': order_line.get('ucBatchCode'),
                'channel_mrp': order_line.get('channelMrp'),
                'channel_expiry_date': order_line.get('channelExpiryDate'),
                'channel_vendor_batch_number': order_line.get('channelVendorBatchNumber'),
                'channel_mfd': order_line.get('channelMfd'),
                'country_of_origin': order_line.get('countryOfOrigin'),
                'expected_delivery_date': order_line.get('expectedDeliveryDate'),
                'item_detail_fields': order_line.get('itemDetailFields'),
                'item_details_key': order_line.get('itemDetailsKey'),
                'channel_sale_order_item_code': order_line.get('channelSaleOrderItemCode'),
                'effective_tolerance': order_line.get('effectiveTolerance'),
                'tax_id': search_tax.id if search_tax else False,
                'status': False if product else True,

            }
            prepared_lines.append((0, 0, unicommerce_order_line_vals))
        return prepared_lines

    def generate_success_log(self, message, start_date, end_date=False, count=1, state='', operation_performed=''):
        """ Generate The Success logs for the processed requests """
        shop_import_logs_obj = self.env['shop.import.logs']
        vals = {
            'name': "Success",
            'shop_id': self.id,
            'message': message,
            'start_date': start_date,
            'end_date': end_date,
            'count': count,
            'state': state,
            'operation_performed': operation_performed,
        }
        shop_import_logs_obj.create(vals)

    def generate_exception_log(self, message, start_date, end_date=False, count=1, state='', operation_performed='',
                               error_message=''):
        """ Generate The Exception logs for the processed requests """
        shop_import_logs_obj = self.env['shop.import.logs']
        vals = {
            'name': "Exception",
            'shop_id': self.id,
            'message': message,
            'start_date': start_date,
            'end_date': end_date,
            'count': count,
            'state': state,
            'operation_performed': operation_performed,
            'error_message': error_message,
        }
        shop_import_logs_obj.create(vals)

    def create_sales(self):
        # Get all orders that are in draft state
        orders = self.env['unicommerce.orders'].search([('order_state', '=', 'draft')])
        count = 0
        sale_orders = list()
        stock_location = self.env['stock.location'].search([('name', '=', 'BHW')], limit=1)
        location_id = self.env['stock.location'].search(
            [('name', '=', 'Stock'), ('location_id', '=', stock_location.id)], limit=1)
        start_date = fields.Datetime.now()
        try:
            for order in orders:
                # Create sale order
                # partners = self.create_partner(order)
                partner_id = self.create_partner(order)
                # billing_id = self.env['res.partner'].search(
                #     [('parent_id', '=', partner_id.id), ('type', '=', 'invoice')])
                # shipping_id = self.env['res.partner'].search(
                #     [('parent_id', '=', partner_id.id), ('type', '=', 'delivery')])
                vals_list = {
                    'partner_id': partner_id.id,
                    'order_line': self.create_order_lines(order),
                    'l10n_in_journal_id': order.sales_channel_id.sale_journal_id.id,
                    'date_order': order.displayOrderDateTime,
                    'state': 'draft',
                    'shop_instance_id': order.shop_instance_id.id,
                    'sales_channel_id': order.sales_channel_id.id,
                    'unicommerce_order_id': order.id,
                    'partner_shipping_id': partner_id.id,
                    'partner_invoice_id': partner_id.id,
                    'dump_sequence': order.code,
                    'location_id': location_id.id,
                    'gstin_id': self.env.company.partner_id.id,
                    'client_order_ref': order.displayOrderCode,
                }
                logger.info(vals_list)
                sale_order = self.env['sale.order'].create(vals_list)
                # Update order state to "done"
                sale_order.set_order_line()
                order.order_state = 'done'
                order.name = sale_order.id
                sale_orders.append(sale_order)
                count += 1
            if orders:
                self.sale_order_confirm_batch(sale_orders, "unicommerce", orders[0].code)
                # payments = [self.create_payments_entries(order, order.sales_channel_id) for order in sale_orders if
                #             order.state == "sale"]
                self.generate_success_log(message="Successfully Created Sales Orders", start_date=start_date,
                                          end_date=fields.Datetime.now(), count=count, state='success',
                                          operation_performed='Sales Order Creation')
        except Exception as e:
            self.generate_exception_log(message=e, start_date=fields.Datetime.now(),
                                        operation_performed='Sales Order Creation',
                                        end_date=fields.Datetime.now(), count=1, state='exception')
            raise UserError(_(e))

    # def create_payments_entries(self, order, sales_channel_id):
    #     """Create payments for the sale orders """
    #     if not sales_channel_id.is_no_invoice:
    #         invoice_ids = order.invoice_ids
    #         journal_id = sales_channel_id.prepaid_holding_journal_id if not order.unicommerce_order_id.cod else sales_channel_id.cod_holding_journal_id
    #         search_payment_method = self.env["account.payment.method"].search([('name', '=', 'Manual')], limit=1)
    #         search_payment_method_line = self.env["account.payment.method.line"].search([
    #             ('payment_method_id', '=', search_payment_method.id),
    #             ('journal_id', '=', journal_id.id)
    #         ])
    #
    #         payment_obj = self.env["account.payment.register"]
    #
    #         acc_type = 'asset_receivable' if invoice_ids[0].move_type == 'out_invoice' else 'liability_payable'
    #
    #         # Filter invoice lines for each invoice and prepare payment
    #         payments = []
    #         for invoice_id in invoice_ids:
    #             payment_move_line = invoice_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)
    #             if payment_move_line:
    #                 payment_id = payment_obj.with_context({
    #                     'active_model': 'account.move',
    #                     'active_ids': invoice_id.ids
    #                 }).create({
    #                     'journal_id': journal_id.id,
    #                     'payment_method_line_id': search_payment_method_line.id,
    #                     'line_ids': [(4, line.id) for line in payment_move_line]
    #                 })
    #                 payments.append(payment_id)
    #
    #         # Create and post payments
    #         for payment in payments:
    #             try:
    #                 payment._create_payments()
    #             except UserError as e:
    #                 # Handle any errors while creating payments
    #                 logger.error(e)
    #
    #         return payments

    def sale_order_confirm_batch(self, sale_orders, record_type, dump_sequence):
        order_dates = {}
        shipment_dates = {}
        invoice_dates = {}

        for sale_order in sale_orders:
            if sale_order.sales_channel_id:
                sale_order.action_confirm()
                if record_type == "unicommerce":
                    order_dates[sale_order.id] = sale_order.unicommerce_order_id.displayOrderDateTime
                    shipment_dates[sale_order.id] = sale_order.unicommerce_order_id.shipping_date
                    invoice_dates[sale_order.id] = sale_order.unicommerce_order_id.invoice_date

        # Batch update order dates
        for order_id, order_date in order_dates.items():
            if order_date:
                self.env["sale.order"].browse(order_id).write({'date_order': order_date})

        # Batch process deliveries
        for sale_order in sale_orders:
            if sale_order.state == "sale":
                search_delivery = self.env["stock.picking"].search([('origin', '=', sale_order.name)])
                search_delivery.write({'dump_sequence': dump_sequence})

                for delivery in search_delivery:
                    delivery.write({'location_id': sale_order.location_id.id})

                    shipment_date = shipment_dates.get(sale_order.id)
                    if shipment_date:
                        delivery.write({'scheduled_date': shipment_date})

                    for stock_move_package in delivery.move_ids_without_package:
                        stock_move_package.quantity_done = stock_move_package.product_uom_qty
                    delivery.action_assign()
                    delivery.button_validate()

        # Batch process invoices
        for sale_order in sale_orders:
            if sale_order.sales_channel_id and not sale_order.sales_channel_id.is_no_invoice:
                invoice_vals = sale_order._prepare_invoice()

                lst = [(0, 0, so_order_line._prepare_invoice_line()) for so_order_line in sale_order.order_line]
                invoice_vals['invoice_line_ids'] = lst
                result = self.env['account.move'].create(invoice_vals)

                invoice_date = invoice_dates.get(sale_order.id)
                if invoice_date:
                    result.write({'invoice_date': invoice_date})

                for invoice_line in result.invoice_line_ids:
                    invoice_line.write({'account_id': result.journal_id.default_account_id.id})

                if sale_order.unicommerce_order_id.invoice_no:
                    result.write({'payment_reference': sale_order.unicommerce_order_id.invoice_no})

                result.write({'dump_sequence': dump_sequence,
                              'sales_channel_id': sale_order.sales_channel_id.id,
                              'shop_instance_id': sale_order.shop_instance_id.id,
                              'unicommerce_order_id': sale_order.unicommerce_order_id.id,
                              })
                result.action_post()

    def create_partner(self, partner_data):
        """ Create partner in Odoo """
        partner_obj = self.env['res.partner']
        partner_data = partner_data.read()[0]
        state_id = self.get_state_id(partner_data.get('billing_state'))
        partner_id = partner_obj.search([('is_website_partner', '=', True), ('state_id', '=', state_id)], limit=1)

        # # Determine if the partner is a business based on GSTIN
        # is_business = bool(partner_data.get('customerGSTIN'))
        #
        # # search for the partner in case the is_business is true
        # if is_business:
        #     partner = partner_obj.search([('vat', '=', partner_data.get('customerGSTIN'))], limit=1)
        #     if partner:
        #         return partner, partner.child_ids.filtered(lambda r: r.type == 'delivery')
        # partner = partner_obj.search([('name', '=', partner_data.get('billing_name')),
        #                               ('state_id.code', '=', partner_data.get('billing_state')),
        #                               ('country_id.code', '=', partner_data.get('billing_country'))], limit=1)
        # Prepare data for billing partner
        # if not partner:
        #     billing_partner_data = {
        #         'name': partner_data.get('billing_name'),
        #         'street': partner_data.get('billing_addressLine1'),
        #         'street2': partner_data.get('billing_addressLine2'),
        #         'city': partner_data.get('billing_city'),
        #         'state_id': self.get_state_id(partner_data.get('billing_state')),
        #         'country_id': self.get_country_id(partner_data.get('billing_country')),
        #         'zip': partner_data.get('billing_pincode'),
        #         'phone': partner_data.get('billing_phone'),
        #         'email': partner_data.get('billing_email'),
        #         'is_company': is_business,
        #         'vat': partner_data.get('customerGSTIN') if is_business else False,
        #         'l10n_in_gst_treatment': 'registered' if is_business else False,
        #     }
        #
        #     # Create billing partner
        #     billing_partner = partner_obj.create(billing_partner_data)
        #
        #     # Prepare data for shipping partner
        #     shipping_partner_data = {
        #         'name': partner_data.get('shipping_name') or partner_data.get('billing_name'),
        #         'street': partner_data.get('shipping_addressLine1') or partner_data.get('billing_addressLine1'),
        #         'street2': partner_data.get('shipping_addressLine2') or partner_data.get('billing_addressLine2'),
        #         'city': partner_data.get('shipping_city') or partner_data.get('billing_city'),
        #         'state_id': self.get_state_id(partner_data.get('shipping_state') or partner_data.get('billing_state')),
        #         'country_id': self.get_country_id(
        #             partner_data.get('shipping_country') or partner_data.get('billing_country')),
        #         'zip': partner_data.get('shipping_pincode') or partner_data.get('billing_pincode'),
        #         'phone': partner_data.get('shipping_phone') or partner_data.get('billing_phone'),
        #         'email': partner_data.get('shipping_email') or partner_data.get('billing_email'),
        #         'is_company': is_business,
        #         'type': 'delivery',
        #         'parent_id': billing_partner.id,
        #     }
        #
        #     # Create shipping partner
        #     shipping_partner = partner_obj.create(shipping_partner_data)
        #     logger.info(f"Created shipping partner: {shipping_partner}")
        #     # return {'billing_partner':billing_partner, 'shipping_partner': shipping_partner}
        #     return billing_partner
        # else:
        #     # return partner, partner.child_ids.filtered(lambda r: r.type == 'delivery')
        return partner_id

    def get_state_id(self, state_name):
        """ Get state ID based on state name """
        country = self.env['res.country'].search([('code', '=', 'IN')], limit=1)
        state = self.env['res.country.state'].search([('code', '=', state_name), ('country_id', '=', country.id)],
                                                     limit=1)
        return state.id if state else False

    def get_country_id(self, country_name):
        """ Get country ID based on country name """
        country = self.env['res.country'].search([('code', '=', country_name)], limit=1)
        return country.id if country else False

    def create_order_lines(self, order):
        """ Create order lines for Sale Order """
        order_lines = []
        uom_id = self.env['uom.uom'].search([('name', '=', 'Pieces')], limit=1)
        for line in order.order_line:
            # added the discount deduction in line level to avoid the conflict with the pricing.
            line.product_id.write({'taxes_id': [(6, 0, [line.tax_id.id])] if line.tax_id else False})
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom_qty': 1,
                'price_unit': line.selling_price_without_taxes_and_discount - line.discount,
                'tax_id': [(6, 0, [line.tax_id.id])] if line.tax_id else False,
                'product_uom': uom_id.id,
                'analytic_distribution': {f"{order.sales_channel_id.analytics_id.id}": 100},
            }))
        return order_lines

    def create_returns_sales(self):
        """ Create the Returns for the Orders with the return status True from unicommerce orders dump\n
            1. Create a return delivery,\n
            2. Create a credit note,\n
            3. Change the order_state to done again.
        """
        start_date = fields.Datetime.now()
        count = 0
        try:
            orders = self.env['unicommerce.orders'].search(
                [('is_return', '=', True), ('name', '!=', False), ('return_state', '=', 'draft')])
            for uni_order in orders:
                lines_to_return = uni_order.order_line.filtered(lambda x: x.return_status is True)
                search_delivery = self.env["stock.picking"].search([('origin', '=', uni_order.name.name)])
                if lines_to_return:
                    if len(uni_order.order_line) == len(lines_to_return):
                        # create a full return/refund
                        stock_return_picking_obj = self.env["stock.return.picking"]
                        for delivery in search_delivery:
                            lst = []
                            for move_id_package in delivery.move_ids_without_package:
                                reverse_transfer_line_val = (0, 0, {
                                    'product_id': move_id_package.product_id.id,
                                    'quantity': move_id_package.quantity_done,
                                    'uom_id': move_id_package.product_uom.id,
                                    'move_id': move_id_package.id,
                                    'to_refund': True,
                                })
                                lst.append(reverse_transfer_line_val)
                            reverse_transfer_val = {
                                'location_id': delivery.location_id.id,
                                'picking_id': delivery.id,
                                'product_return_moves': lst
                            }
                            stock_return_wizard_id = stock_return_picking_obj.create(reverse_transfer_val)
                            new_picking_id = stock_return_wizard_id.create_returns()
                            new_picking_id = new_picking_id.get('res_id', False)
                            if new_picking_id:
                                search_return_delivery = self.env["stock.picking"].search([('id', '=', new_picking_id)])
                                for new_delivery in search_return_delivery:
                                    if new_delivery.products_availability == "Not Available":
                                        for stock_move_package in new_delivery.move_ids_without_package:
                                            stock_move_package.quantity_done = stock_move_package.product_uom_qty

                                if search_return_delivery.state != 'done':
                                    search_return_delivery.action_set_quantities_to_reservation()
                                    search_return_delivery.button_validate()
                                    search_return_delivery.write({'dump_sequence': uni_order.code})
                        # create a credit note
                        # self.create_credit_note(uni_order)
                        lines_to_return.write({'return_status': False, 'is_returned': True})
                        uni_order.order_state = 'done'
                        uni_order.is_return = False
                        count += 1
                    else:
                        # handle the partial line return
                        move_lines = []
                        stock_return_picking_obj = self.env["stock.return.picking"]
                        # Create a dictionary to map default codes to lines
                        lines_dict = {line.product_id.default_code: line for line in lines_to_return}
                        for delivery in search_delivery:
                            lst = []
                            for move_id_package in delivery.move_ids_without_package:
                                line = lines_dict.get(move_id_package.product_id.default_code)
                                if line:
                                    reverse_transfer_line_val = (0, 0, {
                                        'product_id': move_id_package.product_id.id,
                                        'quantity': 1,
                                        'uom_id': move_id_package.product_uom.id,
                                        'move_id': move_id_package.id,
                                        'to_refund': True,
                                    })
                                    lst.append(reverse_transfer_line_val)
                                    move_lines.append(move_id_package)
                            if lst:  # if the products are not consumable then only create the reverse delivery
                                reverse_transfer_val = {
                                    'location_id': delivery.location_id.id,
                                    'picking_id': delivery.id,
                                    'product_return_moves': lst
                                }
                                stock_return_wizard_id = stock_return_picking_obj.create(reverse_transfer_val)
                                new_picking_id = stock_return_wizard_id.create_returns()
                                new_picking_id = new_picking_id.get('res_id', False)
                                if new_picking_id:
                                    search_return_delivery = self.env["stock.picking"].search(
                                        [('id', '=', new_picking_id)])
                                    for new_delivery in search_return_delivery:
                                        new_delivery.write({'shop_instance_id': uni_order.shop_instance_id.id})
                                        if new_delivery.products_availability == "Not Available":
                                            for stock_move_package in new_delivery.move_ids_without_package:
                                                stock_move_package.quantity_done = stock_move_package.product_uom_qty
                                    if search_return_delivery.state != 'done':
                                        search_return_delivery.action_set_quantities_to_reservation()
                                        search_return_delivery.button_validate()
                                        search_return_delivery.write({'dump_sequence': uni_order.code})
                        # create a credit note
                        # self.create_partial_credit_note(uni_order, lines_dict)
                        lines_to_return.write({'return_status': False, 'is_returned': True})
                        uni_order.order_state = 'done'
                        uni_order.is_return = False
                        count += 1

        except Exception as e:
            self.generate_exception_log(message=e, start_date=fields.Datetime.now(),
                                        operation_performed='Return Order Creation',
                                        end_date=fields.Datetime.now(), count=1, state='exception')

    # def create_credit_note(self, order):
    #     if not order.sales_channel_id.is_no_invoice:
    #         sale_order = order.name
    #         search_invoice = self.env["account.move"].search([('invoice_origin', '=', sale_order.name),
    #                                                           ('move_type', '=', 'out_invoice')])
    #         invoice_no = order.return_invoice_no
    #         account_move_reversal_obj = self.env["account.move.reversal"]
    #         invoice_val = {
    #             'refund_method': 'cancel',
    #             'date_mode': 'entry',
    #             'journal_id': search_invoice.journal_id.id,
    #             'move_ids': [(4, search_invoice.id)]
    #         }
    #         account_move_reverse_wizard_id = account_move_reversal_obj.create(invoice_val)
    #         data = account_move_reverse_wizard_id.reverse_moves()
    #         search_credit_note = self.env["account.move"].search([('id', '=', data['res_id'])])
    #         if invoice_no:
    #             search_credit_note.write({'payment_reference': invoice_no, 'dump_sequence': order.code})
    #             return True
    #         return False

    # def create_partial_credit_note(self, order, lines_to_return):
    #     """ Create a partial credit note for the returned items """
    #     if not order.sales_channel_id.is_no_invoice:
    #         sale_order = order.name
    #         credit_note_no = order.return_invoice_no
    #         search_invoice = self.env["account.move"].search([('invoice_origin', '=', sale_order.name),
    #                                                           ('move_type', '=', 'out_invoice')])
    #         # search_invoice.write("name")
    #         account_move_reversal_obj = self.env["account.move.reversal"]
    #         # in this invoice replace the invoice line with only the refundable products
    #         invoice_val = {
    #             'refund_method': 'refund',
    #             'date_mode': 'entry',
    #             'journal_id': search_invoice.journal_id.id,
    #             'move_ids': [(4, search_invoice.id)]
    #         }
    #         account_move_reverse_wizard_id = account_move_reversal_obj.create(invoice_val)
    #         data = account_move_reverse_wizard_id.reverse_moves()
    #         search_credit_note = self.env["account.move"].search([('id', '=', data['res_id'])])
    #         # create the credit note lines
    #         lines_to_refund = list()
    #         for move_line in search_credit_note.invoice_line_ids:
    #             line = lines_to_return.get(move_line.product_id.default_code)
    #             if line:
    #                 lines_to_refund.append(move_line.id)
    #                 move_line.quantity = 1
    #         search_credit_note.write({'invoice_line_ids': [(6, 0, lines_to_refund)]})
    #         if credit_note_no:
    #             search_credit_note.write({'payment_reference': credit_note_no, 'dump_sequence': order.code})
    #             search_credit_note.action_post()
    #             journal_id = search_invoice.sales_channel_id.prepaid_holding_journal_id if not order.cod \
    #                 else search_invoice.sales_channel_id.cod_holding_journal_id
    #             self.action_create_payment_entries_partial_line(invoice_id=search_credit_note,
    #                                                             journal_id=journal_id)
    #             return True

    # def action_create_payment_entries_partial_line(self, invoice_id, journal_id):
    #     search_payment_method = self.env["account.payment.method"].search([('name', '=', 'Manual')], limit=1)
    #     search_payment_method_line = self.env["account.payment.method.line"].search([('payment_method_id', '=',
    #                                                                                   search_payment_method.id),
    #                                                                                  ('journal_id', '=',
    #                                                                                   journal_id.id)]
    #                                                                                 )
    #
    #     payment_obj = self.env["account.payment.register"]
    #
    #     acc_type = 'asset_receivable' if invoice_id.move_type == 'out_refund' else 'liability_payable'
    #     payment_move_line = invoice_id.line_ids.filtered(lambda x: x.account_id.account_type == acc_type)
    #
    #     payment_id = payment_obj.with_context({'active_model': 'account.move',
    #                                            'active_ids': invoice_id.ids}).create({'journal_id': journal_id.id,
    #                                                                                   'payment_method_line_id': search_payment_method_line.id,
    #                                                                                   'payment_type': 'outbound',
    #                                                                                   'line_ids': [(4, line.id) for
    #                                                                                                line in
    #                                                                                                payment_move_line],
    #                                                                                   })
    #     payment_id._create_payments()
    #     return payment_id

    def sync_odoo_inventory(self):
        """ Sync the inventory of the products from the shop instance to the Odoo """
        start_date = fields.Datetime.now()
        count = 0
        shop_instances = self.env['shop.instance'].search([])
        for instance in shop_instances:
            try:
                parent_location_id = self.env['stock.location'].search([('name', '=', 'BHW')], limit=1)
                location_id = self.env['stock.location'].search(
                    [('name', '=', 'Stock'), ('location_id', '=', parent_location_id.id)], limit=1)
                stock_quant = self.env['stock.quant'].search([('location_id', '=', location_id.id)])
                inventory_adjustment = [
                    {
                        "itemSKU": quant.product_id.default_code,
                        "quantity": quant.available_quantity,
                        "shelfCode": "DEFAULT",
                        "inventoryType": "GOOD_INVENTORY",
                        "adjustmentType": "REPLACE",
                        "facilityCode": "playr"
                    } for quant in stock_quant if quant.available_quantity > 0 and quant.product_id.default_code
                ]
                if inventory_adjustment:
                    url = instance.shop_url + '/services/rest/v1/inventory/adjust/bulk'
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': instance.auth_bearer,
                        'Accept': 'application/json'
                    }
                    data = {
                        "inventoryAdjustments": inventory_adjustment
                    }
                    response = requests.post(url, headers=headers, data=json.dumps(data))

                    if response.status_code == 200:
                        data = response.json()
                        for line in data['inventoryAdjustmentResponses']:
                            if line['successful']:
                                instance.generate_success_log(
                                    message='Inventory Updated Successfully,For %s Product' %
                                            line['facilityInventoryAdjustment']['itemSKU'],
                                    count=line['facilityInventoryAdjustment']['quantity'],
                                    start_date=start_date,
                                    end_date=fields.Datetime.now(),
                                    state='success',
                                    operation_performed='Inventory Adjustment')
                                count += 1
                            elif line['errors']:
                                # logger.log(level=40, msg=line)
                                instance.generate_exception_log(
                                    message='Inventory Update Failed,For %s Product' %
                                            line['facilityInventoryAdjustment']['itemSKU'],
                                    start_date=start_date,
                                    end_date=fields.Datetime.now(), state='exception',
                                    operation_performed='Inventory Adjustment',
                                    error_message=json.dumps(data['errors'], indent=2) + "\n" + json.dumps(
                                        line['errors'], indent=2))
                            elif line['warnings']:
                                # logger.log(level=30, msg=data)
                                instance.generate_exception_log(
                                    message='Inventory Update Failed,For %s Product' %
                                            line['facilityInventoryAdjustment']['itemSKU'],
                                    start_date=start_date,
                                    end_date=fields.Datetime.now(), state='exception',
                                    operation_performed='Inventory Adjustment',
                                    error_message=json.dumps(data['errors'], indent=2) + "\n" + json.dumps(
                                        line['errors'], indent=2))
                            else:
                                # logger.log(level=30, msg=data)
                                instance.generate_exception_log(
                                    message='Inventory Update Failed,For %s Product' %
                                            line['facilityInventoryAdjustment']['itemSKU'],
                                    start_date=start_date,
                                    end_date=fields.Datetime.now(), state='exception',
                                    operation_performed='Inventory Adjustment',
                                    error_message=json.dumps(data['errors'], indent=2) + "\n" + json.dumps(
                                        line['errors'], indent=2))
                    else:
                        raise
            except TypeError as e:
                instance.generate_exception_log(message="Your Token Has Probably Expired!",
                                                start_date=fields.Datetime.now(),
                                                operation_performed='Inventory Sync',
                                                end_date=fields.Datetime.now(), count=1, state='exception')
                pass
            except Exception as e:
                response = response.json()
                instance.generate_exception_log(message=response['errors'][0]['message'],
                                                start_date=fields.Datetime.now(),
                                                operation_performed='Inventory Sync',
                                                end_date=fields.Datetime.now(), count=1, state='exception',
                                                error_message=json.dumps(response, indent=2))
                pass

    @staticmethod
    def has_exception(dictionary_list):
        """
        Check if any dictionary in the list has the 'exception' key set to True.

        Args:
            dictionary_list (list): List of dictionaries.

        Returns:
            bool: True if any dictionary has 'exception' set to True, False otherwise.
        """
        for item in dictionary_list:
            if item[2].get('status') is True:
                return True
        return False

    # cron jobs

    def generate_auth_token(self):
        get_instance_ids = self.search([])
        for instance_id in get_instance_ids:
            instance_id.generate_token()

    def get_unicomm_orders(self):
        get_instance_ids = self.search([])
        for instance_id in get_instance_ids:
            instance_id.get_orders()

    def create_unicomm_sales(self):
        get_instance_ids = self.search([])
        for instance_id in get_instance_ids:
            instance_id.create_sales()

    def create_unicomm_returns(self):
        get_instance_ids = self.search([])
        for instance_id in get_instance_ids:
            instance_id.create_returns_sales()

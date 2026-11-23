from odoo import models, fields, api, _
import json
import requests

from odoo.exceptions import UserError


class FetchMissingOrders(models.TransientModel):
    _name = 'fetch.missing.orders'
    _description = 'Fetch Missing Unicommerce Orders'

    shop_instance_id = fields.Many2one('shop.instance', string='Shop Instance')
    facility_mapping_id = fields.Many2one(
        'shop.facility.mapping',
        string='Facility / Branch',
        domain="[('shop_instance_id', '=', shop_instance_id)]",
        help="Optional. Leave empty to search across all active facilities configured on the Shop Instance.",
    )
    order_id = fields.Char(string='Order No', help="Enter the order no to fetch from Unicommerce")
    order_in_system_id = fields.Many2one("unicommerce.orders", string='Order In System ID')

    def search_order(self):
        # Check if the order already exists in the system
        existing_order = self.env['unicommerce.orders'].search(
            ['|', ('code', '=', self.order_id), ('displayOrderCode', '=', self.order_id)], limit=1)
        if existing_order:
            self.order_in_system_id = existing_order.id
            action = self.env.ref('unicommerce_integration.action_unicommerce_orders')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Order Found'),
                    'message': '%s',
                    'links': [{
                        'label': existing_order.code,
                        'url': f'#action={action.id}&id={existing_order.id}&model=unicommerce.orders&view_type=form',
                    }],
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            # If not present, fetch from Unicommerce API
            data = self.fetch_order_from_unicommerce()
            return data

    def fetch_order_from_unicommerce(self):
        base_url = (self.shop_instance_id.shop_url or "https://playr.unicommerce.com").rstrip('/')
        url = base_url + "/services/rest/v1/oms/saleorder/get"
        payload = json.dumps({
            "code": self.order_id
        })
        if self.facility_mapping_id:
            facility_codes = [self.facility_mapping_id.facility_code.strip()]
        else:
            facility_codes = self.shop_instance_id._get_active_facility_codes()

        last_error = None
        for facility_code in facility_codes:
            headers = {
                'Authorization': self.shop_instance_id.auth_bearer,
                'Facility': facility_code,
                'Content-Type': 'application/json',
            }
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                orders_list = response.json()
                if orders_list.get("errors", []):
                    last_error = orders_list.get("errors", [])[0].get("message")
                    continue
                if orders_list.get('saleOrderDTO'):
                    order = self.process_orders(orders_list['saleOrderDTO'], facility_code=facility_code)
                    if order:
                        action = self.env.ref('unicommerce_integration.action_unicommerce_orders')
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Orders Fetched'),
                                'message': '%s',
                                'links': [{
                                    'label': order.code,
                                    'url': f'#action={action.id}&id={order.id}&model=unicommerce.orders&view_type=form',
                                }],
                                'sticky': False,
                            }}
            else:
                last_error = response.text

        if last_error:
            raise UserError(_(last_error))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('No Orders Found'),
                'message': _('No orders were found in Unicommerce for the given Order ID.'),
                'sticky': False,
            }
        }

    def process_orders(self, orders_list, facility_code=False):
        # Process and create or update orders
        start_date = fields.Datetime.now()
        orders_list = [orders_list]
        orders, updated_order = self.shop_instance_id.create_orders(orders=orders_list, facility_code=facility_code)
        end_date = fields.Datetime.now()
        if orders:
            self.shop_instance_id.generate_success_log(
                message="Successfully Fetched The Orders",
                count=len(orders),
                start_date=start_date,
                end_date=end_date,
                state='success',
                operation_performed='Fetching Missing Orders'
            )
            return orders

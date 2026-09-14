from odoo import models, fields, api, _
import json
import requests

from odoo.exceptions import UserError


class FetchMissingOrders(models.TransientModel):
    _name = 'fetch.missing.orders'
    _description = 'Fetch Missing Unicommerce Orders'

    shop_instance_id = fields.Many2one('shop.instance', string='Shop Instance')
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
        url = "https://playr.unicommerce.com/services/rest/v1/oms/saleorder/get"
        payload = json.dumps({
            "code": self.order_id
        })
        headers = {
            'Authorization': self.shop_instance_id.auth_bearer,  # replace with actual token
            'Facility': 'karan',  # replace with actual facility
            'Content-Type': 'application/json',
        }

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            orders_list = response.json()
            if orders_list.get("errors", []):
                raise UserError(_(orders_list.get("errors", [])[0]["message"]))
            if orders_list:
                # Call methods to process and create orders
                order = self.process_orders(orders_list['saleOrderDTO'])
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
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('No Orders Found'),
                        'message': _('No orders were found in Unicommerce for the given Order ID.'),
                        'sticky': False,
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to fetch the order from Unicommerce.'),
                    'sticky': False,
                }
            }

    def process_orders(self, orders_list):
        # Process and create or update orders
        start_date = fields.Datetime.now()
        orders_list = [orders_list]
        orders, updated_order = self.shop_instance_id.create_orders(orders=orders_list)
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

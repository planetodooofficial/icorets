import json

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InheritPicking(models.Model):
    _inherit = 'stock.picking'

    dump_sequence = fields.Char(string='Sequence')
    shop_instance_id = fields.Many2one('shop.instance', string='Shop Instance')
    is_synced = fields.Boolean(string='Is Synced', default=False)

    def sync_inventory(self):
        if self.picking_type_code == 'incoming' and self.location_dest_id.is_sync_with_unicommerce:
            start_date = fields.Datetime.now()
            lines = self.move_ids_without_package
            inventory_adjustment = []
            # search the product and location in stock.quant and get the quantity
            for line in lines:
                quants = self.env['stock.quant'].search(
                    [('product_id', '=', line.product_id.id), ('location_id', '=', self.location_dest_id.id)])
                if quants:
                    total_available_quantity = sum(quants.mapped('available_quantity'))
                    if total_available_quantity:
                        inventory_adjustment.append(
                            {
                                "itemSKU": line.product_id.default_code,
                                "quantity": total_available_quantity,
                                "shelfCode": "DEFAULT",
                                "inventoryType": "GOOD_INVENTORY",
                                "adjustmentType": "REPLACE",
                                "facilityCode": "playr"
                            }
                        )
            url = self.shop_instance_id.shop_url + '/services/rest/v1/inventory/adjust/bulk'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.shop_instance_id.auth_bearer,
                'Accept': 'application/json'
            }
            data = {
                "inventoryAdjustments": inventory_adjustment
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            count = 0
            if response.status_code == 200:
                data = response.json()
                for line in data['inventoryAdjustmentResponses']:
                    if line['successful']:
                        self.shop_instance_id.generate_success_log(
                            message='Inventory Updated Successfully,For %s Product' %
                                    line['facilityInventoryAdjustment'][
                                        'itemSKU'],
                            start_date=start_date,
                            end_date=fields.Datetime.now(), state='success',
                            operation_performed='Inventory Adjustment')
                        count += 1
                    else:
                        raise UserError(
                            'Error in updating Unicommerce Inventory, For %s Product' %
                            line['facilityInventoryAdjustment'][
                                'itemSKU'] + "\n" + line['errors'][0]['description'])
                if count == len(inventory_adjustment):
                    self.write({'is_synced': True})
            else:
                raise UserError('Error in updating Unicommerce Inventory. \n' + response.text)
            return True
        else:
            raise UserError('This operation is not allowed for this type of picking')


class InheritStockLocation(models.Model):
    _inherit = 'stock.location'

    is_sync_with_unicommerce = fields.Boolean(string='Sync With Unicommerce ?',
                                              help='If checked, then this picking type will be synced with unicommerce')

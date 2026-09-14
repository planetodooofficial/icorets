from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import float_compare, float_round, float_is_zero

class ProductProduct(models.Model):
    _inherit = "product.product"

    def calculate_product_cogs(self):
        receipt_moves = self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('product_id.is_storable', '=', True),
            ('location_id.usage', '=', 'supplier'),
            ('date', '<=', datetime(2025, 3, 31, 23, 59, 59)),
            ('missing_valuation', '=', False),
        ], limit=3000)

        receipt_valuation_amount = 0.0

        for move in receipt_moves:
            valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)], limit=1)
            purchase_unit_price = move.purchase_line_id.price_unit if move.purchase_line_id else move.product_id.standard_price
            quantity_done = move.quantity

            expected_value = purchase_unit_price * quantity_done

            if valuation:
                if valuation.value != expected_value:
                    amount = expected_value - valuation.value
                    receipt_valuation_amount += expected_value - valuation.value
                    self._create_missing_valuation(products=move.product_id, quantity=quantity_done, new_price=purchase_unit_price, value=amount)
                    move.missing_valuation = True
            else:
                receipt_valuation_amount += expected_value
                self._create_missing_valuation(products=move.product_id, quantity=quantity_done, new_price=purchase_unit_price,
                                               value=expected_value)
                move.missing_valuation = True

        # for adjustment
        adjustment_moves = self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('product_id.is_storable', '=', True), '|',
            ('location_id.usage', '=', 'inventory'),
            ('location_dest_id.usage', '=', 'inventory'),
            ('missing_valuation', '=', False),
            ('date', '<=', datetime(2025, 3, 31, 23, 59, 59)),
        ], limit=3000)

        internal_valuation_amount = 0.0

        for move in adjustment_moves:
            valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)], limit=1)
            product_cost = move.product_id.standard_price or 0.0
            quantity_done = move.quantity
            expected_value = product_cost * quantity_done

            if valuation:
                if valuation.value != expected_value:
                    if valuation.value > 0:
                        adjustment_amt = abs(valuation.value - expected_value)
                        internal_valuation_amount += abs(valuation.value - expected_value)
                        self._create_missing_valuation(products=move.product_id, quantity=quantity_done,
                                                       new_price=0,
                                                       value=adjustment_amt)
                        move.missing_valuation = True
                    if valuation.value < 0:
                        adjustment_amt = abs(valuation.value + expected_value)
                        internal_valuation_amount += abs(valuation.value + expected_value)
                        self._create_missing_valuation(products=move.product_id, quantity=quantity_done,
                                                       new_price=0,
                                                       value=-adjustment_amt)
                        move.missing_valuation = True
            else:
                internal_valuation_amount += expected_value
                move.missing_valuation = True
                self._create_missing_valuation(products=move.product_id, quantity=quantity_done, new_price=product_cost,
                                               value=expected_value)

        # Delivery moves
        delivery_moves = self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('product_id.is_storable', '=', True),
            ('location_dest_id.usage', '=', 'customer'),
            ('date', '<=', datetime(2025, 3, 31, 23, 59, 59)),
            ('missing_valuation', '=', False),
        ], limit=3000)

        delivery_valuation_amount = 0.0

        for move in delivery_moves:
            valuation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)], limit=1)
            product_cost = move.product_id.standard_price or 0.0
            quantity_done = move.quantity
            expected_value = product_cost * quantity_done

            if valuation:
                if valuation.value != expected_value:
                    amount = valuation.value + expected_value
                    delivery_valuation_amount += valuation.value + expected_value
                    self._create_missing_valuation(products=move.product_id, quantity=quantity_done, new_price=product_cost,
                                                   value=-1 * abs(amount))
                    move.missing_valuation = True
            else:
                delivery_valuation_amount += expected_value
                self._create_missing_valuation(products=move.product_id, quantity=quantity_done, new_price=0,
                                               value=-expected_value)
                move.missing_valuation = True

    def _create_missing_valuation(self, products, new_price, quantity, value):
        svl_vals_list = []
        company_id = self.env.company
        for product in products:
            if company_id.currency_id.is_zero(value):
                continue

            svl_vals = {
                'company_id': company_id.id,
                'product_id': product.id,
                'missing_valuation': True,
                'description': _('Product Missing Valuation Amount'),
                'value': value,
                'unit_cost': 0.0,
                'quantity': quantity,
            }
            svl_vals_list.append(svl_vals)
        stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

        # Handle account moves.
        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in products}
        am_vals_list = []
        for stock_valuation_layer in stock_valuation_layers:
            product = stock_valuation_layer.product_id
            value = stock_valuation_layer.value

            if not product.is_storable or product.valuation != 'real_time':
                continue

            if value < 0:
                debit_account_id = product_accounts[product.id]['stock_output'].id
                credit_account_id = product_accounts[product.id]['stock_valuation'].id
            else:
                debit_account_id = product_accounts[product.id]['stock_valuation'].id
                credit_account_id = product_accounts[product.id]['stock_input'].id

            move_date = self._context.get('force_period_date', fields.Date.context_today(self))
            move_vals = {
                'date': move_date,
                'journal_id': product_accounts[product.id]['stock_journal'].id,
                'company_id': company_id.id,
                'ref': product.default_code,
                'stock_valuation_layer_ids': [(6, None, [stock_valuation_layer.id])],
                'move_type': 'entry',
                'missing_valuation': True,
                'line_ids': [(0, 0, {
                    'name': _(
                        '%(user)s changed cost%(new_price)s - %(product)s',
                        user=self.env.user.name,
                        new_price=0.0,
                        product=product.display_name
                    ),
                    'account_id': debit_account_id,
                    'debit': abs(value),
                    'credit': 0,
                    'product_id': product.id,
                }), (0, 0, {
                    'name': _(
                        '%(user)s changed cost %(new_price)s - %(product)s',
                        user=self.env.user.name,
                        new_price=0.0,
                        product=product.display_name
                    ),
                    'account_id': credit_account_id,
                    'debit': 0,
                    'credit': abs(value),
                    'product_id': product.id,
                })],
            }
            am_vals_list.append(move_vals)

        account_moves = self.env['account.move'].sudo().create(am_vals_list)
        if account_moves:
            account_moves.action_post()


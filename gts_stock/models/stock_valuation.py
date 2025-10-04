from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    missing_valuation = fields.Boolean(string="Missing Valuation", default=False)

    def update_date(self, date=None):
        """Update valuation layer date and related journal entry date (SQL)"""
        if not date:
            raise UserError(_("Please provide a valid date."))

        try:
            new_date = datetime.strptime(date, "%d/%m/%Y").date()
        except Exception:
            raise UserError(_("Date format should be DD/MM/YYYY (e.g., 01/04/2025)."))

        updated_layers, updated_moves = 0, 0

        for layer in self:
            # Update stock valuation layer
            self.env.cr.execute(
                """
                UPDATE stock_valuation_layer
                SET create_date = %s, write_date = now()
                WHERE id = %s
                """,
                (new_date, layer.id),
            )
            updated_layers += 1

            # Update related account move + move lines
            if layer.account_move_id:
                self.env.cr.execute(
                    """
                    UPDATE account_move
                    SET date = %s, write_date = now()
                    WHERE id = %s
                    """,
                    (new_date, layer.account_move_id.id),
                )
                updated_moves += self.env.cr.rowcount

                self.env.cr.execute(
                    """
                    UPDATE account_move_line
                    SET date = %s, write_date = now()
                    WHERE move_id = %s
                    """,
                    (new_date, layer.account_move_id.id),
                )

        # Commit updates (important for SQL queries)
        self.env.cr.commit()

        return {
            "effect": {
                "fadeout": "slow",
                "message": f"{updated_layers} valuation layers and {updated_moves} journal entries updated (SQL).",
                "type": "rainbow_man",
            }
        }

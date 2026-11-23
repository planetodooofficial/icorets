from odoo import models, fields, api, _


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    unicommerce_order_id = fields.Many2one('unicommerce.orders', string='Unicommerce Order Id')
    shop_instance_id = fields.Many2one('shop.instance', string='Shop Instance')
    sales_channel_id = fields.Many2one('shop.sales.channel', string='Sales Channel')
    dump_sequence = fields.Char(string='Sequence')

    def get_fiscal_position(self):
        """For Unicommerce branch orders using a common parent journal, resolve seller state
        from the order's branch (company_id / gstin_id / warehouse) and look up fiscal positions
        across both the branch and its parent companies."""
        if not self.unicommerce_order_id:
            return super().get_fiscal_position()

        buyer_state = self.partner_shipping_id.state_id or self.partner_invoice_id.state_id or self.partner_id.state_id
        buyer_country = self.partner_shipping_id.country_id or self.partner_invoice_id.country_id or self.partner_id.country_id
        seller_state = (
            self.company_id.state_id
            or self.company_id.partner_id.state_id
            or (self.gstin_id.state_id if self.gstin_id else False)
            or (self.warehouse_id.partner_id.state_id if self.warehouse_id else False)
        )
        company_ids = self.company_id.parent_ids.ids + [False]
        fpos_obj = self.env['account.fiscal.position'].sudo()
        fpos = None

        if buyer_country and buyer_country.code != 'IN':
            fpos = fpos_obj.search([
                ('company_id', 'in', company_ids),
                ('name', '=ilike', 'Export%'),
            ], limit=1)

        is_intra = bool(seller_state and buyer_state and seller_state.id == buyer_state.id)
        if not fpos:
            if is_intra:
                if seller_state and seller_state.code:
                    fpos = fpos_obj.search([
                        ('company_id', 'in', company_ids),
                        ('name', '=ilike', f'{seller_state.code}-Intra%'),
                    ], limit=1)
                if not fpos:
                    fpos = fpos_obj.search([
                        ('company_id', 'in', company_ids),
                        ('name', '=ilike', 'Intra%'),
                    ], limit=1)
            else:
                if seller_state and seller_state.code:
                    fpos = fpos_obj.search([
                        ('company_id', 'in', company_ids),
                        ('name', '=ilike', f'{seller_state.code}-Inter%'),
                    ], limit=1)
                if not fpos:
                    fpos = fpos_obj.search([
                        ('company_id', 'in', company_ids),
                        ('name', '=ilike', 'Inter%'),
                    ], limit=1)

        if not fpos:
            fpos = fpos_obj.with_company(self.company_id)._get_fiscal_position(
                self.partner_id, self.partner_shipping_id
            )
        return fpos.id if fpos else False

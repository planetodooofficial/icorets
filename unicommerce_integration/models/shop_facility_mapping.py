from odoo import api, fields, models, _


class ShopFacilityMapping(models.Model):
    _name = 'shop.facility.mapping'
    _description = 'Unicommerce Facility to Branch Mapping'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Facility Name', tracking=True)
    facility_code = fields.Char(
        string='Facility Code',
        required=True,
        tracking=True,
        help="Unicommerce Facility Code (e.g. playR_Delhi, karan). Used in API Facility header and matched against order line facilityCode.",
    )
    shop_instance_id = fields.Many2one(
        'shop.instance',
        string='Shop Instance',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Branch / Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        help="Target Odoo Branch (Company) in which Sale Orders, Deliveries, Invoices, and Returns will be created.",
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        domain="[('company_id', '=', company_id)]",
        tracking=True,
        help="Warehouse belonging to the selected branch.",
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Stock Location',
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        tracking=True,
        help="Source Stock Location used for orders and inventory sync for this facility. Defaults to the Warehouse's Stock location.",
    )
    sale_journal_id = fields.Many2one(
        'account.journal',
        string='Sales Journal',
        domain="[('type', '=', 'sale')]",
        tracking=True,
        help="Sales Journal used on Sale Orders and Invoices for this facility. If left empty, falls back to the Sales Channel's journal.",
    )
    active = fields.Boolean(string='Active', default=True, tracking=True)

    _facility_instance_uniq = models.Constraint(
        'unique(shop_instance_id, facility_code)',
        'Facility Code must be unique per Shop Instance!',
    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            if rec.company_id:
                warehouse = self.env['stock.warehouse'].sudo().search(
                    [('company_id', '=', rec.company_id.id)], limit=1
                )
                rec.warehouse_id = warehouse.id if warehouse else False
                rec.location_id = warehouse.lot_stock_id.id if warehouse else False
            else:
                rec.warehouse_id = False
                rec.location_id = False

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        for rec in self:
            if rec.warehouse_id and rec.warehouse_id.lot_stock_id:
                rec.location_id = rec.warehouse_id.lot_stock_id.id

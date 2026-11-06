# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this warehouse company ownership was automatically assigned/transferred based on GST code matching.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)

    def write(self, vals):
        """Allow updating company_id when called in company assignment context."""
        if self.env.context.get("allow_warehouse_company_update") and "company_id" in vals:
            company_id = vals.pop("company_id")
            if vals:
                super().write(vals)
            from odoo.addons.stock.models.stock_warehouse import StockWarehouse as CoreStockWarehouse
            return super(CoreStockWarehouse, self).write({"company_id": company_id})
        return super().write(vals)

    def _get_partner_gst_code(self):
        """Read and format the GST code from warehouse contact (partner_id.gst_code)."""
        self.ensure_one()
        partner = self.partner_id.sudo() if self.partner_id else False
        if not partner:
            return ""
        code = getattr(partner, "gst_code", False)
        if not code and "gst_code" in partner._fields:
            code = partner.gst_code
        return (code or "").strip().upper()

    def _find_destination_branch_by_gst(self):
        """Find matching branch company within the parent hierarchy based on GST code."""
        self.ensure_one()
        self = self.sudo()
        code = self._get_partner_gst_code()
        if not code:
            partner = self.partner_id.sudo() if self.partner_id else False
            raise UserError(
                _(
                    "The warehouse partner '%(partner)s' does not have a GST code configured. "
                    "Set 'partner_id.gst_code' before matching.",
                    partner=partner.display_name if partner else _("Undefined"),
                )
            )

        # Resolve the root parent company in the multi-company hierarchy
        company = self.company_id.sudo()
        root = company.root_id if hasattr(company, "root_id") and company.root_id else False
        if not root:
            root = company
            while root.parent_id:
                root = root.parent_id.sudo()

        branches = self.env["res.company"].sudo().search([
            ("gst_code_matching_com", "=ilike", code),
            ("id", "child_of", root.id),
        ])

        if not branches:
            raise UserError(
                _(
                    "No branch company was found under parent company '%(parent)s' with GST matching code '%(code)s'.",
                    parent=root.display_name,
                    code=code,
                )
            )

        if len(branches) > 1:
            raise UserError(
                _(
                    "Multiple branch companies (%(branches)s) match GST code '%(code)s' under '%(parent)s'. "
                    "GST matching codes must be unique within the company hierarchy.",
                    branches=", ".join(branches.mapped("display_name")),
                    code=code,
                    parent=root.display_name,
                )
            )

        destination = branches
        is_already_matched = destination.id == self.company_id.id
        return destination, is_already_matched

    def _get_exclusive_configuration_records_sql(self):
        """Inspect and return configuration record IDs belonging exclusively to this warehouse via direct SQL.
        Bypasses any multi-company record rule restrictions.
        """
        self.ensure_one()
        cr = self.env.cr

        # 1. Locations: recursive CTE for warehouse root locations and all child locations
        cr.execute("""
            WITH RECURSIVE loc_tree AS (
                SELECT id FROM stock_location WHERE id IN (
                    SELECT view_location_id FROM stock_warehouse WHERE id = %(wh_id)s
                    UNION SELECT lot_stock_id FROM stock_warehouse WHERE id = %(wh_id)s
                    UNION SELECT wh_input_stock_loc_id FROM stock_warehouse WHERE id = %(wh_id)s
                    UNION SELECT wh_qc_stock_loc_id FROM stock_warehouse WHERE id = %(wh_id)s
                    UNION SELECT wh_output_stock_loc_id FROM stock_warehouse WHERE id = %(wh_id)s
                    UNION SELECT wh_pack_stock_loc_id FROM stock_warehouse WHERE id = %(wh_id)s
                )
                UNION
                SELECT c.id FROM stock_location c JOIN loc_tree p ON c.location_id = p.id
            )
            SELECT DISTINCT id FROM loc_tree WHERE id IS NOT NULL;
        """, {"wh_id": self.id})
        loc_ids = [r[0] for r in cr.fetchall()]

        # 2. Operation Types (stock.picking.type) & Sequences
        cr.execute("""
            SELECT id, sequence_id FROM stock_picking_type WHERE warehouse_id = %(wh_id)s;
        """, {"wh_id": self.id})
        pt_rows = cr.fetchall()
        pt_ids = [r[0] for r in pt_rows]
        seq_ids = [r[1] for r in pt_rows if r[1]]

        # 3. Stock Rules (stock.rule)
        cr.execute("""
            SELECT id FROM stock_rule 
            WHERE warehouse_id = %(wh_id)s 
               OR (picking_type_id IS NOT NULL AND picking_type_id IN %(pt_ids)s);
        """, {"wh_id": self.id, "pt_ids": tuple(pt_ids) if pt_ids else (0,)})
        rule_ids = [r[0] for r in cr.fetchall()]

        # 4. Reordering Rules (stock.warehouse.orderpoint)
        orderpoint_ids = []
        try:
            cr.execute("SELECT id FROM stock_warehouse_orderpoint WHERE warehouse_id = %(wh_id)s;", {"wh_id": self.id})
            orderpoint_ids = [r[0] for r in cr.fetchall()]
        except Exception:
            pass

        return loc_ids, pt_ids, seq_ids, rule_ids, orderpoint_ids

    def _get_exclusive_configuration_records(self):
        """Inspect and return configuration records belonging exclusively to this warehouse."""
        self.ensure_one()
        self = self.sudo()
        loc_ids, pt_ids, seq_ids, rule_ids, orderpoint_ids = self._get_exclusive_configuration_records_sql()

        Location = self.env["stock.location"].sudo()
        PickingType = self.env["stock.picking.type"].sudo()
        Rule = self.env["stock.rule"].sudo()
        Orderpoint = (
            self.env["stock.warehouse.orderpoint"].sudo()
            if "stock.warehouse.orderpoint" in self.env
            else (self.env["stock.reorder.point"].sudo() if "stock.reorder.point" in self.env else False)
        )

        locations = Location.browse(loc_ids)
        picking_types = PickingType.browse(pt_ids)
        rules = Rule.browse(rule_ids)
        orderpoints = Orderpoint.browse(orderpoint_ids) if Orderpoint else False

        return locations, picking_types, rules, orderpoints

    def _validate_safe_company_reassignment(self, locations, allow_history=True):
        """Validate safety constraints via direct SQL queries."""
        self.ensure_one()
        cr = self.env.cr

        # If strict safety mode is requested and history exists, block
        if not allow_history:
            cr.execute("""
                SELECT COUNT(*) FROM stock_picking p
                JOIN stock_picking_type pt ON p.picking_type_id = pt.id
                WHERE pt.warehouse_id = %s AND p.state = 'done';
            """, [self.id])
            done_pickings = cr.fetchone()[0]

            cr.execute("""
                SELECT COUNT(*) FROM stock_move 
                WHERE warehouse_id = %s AND state = 'done';
            """, [self.id])
            done_moves = cr.fetchone()[0]

            if done_pickings or done_moves:
                raise UserError(
                    _(
                        "Warehouse '%(wh)s' has %(pickings)s completed stock pickings and %(moves)s completed moves. "
                        "Reassignment blocked in strict mode.",
                        wh=self.display_name,
                        pickings=done_pickings,
                        moves=done_moves,
                    )
                )

        return ""

    def _prepare_gst_company_match(self, allow_history=True):
        """Validate warehouse match and return destination company and exclusive configuration records."""
        self.ensure_one()
        self = self.sudo()
        destination, is_already_matched = self._find_destination_branch_by_gst()
        if is_already_matched:
            return destination, is_already_matched, self.env["stock.location"].sudo(), self.env["stock.picking.type"].sudo(), self.env["stock.rule"].sudo(), False, _("Already matched")

        locations, picking_types, rules, orderpoints = self._get_exclusive_configuration_records()
        history_summary = self._validate_safe_company_reassignment(locations, allow_history=allow_history)

        return destination, is_already_matched, locations, picking_types, rules, orderpoints, history_summary

    def _reassign_warehouse_to_company(self, destination):
        """Atomically reassign warehouse, locations, operation types, sequences, routes,
        quants, and rules to destination company via direct SQL queries and cache invalidation.
        Strictly executes direct SQL to avoid any multi-company record rule restrictions.
        Marks is_company_transferred = TRUE on all modified tables for past and future tracking.
        Never deletes any record or relation.
        """
        self.ensure_one()
        self = self.sudo()
        cr = self.env.cr
        dest_id = destination.id

        # Ensure column exists on all 7 target tables
        for table in (
            "stock_warehouse",
            "stock_location",
            "stock_picking_type",
            "stock_rule",
            "stock_warehouse_orderpoint",
            "stock_route",
            "stock_quant",
        ):
            try:
                cr.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS is_company_transferred BOOLEAN DEFAULT FALSE")
            except Exception:
                pass

        loc_ids, pt_ids, seq_ids, rule_ids, orderpoint_ids = self._get_exclusive_configuration_records_sql()

        # 1. Locations: view_location_id and ALL descendants
        if loc_ids:
            cr.execute(
                "UPDATE stock_location SET company_id = %s, is_company_transferred = TRUE WHERE id IN %s",
                [dest_id, tuple(loc_ids)],
            )
            # Keep active inventory quants aligned with their locations
            cr.execute(
                "UPDATE stock_quant SET company_id = %s, is_company_transferred = TRUE WHERE location_id IN %s",
                [dest_id, tuple(loc_ids)],
            )

        # 2. Operation Types (stock.picking.type)
        if pt_ids:
            cr.execute(
                "UPDATE stock_picking_type SET company_id = %s, is_company_transferred = TRUE WHERE id IN %s",
                [dest_id, tuple(pt_ids)],
            )

        # 3. Stock Rules
        if rule_ids:
            cr.execute(
                "UPDATE stock_rule SET company_id = %s, is_company_transferred = TRUE WHERE id IN %s",
                [dest_id, tuple(rule_ids)],
            )

        # 4. Reordering Rules
        if orderpoint_ids:
            cr.execute(
                "UPDATE stock_warehouse_orderpoint SET company_id = %s, is_company_transferred = TRUE WHERE id IN %s",
                [dest_id, tuple(orderpoint_ids)],
            )

        # 5. Warehouse Routes & Rules (Only update company_id, DO NOT delete any record or relation)
        cr.execute("""
            SELECT rw.route_id FROM stock_route_warehouse rw
            WHERE rw.warehouse_id = %(wh_id)s
            GROUP BY rw.route_id
            HAVING (SELECT COUNT(*) FROM stock_route_warehouse WHERE route_id = rw.route_id) <= 1
        """, {"wh_id": self.id})
        exclusive_route_ids = [r[0] for r in cr.fetchall()]
        if exclusive_route_ids:
            cr.execute(
                "UPDATE stock_route SET company_id = %s, is_company_transferred = TRUE WHERE id IN %s",
                [dest_id, tuple(exclusive_route_ids)],
            )
            cr.execute(
                "UPDATE stock_rule SET company_id = %s, is_company_transferred = TRUE WHERE route_id IN %s",
                [dest_id, tuple(exclusive_route_ids)],
            )

        # 6. Warehouse record itself
        cr.execute(
            "UPDATE stock_warehouse SET company_id = %s, is_company_transferred = TRUE WHERE id = %s",
            [dest_id, self.id],
        )

        # 7. Complete cache invalidation across the ORM
        self.env.invalidate_all()

    def _create_single_assignment_log(
        self,
        status,
        current_com,
        destination,
        code,
        message,
        history_summary,
        loc_count=0,
        pt_count=0,
        r_count=0,
        op_count=0,
    ):
        """Helper to create persistent tracking log for single warehouse assignments."""
        try:
            return self.env["warehouse.gst.assignment.log"].sudo().create({
                "source": "single",
                "total_processed": 1,
                "total_success": 1 if status == "success" else 0,
                "total_already_matched": 1 if status == "already_matched" else 0,
                "total_skipped": 1 if status == "skipped" else 0,
                "total_failed": 1 if status == "failed" else 0,
                "summary": message,
                "line_ids": [(0, 0, {
                    "warehouse_id": self.id,
                    "partner_id": self.partner_id.id if self.partner_id else False,
                    "gst_code": code,
                    "src_company_id": current_com.id if current_com else False,
                    "dest_company_id": destination.id if destination else False,
                    "status": status,
                    "message": message,
                    "history_summary": history_summary,
                    "locations_count": loc_count,
                    "picking_types_count": pt_count,
                    "rules_count": r_count,
                    "orderpoints_count": op_count,
                })],
            })
        except Exception:
            return False

    def action_match_company_by_gst_code(self, allow_history=True):
        """Button action on warehouse form to match and assign branch company by GST code."""
        self.ensure_one()
        self = self.sudo()
        current_com = self.company_id.sudo()
        code = self._get_partner_gst_code()

        try:
            (
                destination,
                is_already_matched,
                locations,
                picking_types,
                rules,
                orderpoints,
                history_summary,
            ) = self._prepare_gst_company_match(allow_history=allow_history)
        except Exception as exc:
            self._create_single_assignment_log(
                status="failed",
                current_com=current_com,
                destination=False,
                code=code,
                message=str(exc),
                history_summary=_("Failed: %s") % str(exc),
            )
            raise

        if is_already_matched:
            msg = _(
                "Warehouse '%(wh)s' is already assigned to '%(company)s' (GST Code: %(code)s).",
                wh=self.display_name,
                company=current_com.display_name,
                code=code,
            )
            self._create_single_assignment_log(
                status="already_matched",
                current_com=current_com,
                destination=destination,
                code=code,
                message=msg,
                history_summary=_("Already matched"),
            )
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Already Matched"),
                    "message": msg,
                    "type": "info",
                    "sticky": False,
                },
            }

        # Perform atomic reassignment inside a savepoint
        with self.env.cr.savepoint():
            self._reassign_warehouse_to_company(destination)

        loc_count = len(locations)
        pt_count = len(picking_types)
        r_count = len(rules)
        op_count = len(orderpoints) if orderpoints else 0
        success_msg = _(
            "Warehouse '%(wh)s' and %(loc)s locations, %(types)s operation types, "
            "%(rules)s stock rules, and %(op)s reordering rules were assigned to '%(company)s'.",
            wh=self.display_name,
            loc=loc_count,
            types=pt_count,
            rules=r_count,
            op=op_count,
            company=destination.display_name,
        )

        self._create_single_assignment_log(
            status="success",
            current_com=current_com,
            destination=destination,
            code=code,
            message=success_msg,
            history_summary=history_summary,
            loc_count=loc_count,
            pt_count=pt_count,
            r_count=r_count,
            op_count=op_count,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Company Assigned Successfully"),
                "message": success_msg,
                "type": "success",
                "sticky": False,
            },
        }

    def action_open_gst_company_match_wizard(self):
        """Open batch processing wizard for selected warehouses."""
        return {
            "type": "ir.actions.act_window",
            "name": _("Mass Match Company by GST Code"),
            "res_model": "warehouse.gst.company.match.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_warehouse_ids": [(6, 0, self.ids)],
                "default_preserve_history": True,
            },
        }


class StockLocation(models.Model):
    _inherit = "stock.location"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this location company ownership was automatically assigned/transferred based on GST code matching.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockRoute(models.Model):
    _inherit = "stock.route"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this route company ownership was automatically assigned/transferred based on GST code matching.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this operation type company ownership was automatically assigned/transferred based on GST code matching.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockRule(models.Model):
    _inherit = "stock.rule"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this stock rule company ownership was automatically assigned/transferred based on GST code matching.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this reordering rule company ownership was automatically assigned/transferred based on GST code matching.",
    )


class StockQuant(models.Model):
    _inherit = "stock.quant"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this inventory quant company ownership was automatically assigned/transferred based on GST code matching.",
    )

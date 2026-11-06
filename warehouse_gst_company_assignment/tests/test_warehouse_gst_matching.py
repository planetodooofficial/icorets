# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestWarehouseGstMatching(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Parent Company
        cls.parent_company = cls.env["res.company"].create({
            "name": "Main Corporate Parent",
        })

        # Branches under parent company
        cls.branch_delhi = cls.env["res.company"].create({
            "name": "Delhi Branch",
            "parent_id": cls.parent_company.id,
            "gst_code_matching_com": "DL",
        })
        cls.branch_chennai = cls.env["res.company"].create({
            "name": "Chennai Branch",
            "parent_id": cls.parent_company.id,
            "gst_code_matching_com": "CH",
        })
        cls.branch_haryana = cls.env["res.company"].create({
            "name": "Haryana Branch",
            "parent_id": cls.parent_company.id,
            "gst_code_matching_com": "HR",
        })

        # Separate parent company (unrelated hierarchy)
        cls.other_parent = cls.env["res.company"].create({
            "name": "Unrelated Parent Corp",
        })
        cls.other_branch_delhi = cls.env["res.company"].create({
            "name": "Other Delhi Branch",
            "parent_id": cls.other_parent.id,
            "gst_code_matching_com": "DL",
        })

        # Warehouse partners
        cls.partner_delhi = cls.env["res.partner"].create({
            "name": "Delhi Warehouse Contact",
            "gst_code": "DL",
            "company_id": cls.parent_company.id,
        })
        cls.partner_haryana = cls.env["res.partner"].create({
            "name": "Haryana Warehouse Contact",
            "gst_code": "HR",
            "company_id": cls.parent_company.id,
        })
        cls.partner_no_gst = cls.env["res.partner"].create({
            "name": "No GST Contact",
            "company_id": cls.parent_company.id,
        })
        cls.partner_unknown_gst = cls.env["res.partner"].create({
            "name": "Unknown State Contact",
            "gst_code": "ZZ",
            "company_id": cls.parent_company.id,
        })

        # Create a test warehouse under Main Corporate Parent
        cls.warehouse_delhi = cls.env["stock.warehouse"].create({
            "name": "Delhi WH",
            "code": "DWH",
            "company_id": cls.parent_company.id,
            "partner_id": cls.partner_delhi.id,
        })

    def test_01_company_gst_code_uniqueness(self):
        """Test unique constraint of gst_code_matching_com within the same hierarchy."""
        with self.assertRaises(ValidationError):
            self.env["res.company"].create({
                "name": "Duplicate Delhi Branch",
                "parent_id": self.parent_company.id,
                "gst_code_matching_com": "dl",  # Case-insensitive duplicate
            })

    def test_02_dynamic_branch_matching(self):
        """Test matching partner_id.gst_code with company.gst_code_matching_com."""
        destination, is_already_matched = self.warehouse_delhi._find_destination_branch_by_gst()
        self.assertEqual(destination.id, self.branch_delhi.id)
        self.assertFalse(is_already_matched)

    def test_03_hierarchy_restriction(self):
        """Ensure matching resolves exclusively within the warehouse's parent company hierarchy."""
        destination, is_matched = self.warehouse_delhi._find_destination_branch_by_gst()
        self.assertEqual(destination.id, self.branch_delhi.id)
        self.assertNotEqual(destination.id, self.other_branch_delhi.id)

    def test_04_missing_or_invalid_gst_code(self):
        """Validation fails if partner GST code is empty or no branch matches."""
        wh_no_gst = self.env["stock.warehouse"].create({
            "name": "No GST WH",
            "code": "NGW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_no_gst.id,
        })
        with self.assertRaises(UserError):
            wh_no_gst._find_destination_branch_by_gst()

        wh_unknown_gst = self.env["stock.warehouse"].create({
            "name": "Unknown GST WH",
            "code": "UGW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_unknown_gst.id,
        })
        with self.assertRaises(UserError):
            wh_unknown_gst._find_destination_branch_by_gst()

    def test_05_already_matched_warehouse(self):
        """Already assigned warehouse is recognized and skipped safely."""
        wh_already = self.env["stock.warehouse"].create({
            "name": "Already Haryana WH",
            "code": "AHW",
            "company_id": self.branch_haryana.id,
            "partner_id": self.partner_haryana.id,
        })
        destination, is_already_matched = wh_already._find_destination_branch_by_gst()
        self.assertEqual(destination.id, self.branch_haryana.id)
        self.assertTrue(is_already_matched)

    def test_06_configuration_records_reassignment(self):
        """Verify warehouse and its exclusive locations, operation types, and rules are reassigned."""
        locations, picking_types, rules, orderpoints = self.warehouse_delhi._get_exclusive_configuration_records()
        self.assertTrue(bool(locations))
        self.assertTrue(bool(picking_types))

        # Perform match action
        self.warehouse_delhi.action_match_company_by_gst_code()

        # Warehouse company updated
        self.assertEqual(self.warehouse_delhi.company_id.id, self.branch_delhi.id)

        # Related configuration updated
        for loc in locations:
            if loc.company_id:
                self.assertEqual(loc.company_id.id, self.branch_delhi.id)
        for pt in picking_types:
            self.assertEqual(pt.company_id.id, self.branch_delhi.id)

    def test_07_safety_history_preservation_and_strict_mode(self):
        """Verify completed pickings/quants are preserved safely without blocking, but blocked in strict mode."""
        product = self.env["product.product"].create({
            "name": "Test Safety Product",
            "type": "consu",
        })
        # Create an on-hand quant
        self.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": self.warehouse_delhi.lot_stock_id.id,
            "quantity": 10.0,
        })

        # By default (allow_history=True), warehouse is migrated and history is preserved safely
        self.warehouse_delhi.action_match_company_by_gst_code(allow_history=True)
        self.assertEqual(self.warehouse_delhi.company_id.id, self.branch_delhi.id)

        # In strict mode (allow_history=False) on warehouse with history, UserError is raised
        wh_with_pick = self.env["stock.warehouse"].create({
            "name": "Strict Test WH",
            "code": "STW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_haryana.id,
        })
        # Simulate a completed move
        picking_type = self.env["stock.picking.type"].search([("warehouse_id", "=", wh_with_pick.id)], limit=1)
        self.env["stock.move"].create({
            "name": "Test Move",
            "product_id": product.id,
            "product_uom_qty": 1.0,
            "product_uom": product.uom_id.id,
            "location_id": wh_with_pick.lot_stock_id.id,
            "location_dest_id": wh_with_pick.lot_stock_id.id,
            "warehouse_id": wh_with_pick.id,
            "picking_type_id": picking_type.id,
            "state": "done",
        })
        with self.assertRaises(UserError):
            wh_with_pick.action_match_company_by_gst_code(allow_history=False)

    def test_08_wizard_bulk_processing_execution(self):
        """Test batch wizard execution with statistics."""
        wh_hr = self.env["stock.warehouse"].create({
            "name": "Haryana Batch WH",
            "code": "HBW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_haryana.id,
        })
        wh_skip = self.env["stock.warehouse"].create({
            "name": "Skip Batch WH",
            "code": "SBW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_no_gst.id,
        })

        wizard = self.env["warehouse.gst.company.match.wizard"].create({
            "warehouse_ids": [(6, 0, [wh_hr.id, wh_skip.id])],
        })
        wizard.action_process()

        self.assertEqual(wizard.state, "done")
        self.assertEqual(wizard.total_processed, 2)
        self.assertEqual(wizard.total_success, 1)
        self.assertEqual(wizard.total_skipped, 1)
        self.assertEqual(wh_hr.company_id.id, self.branch_haryana.id)

    def test_09_is_company_transferred_flag_on_all_modified_tables(self):
        """Test that is_company_transferred flag is updated to True on all 7 modified records."""
        product = self.env["product.product"].create({
            "name": "Transferred Flag Product",
            "type": "consu",
        })
        quant = self.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": self.warehouse_delhi.lot_stock_id.id,
            "quantity": 5.0,
        })

        locations, picking_types, rules, orderpoints = self.warehouse_delhi._get_exclusive_configuration_records()

        # Before transfer, is_company_transferred is False
        self.assertFalse(self.warehouse_delhi.is_company_transferred)
        for loc in locations:
            self.assertFalse(loc.is_company_transferred)
        for pt in picking_types:
            self.assertFalse(pt.is_company_transferred)

        # Perform match action
        self.warehouse_delhi.action_match_company_by_gst_code()

        # After transfer, warehouse is marked transferred
        self.assertTrue(self.warehouse_delhi.is_company_transferred)

        # Locations are marked transferred
        for loc in locations:
            self.assertTrue(loc.is_company_transferred)

        # Picking types are marked transferred
        for pt in picking_types:
            self.assertTrue(pt.is_company_transferred)

        # Stock rules are marked transferred
        for rule in rules:
            self.assertTrue(rule.is_company_transferred)

        # Active inventory quant is marked transferred
        quant.invalidate_recordset()
        self.assertTrue(quant.is_company_transferred)

    def test_10_persistent_audit_logging_and_tracking(self):
        """Verify persistent audit logging tracks what is done and not done."""
        wh_audit = self.env["stock.warehouse"].create({
            "name": "Audit Test WH",
            "code": "ATW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_haryana.id,
        })
        wh_skip = self.env["stock.warehouse"].create({
            "name": "Audit Skip WH",
            "code": "ASW",
            "company_id": self.parent_company.id,
            "partner_id": self.partner_no_gst.id,
        })

        # Process via wizard
        wizard = self.env["warehouse.gst.company.match.wizard"].create({
            "warehouse_ids": [(6, 0, [wh_audit.id, wh_skip.id])],
        })
        wizard.action_process()

        # Persistent log must be created
        self.assertTrue(bool(wizard.persistent_log_id))
        log = wizard.persistent_log_id
        self.assertEqual(log.total_processed, 2)
        self.assertEqual(log.total_success, 1)
        self.assertEqual(log.total_skipped, 1)

        # Check line details: what is done and what is not
        done_lines = log.line_ids.filtered(lambda l: l.is_done)
        not_done_lines = log.line_ids.filtered(lambda l: not l.is_done)

        self.assertEqual(len(done_lines), 1)
        self.assertEqual(done_lines.warehouse_id.id, wh_audit.id)
        self.assertEqual(done_lines.status, "success")
        self.assertEqual(done_lines.dest_company_id.id, self.branch_haryana.id)
        self.assertTrue(done_lines.is_done)

        self.assertEqual(len(not_done_lines), 1)
        self.assertEqual(not_done_lines.warehouse_id.id, wh_skip.id)
        self.assertEqual(not_done_lines.status, "skipped")
        self.assertFalse(not_done_lines.is_done)

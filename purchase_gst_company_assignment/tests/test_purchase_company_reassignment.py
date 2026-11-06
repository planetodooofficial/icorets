# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestPurchaseCompanyReassignment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.parent_company = cls.env["res.company"].create({
            "name": "Global Test Parent Corp PO",
        })

        cls.branch_delhi = cls.env["res.company"].create({
            "name": "Delhi Branch Corp PO",
            "parent_id": cls.parent_company.id,
            "gst_code_matching_com": "07",
        })

        cls.vendor_delhi = cls.env["res.partner"].create({
            "name": "Delhi GSTIN Vendor",
            "gst_code": "07",
            "company_id": False,
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test Purchase Reassignment Item",
            "type": "consu",
            "company_id": False,
        })

        cls.purchase_order = cls.env["purchase.order"].create({
            "partner_id": cls.vendor_delhi.id,
            "company_id": cls.parent_company.id,
            "order_line": [
                (0, 0, {
                    "product_id": cls.product.id,
                    "name": cls.product.name,
                    "product_qty": 10.0,
                    "price_unit": 100.0,
                    "company_id": cls.parent_company.id,
                })
            ],
        })

    def test_01_tool_target_company_resolution(self):
        """Test tool resolves target company correctly via vendor GST code."""
        tool = self.env["purchase.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.vendor_delhi.id,
        })
        self.assertEqual(tool.gst_code, "07")
        self.assertEqual(tool.target_company_id.id, self.branch_delhi.id)

    def test_02_fetch_record_counts(self):
        """Test tool correctly fetches record counts for Purchase Orders."""
        tool = self.env["purchase.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.vendor_delhi.id,
        })
        res = tool.action_fetch_records_count()
        self.assertGreaterEqual(tool.count_purchase_orders, 1)
        self.assertGreaterEqual(tool.count_purchase_order_lines, 1)
        self.assertEqual(res.get("type"), "ir.actions.client")

    def test_03_pipeline_update_all(self):
        """Test atomic pipeline update for PO and POL."""
        po = self.env["purchase.order"].create({
            "partner_id": self.vendor_delhi.id,
            "company_id": self.parent_company.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product.id,
                    "name": self.product.name,
                    "product_qty": 5.0,
                    "price_unit": 50.0,
                    "company_id": self.parent_company.id,
                })
            ],
        })

        tool = self.env["purchase.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.vendor_delhi.id,
        })
        tool.action_update_all()
        po.invalidate_recordset()

        self.assertEqual(po.company_id.id, self.branch_delhi.id)
        self.assertTrue(po.is_company_transferred)
        for line in po.order_line:
            self.assertEqual(line.company_id.id, self.branch_delhi.id)
            self.assertTrue(line.is_company_transferred)
        self.assertTrue(bool(tool.log_ids))
        self.assertEqual(tool.log_ids[0].status, "success")

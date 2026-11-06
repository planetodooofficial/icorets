# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestSaleCompanyReassignment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.parent_company = cls.env["res.company"].create({
            "name": "Global Test Parent Corp",
        })

        cls.branch_delhi = cls.env["res.company"].create({
            "name": "Delhi Branch Corp",
            "parent_id": cls.parent_company.id,
            "gst_code_matching_com": "DL",
        })

        cls.branch_haryana = cls.env["res.company"].create({
            "name": "Haryana Branch Corp",
            "parent_id": cls.parent_company.id,
            "gst_code_matching_com": "HR",
        })

        cls.partner_delhi = cls.env["res.partner"].create({
            "name": "Delhi GSTIN Partner",
            "gst_code": "DL",
            "company_id": False,
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test Sale Reassignment Item",
            "type": "consu",
            "company_id": False,
        })

        cls.sale_order = cls.env["sale.order"].create({
            "partner_id": cls.partner_delhi.id,
            "company_id": cls.parent_company.id,
            "order_line": [
                (0, 0, {
                    "product_id": cls.product.id,
                    "product_uom_qty": 10.0,
                    "price_unit": 100.0,
                    "company_id": cls.parent_company.id,
                })
            ],
        })

    def test_01_tool_target_company_resolution(self):
        """Test tool resolves target company correctly via GST code."""
        tool = self.env["sale.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.partner_delhi.id,
        })
        self.assertEqual(tool.gst_code, "DL")
        self.assertEqual(tool.target_company_id.id, self.branch_delhi.id)

    def test_02_fetch_record_counts(self):
        """Test tool correctly fetches record counts across models."""
        tool = self.env["sale.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.partner_delhi.id,
            "model_target": "sale_order",
        })
        tool.action_fetch_records_count()
        self.assertGreaterEqual(tool.count_sale_orders, 1)
        self.assertGreaterEqual(tool.count_sale_order_lines, 1)
        self.assertEqual(tool.count_selected_model, tool.count_sale_orders)

    def test_03_individual_update_sale_orders(self):
        """Test updating sale orders individually sets company_id and is_company_transferred."""
        tool = self.env["sale.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.partner_delhi.id,
        })
        self.assertFalse(self.sale_order.is_company_transferred)
        self.assertEqual(self.sale_order.company_id.id, self.parent_company.id)

        tool.action_update_sale_orders()
        self.sale_order.invalidate_recordset()

        self.assertEqual(self.sale_order.company_id.id, self.branch_delhi.id)
        self.assertTrue(self.sale_order.is_company_transferred)
        self.assertTrue(bool(tool.log_ids))
        self.assertEqual(tool.log_ids[0].status, "success")

    def test_04_pipeline_update_all(self):
        """Test atomic pipeline update for SO and SOL."""
        so = self.env["sale.order"].create({
            "partner_id": self.partner_delhi.id,
            "company_id": self.parent_company.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product.id,
                    "product_uom_qty": 5.0,
                    "price_unit": 50.0,
                    "company_id": self.parent_company.id,
                })
            ],
        })

        tool = self.env["sale.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.partner_delhi.id,
            "model_target": "all",
        })
        tool.action_update_all()
        so.invalidate_recordset()

        self.assertEqual(so.company_id.id, self.branch_delhi.id)
        self.assertTrue(so.is_company_transferred)
        for line in so.order_line:
            self.assertEqual(line.company_id.id, self.branch_delhi.id)
            self.assertTrue(line.is_company_transferred)

    def test_05_payment_and_reconciliation_fields(self):
        """Test tool supports payment and reconciliation counting and dispatching."""
        tool = self.env["sale.company.reassignment.tool"].create({
            "source_company_id": self.parent_company.id,
            "gstin_id": self.partner_delhi.id,
            "model_target": "account_payment",
        })
        tool.action_fetch_records_count()
        self.assertEqual(tool.model_target, "account_payment")
        self.assertEqual(
            tool.count_selected_model,
            tool.count_payments + tool.count_payment_moves + tool.count_payment_lines + tool.count_partial_reconciles + tool.count_bank_statement_lines + tool.count_bank_statements
        )

    def test_06_payments_widget_popover_branch(self):
        """Test payment popover widget reflects the updated branch name."""
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_delhi.id,
            "company_id": self.branch_delhi.id,
        })
        move.invoice_payments_widget = {
            "title": "Less Payment",
            "outstanding": False,
            "content": [
                {
                    "name": "Payment Info Test",
                    "journal_name": "Test Journal",
                    "company_name": "Old Company DL",
                    "move_id": move.id,
                }
            ],
        }
        move._compute_payments_widget_reconciled_info()
        content = move.invoice_payments_widget.get("content", [])
        self.assertTrue(content)
        self.assertEqual(content[0]["company_name"], self.branch_delhi.display_name)



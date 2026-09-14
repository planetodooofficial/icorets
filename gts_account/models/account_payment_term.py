from odoo import api, fields, models


class PaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, cash_rounding=None):
        res = super()._compute_terms(
            date_ref=date_ref,
            currency=currency,
            company=company,
            tax_amount=tax_amount,
            tax_amount_currency=tax_amount_currency,
            sign=sign,
            untaxed_amount=untaxed_amount,
            untaxed_amount_currency=untaxed_amount_currency,
            cash_rounding=cash_rounding,
        )
        if isinstance(res, dict) and 'line_ids' in res:
            for i, line in enumerate(self.line_ids):
                if i < len(res['line_ids']):
                    res['line_ids'][i]['desc'] = line.desc or ''
                    res['line_ids'][i]['value'] = line.value
                    res['line_ids'][i]['percent'] = line.value_amount if line.value == 'percent' else 0.0
        return res


class PaymentTermLineInherit(models.Model):
    _inherit = "account.payment.term.line"
    _order = "sequence,id"

    label = fields.Char(string='Label')
    desc = fields.Char(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

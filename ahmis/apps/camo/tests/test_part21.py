from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.camo.models import ModificationRepair
from apps.core.tests.factories import make_world, today


class Part21Tests(TestCase):
    def setUp(self):
        self.w = make_world()

    def mod(self, **kw):
        base = dict(aircraft=self.w["ac"], title="Treuil", classification="major", approval_basis="stc", approval_reference="STC-1")
        base.update(kw)
        return ModificationRepair(**base)

    def errors(self, m):
        try:
            m.full_clean()
        except ValidationError as e:
            return e.message_dict
        return {}

    def test_major_requires_part21_file(self):
        self.assertIn("part21_status", self.errors(self.mod()))
        self.assertNotIn("part21_status", self.errors(self.mod(part21_status="to_request")))
        self.assertFalse(self.mod(classification="minor", approval_basis="oem_sb").needs_part21)

    def test_approved_needs_holder_dates_and_reference(self):
        e = self.errors(self.mod(part21_status="approved"))
        for f in ("design_holder", "part21_requested_on", "part21_approved_on", "part21_reference"):
            self.assertIn(f, e)
        e = self.errors(self.mod(part21_status="approved", design_holder="DOA", part21_requested_on=today(),
                                 part21_approved_on=today() - timedelta(days=1), part21_reference="STC-1"))
        self.assertIn("part21_approved_on", e)

    def test_embodiment_blocked_until_approved(self):
        common = dict(status="embodied", embodied_on=today(), ica_none=True, design_holder="DOA", part21_requested_on=today() - timedelta(days=10))
        self.assertIn("status", self.errors(self.mod(part21_status="requested", **common)))
        e = self.errors(self.mod(part21_status="approved", part21_approved_on=today() + timedelta(days=1) - timedelta(days=2),
                                 part21_reference="STC-1", **{**common, "embodied_on": today() - timedelta(days=5)}))
        self.assertIn("embodied_on", e)
        self.assertEqual(self.errors(self.mod(part21_status="approved", part21_approved_on=today() - timedelta(days=1),
                                              part21_reference="STC-1", **common)), {})

    def test_compliance_issue_listed(self):
        m = self.mod(part21_status="to_request")
        m.save()
        self.assertTrue(any("Part-21" in str(i) for i in m.compliance_issues))

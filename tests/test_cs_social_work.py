from datetime import date, datetime, timedelta

from odoo.tests.common import TransactionCase


class TestCsSocialWorkBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner = cls.env['res.partner'].create({'name': 'Trabajadora Social Test'})
        cls.worker = cls.env['cs.worker'].create({
            'partner_id': partner.id,
            'job_title': 'trabajador_social',
        })
        cls.residence = cls.env['cs.residence'].create({
            'name': 'Residencia Test TS',
            'code': 'TTS',
        })
        cls.resident = cls.env['cs.resident'].create({
            'name': 'Residente Test TS',
            'dni': '00000003T',
            'fecha_nacimiento': '1975-03-10',
            'residence_id': cls.residence.id,
        })

    def _make_session(self, **kwargs):
        defaults = {
            'resident_id': self.resident.id,
            'social_worker_id': self.worker.id,
            'session_date': datetime.now() + timedelta(days=1),
        }
        defaults.update(kwargs)
        return self.env['cs.social.session'].create(defaults)

    def _make_report(self, **kwargs):
        defaults = {
            'resident_id': self.resident.id,
            'social_worker_id': self.worker.id,
        }
        defaults.update(kwargs)
        return self.env['cs.social.report'].create(defaults)

    def _make_procedure(self, **kwargs):
        defaults = {
            'resident_id': self.resident.id,
            'social_worker_id': self.worker.id,
            'procedure_type': 'dependencia',
            'description': 'Solicitud grado dependencia',
        }
        defaults.update(kwargs)
        return self.env['cs.social.procedure'].create(defaults)


class TestWorkerJobTitle(TestCsSocialWorkBase):

    def test_job_title_selection_extended(self):
        selection = dict(
            self.env['cs.worker']._fields['job_title'].get_description(self.env)['selection']
        )
        self.assertIn('trabajador_social', selection)


class TestSocialSession(TestCsSocialWorkBase):

    def test_sequence_assigned_on_create(self):
        session = self._make_session()
        self.assertTrue(session.name.startswith('TS/CIT/'))

    def test_default_state_is_planned(self):
        session = self._make_session()
        self.assertEqual(session.state, 'planned')

    def test_calendar_event_created(self):
        session = self._make_session()
        self.assertTrue(session.calendar_event_id)
        event = session.calendar_event_id
        self.assertTrue(event.cs_is_social_work_visit)
        self.assertEqual(event.cs_resident_id, self.resident)
        self.assertEqual(event.cs_social_worker_id, self.worker)
        self.assertEqual(event.cs_social_session_id, session)
        self.assertIn(self.resident.name, event.name)

    def test_session_date_change_syncs_event(self):
        session = self._make_session()
        new_date = (datetime.now() + timedelta(days=5)).replace(microsecond=0)
        session.write({'session_date': new_date})
        self.assertEqual(session.calendar_event_id.start, new_date)

    def test_event_date_change_syncs_session(self):
        session = self._make_session(duration_minutes=30)
        event = session.calendar_event_id
        new_start = datetime.now().replace(microsecond=0) + timedelta(days=7)
        event.write({'start': new_start, 'stop': new_start + timedelta(minutes=45)})
        self.assertEqual(session.session_date, new_start)
        self.assertEqual(session.duration_minutes, 45)

    def test_cancel_archives_event(self):
        session = self._make_session()
        event = session.calendar_event_id
        session.action_mark_cancelled()
        self.assertEqual(session.state, 'cancelled')
        self.assertFalse(event.active)

    def test_mark_done(self):
        session = self._make_session()
        session.action_mark_done()
        self.assertEqual(session.state, 'done')

    def test_unlink_removes_event(self):
        session = self._make_session()
        event = session.calendar_event_id
        session.unlink()
        self.assertFalse(event.exists())


class TestSocialReport(TestCsSocialWorkBase):

    def test_sequence_assigned_on_create(self):
        report = self._make_report()
        self.assertTrue(report.name.startswith('TS/INF/'))

    def test_default_state_is_draft(self):
        report = self._make_report()
        self.assertEqual(report.state, 'draft')

    def test_default_type_is_valoracion(self):
        report = self._make_report()
        self.assertEqual(report.report_type, 'valoracion_inicial')

    def test_mark_done_and_reopen(self):
        report = self._make_report()
        report.action_mark_done()
        self.assertEqual(report.state, 'done')
        report.action_set_draft()
        self.assertEqual(report.state, 'draft')

    def test_partner_related_to_resident(self):
        report = self._make_report()
        self.assertEqual(report.partner_id, self.resident.partner_id)


class TestSocialProcedure(TestCsSocialWorkBase):

    def test_sequence_assigned_on_create(self):
        procedure = self._make_procedure()
        self.assertTrue(procedure.name.startswith('TS/GES/'))

    def test_default_state_is_pending(self):
        procedure = self._make_procedure()
        self.assertEqual(procedure.state, 'pending')

    def test_state_flow_to_done_sets_completion_date(self):
        procedure = self._make_procedure()
        procedure.action_start()
        self.assertEqual(procedure.state, 'in_progress')
        procedure.action_mark_done()
        self.assertEqual(procedure.state, 'done')
        self.assertEqual(procedure.completion_date, date.today())

    def test_cancel(self):
        procedure = self._make_procedure()
        procedure.action_mark_cancelled()
        self.assertEqual(procedure.state, 'cancelled')

    def test_reopen_clears_completion_date(self):
        procedure = self._make_procedure()
        procedure.action_start()
        procedure.action_mark_done()
        procedure.action_set_pending()
        self.assertEqual(procedure.state, 'pending')
        self.assertFalse(procedure.completion_date)


class TestResidentExtension(TestCsSocialWorkBase):

    def test_counts(self):
        self._make_session()
        self._make_session()
        self._make_report()
        self._make_procedure()
        self.assertEqual(self.resident.social_session_count, 2)
        self.assertEqual(self.resident.social_report_count, 1)
        self.assertEqual(self.resident.social_procedure_count, 1)

    def test_open_actions_domains(self):
        action = self.resident.action_open_social_sessions()
        self.assertEqual(action['res_model'], 'cs.social.session')
        self.assertIn(('resident_id', '=', self.resident.id), action['domain'])

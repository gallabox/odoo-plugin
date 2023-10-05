from datetime import timedelta, datetime
from odoo import models
from dateutil.relativedelta import relativedelta


class GcsCron(models.Model):
    _inherit = 'gcs.whatsapp'

    def gcs_daily_whatsapp_log_clear_cron(self):
        interval_type = self.env['gcs.whatsapp.config'].search([], limit=1)
        today = datetime.now()
        if interval_type.clear_log_interval == 'weekly':
            start_date = today - timedelta(days=7)
            end_date = today
            whatsapp_log_records = self.env['gcs.whatsapp'].search([
                ('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_date.strftime('%Y-%m-%d %H:%M:%S'))])
            whatsapp_log_records.unlink()

        elif interval_type.clear_log_interval == 'monthly':
            start_date = today - relativedelta(months=1)  # One month ago from today
            end_date = today
            whatsapp_log_records = self.env['gcs.whatsapp'].search([
                ('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<=', end_date.strftime('%Y-%m-%d %H:%M:%S'))])
            whatsapp_log_records.unlink()

        elif not interval_type.clear_log_interval or interval_type.clear_log_interval == 'never':
            pass

    # def gcs_daily_whatsapp_log_clear_cron(self):
    #     interval_type = self.env['gcs.whatsapp.config'].search([], limit=1)
    #
    #     today = datetime.now()
    #     start_date = today
    #     end_date = today
    #
    #     if interval_type.clear_log_interval == 'weekly':
    #         start_date = today - timedelta(days=7)
    #         end_date = today
    #     elif interval_type.clear_log_interval == 'monthly':
    #         start_date = today - relativedelta(months=1)  # One month ago from today
    #         end_date = today
    #     elif not interval_type.clear_log_interval or interval_type.clear_log_interval == 'never':
    #         return False
    #     whatsapp_log_records = self.env['gcs.whatsapp'].search([
    #         ('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
    #         ('create_date', '<=', end_date.strftime('%Y-%m-%d %H:%M:%S'))
    #     ])
    #     whatsapp_log_records.unlink()
    #

from elastalert.alerts import EmailAlerter

from elastalert.util import EAException
from elastalert.util import elastalert_logger
from elastalert.util import lookup_es_key

from email.mime.text import MIMEText
from email.utils import formatdate


from smtplib import SMTP
from smtplib import SMTP_SSL
from smtplib import SMTPAuthenticationError
from smtplib import SMTPException
from socket import error

class PriorityEmailAlerter(EmailAlerter):
    def get_alert_priority(self):
        priority = self.rule['email_priority']
        if priority == "lowest":
            return 5
        elif priority == "low":
            return 4
        elif priority == "normal":
            return 3
        elif priority == "high":
            return 2
        elif priority == "highest":
            return 1
        return None

    def alert(self, matches):
        body = self.create_alert_body(matches)

        # Add JIRA ticket if it exists
        if self.pipeline is not None and 'jira_ticket' in self.pipeline:
            url = '%s/browse/%s' % (self.pipeline['jira_server'], self.pipeline['jira_ticket'])
            body += '\nJIRA ticket: %s' % (url)

        to_addr = self.rule['email']
        if 'email_from_field' in self.rule:
            recipient = lookup_es_key(matches[0], self.rule['email_from_field'])
            if isinstance(recipient, str):
                if '@' in recipient:
                    to_addr = [recipient]
                elif 'email_add_domain' in self.rule:
                    to_addr = [recipient + self.rule['email_add_domain']]
            elif isinstance(recipient, list):
                to_addr = recipient
                if 'email_add_domain' in self.rule:
                    to_addr = [name + self.rule['email_add_domain'] for name in to_addr]
        if self.rule.get('email_format') == 'html':
            email_msg = MIMEText(body, 'html', _charset='UTF-8')
        else:
            email_msg = MIMEText(body, _charset='UTF-8')
        email_msg['Subject'] = self.create_title(matches)
        email_msg['To'] = ', '.join(to_addr)
        email_msg['From'] = self.from_addr
        email_msg['Reply-To'] = self.rule.get('email_reply_to', email_msg['To'])
        email_msg['Date'] = formatdate()
        priority = self.get_alert_priority()
        if priority != None:
            email_msg['X-Priority'] = priority
        if self.rule.get('cc'):
            email_msg['CC'] = ','.join(self.rule['cc'])
            to_addr = to_addr + self.rule['cc']
        if self.rule.get('bcc'):
            to_addr = to_addr + self.rule['bcc']

        try:
            if self.smtp_ssl:
                if self.smtp_port:
                    self.smtp = SMTP_SSL(self.smtp_host, self.smtp_port, keyfile=self.smtp_key_file,
                                         certfile=self.smtp_cert_file)
                else:
                    self.smtp = SMTP_SSL(self.smtp_host, keyfile=self.smtp_key_file, certfile=self.smtp_cert_file)
            else:
                if self.smtp_port:
                    self.smtp = SMTP(self.smtp_host, self.smtp_port)
                else:
                    self.smtp = SMTP(self.smtp_host)
                self.smtp.ehlo()
                if self.smtp.has_extn('STARTTLS'):
                    self.smtp.starttls(keyfile=self.smtp_key_file, certfile=self.smtp_cert_file)
            if 'smtp_auth_file' in self.rule:
                self.smtp.login(self.user, self.password)
        except (SMTPException, error) as e:
            raise EAException("Error connecting to SMTP host: %s" % (e))
        except SMTPAuthenticationError as e:
            raise EAException("SMTP username/password rejected: %s" % (e))
        self.smtp.sendmail(self.from_addr, to_addr, email_msg.as_string())
        self.smtp.quit()

        elastalert_logger.info("Sent email to %s" % (to_addr))


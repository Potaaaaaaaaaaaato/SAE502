#!/usr/bin/env python3
"""
Comprehensive Health Check and Monitoring Script for SAE502
Checks Django, PostgreSQL, Redis, and disk space
Sends alerts via email and webhook on failures
"""

import os
import sys
import json
import logging
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
import psycopg2
import redis as redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'True').lower() == 'true'
ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DJANGO_URL = os.getenv('DJANGO_URL', 'http://django-app:8000')
DB_HOST = os.getenv('DB_HOST', 'postgresql')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'django_db')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

DISK_THRESHOLD = 90  # Alert if disk usage > 90%


class HealthChecker:
    """Main health checker class"""
    
    def __init__(self):
        self.status = {
            'timestamp': datetime.now().isoformat(),
            'django': {'healthy': False, 'message': ''},
            'postgresql': {'healthy': False, 'message': ''},
            'redis': {'healthy': False, 'message': ''},
            'disk': {'healthy': True, 'message': '', 'usage_percent': 0},
            'overall_healthy': False
        }
    
    def check_django(self):
        """Check Django application health"""
        try:
            response = requests.get(f'{DJANGO_URL}/health/', timeout=10)
            if response.status_code == 200:
                self.status['django'] = {
                    'healthy': True,
                    'message': 'Django is responding correctly'
                }
                logger.info("✅ Django healthcheck passed")
            else:
                self.status['django'] = {
                    'healthy': False,
                    'message': f'Django returned status code {response.status_code}'
                }
                logger.error(f"❌ Django healthcheck failed: status {response.status_code}")
        except Exception as e:
            self.status['django'] = {
                'healthy': False,
                'message': f'Cannot reach Django: {str(e)}'
            }
            logger.error(f"❌ Django healthcheck failed: {e}")
    
    def check_postgresql(self):
        """Check PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            
            self.status['postgresql'] = {
                'healthy': True,
                'message': 'PostgreSQL connection successful'
            }
            logger.info("✅ PostgreSQL healthcheck passed")
        except Exception as e:
            self.status['postgresql'] = {
                'healthy': False,
                'message': f'PostgreSQL connection failed: {str(e)}'
            }
            logger.error(f"❌ PostgreSQL healthcheck failed: {e}")
    
    def check_redis(self):
        """Check Redis connection"""
        try:
            r = redis_client.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                socket_connect_timeout=5
            )
            r.ping()
            
            self.status['redis'] = {
                'healthy': True,
                'message': 'Redis connection successful'
            }
            logger.info("✅ Redis healthcheck passed")
        except Exception as e:
            self.status['redis'] = {
                'healthy': False,
                'message': f'Redis connection failed: {str(e)}'
            }
            logger.error(f"❌ Redis healthcheck failed: {e}")
    
    def check_disk_space(self):
        """Check disk space usage"""
        try:
            result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                usage_str = parts[4].rstrip('%')
                usage_percent = int(usage_str)
                
                self.status['disk']['usage_percent'] = usage_percent
                
                if usage_percent > DISK_THRESHOLD:
                    self.status['disk'] = {
                        'healthy': False,
                        'message': f'Disk usage is {usage_percent}% (threshold: {DISK_THRESHOLD}%)',
                        'usage_percent': usage_percent
                    }
                    logger.warning(f"⚠️  High disk usage: {usage_percent}%")
                else:
                    self.status['disk'] = {
                        'healthy': True,
                        'message': f'Disk usage is {usage_percent}%',
                        'usage_percent': usage_percent
                    }
                    logger.info(f"✅ Disk space OK: {usage_percent}%")
        except Exception as e:
            self.status['disk'] = {
                'healthy': True,  # Don't fail on disk check errors
                'message': f'Could not check disk space: {str(e)}',
                'usage_percent': 0
            }
            logger.warning(f"⚠️  Could not check disk space: {e}")
    
    def run_all_checks(self):
        """Run all health checks"""
        logger.info("🔍 Starting health checks...")
        
        self.check_django()
        self.check_postgresql()
        self.check_redis()
        self.check_disk_space()
        
        # Determine overall health
        critical_checks = ['django', 'postgresql', 'redis']
        self.status['overall_healthy'] = all(
            self.status[check]['healthy'] for check in critical_checks
        )
        
        if self.status['overall_healthy']:
            logger.info("✅ All health checks passed!")
        else:
            logger.error("❌ Some health checks failed!")
        
        return self.status
    
    def send_email_alert(self, status):
        """Send email alert on failure"""
        if not ALERT_EMAIL or not EMAIL_USER or not EMAIL_PASSWORD:
            logger.warning("⚠️  Email alerting not configured, skipping")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = ALERT_EMAIL
            msg['Subject'] = f"🚨 SAE502 Health Check Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = f"""
            <html>
            <body>
                <h2>🚨 Health Check Alert</h2>
                <p><strong>Timestamp:</strong> {status['timestamp']}</p>
                <h3>Status Summary:</h3>
                <ul>
                    <li>Django: {'✅ OK' if status['django']['healthy'] else '❌ FAILED'} - {status['django']['message']}</li>
                    <li>PostgreSQL: {'✅ OK' if status['postgresql']['healthy'] else '❌ FAILED'} - {status['postgresql']['message']}</li>
                    <li>Redis: {'✅ OK' if status['redis']['healthy'] else '❌ FAILED'} - {status['redis']['message']}</li>
                    <li>Disk Space: {'✅ OK' if status['disk']['healthy'] else '⚠️  WARNING'} - {status['disk']['message']}</li>
                </ul>
                <p><strong>Overall Status:</strong> {'✅ HEALTHY' if status['overall_healthy'] else '❌ UNHEALTHY'}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"📧 Email alert sent to {ALERT_EMAIL}")
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
    
    def send_webhook_alert(self, status):
        """Send webhook alert (Slack/Discord/etc)"""
        if not WEBHOOK_URL:
            logger.warning("⚠️  Webhook alerting not configured, skipping")
            return
        
        try:
            emoji = '✅' if status['overall_healthy'] else '🚨'
            color = '#36a64f' if status['overall_healthy'] else '#ff0000'
            
            # Slack-compatible format
            payload = {
                'text': f'{emoji} SAE502 Health Check',
                'attachments': [{
                    'color': color,
                    'fields': [
                        {'title': 'Django', 'value': '✅' if status['django']['healthy'] else '❌', 'short': True},
                        {'title': 'PostgreSQL', 'value': '✅' if status['postgresql']['healthy'] else '❌', 'short': True},
                        {'title': 'Redis', 'value': '✅' if status['redis']['healthy'] else '❌', 'short': True},
                        {'title': 'Disk', 'value': f"{status['disk']['usage_percent']}%", 'short': True},
                    ],
                    'footer': f"Timestamp: {status['timestamp']}"
                }]
            }
            
            response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("🔔 Webhook alert sent successfully")
            else:
                logger.error(f"❌ Webhook returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to send webhook alert: {e}")


def main():
    """Main entry point"""
    if not MONITORING_ENABLED:
        logger.info("ℹ️  Monitoring is disabled")
        return 0
    
    checker = HealthChecker()
    status = checker.run_all_checks()
    
    # Print status as JSON for logging
    print(json.dumps(status, indent=2))
    
    # Send alerts only if unhealthy
    if not status['overall_healthy']:
        logger.warning("🚨 System is unhealthy, sending alerts...")
        checker.send_email_alert(status)
        checker.send_webhook_alert(status)
    
    # Exit with appropriate code
    return 0 if status['overall_healthy'] else 1


if __name__ == '__main__':
    sys.exit(main())

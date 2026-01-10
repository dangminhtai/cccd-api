"""
Email Service - Send emails using SMTP
Simple SMTP-based email service
"""
from __future__ import annotations

import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Email service sử dụng SMTP"""
    
    def __init__(self):
        self.from_email = os.getenv("EMAIL_FROM", "noreply@cccd-api.com")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "CCCD API")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured, email sending will fail")
            logger.warning("Please set SMTP_USERNAME and SMTP_PASSWORD in .env file")
        else:
            logger.info(f"SMTP email service initialized: {self.smtp_host}:{self.smtp_port}")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional, auto-generated from HTML if not provided)
            to_name: Recipient name (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # Create text content (auto-generate from HTML if not provided)
            if not text_content:
                # Simple HTML to text conversion (remove tags)
                text_content = re.sub(r"<[^>]+>", "", html_content)
                text_content = re.sub(r"\s+", " ", text_content).strip()
            
            # Add both text and HTML parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Connect to SMTP server
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Login and send
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email via SMTP: {str(e)}", exc_info=True)
            return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance (singleton)"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    to_name: Optional[str] = None,
) -> bool:
    """
    Convenience function to send email
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
        to_name: Recipient name (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    service = get_email_service()
    return service.send_email(to_email, subject, html_content, text_content, to_name)


def send_welcome_email(to_email: str, to_name: str, verification_url: Optional[str] = None) -> bool:
    """Send welcome email to new user"""
    try:
        from flask import render_template
        
        subject = "Chào mừng đến với CCCD API"
        html_content = render_template(
            "emails/welcome.html",
            user_name=to_name,
            verification_url=verification_url
        )
        
        return send_email(to_email, subject, html_content, to_name=to_name)
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}", exc_info=True)
        return False


def send_verification_email(to_email: str, to_name: str, verification_url: str) -> bool:
    """Send email verification email"""
    try:
        from flask import render_template
        
        subject = "Xác thực email của bạn - CCCD API"
        html_content = render_template(
            "emails/verification.html",
            user_name=to_name,
            verification_url=verification_url
        )
        
        return send_email(to_email, subject, html_content, to_name=to_name)
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}", exc_info=True)
        return False


def send_password_reset_email(to_email: str, to_name: str, reset_url: str) -> bool:
    """Send password reset email"""
    try:
        from flask import render_template
        
        subject = "Đặt lại mật khẩu - CCCD API"
        html_content = render_template(
            "emails/password_reset.html",
            user_name=to_name,
            reset_url=reset_url
        )
        
        return send_email(to_email, subject, html_content, to_name=to_name)
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}", exc_info=True)
        return False

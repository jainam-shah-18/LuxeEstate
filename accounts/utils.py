"""
Utility functions for accounts app
"""
import os
import smtplib
import ssl

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_otp_email(email, otp_code, user_name=None):
    """
    Send OTP via email.

    Returns:
        None on success, or a short failure code for UI messaging: 'auth', 'tls', 'other'.
    """
    try:
        subject = "Your LuxeEstate OTP Code"
        display_name = user_name or 'User'
        
        context = {
            'otp_code': otp_code,
            'user_name': display_name,
            'validity_minutes': 10,
        }
        
        # You can create an email template later
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
                <div style="background-color: white; max-width: 600px; margin: 0 auto; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #003580; margin-bottom: 20px;">Email Verification</h2>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        Hi {display_name},
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-bottom: 30px;">
                        Use the following OTP code to complete your sign-in or verify your email address:
                    </p>
                    
                    <div style="background-color: #f0f7ff; border-left: 4px solid #003580; padding: 20px; margin: 30px 0; text-align: center;">
                        <p style="margin: 0; color: #003580; font-size: 32px; font-weight: bold; letter-spacing: 5px;">
                            {otp_code}
                        </p>
                    </div>
                    
                    <p style="color: #999; font-size: 13px; text-align: center; margin: 30px 0;">
                        This OTP will expire in 10 minutes
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin: 20px 0;">
                        If you didn't request this code, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        © 2026 LuxeEstate. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        from_email = (getattr(settings, 'EMAIL_HOST_USER', '') or '').strip() or settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"OTP email sent successfully to {email}")
        return None

    except smtplib.SMTPAuthenticationError as e:
        logger.error("OTP email SMTP authentication failed for %s: %s", email, e)
        return "auth"
    except ssl.SSLError as e:
        logger.error("OTP email TLS/SSL error for %s: %s", email, e)
        return "tls"
    except Exception as e:
        err_s = str(e)
        if (
            "CERTIFICATE_VERIFY_FAILED" in err_s
            or "Basic Constraints" in err_s
            or "certificate verify failed" in err_s.lower()
        ):
            logger.error("OTP email certificate verification failed for %s: %s", email, e)
            return "tls"
        logger.error("Error sending OTP email to %s: %s", email, e)
        return "other"


def send_welcome_email(email, user_name, activation_link=None):
    """
    Send welcome email after successful registration
    """
    try:
        subject = "Welcome to LuxeEstate - Your Real Estate Partner"
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
                <div style="background-color: white; max-width: 600px; margin: 0 auto; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h1 style="color: #003580; margin-bottom: 20px;">Welcome to LuxeEstate! 🏠</h1>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        Hi {user_name},
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                        Thank you for joining LuxeEstate, your ultimate destination for finding the perfect property. 
                        Explore thousands of listings, save your favorites, and connect directly with agents.
                    </p>
                    
                    <h3 style="color: #003580; margin-top: 30px; margin-bottom: 15px;">Getting Started:</h3>
                    <ul style="color: #666; font-size: 14px; line-height: 1.8;">
                        <li>Complete your profile to help us find better matches</li>
                        <li>Search properties by city, price, and type</li>
                        <li>Save your favorite listings</li>
                        <li>Chat directly with property agents</li>
                        <li>Compare multiple properties side-by-side</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{settings.SITE_URL}" style="background-color: #003580; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            Start Exploring Now
                        </a>
                    </p>
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                        © 2026 LuxeEstate. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending welcome email to {email}: {str(e)}")
        return False


def send_password_reset_email(email, user_name, reset_link):
    """
    Send password reset email
    """
    try:
        subject = "Reset Your LuxeEstate Password"
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
                <div style="background-color: white; max-width: 600px; margin: 0 auto; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #003580; margin-bottom: 20px;">Password Reset Request</h2>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        Hi {user_name},
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                        We received a request to reset the password for your LuxeEstate account. 
                        Click the link below to set a new password:
                    </p>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #003580; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin: 20px 0;">
                        This link will expire in 24 hours
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin: 20px 0;">
                        If you didn't request this reset, please ignore this email.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                        © 2026 LuxeEstate. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {str(e)}")
        return False


def send_property_inquiry_confirmation(email, user_name, property_title, agent_name):
    """
    Send confirmation when user inquires about a property
    """
    try:
        subject = f"Your Inquiry About {property_title}"
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
                <div style="background-color: white; max-width: 600px; margin: 0 auto; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #003580; margin-bottom: 20px;">Inquiry Received</h2>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        Hi {user_name},
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                        We've received your inquiry about <strong>{property_title}</strong>. 
                        Agent <strong>{agent_name}</strong> will get back to you shortly.
                    </p>
                    
                    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                        Check your message inbox on LuxeEstate for direct communication with the agent.
                    </p>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{settings.SITE_URL}/messaging/" style="background-color: #003580; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            View Message Thread
                        </a>
                    </p>
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                        © 2026 LuxeEstate. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Property inquiry confirmation email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending property inquiry email to {email}: {str(e)}")
        return False

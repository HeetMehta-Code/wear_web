import os
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from .models import User

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created and instance.email:
        subject = 'Welcome to the RAMYA Community! 🙏'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [instance.email]

        # HTML layout with your poster image referenced as 'cid:welcome_poster'
        html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
                    <div style="display: inline-block; border: 1px solid #ddd; padding: 10px; border-radius: 8px;">
                        <img src="cid:welcome_poster" style="width: 100%; max-width: 500px; height: auto;">
                        <h2 style="color: #333;">Glad to have you, {instance.email}!</h2>
                    </div>
                </body>
            </html>
        """
        
        msg = EmailMultiAlternatives(subject, "Welcome to RAMYA!", from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.mixed_subtype = 'related' 

        # Using your specific filename: ty.png
        image_path = os.path.join(settings.BASE_DIR, 'static/images/ty.png')
        
        try:
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<welcome_poster>') 
                img.add_header('Content-Disposition', 'inline', filename='ty.png')
                msg.attach(img)

            msg.send()
            print(f"✅ Success: Welcome poster (ty.png) sent to {instance.email}")
        except FileNotFoundError:
            print(f"❌ Error: Could not find the file at {image_path}. Check your folder structure!")
        except Exception as e:
            print(f"❌ Email failed: {e}")
import re
from flask import current_app
from flask_mail import Message
from app import mail


def _strip_html(html):
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _send_email(subject, recipient, html_body, text_body=None):
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_body,
            body=text_body or _strip_html(html_body)
        )
        mail.send(msg)
        current_app.logger.info(f"[EMAIL OK] {recipient} | {subject}")
        return True
    except Exception as e:
        current_app.logger.error(f"[EMAIL ERROR] {e}")
        codes = re.findall(r'(\d{6})', html_body)
        links = re.findall(r'href=["\']([^"\']*reset[^"\']*)["\']', html_body)
        print("\n" + "=" * 60)
        print(f"  EMAIL NO ENVIADO (consola fallback)")
        print(f"  Para: {recipient}")
        print(f"  Asunto: {subject}")
        if codes:
            print(f"  CODIGO: {codes[0]}")
        if links:
            print(f"  ENLACE: {links[0]}")
        print("=" * 60 + "\n")
        return True


def _base_template(title, content):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f0f;padding:40px 20px;">
  <tr><td align="center">
    <table width="520" cellpadding="0" cellspacing="0"
           style="background:#1a1a1a;border-radius:16px;overflow:hidden;border:1px solid #2a2a2a;">
      <tr>
        <td style="background:#111;padding:24px 36px;border-bottom:3px solid #ffb700;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td>
              <span style="font-size:24px;font-weight:900;color:#fff;">
                TUT<span style="color:#ffb700;">0</span>HUB
              </span>
            </td>
            <td align="right">
              <span style="font-size:11px;color:#555;text-transform:uppercase;letter-spacing:1px;">
                Correo automatico
              </span>
            </td>
          </tr></table>
        </td>
      </tr>
      <tr><td style="padding:36px;">{content}</td></tr>
      <tr>
        <td style="background:#111;padding:18px 36px;border-top:1px solid #2a2a2a;">
          <p style="margin:0;font-size:12px;color:#555;text-align:center;">
            Este correo fue generado automaticamente por TUT0hub. No respondas este mensaje.<br>
            Si no solicitaste esto, puedes ignorarlo con seguridad.
          </p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def send_sms_code(user_email, code):
    """Envia el codigo de recuperacion simulando un SMS por email"""
    digits_html = "".join(
        f'<td style="padding:0 3px;">'
        f'<span style="display:inline-block;width:40px;height:52px;line-height:52px;'
        f'text-align:center;background:#111;border:2px solid #ffb700;border-radius:8px;'
        f'font-size:26px;font-weight:900;color:#ffb700;">{d}</span></td>'
        for d in str(code)
    )

    content = f"""
<h1 style="margin:0 0 6px;font-size:20px;font-weight:800;color:#fff;">
  Codigo de recuperacion por SMS
</h1>
<p style="margin:0 0 24px;font-size:14px;color:#888;">
  Recibiste este codigo porque solicitaste recuperar tu contrasena.
</p>

<table cellpadding="0" cellspacing="0"
       style="margin:0 auto 24px;background:#1e1e1e;border-radius:14px;
              border:1px solid #2a2a2a;width:280px;">
  <tr>
    <td style="padding:14px 16px;border-bottom:1px solid #2a2a2a;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td>
          <span style="font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;">
            Mensaje de texto
          </span>
        </td>
        <td align="right">
          <span style="font-size:11px;color:#555;">TUT0hub</span>
        </td>
      </tr></table>
    </td>
  </tr>
  <tr>
    <td style="padding:20px 16px;">
      <p style="margin:0 0 8px;font-size:12px;color:#777;">
        Tu codigo de verificacion de TUT0hub es:
      </p>
      <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
        <tr>{digits_html}</tr>
      </table>
      <p style="margin:12px 0 0;font-size:11px;color:#555;text-align:center;">
        Expira en 10 minutos
      </p>
    </td>
  </tr>
  <tr>
    <td style="padding:10px 16px;background:#111;border-top:1px solid #2a2a2a;
               border-radius:0 0 12px 12px;">
      <p style="margin:0;font-size:10px;color:#444;text-align:center;">
        Numero simulado: +52 (449) XXX-XXXX
      </p>
    </td>
  </tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#111;border-radius:10px;border-left:4px solid #2196f3;margin-bottom:20px;">
  <tr>
    <td style="padding:14px 18px;">
      <p style="margin:0;font-size:13px;color:#aaa;">
        En produccion este codigo llegaria a tu celular mediante
        <strong style="color:#fff;">Twilio SMS</strong> o
        <strong style="color:#fff;">AWS SNS</strong>.
      </p>
    </td>
  </tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#111;border-radius:10px;border-left:4px solid #f44336;">
  <tr>
    <td style="padding:12px 18px;">
      <p style="margin:0;font-size:13px;color:#aaa;">
        Nunca compartas este codigo con nadie. TUT0hub nunca te lo pedira.
      </p>
    </td>
  </tr>
</table>
"""
    html = _base_template("Codigo de recuperacion SMS — TUT0hub", content)
    text = f"TUT0hub SMS: Tu codigo de recuperacion es {code}. Expira en 10 minutos. No lo compartas."
    return _send_email("Codigo de recuperacion SMS — TUT0hub", user_email, html, text)


def send_mfa_code(user_email, code):
    """Envia codigo OTP para verificacion MFA al iniciar sesion"""
    digits_html = "".join(
        f'<td style="padding:0 3px;">'
        f'<span style="display:inline-block;width:40px;height:52px;line-height:52px;'
        f'text-align:center;background:#111;border:2px solid #ffb700;border-radius:8px;'
        f'font-size:26px;font-weight:900;color:#ffb700;">{d}</span></td>'
        for d in str(code)
    )

    content = f"""
<h1 style="margin:0 0 6px;font-size:20px;font-weight:800;color:#fff;">
  Verificacion de identidad
</h1>
<p style="margin:0 0 24px;font-size:14px;color:#888;">
  Alguien intento iniciar sesion en tu cuenta. Ingresa este codigo para confirmar que eres tu.
</p>

<table cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
  <tr>{digits_html}</tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#111;border-radius:10px;margin-bottom:20px;">
  <tr>
    <td style="padding:12px 18px;">
      <p style="margin:0;font-size:13px;color:#aaa;">
        Este codigo expira en <strong style="color:#ffb700;">10 minutos</strong>.
      </p>
    </td>
  </tr>
  <tr>
    <td style="padding:0 18px 12px;">
      <p style="margin:0;font-size:13px;color:#aaa;">
        Nunca compartas este codigo. TUT0hub nunca te lo pedira.
      </p>
    </td>
  </tr>
</table>

<p style="margin:0;font-size:13px;color:#555;">
  Si no intentaste iniciar sesion, cambia tu contrasena de inmediato.
</p>
"""
    html = _base_template("Codigo de verificacion MFA — TUT0hub", content)
    text = f"Tu codigo MFA de TUT0hub es: {code}. Expira en 10 minutos."
    return _send_email("Tu codigo de acceso — TUT0hub", user_email, html, text)


def send_password_reset_email(user_email, reset_link):
    """Envia enlace de restablecimiento de contrasena"""
    content = f"""
<h1 style="margin:0 0 6px;font-size:20px;font-weight:800;color:#fff;">
  Restablece tu contrasena
</h1>
<p style="margin:0 0 24px;font-size:14px;color:#888;">
  Recibimos una solicitud para restablecer la contrasena de tu cuenta.
  Haz clic en el boton para continuar.
</p>

<table cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
  <tr>
    <td style="background:#ffb700;border-radius:50px;">
      <a href="{reset_link}"
         style="display:inline-block;padding:14px 36px;font-size:14px;
                font-weight:800;color:#000;text-decoration:none;letter-spacing:0.5px;">
        CAMBIAR CONTRASENA
      </a>
    </td>
  </tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#111;border-radius:10px;border-left:4px solid #ffb700;margin-bottom:20px;">
  <tr>
    <td style="padding:12px 18px;">
      <p style="margin:0;font-size:13px;color:#aaa;">
        Este enlace expira en <strong style="color:#ffb700;">30 minutos</strong>
        y solo puede usarse una vez.
      </p>
    </td>
  </tr>
</table>

<p style="margin:0 0 4px;font-size:11px;color:#555;">
  Si el boton no funciona, copia este enlace:
</p>
<p style="margin:0;font-size:11px;word-break:break-all;">
  <a href="{reset_link}" style="color:#ffb700;text-decoration:none;">{reset_link}</a>
</p>
"""
    html = _base_template("Restablece tu contrasena — TUT0hub", content)
    text = f"Restablece tu contrasena de TUT0hub:\n{reset_link}\n\nExpira en 30 minutos."
    return _send_email("Restablece tu contrasena — TUT0hub", user_email, html, text)


def send_call_code_simulated(user_email, code):
    """Simula codigo por llamada — lo envia por email"""
    spoken = " - ".join(list(str(code)))
    content = f"""
<h1 style="margin:0 0 6px;font-size:20px;font-weight:800;color:#fff;">
  Codigo de recuperacion por llamada
</h1>
<p style="margin:0 0 24px;font-size:14px;color:#888;">
  En una llamada real escucharias el siguiente mensaje:
</p>

<table cellpadding="0" cellspacing="0"
       style="margin:0 auto 24px;background:#1a1a2e;border:2px solid #333;
              border-radius:16px;width:290px;overflow:hidden;">
  <tr>
    <td style="background:#16213e;padding:10px 20px;text-align:center;
               border-bottom:1px solid #2a2a3e;">
      <p style="margin:0;font-size:11px;color:#888;">Llamada entrante simulada</p>
      <p style="margin:4px 0 0;font-size:13px;color:#fff;font-weight:700;">TUT0hub</p>
    </td>
  </tr>
  <tr>
    <td style="padding:20px;text-align:center;">
      <p style="margin:0 0 8px;font-size:12px;color:#aaa;font-style:italic;">
        "Hola, tu codigo de verificacion de TUT0hub es:"
      </p>
      <p style="margin:0 0 8px;font-size:32px;font-weight:900;
                color:#ffb700;letter-spacing:10px;">
        {code}
      </p>
      <p style="margin:0 0 8px;font-size:12px;color:#aaa;font-style:italic;">
        "{spoken}"
      </p>
      <p style="margin:0;font-size:11px;color:#666;font-style:italic;">
        "Este codigo expira en diez minutos."
      </p>
    </td>
  </tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#111;border-radius:10px;border-left:4px solid #4caf50;">
  <tr>
    <td style="padding:12px 18px;">
      <p style="margin:0;font-size:13px;color:#aaa;">
        En produccion esto seria una llamada de voz automatizada mediante
        <strong style="color:#fff;">Twilio Voice</strong>.
      </p>
    </td>
  </tr>
</table>
"""
    html = _base_template("Codigo por llamada — TUT0hub", content)
    text = f"TUT0hub llamada simulada: Tu codigo es {code} ({spoken}). Expira en 10 minutos."
    return _send_email("Codigo de recuperacion por llamada — TUT0hub", user_email, html, text)
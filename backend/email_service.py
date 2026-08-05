import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)

resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

PACKAGE_LABELS = {
    'conto': 'Conto/novela curta',
    'romance_medio': 'Romance médio',
    'romance_longo': 'Romance longo',
}


async def send_purchase_receipt(email: str, payment: dict):
    if not email or not os.environ.get('RESEND_API_KEY'):
        return
    pacote_label = PACKAGE_LABELS.get(payment['pacote'], payment['pacote'])
    valor_formatado = f"{float(payment['valor']):.2f}".replace('.', ',')
    creditos = payment['creditos_concedidos']

    html = f"""
    <div style="font-family: Georgia, serif; background:#0C0C0E; color:#E6E4DD; padding:32px; max-width:480px; margin:0 auto;">
      <h2 style="color:#F4F4F5; margin-bottom:8px;">Pagamento confirmado</h2>
      <p style="color:#9CA3AF;">Recebemos seu pagamento com sucesso. Seus créditos já estão disponíveis na sua carteira do CoWriter.</p>
      <table style="width:100%; border-collapse:collapse; margin-top:16px;">
        <tr><td style="padding:8px 0; color:#9CA3AF; border-bottom:1px solid #27272A;">Pacote</td><td style="padding:8px 0; text-align:right; border-bottom:1px solid #27272A;">{pacote_label}</td></tr>
        <tr><td style="padding:8px 0; color:#9CA3AF; border-bottom:1px solid #27272A;">Créditos adicionados</td><td style="padding:8px 0; text-align:right; color:#34D399; border-bottom:1px solid #27272A;">+{creditos}</td></tr>
        <tr><td style="padding:8px 0; color:#9CA3AF;">Valor pago</td><td style="padding:8px 0; text-align:right;">R$ {valor_formatado}</td></tr>
      </table>
      <p style="margin-top:24px; font-size:12px; color:#6B7280;">Os créditos não expiram. Obrigado por escrever com o CoWriter.</p>
    </div>
    """

    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": "Pagamento confirmado — créditos adicionados ao CoWriter",
        "html": html,
    }
    try:
        await asyncio.to_thread(resend.Emails.send, params)
    except Exception as e:
        logger.error(f"Failed to send purchase receipt email to {email}: {e}")

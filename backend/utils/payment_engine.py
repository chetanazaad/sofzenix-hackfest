import json, uuid, hashlib, base64, requests
from datetime import datetime
from flask import current_app


def initiate_upi_payout(upi_id: str, amount: float, reference_id: str) -> dict:
    from models import RewardSettings
    settings = RewardSettings.query.first()
    gateway = settings.primary_gateway if settings else 'razorpay'
    dev_mode = settings.dev_mode if settings else True

    if dev_mode:
        return _mock_payout(upi_id, amount, reference_id, gateway)
    elif gateway == 'phonepe':
        return _phonepe_payout(upi_id, amount, reference_id, settings)
    else:
        return _razorpay_payout(upi_id, amount, reference_id, settings)


def _mock_payout(upi_id, amount, reference_id, gateway='razorpay'):
    mock_txn_id = f"MOCK-TXN-{reference_id}-{uuid.uuid4().hex[:8].upper()}"
    return {
        'success': True,
        'transaction_id': mock_txn_id,
        'message': f'[DEV MODE] Mock payment of ₹{amount} sent to {upi_id} via {gateway}',
        'timestamp': datetime.utcnow().isoformat()
    }


def _razorpay_payout(upi_id, amount, reference_id, settings):
    try:
        key_id = settings.razorpayx_key_id
        key_secret = settings.razorpayx_key_secret
        account_number = settings.razorpayx_account_number
        if not key_id or not key_secret or not account_number:
            return {'success': False, 'message': 'Razorpay API credentials not configured.'}
        payload = {
            "account_number": account_number, "amount": int(amount * 100), "currency": "INR",
            "mode": "UPI", "purpose": "cashback",
            "fund_account": {
                "account_type": "vpa", "vpa": {"address": upi_id},
                "contact": {"name": "Reward Recipient", "contact": "9999999999", "type": "customer"}
            },
            "reference_id": reference_id, "narration": f"Reward {reference_id}"
        }
        response = requests.post("https://api.razorpay.com/v1/payouts", json=payload,
                                  auth=(key_id, key_secret), timeout=30)
        resp_data = response.json()
        if response.status_code in [200, 201] and resp_data.get('id'):
            return {'success': True, 'transaction_id': resp_data.get('id'),
                    'message': f"Payment initiated (Status: {resp_data.get('status')})", 'raw': resp_data}
        return {'success': False, 'transaction_id': None,
                'message': resp_data.get('error', {}).get('description', 'Payment failed'), 'raw': resp_data}
    except Exception as e:
        return {'success': False, 'transaction_id': None, 'message': f'Payment error: {str(e)}'}


def _phonepe_payout(upi_id, amount, reference_id, settings):
    try:
        merchant_id = settings.phonepe_merchant_id
        api_key = settings.phonepe_api_key
        if not merchant_id or not api_key:
            return {'success': False, 'message': 'PhonePe credentials not configured.'}
        payload_json = json.dumps({
            "merchantId": merchant_id, "merchantOrderId": reference_id,
            "amount": int(amount * 100),
            "paymentInstrument": {"type": "UPI_COLLECT", "vpa": upi_id}
        })
        payload_b64 = base64.b64encode(payload_json.encode()).decode()
        sha256_hash = hashlib.sha256((payload_b64 + "/v3/credit/backpayment" + api_key).encode()).hexdigest()
        headers = {"Content-Type": "application/json",
                   "X-VERIFY": sha256_hash + "###1", "X-MERCHANT-ID": merchant_id}
        response = requests.post("https://api.phonepe.com/apis/hermes/v3/credit/backpayment",
                                  json={"request": payload_b64}, headers=headers, timeout=30)
        resp_data = response.json()
        if resp_data.get('success') and resp_data.get('code') == 'PAYMENT_INITIATED':
            return {'success': True,
                    'transaction_id': resp_data.get('data', {}).get('transactionId', reference_id),
                    'message': 'Payment initiated via PhonePe', 'raw': resp_data}
        return {'success': False, 'transaction_id': None,
                'message': resp_data.get('message', 'PhonePe payment failed'), 'raw': resp_data}
    except Exception as e:
        return {'success': False, 'transaction_id': None, 'message': f'PhonePe error: {str(e)}'}

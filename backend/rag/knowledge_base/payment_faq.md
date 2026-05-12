# CartFlow — Payment FAQ

## What payment methods does CartFlow accept?

CartFlow accepts all major payment methods available in India:

- **UPI** — Google Pay (GPay), PhonePe, Paytm UPI, BHIM UPI, Amazon Pay UPI
- **Debit cards** — Rupay, Visa, Mastercard (all Indian banks supported)
- **Credit cards** — Visa, Mastercard, American Express, Rupay Credit Card (HDFC, ICICI, SBI, Axis, Kotak, and more)
- **Net banking** — All major Indian banks (SBI, HDFC, ICICI, Axis, PNB, Canara, and 50+ others)
- **Wallets** — Paytm Wallet, Amazon Pay, Mobikwik, Freecharge
- **CartFlow Wallet** — Pre-loaded wallet for instant payments
- **EMI** — No-cost EMI on credit cards and Bajaj Finserv; minimum order ₹3,000
- **Cash on Delivery (COD)** — Available on eligible orders below ₹10,000

---

## Is UPI payment safe on CartFlow?

Yes. CartFlow's UPI integration is certified by NPCI (National Payments Corporation of India). All UPI transactions are end-to-end encrypted and processed through a PCI-DSS compliant payment gateway. CartFlow never stores your UPI PIN or bank credentials.

---

## Why was my payment declined?

Common reasons for payment failure:
- **Insufficient balance** — Check your bank balance or UPI-linked account
- **Daily transaction limit exceeded** — Most UPI apps have a ₹1 lakh per day limit; credit cards may have per-transaction limits
- **Bank server downtime** — Try again after 10–15 minutes or use a different payment method
- **Card not enabled for online transactions** — Enable online/international transactions via your bank's app or net banking
- **OTP not entered within time** — The OTP expires in 3 minutes; if missed, restart the payment
- **VPA (UPI ID) incorrect** — Double-check the UPI ID if entering manually

If your payment fails but money is debited from your account, it will be automatically reversed within **3–5 business days**. If not, contact CartFlow support with your bank transaction reference number.

---

## How does EMI work on CartFlow?

CartFlow offers No-Cost EMI on eligible products (minimum order value ₹3,000):

1. At checkout, select **EMI** as the payment method
2. Choose your bank and tenure (3, 6, 9, or 12 months)
3. The total amount is divided equally — no extra interest charged to you (CartFlow absorbs the cost)
4. Your credit card is charged the monthly EMI amount automatically on your billing date

Bajaj Finserv EMI Card is also accepted for customers without a credit card. Check eligibility at checkout.

---

## What is CartFlow Wallet?

CartFlow Wallet is a prepaid balance stored in your CartFlow account. You can:
- Add money using UPI, debit card, or net banking
- Receive refunds directly into your wallet (instant)
- Use wallet balance for any CartFlow purchase
- Wallet balance never expires

Maximum wallet balance: ₹50,000 (as per RBI guidelines)

---

## Is Cash on Delivery available?

COD is available for orders below ₹10,000 to most serviceable pin codes. COD may be unavailable for:
- Remote or rural areas
- Orders with very high return rates from the delivery address
- Certain high-value or fragile items

A ₹30 COD handling fee may be applied for orders below ₹499.

---

## I paid but my order was not placed. What do I do?

This can happen due to a brief timeout between your bank and CartFlow's payment gateway. Follow these steps:
1. Check **My Orders** — the order may still have been placed successfully
2. Check your bank account / UPI history to confirm if the amount was debited
3. If debited but no order in My Orders, the payment will auto-reverse in 3–5 business days
4. To speed things up, contact CartFlow support with your payment reference number (UTR for UPI, or transaction ID for cards)

---

## Can I pay with multiple payment methods?

Yes, partially. You can use **CartFlow Wallet** in combination with any other payment method. For example, if your wallet has ₹200 and your order is ₹1,500, CartFlow Wallet covers ₹200 and you pay ₹1,300 via UPI or card.

Combining two external payment methods (e.g., two different credit cards) is not supported.

---

## How do I get a GST invoice?

During checkout, enter your **GSTIN** (GST Identification Number) in the "Add GST Details" section. A GST invoice will be generated and emailed to you within 24 hours of order dispatch. You can also download it from **My Orders > View Invoice**.

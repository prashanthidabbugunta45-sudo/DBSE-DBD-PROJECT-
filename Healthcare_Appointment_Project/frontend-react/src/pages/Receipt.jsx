import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api';

export default function Receipt() {
  const { receiptNumber } = useParams();
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { api(`/payments/receipt/${receiptNumber}`).then(setReceipt).catch((err) => setError(err.message)); }, [receiptNumber]);
  if (error) return <div className="container page"><div className="message error">{error}</div></div>;
  if (!receipt) return <div className="container page"><p className="muted">Loading receipt...</p></div>;
  function downloadReceipt() {
    const rows = [
      ['Receipt Number', receipt.receipt_number],
      ['Patient', `${receipt.patient_name} (${receipt.patient_id})`],
      ['Doctor', receipt.doctor_name],
      ['Specialization', receipt.specialization],
      ['Appointment Date', receipt.appointment_date],
      ['Appointment Time', receipt.appointment_time],
      ['Amount', `Rs. ${receipt.amount}`],
      ['Payment method', receipt.payment_method],
      ['Status', receipt.payment_status],
      ['Payment date', receipt.payment_date],
    ];
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>CarePlus Receipt ${receipt.receipt_number}</title><style>body{font-family:Arial,sans-serif;padding:32px;color:#1a1a1a}.brand{font-size:22px;font-weight:700;color:#0f766e;margin-bottom:4px}.sub{color:#666;margin-bottom:24px}table{width:100%;border-collapse:collapse}td{padding:10px 12px;border-bottom:1px solid #e5e5e5}td:first-child{color:#666;width:40%}.total{font-weight:700;font-size:18px}</style></head><body><div class="brand">♥ CarePlus</div><div class="sub">Official Payment Receipt</div><table>${rows.map(([label, value]) => `<tr><td>${label}</td><td>${value ?? ''}</td></tr>`).join('')}</table><p class="total">Amount Paid: Rs. ${receipt.amount}</p></body></html>`;
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `CarePlus_Receipt_${receipt.receipt_number}.html`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }
  return <div className="container page"><div className="receipt-card panel"><div className="receipt-success">✓</div><h1 className="page-title">Payment Successful</h1><p>CarePlus demo payment receipt</p><div className="receipt-number">{receipt.receipt_number}</div><dl className="receipt-details"><dt>Patient</dt><dd>{receipt.patient_name} ({receipt.patient_id})</dd><dt>Doctor</dt><dd>{receipt.doctor_name}</dd><dt>Specialization</dt><dd>{receipt.specialization}</dd><dt>Appointment Date</dt><dd>{receipt.appointment_date}</dd><dt>Appointment Time</dt><dd>{receipt.appointment_time}</dd><dt>Amount</dt><dd>Rs. {receipt.amount}</dd><dt>Payment method</dt><dd>{receipt.payment_method}</dd><dt>Status</dt><dd>{receipt.payment_status}</dd><dt>Payment date</dt><dd>{receipt.payment_date}</dd></dl><div className="actions"><button className="button primary" onClick={downloadReceipt}>Download Receipt</button><button className="button ghost" onClick={() => window.print()}>Print Receipt</button><Link className="button" to="/appointments">My Appointments</Link></div></div></div>;
}

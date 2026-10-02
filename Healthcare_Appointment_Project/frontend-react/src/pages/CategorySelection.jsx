import { Link } from 'react-router-dom';

const categories = [
  ['Heart / Chest Problem', 'Cardiology', '♥'],
  ['Skin Problem', 'Dermatology', '✦'],
  ['Headache / Nervous System', 'Neurology', '◉'],
  ['Bone / Joint', 'Orthopedics', '◆'],
  ['Eye Problem', 'Ophthalmology', '◌'],
  ['Dental Problem', 'Dentistry', '✚'],
  ['General Checkup', 'General Medicine', '＋'],
  ['Other', 'General Medicine', '…']
];

export default function CategorySelection() {
  return <div className="container page"><div className="category-heading"><div className="eyebrow">CarePlus patient portal</div><h1 className="page-title">What brings you here today?</h1><p className="muted">Select a general health concern to find the right specialist.</p></div><div className="category-grid">{categories.map(([label, value, icon]) => <Link className="category-card" to={`/doctors?specialization=${encodeURIComponent(value)}`} key={label}><span className="category-icon">{icon}</span><strong>{label}</strong><small>{value}</small></Link>)}</div></div>;
}

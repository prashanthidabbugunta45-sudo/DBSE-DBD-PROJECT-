import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api';

export default function DoctorProfile() {
  const { doctorId } = useParams();
  const [doctor, setDoctor] = useState(null);
  const [availability, setAvailability] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { Promise.all([api(`/doctors/${doctorId}`), api(`/doctors/${doctorId}/availability`)]).then(([profile, days]) => { setDoctor(profile); setAvailability(days); }).catch((err) => setError(err.message)); }, [doctorId]);
  if (error) return <div className="container page"><div className="message error">{error}</div></div>;
  if (!doctor) return <div className="container page"><p className="muted">Loading doctor profile...</p></div>;
  const days = [...new Set(availability.map((item) => item.day_of_week))];
  return <div className="container page"><Link to="/categories" className="muted">← Back to doctors</Link><div className="doctor-profile-page panel"><div className="doctor-profile-avatar">{doctor.full_name.split(' ').filter(Boolean).slice(-1)[0][0]}</div><div><div className="eyebrow">Doctor profile</div><h1 className="page-title">{doctor.full_name}</h1><p className="profile-specialization">{doctor.specialization}</p><p>{doctor.bio || 'Experienced CarePlus healthcare professional.'}</p><div className="profile-facts"><span><strong>Qualification</strong>{doctor.qualification || 'Healthcare specialist'}</span><span><strong>Experience</strong>{doctor.experience_years} years</span><span><strong>Available days</strong>{days.join(', ') || 'Not configured'}</span><span><strong>Consultation fee</strong>₹{doctor.consultation_fee}</span><span><strong>Contact</strong>{doctor.phone || doctor.email || 'CarePlus reception'}</span></div><Link className="button primary" to={`/doctors/${doctorId}/calendar`}>Book Appointment</Link></div></div></div>;
}

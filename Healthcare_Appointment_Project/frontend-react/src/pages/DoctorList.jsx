import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../api';

export default function DoctorList() {
  const [params] = useSearchParams();
  const [specializations, setSpecializations] = useState([]);
  const [specialization, setSpecialization] = useState(params.get('specialization') || '');
  const [doctors, setDoctors] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { async function load() { try { const items = await api('/doctors/specializations'); setSpecializations(items); const selected = items.find((item) => item.name === specialization) || items[0]; if (selected) { setSpecialization(selected.name); setDoctors(await api(`/doctors/by-specialization/${selected.specialization_id}`)); } } catch (err) { setError(err.message); } } load(); }, []);
  async function filter(event) { const name = event.target.value; setSpecialization(name); const selected = specializations.find((item) => item.name === name); if (!selected) return setDoctors([]); try { setDoctors(await api(`/doctors/by-specialization/${selected.specialization_id}`)); } catch (err) { setError(err.message); } }
  return <div className="container page"><div className="eyebrow">Dashboard / Doctors</div><h1 className="page-title">Find a Doctor</h1>{error && <div className="message error">{error}</div>}<div className="doctor-list-layout"><aside className="filter-panel panel"><label>Filter by specialization</label><select value={specialization} onChange={filter}><option value="">All specializations</option>{specializations.map((item) => <option key={item.specialization_id}>{item.name}</option>)}</select></aside><section className="doctor-results"><div className="doctor-grid">{doctors.map((doctor) => <article className="doctor-card-react card" key={doctor.doctor_id}><div className="doctor-card-avatar">{doctor.full_name.split(' ').filter(Boolean).slice(-1)[0][0]}</div><div><h3>{doctor.full_name}</h3><p className="profile-specialization">{specialization}</p><p className="muted">{doctor.qualification || 'Healthcare specialist'}</p><p className="muted">{doctor.experience_years} years experience</p>{doctor.available_days && <p className="muted">Available: {doctor.available_days}{doctor.available_from ? ` | ${doctor.available_from} - ${doctor.available_to}` : ''}</p>}<p className="muted">Consultation fee: ₹{doctor.consultation_fee}</p><Link className="button primary" to={`/doctors/${doctor.doctor_id}`}>View Profile</Link></div></article>)}</div>{!doctors.length && <p className="muted">No doctors found for this specialization.</p>}</section></div></div>;
}

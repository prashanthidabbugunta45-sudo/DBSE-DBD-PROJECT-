import { useEffect, useState } from 'react';
import { api } from '../api';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function ManageDoctors() {
  const [doctors, setDoctors] = useState([]);
  const [specializations, setSpecializations] = useState([]);
  const [form, setForm] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState('');
  const [availabilityDoctorId, setAvailabilityDoctorId] = useState(null);
  const [availability, setAvailability] = useState([]);
  const [availForm, setAvailForm] = useState({ day_of_week: 'Monday', start_time: '09:00', end_time: '11:00', is_available: true });

  async function load() {
    try {
      const [d, s] = await Promise.all([api('/admin/doctors'), api('/doctors/specializations')]);
      setDoctors(d);
      setSpecializations(s);
    } catch (e) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  function startEdit(d) {
    setEditingId(d.doctor_id);
    setForm({
      full_name: d.full_name, specialization_id: d.specialization_id, qualification: d.qualification || '',
      experience_years: d.experience_years, phone: d.phone || '', email: d.email || '', bio: d.bio || '',
      consultation_fee: d.consultation_fee,
    });
    document.getElementById('doctor-add').scrollIntoView();
  }

  function cancelEdit() { setEditingId(null); setForm({}); }

  async function submit(e) {
    e.preventDefault();
    setError('');
    const body = {
      ...form,
      specialization_id: Number(form.specialization_id),
      experience_years: Number(form.experience_years || 0),
      consultation_fee: form.consultation_fee ? Number(form.consultation_fee) : undefined,
    };
    try {
      if (editingId) {
        await api(`/admin/doctors/${editingId}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/admin/doctors', { method: 'POST', body: JSON.stringify(body) });
      }
      setEditingId(null);
      setForm({});
      load();
    } catch (err) { setError(err.message); }
  }

  async function openAvailability(doctorId) {
    setAvailabilityDoctorId(doctorId);
    try { setAvailability(await api(`/doctors/${doctorId}/availability`)); } catch (err) { setError(err.message); }
  }

  async function addAvailability(e) {
    e.preventDefault();
    try {
      await api(`/admin/doctors/${availabilityDoctorId}/availability`, { method: 'POST', body: JSON.stringify(availForm) });
      setAvailability(await api(`/doctors/${availabilityDoctorId}/availability`));
    } catch (err) { setError(err.message); }
  }

  async function removeAvailability(availabilityId) {
    try {
      await api(`/admin/availability/${availabilityId}`, { method: 'DELETE' });
      setAvailability(await api(`/doctors/${availabilityDoctorId}/availability`));
    } catch (err) { setError(err.message); }
  }

  return <div className="container page">
    <div className="dashboard-head">
      <div><div className="eyebrow">Administration</div><h1 className="page-title">Manage Doctors</h1></div>
      <button className="button primary" onClick={() => document.getElementById('doctor-add').scrollIntoView()}>+ Add Doctor</button>
    </div>
    {error && <div className="message error">{error}</div>}
    <div className="panel"><div className="table-wrap"><table className="table">
      <thead><tr><th>ID</th><th>Doctor</th><th>Specialization</th><th>Fee</th><th>Contact</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>{doctors.map((d) => <tr key={d.doctor_id}>
        <td>{d.doctor_id}</td><td>{d.full_name}</td><td>{d.specialization}</td>
        <td>₹{d.consultation_fee}</td><td>{d.phone || d.email || '-'}</td>
        <td><span className="status">{d.is_active ? 'Active' : 'Inactive'}</span></td>
        <td><button className="button ghost" onClick={() => startEdit(d)}>Edit</button>{' '}
          <button className="button ghost" onClick={() => openAvailability(d.doctor_id)}>Availability</button></td>
      </tr>)}</tbody>
    </table></div></div>

    <div id="doctor-add" className="panel add-form">
      <h2>{editingId ? `Edit Doctor #${editingId}` : 'Add Doctor'}</h2>
      <form className="form-grid" onSubmit={submit}>
        <div className="field"><label>Name</label><input name="full_name" required value={form.full_name || ''} onChange={update} /></div>
        <div className="field"><label>Specialization</label>
          <select name="specialization_id" required value={form.specialization_id || ''} onChange={update}>
            <option value="">Choose</option>
            {specializations.map((s) => <option key={s.specialization_id} value={s.specialization_id}>{s.name}</option>)}
          </select>
        </div>
        <div className="field"><label>Qualification</label><input name="qualification" value={form.qualification || ''} onChange={update} /></div>
        <div className="field"><label>Experience years</label><input name="experience_years" type="number" value={form.experience_years || ''} onChange={update} /></div>
        <div className="field"><label>Phone</label><input name="phone" value={form.phone || ''} onChange={update} /></div>
        <div className="field"><label>Email</label><input name="email" type="email" value={form.email || ''} onChange={update} /></div>
        <div className="field"><label>Consultation fee</label><input name="consultation_fee" type="number" step="0.01" value={form.consultation_fee || ''} onChange={update} /></div>
        <div className="field full"><label>Bio</label><input name="bio" value={form.bio || ''} onChange={update} /></div>
        <div className="field full">
          <button className="button primary">{editingId ? 'Save Changes' : 'Create Doctor'}</button>{' '}
          {editingId && <button type="button" className="button ghost" onClick={cancelEdit}>Cancel</button>}
        </div>
      </form>
    </div>

    {availabilityDoctorId && <div className="panel add-form">
      <h2>Availability for Doctor #{availabilityDoctorId}</h2>
      <div className="table-wrap"><table className="table">
        <thead><tr><th>Day</th><th>Start</th><th>End</th><th>Available</th><th></th></tr></thead>
        <tbody>{availability.map((a) => <tr key={a.availability_id}>
          <td>{a.day_of_week}</td><td>{a.start_time}</td><td>{a.end_time}</td><td>{a.is_available ? 'Yes' : 'No'}</td>
          <td><button className="button ghost" onClick={() => removeAvailability(a.availability_id)}>Remove</button></td>
        </tr>)}</tbody>
      </table></div>
      <form className="form-grid" onSubmit={addAvailability}>
        <div className="field"><label>Day</label>
          <select value={availForm.day_of_week} onChange={(e) => setAvailForm({ ...availForm, day_of_week: e.target.value })}>
            {WEEKDAYS.map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
        <div className="field"><label>Start time</label><input type="time" value={availForm.start_time} onChange={(e) => setAvailForm({ ...availForm, start_time: e.target.value })} /></div>
        <div className="field"><label>End time</label><input type="time" value={availForm.end_time} onChange={(e) => setAvailForm({ ...availForm, end_time: e.target.value })} /></div>
        <div className="field full"><button className="button primary">Add Availability Slot</button></div>
      </form>
    </div>}
  </div>;
}

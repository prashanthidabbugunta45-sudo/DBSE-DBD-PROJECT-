/* =========================================
   CAREPLUS - FRONTEND APP.JS
   Connects to FastAPI backend at localhost:8000
   ========================================= */

const API_BASE = "http://localhost:8001";

function getApiErrorMessage(data, fallback) {
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
        return data.detail.map(error => error.msg || "Invalid information.").join(" ");
    }
    return fallback;
}

/* =========================================
   1. NUMBER COUNTING ANIMATION (Homepage)
========================================= */
document.addEventListener("DOMContentLoaded", () => {
    const counters = document.querySelectorAll('.stat-number');
    if (!counters.length) return;

    const animateCounter = (counter) => {
        const target = +counter.getAttribute('data-target');
        const suffix = counter.getAttribute('data-suffix') || '';
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.innerText = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.innerText = target + suffix;
            }
        };
        updateCounter();
    };

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => observer.observe(c));
});


/* =========================================
   2. PASSWORD TOGGLE (Login Page)
========================================= */
const togglePassword = document.getElementById("togglePassword");
const loginPassword = document.getElementById("loginPassword");

if (togglePassword && loginPassword) {
    togglePassword.addEventListener("click", () => {
        const icon = togglePassword.querySelector("i");
        if (loginPassword.type === "password") {
            loginPassword.type = "text";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
        } else {
            loginPassword.type = "password";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
        }
    });
}


/* =========================================
   3. PATIENT REGISTRATION FORM
========================================= */
const registrationForm = document.getElementById("registrationForm");
if (registrationForm) {
    registrationForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const password = document.getElementById("regPassword").value;
        const confirm = document.getElementById("regConfirmPassword").value;

        if (password !== confirm) {
            alert("Passwords do not match");
            return;
        }

        const payload = {
            full_name: document.getElementById("regFullName").value.trim(),
            email: document.getElementById("regEmail").value.trim(),
            password: password,
            phone: document.getElementById("regPhone").value.trim(),
            date_of_birth: document.getElementById("regDob").value,
            age: parseInt(document.getElementById("regAge").value) || 0,
            gender: document.getElementById("regGender").value || null,
            address: document.getElementById("regAddress").value || null,
            emergency_contact_name: document.getElementById("regEmergencyName").value || null,
            emergency_contact_number: document.getElementById("regEmergencyNumber").value || null
        };

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                registrationForm.classList.add("hidden");
                document.getElementById("registrationSuccess").classList.remove("hidden");
                document.getElementById("registeredPatientName").textContent = data.patient_name;
                document.getElementById("registeredPatientId").textContent = data.patient_id;
            } else {
                alert(getApiErrorMessage(data, "Registration failed"));
            }
        } catch (err) {
            console.error(err);
            alert("Could not connect to server. Is the backend running?");
        }
    });
}


/* =========================================
   4. PATIENT LOGIN FORM
========================================= */
const patientLoginForm = document.getElementById("patientLoginForm");
if (patientLoginForm) {
    patientLoginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const login_id = document.getElementById("patientId").value.trim();
        const password = document.getElementById("loginPassword").value;

        if (!login_id || !password) {
            alert("Please enter your Patient ID/Email and password.");
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ login_id, password })
            });
            const data = await res.json();

            if (res.ok) {
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("patient_id", data.patient_id);
                localStorage.setItem("full_name", data.full_name);
                window.location.href = "dashboard.html";
            } else {
                alert(getApiErrorMessage(data, "Invalid Patient ID/email or password."));
            }
        } catch (err) {
            console.error(err);
            alert("Could not connect to server.");
        }
    });
}


/* =========================================
   5. ADMIN LOGIN FORM
========================================= */
const adminLoginForm = document.getElementById("adminLoginForm");
if (adminLoginForm) {
    adminLoginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("adminEmail").value.trim();
        const password = document.getElementById("adminPassword").value;

        try {
            const res = await fetch(`${API_BASE}/auth/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (res.ok) {
                localStorage.setItem("admin_token", data.access_token);
                localStorage.setItem("admin_name", data.full_name);
                window.location.href = "admin-dashboard.html";
            } else {
                alert(data.detail || "Admin login failed");
            }
        } catch (err) {
            console.error(err);
            alert("Could not connect to server.");
        }
    });
}


/* =========================================
   6. DASHBOARD
========================================= */
document.addEventListener("DOMContentLoaded", () => {
    if (!document.querySelector(".dashboard-page")) return;

    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "patient-login.html";
        return;
    }

    document.getElementById("patientName").textContent =
        localStorage.getItem("full_name") || "Patient";
    document.getElementById("patientIdDisplay").textContent =
        localStorage.getItem("patient_id") || "";

    loadMyAppointments(token);
    loadNotifications(token);
});

async function loadMyAppointments(token) {
    const list = document.getElementById("appointmentList");
    if (!list) return;
    list.innerHTML = "<p>Loading...</p>";

    try {
        const res = await fetch(`${API_BASE}/appointments/my`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (!res.ok) {
            list.innerHTML = `<p class="error-text">${data.detail}</p>`;
            return;
        }

        if (data.length === 0) {
            list.innerHTML = "<p>No appointments yet. Book your first appointment!</p>";
            return;
        }

        list.innerHTML = data.map(a => `
            <div class="appt-card">
                <div class="appt-header">
                    <strong>${a.doctor_name}</strong>
                    <span class="status-badge status-${a.status.replace(/\s/g, '')}">${a.status}</span>
                </div>
                <p>${a.specialization}</p>
                <p><i class="fa-regular fa-calendar"></i> ${a.appointment_date} at ${a.appointment_time}</p>
                <p><i class="fa-solid fa-hashtag"></i> Slot ${a.slot_number} &nbsp;|&nbsp; ID: ${a.appointment_id}</p>
                ${a.status === "Booked" || a.status === "Confirmed"
                ? `<button class="btn btn-outline" onclick="cancelAppointment(${a.appointment_id})">Cancel</button>`
                : ""}
                ${a.status === "Booked"
                ? `<button class="btn btn-solid" onclick="goToPayment(${a.appointment_id})">Pay Now</button>`
                : ""}
            </div>
        `).join("");
    } catch (err) {
        list.innerHTML = `<p class="error-text">Connection error</p>`;
    }
}

async function loadNotifications(token) {
    const list = document.getElementById("notificationList");
    if (!list) return;

    try {
        const res = await fetch(`${API_BASE}/notifications/my`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (!res.ok || data.length === 0) {
            list.innerHTML = "<p>No notifications.</p>";
            return;
        }

        list.innerHTML = data.map(n => `
            <div class="notif-card ${n.is_read ? 'read' : 'unread'}">
                <strong>${n.title}</strong>
                <p>${n.message}</p>
                <small>${n.created_at}</small>
                ${n.is_read ? "" : `<button class="btn btn-outline" onclick="markNotificationRead(${n.notification_id})">Mark read</button>`}
            </div>
        `).join("");
    } catch (err) {
        list.innerHTML = "<p>Connection error</p>";
    }
}

async function cancelAppointment(apptId) {
    if (!confirm("Cancel this appointment?")) return;
    const token = localStorage.getItem("token");
    try {
        const res = await fetch(`${API_BASE}/appointments/cancel/${apptId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        alert(data.message || data.detail);
        loadMyAppointments(token);
    } catch (err) {
        alert("Error cancelling");
    }
}

function goToPayment(apptId) {
    localStorage.setItem("pay_appt_id", apptId);
    window.location.href = "payment.html";
}

function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}


/* =========================================
   7. BOOKING PAGE
========================================= */
let selectedSpecId = null;
let selectedSpecName = null;
let selectedDoctorId = null;
let selectedDoctorName = null;
let selectedDate = null;

document.addEventListener("DOMContentLoaded", () => {
    if (!document.querySelector(".booking-page")) return;
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "patient-login.html";
        return;
    }
    document.querySelectorAll(".problem-card").forEach(btn => {
        btn.addEventListener("click", () => {
            selectedSpecName = btn.dataset.spec;
            loadDoctorsBySpec(selectedSpecName);
        });
    });
});

async function loadDoctorsBySpec(specName) {
    try {
        // Get all specializations
        const specRes = await fetch(`${API_BASE}/doctors/specializations`);
        const specs = await specRes.json();
        const spec = specs.find(s => s.name === specName);
        if (!spec) {
            alert("Specialization not found");
            return;
        }
        selectedSpecId = spec.specialization_id;

        const docRes = await fetch(`${API_BASE}/doctors/by-specialization/${selectedSpecId}`);
        const doctors = await docRes.json();

        document.getElementById("step1").classList.add("hidden");
        document.getElementById("step2").classList.remove("hidden");

        const list = document.getElementById("doctorList");
        if (doctors.length === 0) {
            list.innerHTML = "<p>No doctors available in this specialization.</p>";
            return;
        }
        list.innerHTML = doctors.map(d => `
            <div class="doctor-card" onclick="selectDoctor(${d.doctor_id}, '${d.full_name}')">
                <div class="doctor-avatar"><i class="fa-solid fa-user-doctor"></i></div>
                <h3>${d.full_name}</h3>
                <p>${d.qualification}</p>
                <p>${d.experience_years} years experience</p>
                <button class="btn btn-solid">Select Doctor</button>
            </div>
        `).join("");
    } catch (err) {
        alert("Error loading doctors");
    }
}

function selectDoctor(id, name) {
    selectedDoctorId = id;
    selectedDoctorName = name;
    document.getElementById("selectedDoctorName").textContent = "Doctor: " + name;
    document.getElementById("step2").classList.add("hidden");
    document.getElementById("step3").classList.remove("hidden");
    loadDoctorProfile(id);
    loadCalendar(id);
}

async function loadDoctorProfile(doctorId) {
    const profile = document.getElementById("doctorProfile");
    if (!profile) return;
    profile.textContent = "Loading doctor profile...";
    try {
        const res = await fetch(`${API_BASE}/doctors/${doctorId}`);
        const doctor = await res.json();
        if (!res.ok) {
            profile.textContent = getApiErrorMessage(doctor, "Doctor profile unavailable");
            return;
        }
        profile.innerHTML = `
            <strong>${doctor.full_name}</strong>
            <span>${doctor.qualification || "Healthcare specialist"} | ${doctor.experience_years} years experience</span>
            <p>${doctor.bio || "Available for CarePlus appointments."}</p>
        `;
    } catch (error) {
        profile.textContent = "Doctor profile unavailable";
    }
}

async function loadCalendar(doctorId) {
    const cal = document.getElementById("calendar");
    cal.innerHTML = "<p>Loading calendar...</p>";

    try {
        const res = await fetch(`${API_BASE}/appointments/calendar/${doctorId}`);
        const data = await res.json();

        cal.innerHTML = data.map(day => `
              <div class="calendar-day ${day.status.toLowerCase()}"
                  onclick="selectDate('${day.date}', '${day.status}')">
                <span class="day-date">${day.date}</span>
                <span class="day-status">${day.status}</span>
                ${day.status === "Available"
                ? `<small>${day.booked}/10</small>`
                : day.status === "Holiday"
                    ? `<small>${day.reason}</small>`
                    : day.status === "Unavailable"
                        ? `<small>Not available</small>`
                        : `<small>10/10</small>`}
            </div>
        `).join("");
    } catch (err) {
        cal.innerHTML = "<p>Error loading calendar</p>";
    }
}

async function selectDate(dateStr, status) {
    if (status === "Holiday") {
        alert("Holiday - Hospital Closed");
        return;
    }
    if (status === "Full") {
        alert("This doctor is fully booked on this date (10/10). Please select another date.");
        return;
    }
    if (status === "Unavailable") {
        alert("This doctor is not available on the selected date.");
        return;
    }

    selectedDate = dateStr;
    document.getElementById("apptPatientName").value = localStorage.getItem("full_name") || "";
    document.getElementById("apptDoctorName").value = selectedDoctorName;
    document.getElementById("apptDate").value = dateStr;

    // Load time slots
    const token = localStorage.getItem("token");
    try {
        const res = await fetch(`${API_BASE}/appointments/available-slots/${selectedDoctorId}/${dateStr}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.detail);
            return;
        }

        const sel = document.getElementById("apptTime");
        sel.innerHTML = '<option value="">Choose a time slot</option>';
        data.available_slots.forEach(t => {
            sel.innerHTML += `<option value="${t}">${t}</option>`;
        });
        document.getElementById("slotsInfo").textContent =
            `${data.booked}/10 booked — ${data.remaining} slots remaining`;

        document.getElementById("step3").classList.add("hidden");
        document.getElementById("step4").classList.remove("hidden");
    } catch (err) {
        alert("Error loading slots");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("confirmBookingBtn");
    if (!btn) return;
    btn.addEventListener("click", async () => {
        const time = document.getElementById("apptTime").value;
        const reason = document.getElementById("apptReason").value.trim();
        if (!time || !reason) {
            alert("Please select a time and enter the reason");
            return;
        }

        const token = localStorage.getItem("token");
        try {
            const appointmentsRes = await fetch(`${API_BASE}/appointments/my`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const appointments = await appointmentsRes.json();
            const sameDayOtherDoctor = appointments.find(appointment =>
                appointment.appointment_date === selectedDate &&
                appointment.doctor_id !== selectedDoctorId &&
                !["Cancelled", "No Show", "Visited – Appointment Not Completed"].includes(appointment.status)
            );
            if (sameDayOtherDoctor && !confirm("You already have an appointment with another doctor on this date. Continue with this second doctor?")) {
                return;
            }

            const res = await fetch(`${API_BASE}/appointments/book`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    doctor_id: selectedDoctorId,
                    specialization_id: selectedSpecId,
                    appointment_date: selectedDate,
                    appointment_time: time,
                    reason: reason
                })
            });
            const data = await res.json();

            if (res.ok) {
                alert("Appointment Booked!\n\nAppointment ID: " + data.appointment_id +
                    "\nSlot #" + data.slot_number +
                    "\n\nProceeding to payment...");
                localStorage.setItem("pay_appt_id", data.appointment_id);
                window.location.href = "payment.html";
            } else {
                alert(data.detail || "Booking failed");
            }
        } catch (err) {
            alert("Connection error");
        }
    });
});

function goBackToStep1() {
    document.getElementById("step2").classList.add("hidden");
    document.getElementById("step1").classList.remove("hidden");
}
function goBackToStep2() {
    document.getElementById("step3").classList.add("hidden");
    document.getElementById("step2").classList.remove("hidden");
}
function goBackToStep3() {
    document.getElementById("step4").classList.add("hidden");
    document.getElementById("step3").classList.remove("hidden");
}


/* =========================================
   8. PAYMENT PAGE
========================================= */
document.addEventListener("DOMContentLoaded", () => {
    if (!document.querySelector(".payment-page")) return;
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "patient-login.html";
        return;
    }
    const apptId = localStorage.getItem("pay_appt_id");
    if (!apptId) {
        alert("No appointment selected");
        window.location.href = "dashboard.html";
        return;
    }
    document.getElementById("payApptId").textContent = apptId;

    document.getElementById("payNowBtn").addEventListener("click", async () => {
        const method = document.getElementById("paymentMethod").value;
        try {
            const res = await fetch(`${API_BASE}/payments/pay`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    appointment_id: parseInt(apptId),
                    payment_method: method
                })
            });
            const data = await res.json();

            if (res.ok) {
                document.getElementById("receiptNum").textContent = data.receipt_number;
                document.getElementById("receiptAmount").textContent = data.amount;
                document.getElementById("receiptSection").classList.remove("hidden");
                document.getElementById("payNowBtn").style.display = "none";
            } else {
                alert(data.detail || "Payment failed");
            }
        } catch (err) {
            alert("Connection error");
        }
    });
});


/* =========================================
   9. ADMIN DASHBOARD
========================================= */
document.addEventListener("DOMContentLoaded", () => {
    if (!document.querySelector(".admin-dashboard-page")) return;
    const token = localStorage.getItem("admin_token");
    if (!token) {
        window.location.href = "admin-login.html";
        return;
    }
    document.getElementById("adminName").textContent =
        localStorage.getItem("admin_name") || "Admin";

    loadAdminStats(token);
    loadAllAppointments(token);
    loadAllPatients(token);
    loadAdminDoctors(token);
    loadAdminHolidays(token);
    loadAdminPayments(token);
    setupAdminForms(token);
});

async function loadAdminStats(token) {
    try {
        const res = await fetch(`${API_BASE}/admin/dashboard`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const d = await res.json();
        document.getElementById("statPatients").textContent = d.total_patients;
        document.getElementById("statDoctors").textContent = d.total_doctors;
        document.getElementById("statAppointments").textContent = d.total_appointments;
        document.getElementById("statToday").textContent = d.today_appointments;
    } catch (err) {
        console.error(err);
    }
}

async function loadAllAppointments(token) {
    const list = document.getElementById("adminAppointmentList");
    if (!list) return;

    try {
        const res = await fetch(`${API_BASE}/admin/appointments`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        list.innerHTML = `
            <table class="admin-table">
                <thead>
                    <tr>
                        <th>ID</th><th>Patient</th><th>Doctor</th>
                        <th>Date</th><th>Time</th><th>Slot</th>
                        <th>Status</th><th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(a => `
                        <tr>
                            <td>${a.appointment_id}</td>
                            <td>${a.patient_name}</td>
                            <td>${a.doctor_name}</td>
                            <td>${a.appointment_date}</td>
                            <td>${a.appointment_time}</td>
                            <td>${a.slot_number}</td>
                            <td>${a.status}</td>
                            <td>
                                <select onchange="updateStatus(${a.appointment_id}, this.value)">
                                    <option value="">Update</option>
                                    <option value="Confirmed">Confirmed</option>
                                    <option value="Completed">Completed</option>
                                    <option value="Visited – Appointment Not Completed">Visited – Not Completed</option>
                                    <option value="No Show">No Show</option>
                                    <option value="Cancelled">Cancelled</option>
                                </select>
                            </td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    } catch (err) {
        list.innerHTML = "<p>Error loading appointments</p>";
    }
}

async function loadAllPatients(token) {
    const list = document.getElementById("adminPatientList");
    if (!list) return;

    try {
        const res = await fetch(`${API_BASE}/admin/patients`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        list.innerHTML = `
            <table class="admin-table">
                <thead>
                    <tr><th>Patient ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Age</th><th>Gender</th></tr>
                </thead>
                <tbody>
                    ${data.map(p => `
                        <tr>
                            <td>${p.patient_id}</td>
                            <td>${p.full_name}</td>
                            <td>${p.email}</td>
                            <td>${p.phone}</td>
                            <td>${p.age || "-"}</td>
                            <td>${p.gender || "-"}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    } catch (err) {
        list.innerHTML = "<p>Error loading patients</p>";
    }
}

async function updateStatus(apptId, newStatus) {
    if (!newStatus) return;
    const token = localStorage.getItem("admin_token");
    try {
        const res = await fetch(`${API_BASE}/admin/appointments/${apptId}/status`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (res.ok) {
            alert("Status updated");
            loadAllAppointments(token);
        } else {
            alert(data.detail || "Update failed");
        }
    } catch (err) {
        alert("Error updating status");
    }
}

function adminLogout() {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_name");
    window.location.href = "admin-login.html";
}

async function loadAdminDoctors(token) {
    const list = document.getElementById("adminDoctorList");
    if (!list) return;
    try {
        const res = await fetch(`${API_BASE}/admin/doctors`, { headers: { "Authorization": `Bearer ${token}` } });
        const data = await res.json();
        list.innerHTML = `<table class="admin-table"><thead><tr><th>Name</th><th>Specialization</th><th>Experience</th><th>Status</th></tr></thead><tbody>${data.map(d => `
            <tr><td>${d.full_name}</td><td>${d.specialization}</td><td>${d.experience_years} years</td><td>${d.is_active ? "Active" : "Inactive"}</td></tr>
        `).join("")}</tbody></table>`;
        const specRes = await fetch(`${API_BASE}/doctors/specializations`);
        const specs = await specRes.json();
        document.getElementById("doctorSpecialization").innerHTML = specs.map(s => `<option value="${s.specialization_id}">${s.name}</option>`).join("");
    } catch (error) {
        list.innerHTML = "<p class='error-text'>Error loading doctors</p>";
    }
}

async function loadAdminHolidays(token) {
    const list = document.getElementById("adminHolidayList");
    if (!list) return;
    try {
        const res = await fetch(`${API_BASE}/admin/holidays`, { headers: { "Authorization": `Bearer ${token}` } });
        const data = await res.json();
        list.innerHTML = `<table class="admin-table"><thead><tr><th>Date</th><th>Reason</th><th>Action</th></tr></thead><tbody>${data.map(h => `
            <tr><td>${h.holiday_date}</td><td>${h.reason}</td><td><button class="btn btn-outline" onclick="deleteHoliday(${h.holiday_id})">Delete</button></td></tr>
        `).join("")}</tbody></table>`;
    } catch (error) {
        list.innerHTML = "<p class='error-text'>Error loading holidays</p>";
    }
}

async function loadAdminPayments(token) {
    const list = document.getElementById("adminPaymentList");
    if (!list) return;
    try {
        const res = await fetch(`${API_BASE}/admin/payments`, { headers: { "Authorization": `Bearer ${token}` } });
        const data = await res.json();
        list.innerHTML = `<table class="admin-table"><thead><tr><th>Receipt</th><th>Patient</th><th>Appointment</th><th>Amount</th><th>Status</th></tr></thead><tbody>${data.map(p => `
            <tr><td>${p.receipt_number}</td><td>${p.patient_name}</td><td>${p.appointment_id}</td><td>₹${p.amount}</td><td>${p.payment_status}</td></tr>
        `).join("")}</tbody></table>`;
    } catch (error) {
        list.innerHTML = "<p class='error-text'>Error loading payments</p>";
    }
}

function setupAdminForms(token) {
    const doctorForm = document.getElementById("doctorForm");
    if (doctorForm) doctorForm.addEventListener("submit", async event => {
        event.preventDefault();
        const payload = {
            full_name: document.getElementById("doctorName").value.trim(),
            specialization_id: Number(document.getElementById("doctorSpecialization").value),
            qualification: document.getElementById("doctorQualification").value.trim() || null,
            experience_years: Number(document.getElementById("doctorExperience").value) || 0,
            phone: document.getElementById("doctorPhone").value.trim() || null,
            email: document.getElementById("doctorEmail").value.trim() || null,
            bio: document.getElementById("doctorBio").value.trim() || null
        };
        const res = await fetch(`${API_BASE}/admin/doctors`, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!res.ok) return alert(getApiErrorMessage(data, "Could not create doctor"));
        doctorForm.reset();
        loadAdminDoctors(token);
    });

    const holidayForm = document.getElementById("holidayForm");
    if (holidayForm) holidayForm.addEventListener("submit", async event => {
        event.preventDefault();
        const payload = { holiday_date: document.getElementById("holidayDate").value, reason: document.getElementById("holidayReason").value.trim() };
        const res = await fetch(`${API_BASE}/admin/holidays`, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!res.ok) return alert(getApiErrorMessage(data, "Could not create holiday"));
        holidayForm.reset();
        loadAdminHolidays(token);
    });
}

async function deleteHoliday(holidayId) {
    if (!confirm("Delete this holiday?")) return;
    const token = localStorage.getItem("admin_token");
    const res = await fetch(`${API_BASE}/admin/holidays/${holidayId}`, { method: "DELETE", headers: { "Authorization": `Bearer ${token}` } });
    const data = await res.json();
    if (!res.ok) return alert(getApiErrorMessage(data, "Could not delete holiday"));
    loadAdminHolidays(token);
}

async function markNotificationRead(notificationId) {
    const token = localStorage.getItem("token");
    const res = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) loadNotifications(token);
}
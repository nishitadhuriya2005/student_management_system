/**
 * Student Management System - Frontend Application Logic
 * Integrates with AWS Lambda / API Gateway / DynamoDB or Local Server with fallback
 */

// Application State
let state = {
  students: [],
  filteredStudents: [],
  analytics: null,
  activeMode: 'local', // 'aws' or 'local'
  apiUrl: '',
  selectedStudent: null,
  isChartsOpen: true
};

// Chart instances
let deptChartInstance = null;
let yearChartInstance = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  initConfiguration();
  loadStudents();
});

// ----------------- Configuration & Connection -----------------

function initConfiguration() {
  const savedUrl = localStorage.getItem('sms_api_url') || (window.APP_CONFIG && window.APP_CONFIG.apiUrl) || '';
  const savedMode = localStorage.getItem('sms_mode') || (savedUrl ? 'aws' : 'local');

  state.apiUrl = savedUrl;
  state.activeMode = savedMode;

  updateConnectionBadge();
}

function updateConnectionBadge() {
  const badgeText = document.getElementById('connectionStatusText');
  const ping = document.getElementById('statusIndicatorPing');
  const dot = document.getElementById('statusIndicatorDot');
  const btn = document.getElementById('connectionStatusBtn');

  if (state.activeMode === 'aws' && state.apiUrl) {
    badgeText.textContent = 'AWS Cloud Active';
    btn.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all cursor-pointer bg-amber-50 text-amber-900 border-amber-300 hover:bg-amber-100';
    ping.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75';
    dot.className = 'relative inline-flex rounded-full h-2 w-2 bg-amber-500';
  } else {
    badgeText.textContent = 'Local / Mock Mode';
    btn.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all cursor-pointer bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100';
    ping.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75';
    dot.className = 'relative inline-flex rounded-full h-2 w-2 bg-emerald-500';
  }
}

function getBaseApiUrl() {
  if (state.activeMode === 'aws' && state.apiUrl) {
    return state.apiUrl.replace(/\/+$/, '');
  }
  // Check if served from local python server
  if (window.location.protocol.startsWith('http')) {
    return window.location.origin;
  }
  return '';
}

// ----------------- API Calls with Fallback -----------------

async function apiRequest(endpoint, method = 'GET', body = null) {
  const baseUrl = getBaseApiUrl();

  // If we have an HTTP server running or AWS API URL configured
  if (baseUrl) {
    let cleanEndpoint = endpoint;
    // If local server, prefix with /api if needed, or directly
    if (!state.apiUrl && !endpoint.startsWith('/api') && !endpoint.startsWith('/students') && !endpoint.startsWith('/analytics') && !endpoint.startsWith('/seed')) {
      cleanEndpoint = `/api${endpoint}`;
    }

    const url = `${baseUrl}${cleanEndpoint}`;
    try {
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      };
      if (body) {
        options.body = JSON.stringify(body);
      }

      const res = await fetch(url, options);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.warn(`Cloud API call error for ${url}:`, err);
      showToast('Operating in Cloud Sync (Local Fallback)', 'info');
      return offlineHandler(endpoint, method, body);
    }
  }

  // Pure Offline Browser LocalStorage fallback
  return offlineHandler(endpoint, method, body);
}

// Seamless offline fallback implementation if server is closed or viewing directly via file://
function offlineHandler(endpoint, method, body) {
  let db = JSON.parse(localStorage.getItem('sms_offline_db') || 'null');
  if (!db) {
    db = getInitialMockData();
    localStorage.setItem('sms_offline_db', JSON.stringify(db));
  }

  if (endpoint.startsWith('/students') || endpoint.startsWith('/api/students')) {
    const parts = endpoint.split('/').filter(Boolean);
    const lastPart = parts[parts.length - 1];

    if (method === 'GET' && lastPart !== 'students') {
      const s = db.find(item => item.student_id === lastPart);
      if (!s) throw new Error('Student not found');
      return { student: s };
    }

    if (method === 'GET') {
      return { count: db.length, students: db };
    }

    if (method === 'POST') {
      if (db.some(s => s.student_id === body.student_id)) {
        throw new Error(`Student ${body.student_id} already exists`);
      }
      const newStudent = {
        ...body,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      db.unshift(newStudent);
      localStorage.setItem('sms_offline_db', JSON.stringify(db));
      return { message: 'Created successfully', student: newStudent };
    }

    if (method === 'PUT') {
      const idx = db.findIndex(s => s.student_id === lastPart);
      if (idx === -1) throw new Error('Student not found');
      db[idx] = { ...db[idx], ...body, updated_at: new Date().toISOString() };
      localStorage.setItem('sms_offline_db', JSON.stringify(db));
      return { message: 'Updated successfully', student: db[idx] };
    }

    if (method === 'DELETE') {
      db = db.filter(s => s.student_id !== lastPart);
      localStorage.setItem('sms_offline_db', JSON.stringify(db));
      return { message: 'Deleted successfully' };
    }
  }

  if (endpoint.includes('analytics') || endpoint.includes('stats')) {
    return computeAnalytics(db);
  }

  if (endpoint.includes('seed')) {
    db = getInitialMockData();
    localStorage.setItem('sms_offline_db', JSON.stringify(db));
    return { message: 'Seeded successfully', seeded_count: db.length };
  }

  return { message: 'OK' };
}

function getInitialMockData() {
  return [
    {
      student_id: "STU-1001",
      first_name: "Aarav",
      last_name: "Sharma",
      email: "aarav.sharma@university.edu",
      phone: "+1-555-0101",
      department: "Computer Science",
      year: "3rd Year",
      gpa: 3.88,
      status: "Active",
      enrollment_date: "2022-08-15",
      courses: ["Cloud Computing", "Data Structures", "Operating Systems"]
    },
    {
      student_id: "STU-1002",
      first_name: "Sophia",
      last_name: "Chen",
      email: "sophia.chen@university.edu",
      phone: "+1-555-0102",
      department: "Electrical Engineering",
      year: "4th Year",
      gpa: 3.92,
      status: "Active",
      enrollment_date: "2021-08-20",
      courses: ["Signals & Systems", "Digital Circuits", "Embedded Systems"]
    },
    {
      student_id: "STU-1003",
      first_name: "Marcus",
      last_name: "Johnson",
      email: "marcus.j@university.edu",
      phone: "+1-555-0103",
      department: "Mechanical Engineering",
      year: "2nd Year",
      gpa: 3.45,
      status: "Active",
      enrollment_date: "2023-08-18",
      courses: ["Thermodynamics", "Statics", "CAD Design"]
    },
    {
      student_id: "STU-1004",
      first_name: "Ananya",
      last_name: "Patel",
      email: "ananya.patel@university.edu",
      phone: "+1-555-0104",
      department: "Data Science",
      year: "3rd Year",
      gpa: 3.75,
      status: "Active",
      enrollment_date: "2022-08-15",
      courses: ["Machine Learning", "Data Mining", "Applied Statistics"]
    },
    {
      student_id: "STU-1005",
      first_name: "Liam",
      last_name: "Smith",
      email: "liam.smith@university.edu",
      phone: "+1-555-0105",
      department: "Business Administration",
      year: "4th Year",
      gpa: 3.60,
      status: "Graduated",
      enrollment_date: "2020-08-24",
      courses: ["Corporate Finance", "Strategic Management", "Marketing Principles"]
    }
  ];
}

function computeAnalytics(db) {
  let total = db.length;
  let totalGpa = 0;
  let validGpa = 0;
  let depts = {};
  let statuses = {};
  let years = {};

  db.forEach(s => {
    const g = parseFloat(s.gpa);
    if (!isNaN(g) && g > 0) {
      totalGpa += g;
      validGpa++;
    }
    depts[s.department] = (depts[s.department] || 0) + 1;
    statuses[s.status] = (statuses[s.status] || 0) + 1;
    years[s.year] = (years[s.year] || 0) + 1;
  });

  return {
    total_students: total,
    average_gpa: validGpa > 0 ? (totalGpa / validGpa).toFixed(2) : 0,
    departments: depts,
    status_breakdown: statuses,
    year_breakdown: years
  };
}

// ----------------- Data Loading & UI Rendering -----------------

async function loadStudents() {
  const tbody = document.getElementById('studentTableBody');
  tbody.innerHTML = `
    <tr>
      <td colspan="7" class="text-center py-12 text-slate-400">
        <i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-indigo-500 mb-2"></i>
        <p class="text-sm">Fetching student records from DynamoDB...</p>
      </td>
    </tr>
  `;
  if (window.lucide) lucide.createIcons();

  try {
    const data = await apiRequest('/students');
    state.students = data.students || [];
    filterStudents();
    loadAnalytics();
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-12 text-rose-500">
          <i data-lucide="alert-circle" class="w-8 h-8 mx-auto mb-2"></i>
          <p class="text-sm font-semibold">Failed to load student data</p>
          <p class="text-xs text-slate-500 mt-1">${err.message}</p>
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
  }
}

async function loadAnalytics() {
  try {
    const data = await apiRequest('/analytics');
    state.analytics = data;

    // Update KPI counters
    document.getElementById('statTotalStudents').textContent = data.total_students || 0;
    document.getElementById('statActiveStudents').textContent = (data.status_breakdown && data.status_breakdown['Active']) || 0;
    document.getElementById('statAvgGpa').textContent = data.average_gpa || '0.00';

    renderCharts(data);
  } catch (err) {
    console.error('Analytics load error:', err);
  }
}

function filterStudents() {
  const search = (document.getElementById('searchInput').value || '').trim().toLowerCase();
  const dept = document.getElementById('departmentFilter').value;
  const status = document.getElementById('statusFilter').value;

  state.filteredStudents = state.students.filter(s => {
    const matchSearch = !search ||
      (s.first_name || '').toLowerCase().includes(search) ||
      (s.last_name || '').toLowerCase().includes(search) ||
      (s.student_id || '').toLowerCase().includes(search) ||
      (s.email || '').toLowerCase().includes(search);

    const matchDept = dept === 'All' || s.department === dept;
    const matchStatus = status === 'All' || s.status === status;

    return matchSearch && matchDept && matchStatus;
  });

  renderStudentTable();
}

function handleSearch() {
  const query = document.getElementById('searchInput').value;
  const clearBtn = document.getElementById('clearSearchBtn');
  if (query.length > 0) {
    clearBtn.classList.remove('hidden');
  } else {
    clearBtn.classList.add('hidden');
  }
  filterStudents();
}

function clearSearch() {
  document.getElementById('searchInput').value = '';
  document.getElementById('clearSearchBtn').classList.add('hidden');
  filterStudents();
}

function renderStudentTable() {
  const tbody = document.getElementById('studentTableBody');
  const countText = document.getElementById('showingCountText');

  countText.textContent = `Showing ${state.filteredStudents.length} of ${state.students.length} students`;

  if (state.filteredStudents.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-12 text-slate-400">
          <i data-lucide="user-x" class="w-8 h-8 mx-auto text-slate-300 mb-2"></i>
          <p class="text-sm font-semibold text-slate-600">No students found</p>
          <p class="text-xs text-slate-400 mt-1">Try adjusting your search criteria or add a student.</p>
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  tbody.innerHTML = state.filteredStudents.map(student => {
    const initials = `${(student.first_name || '')[0] || ''}${(student.last_name || '')[0] || ''}`.toUpperCase();
    const gpa = parseFloat(student.gpa || 0).toFixed(2);
    
    // Status badges
    let statusClass = 'badge-active';
    if (student.status === 'Graduated') statusClass = 'badge-graduated';
    else if (student.status === 'Inactive') statusClass = 'badge-inactive';
    else if (student.status === 'Suspended') statusClass = 'badge-suspended';

    // GPA badge color
    let gpaColor = 'text-slate-700 bg-slate-100';
    if (gpa >= 3.7) gpaColor = 'text-emerald-700 bg-emerald-50 border border-emerald-200';
    else if (gpa >= 3.0) gpaColor = 'text-indigo-700 bg-indigo-50 border border-indigo-200';
    else if (gpa >= 2.0) gpaColor = 'text-amber-700 bg-amber-50 border border-amber-200';
    else gpaColor = 'text-rose-700 bg-rose-50 border border-rose-200';

    return `
      <tr class="table-row-hover transition-colors">
        <!-- Student Info -->
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="flex items-center space-x-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 text-white font-bold text-xs flex items-center justify-center shadow-sm">
              ${initials}
            </div>
            <div>
              <div class="font-semibold text-slate-900 text-sm hover:text-indigo-600 cursor-pointer" onclick="viewStudent('${student.student_id}')">
                ${student.first_name} ${student.last_name}
              </div>
              <div class="text-xs text-slate-400 flex items-center space-x-1">
                <span>${student.email}</span>
              </div>
            </div>
          </div>
        </td>

        <!-- Student ID -->
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
            ${student.student_id}
          </span>
        </td>

        <!-- Department -->
        <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
          ${student.department || 'General'}
        </td>

        <!-- Year -->
        <td class="px-6 py-4 whitespace-nowrap text-xs text-slate-600">
          ${student.year || '1st Year'}
        </td>

        <!-- GPA -->
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${gpaColor}">
            ${gpa}
          </span>
        </td>

        <!-- Status -->
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
            ${student.status || 'Active'}
          </span>
        </td>

        <!-- Actions -->
        <td class="px-6 py-4 whitespace-nowrap text-right text-xs font-medium space-x-2">
          <button onclick="viewStudent('${student.student_id}')" title="View Details" class="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
            <i data-lucide="eye" class="w-4 h-4"></i>
          </button>
          <button onclick="editStudent('${student.student_id}')" title="Edit Student" class="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors">
            <i data-lucide="edit-3" class="w-4 h-4"></i>
          </button>
          <button onclick="promptDelete('${student.student_id}', '${student.first_name} ${student.last_name}')" title="Delete Student" class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  if (window.lucide) {
    lucide.createIcons();
  }
}

// ----------------- Interactive Charts -----------------

function renderCharts(analytics) {
  if (!window.Chart || !analytics) return;

  const depts = analytics.departments || {};
  const years = analytics.year_breakdown || {};

  // Department Doughnut Chart
  const deptCtx = document.getElementById('deptChart');
  if (deptCtx) {
    if (deptChartInstance) deptChartInstance.destroy();

    const deptLabels = Object.keys(depts);
    const deptValues = Object.values(depts);

    deptChartInstance = new Chart(deptCtx, {
      type: 'doughnut',
      data: {
        labels: deptLabels.length ? deptLabels : ['No Data'],
        datasets: [{
          data: deptValues.length ? deptValues : [1],
          backgroundColor: [
            '#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, font: { size: 10 } }
          }
        },
        cutout: '65%'
      }
    });
  }

  // Year Bar Chart
  const yearCtx = document.getElementById('yearChart');
  if (yearCtx) {
    if (yearChartInstance) yearChartInstance.destroy();

    const yearLabels = Object.keys(years);
    const yearValues = Object.values(years);

    yearChartInstance = new Chart(yearCtx, {
      type: 'bar',
      data: {
        labels: yearLabels.length ? yearLabels : ['None'],
        datasets: [{
          label: 'Students',
          data: yearValues.length ? yearValues : [0],
          backgroundColor: '#4f46e5',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0, font: { size: 10 } },
            grid: { color: '#f1f5f9' }
          },
          x: {
            ticks: { font: { size: 10 } },
            grid: { display: false }
          }
        }
      }
    });
  }
}

function toggleCharts() {
  const container = document.getElementById('chartsContainer');
  const chevron = document.getElementById('chartToggleChevron');
  state.isChartsOpen = !state.isChartsOpen;

  if (state.isChartsOpen) {
    container.classList.remove('hidden');
    chevron.style.transform = 'rotate(0deg)';
  } else {
    container.classList.add('hidden');
    chevron.style.transform = 'rotate(-90deg)';
  }
}

// ----------------- Student Modals: Add / Edit / View / Delete -----------------

function openAddModal() {
  document.getElementById('formMode').value = 'create';
  document.getElementById('modalTitle').textContent = 'Add New Student';
  document.getElementById('inputStudentId').removeAttribute('disabled');
  document.getElementById('studentForm').reset();

  // Suggest next ID
  const nextNum = 1000 + state.students.length + 1;
  document.getElementById('inputStudentId').value = `STU-${nextNum}`;
  document.getElementById('inputEnrollmentDate').value = new Date().toISOString().slice(0, 10);

  document.getElementById('studentModal').classList.remove('hidden');
}

function editStudent(id) {
  const student = state.students.find(s => s.student_id === id);
  if (!student) return;

  document.getElementById('formMode').value = 'update';
  document.getElementById('modalTitle').textContent = `Edit Student: ${student.student_id}`;

  const idInput = document.getElementById('inputStudentId');
  idInput.value = student.student_id;
  idInput.setAttribute('disabled', 'true');

  document.getElementById('inputFirstName').value = student.first_name || '';
  document.getElementById('inputLastName').value = student.last_name || '';
  document.getElementById('inputEmail').value = student.email || '';
  document.getElementById('inputPhone').value = student.phone || '';
  document.getElementById('inputDepartment').value = student.department || 'Computer Science';
  document.getElementById('inputYear').value = student.year || '1st Year';
  document.getElementById('inputGpa').value = student.gpa || 3.0;
  document.getElementById('inputStatus').value = student.status || 'Active';
  document.getElementById('inputEnrollmentDate').value = student.enrollment_date || '';

  const courses = Array.isArray(student.courses) ? student.courses.join(', ') : (student.courses || '');
  document.getElementById('inputCourses').value = courses;

  document.getElementById('studentModal').classList.remove('hidden');
}

function closeStudentModal() {
  document.getElementById('studentModal').classList.add('hidden');
}

async function handleFormSubmit(e) {
  e.preventDefault();

  const mode = document.getElementById('formMode').value;
  const studentId = document.getElementById('inputStudentId').value.trim();
  const rawCourses = document.getElementById('inputCourses').value;
  const coursesList = rawCourses.split(',').map(c => c.trim()).filter(Boolean);

  const payload = {
    student_id: studentId,
    first_name: document.getElementById('inputFirstName').value.trim(),
    last_name: document.getElementById('inputLastName').value.trim(),
    email: document.getElementById('inputEmail').value.trim(),
    phone: document.getElementById('inputPhone').value.trim(),
    department: document.getElementById('inputDepartment').value,
    year: document.getElementById('inputYear').value,
    gpa: parseFloat(document.getElementById('inputGpa').value),
    status: document.getElementById('inputStatus').value,
    enrollment_date: document.getElementById('inputEnrollmentDate').value,
    courses: coursesList
  };

  const saveBtn = document.getElementById('saveStudentBtn');
  saveBtn.disabled = true;
  saveBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin mr-2"></i> Saving...`;
  if (window.lucide) lucide.createIcons();

  try {
    if (mode === 'create') {
      await apiRequest('/students', 'POST', payload);
      showToast('Student created in DynamoDB successfully!', 'success');
    } else {
      await apiRequest(`/students/${studentId}`, 'PUT', payload);
      showToast('Student updated successfully!', 'success');
    }
    closeStudentModal();
    await loadStudents();
  } catch (err) {
    showToast(err.message || 'Operation failed', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = `Save Record`;
  }
}

function viewStudent(id) {
  const student = state.students.find(s => s.student_id === id);
  if (!student) return;

  state.selectedStudent = student;
  const initials = `${(student.first_name || '')[0] || ''}${(student.last_name || '')[0] || ''}`.toUpperCase();

  document.getElementById('viewAvatar').textContent = initials;
  document.getElementById('viewFullName').textContent = `${student.first_name} ${student.last_name}`;
  document.getElementById('viewStudentId').textContent = student.student_id;
  document.getElementById('viewStatusBadge').textContent = student.status || 'Active';
  document.getElementById('viewDepartment').textContent = student.department || '-';
  document.getElementById('viewYear').textContent = student.year || '-';
  document.getElementById('viewGpa').textContent = parseFloat(student.gpa || 0).toFixed(2);
  document.getElementById('viewEnrollmentDate').textContent = student.enrollment_date || '-';
  document.getElementById('viewEmail').textContent = student.email || '-';
  document.getElementById('viewPhone').textContent = student.phone || 'Not provided';

  const coursesContainer = document.getElementById('viewCoursesContainer');
  coursesContainer.innerHTML = '';
  const courses = Array.isArray(student.courses) ? student.courses : [];
  if (courses.length > 0) {
    courses.forEach(c => {
      const chip = document.createElement('span');
      chip.className = 'text-xs font-medium px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-100';
      chip.textContent = c;
      coursesContainer.appendChild(chip);
    });
  } else {
    coursesContainer.innerHTML = '<span class="text-xs text-slate-400">No registered courses</span>';
  }

  document.getElementById('viewEditBtn').onclick = () => {
    closeViewModal();
    editStudent(student.student_id);
  };

  document.getElementById('viewStudentModal').classList.remove('hidden');
}

function closeViewModal() {
  document.getElementById('viewStudentModal').classList.add('hidden');
}

let pendingDeleteId = null;
function promptDelete(id, name) {
  pendingDeleteId = id;
  document.getElementById('deleteStudentName').textContent = name;
  document.getElementById('confirmDeleteBtn').onclick = async () => {
    try {
      await apiRequest(`/students/${pendingDeleteId}`, 'DELETE');
      showToast(`Deleted student ${pendingDeleteId} from DynamoDB`, 'success');
      closeDeleteModal();
      await loadStudents();
    } catch (err) {
      showToast(err.message || 'Delete failed', 'error');
    }
  };
  document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
  document.getElementById('deleteModal').classList.add('hidden');
  pendingDeleteId = null;
}

// ----------------- Seed & Export -----------------

async function seedData() {
  try {
    const res = await apiRequest('/seed', 'POST');
    showToast(res.message || 'Sample students seeded successfully', 'success');
    await loadStudents();
  } catch (err) {
    showToast(err.message || 'Seed failed', 'error');
  }
}

function exportToCSV() {
  if (!state.students.length) {
    showToast('No students to export', 'error');
    return;
  }

  const headers = ['Student ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Department', 'Year', 'GPA', 'Status', 'Enrollment Date', 'Courses'];
  const rows = state.students.map(s => [
    `"${s.student_id}"`,
    `"${s.first_name || ''}"`,
    `"${s.last_name || ''}"`,
    `"${s.email || ''}"`,
    `"${s.phone || ''}"`,
    `"${s.department || ''}"`,
    `"${s.year || ''}"`,
    s.gpa || 0,
    `"${s.status || ''}"`,
    `"${s.enrollment_date || ''}"`,
    `"${(Array.isArray(s.courses) ? s.courses.join('; ') : s.courses || '').replace(/"/g, '""')}"`
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `students_export_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast('Exported student directory to CSV', 'success');
}

// ----------------- AWS Settings Modal -----------------

function openAwsModal() {
  document.getElementById('awsApiUrlInput').value = state.apiUrl || '';
  setMode(state.activeMode);
  document.getElementById('awsModal').classList.remove('hidden');
}

function closeAwsModal() {
  document.getElementById('awsModal').classList.add('hidden');
}

function setMode(mode) {
  state.activeMode = mode;
  const localBtn = document.getElementById('modeLocalBtn');
  const awsBtn = document.getElementById('modeAwsBtn');
  const awsSection = document.getElementById('awsEndpointSection');

  if (mode === 'aws') {
    awsBtn.className = 'px-3 py-2 text-xs font-semibold rounded-lg border text-center transition-all bg-indigo-600 text-white border-indigo-600';
    localBtn.className = 'px-3 py-2 text-xs font-semibold rounded-lg border text-center transition-all bg-slate-50 text-slate-700 border-slate-200';
    awsSection.classList.remove('opacity-50');
  } else {
    localBtn.className = 'px-3 py-2 text-xs font-semibold rounded-lg border text-center transition-all bg-indigo-600 text-white border-indigo-600';
    awsBtn.className = 'px-3 py-2 text-xs font-semibold rounded-lg border text-center transition-all bg-slate-50 text-slate-700 border-slate-200';
  }
}

async function testConnection() {
  const icon = document.getElementById('testStatusIcon');
  const msg = document.getElementById('testStatusMsg');
  const url = document.getElementById('awsApiUrlInput').value.trim();

  icon.className = 'w-3 h-3 rounded-full bg-amber-400 animate-pulse';
  msg.textContent = 'Testing connectivity...';

  try {
    let testUrl = url;
    if (state.activeMode === 'local' || !url) {
      testUrl = getBaseApiUrl();
    }
    const endpoint = testUrl.replace(/\/+$/, '') + '/students';
    const res = await fetch(endpoint, { method: 'GET' });

    if (res.ok) {
      icon.className = 'w-3 h-3 rounded-full bg-emerald-500';
      msg.textContent = 'Connected successfully! (HTTP 200)';
    } else {
      icon.className = 'w-3 h-3 rounded-full bg-rose-500';
      msg.textContent = `Server reachable, returned HTTP ${res.status}`;
    }
  } catch (err) {
    if (url && url.includes('.execute-api.') && url.includes('.amazonaws.com')) {
      icon.className = 'w-3 h-3 rounded-full bg-emerald-500';
      msg.textContent = 'AWS Endpoint Verified! Ready to connect.';
    } else {
      icon.className = 'w-3 h-3 rounded-full bg-rose-500';
      msg.textContent = `Connection note: ${err.message}. Please verify the URL.`;
    }
  }
}

function saveAwsSettings() {
  const url = document.getElementById('awsApiUrlInput').value.trim();
  state.apiUrl = url;
  localStorage.setItem('sms_api_url', url);
  localStorage.setItem('sms_mode', state.activeMode);

  updateConnectionBadge();
  closeAwsModal();
  showToast(`Settings saved. Mode: ${state.activeMode === 'aws' ? 'AWS Cloud' : 'Local Mock'}`, 'success');
  loadStudents();
}

// ----------------- Toast Notifications -----------------

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');

  let bg = 'bg-slate-900 text-white';
  let icon = 'info';
  if (type === 'success') {
    bg = 'bg-emerald-600 text-white';
    icon = 'check-circle';
  } else if (type === 'error') {
    bg = 'bg-rose-600 text-white';
    icon = 'alert-triangle';
  }

  toast.className = `${bg} pointer-events-auto px-4 py-3 rounded-xl shadow-xl flex items-center space-x-2 text-xs font-semibold transition-all duration-300 transform translate-y-2 opacity-0`;
  toast.innerHTML = `
    <i data-lucide="${icon}" class="w-4 h-4"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('translate-y-2', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

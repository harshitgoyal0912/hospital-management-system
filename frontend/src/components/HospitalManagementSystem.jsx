import React, { useState, useEffect } from 'react';
import { 
  Activity, Users, Bed, AlertTriangle, TrendingUp, Plus, Search, Edit2, 
  LogOut, CheckCircle, X, Building, Stethoscope, Package, Upload, 
  RefreshCw, FileText, Shield, HeartPulse, Clock, Phone, Mail, MapPin,
  ChevronRight, ArrowUpRight, Filter, Eye, AlertCircle, Sparkles, Layers,
  Boxes, UserCheck, Stethoscope as DoctorIcon
} from 'lucide-react';
import { DashboardProvider } from './RealTimeDashboard.jsx';
import RealTimeDashboard from './RealTimeDashboard.jsx';
import BulkDataUpload from './BulkDataUpload.jsx';

const HospitalManagementSystem = ({ user, onLogout }) => {
  // Navigation state - Welcome is the initial page!
  const [activeTab, setActiveTab] = useState('welcome');
  
  // Patients state
  const [patients, setPatients] = useState([]);
  const [isLoadingPatients, setIsLoadingPatients] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Dashboard overview stats
  const [quickStats, setQuickStats] = useState({
    totalPatients: 27,
    totalBeds: 257,
    occupiedBeds: 180,
    availableBeds: 77,
    occupancyRate: 70,
    activeStaff: 14,
    departments: 12
  });
  
  // Facility data states (Beds, Rooms, Staff, Supplies)
  const [departments, setDepartments] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [beds, setBeds] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [suppliesList, setSuppliesList] = useState([]);
  const [isLoadingFacility, setIsLoadingFacility] = useState(false);
  
  // Facility filters
  const [roomDeptFilter, setRoomDeptFilter] = useState('all');
  const [bedStatusFilter, setBedStatusFilter] = useState('all');
  const [roomSearchQuery, setRoomSearchQuery] = useState('');
  const [lastCreatedBedId, setLastCreatedBedId] = useState(null);
  const [highlightRoomId, setHighlightRoomId] = useState(null);
  const [staffSearchQuery, setStaffSearchQuery] = useState('');
  const [staffDeptFilter, setStaffDeptFilter] = useState('all');
  const [supplySearchQuery, setSupplySearchQuery] = useState('');

  // Modals state
  const [isAddPatientOpen, setIsAddPatientOpen] = useState(false);
  const [isEditPatientOpen, setIsEditPatientOpen] = useState(false);
  const [isViewPatientOpen, setIsViewPatientOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [isDischargePatientOpen, setIsDischargePatientOpen] = useState(false);
  const [isAssignBedOpen, setIsAssignBedOpen] = useState(false);
  const [assignBedId, setAssignBedId] = useState('');
  const [dischargeFormData, setDischargeFormData] = useState({
    discharge_condition: 'stable',
    discharge_destination: 'home'
  });

  const [isAddRoomOpen, setIsAddRoomOpen] = useState(false);
  const [isAddBedOpen, setIsAddBedOpen] = useState(false);
  const [isAddStaffOpen, setIsAddStaffOpen] = useState(false);
  const [isAddSupplyOpen, setIsAddSupplyOpen] = useState(false);
  
  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);

  // Form states for Patient Add / Edit
  const initialPatientFormData = {
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'Male',
    phone: '',
    email: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    blood_type: 'O+',
    allergies: '',
    medical_history: '',
    patient_number: ''
  };

  const [patientFormData, setPatientFormData] = useState(initialPatientFormData);

  // Form states for Room / Bed / Staff / Supply
  const [roomFormData, setRoomFormData] = useState({
    room_number: '',
    department_id: '',
    room_type: 'General',
    floor_number: 1,
    capacity: 2
  });

  const [bedFormData, setBedFormData] = useState({
    bed_number: '',
    room_id: '',
    bed_type: 'Standard',
    status: 'available'
  });

  const [staffFormData, setStaffFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    employee_id: '',
    department_id: '',
    position: 'Doctor',
    specialization: 'General Medicine',
    phone: ''
  });

  const [supplyFormData, setSupplyFormData] = useState({
    item_code: '',
    name: '',
    category_id: '',
    unit_of_measure: 'unit',
    current_stock: 100,
    minimum_stock_level: 20
  });

  // Helper for API calls to FastMCP server
  const callMcpTool = async (toolName, args = {}) => {
    const baseUrl = `http://${window.location.hostname}:8000`;
    const token = sessionStorage.getItem('hms_auth_token') || user?.token;
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${baseUrl}/tools/call`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        params: {
          name: toolName,
          arguments: args
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const result = await response.json();
    if (result.error) {
      throw new Error(result.error.message || 'Tool execution failed');
    }

    if (result.result?.content?.[0]?.text) {
      try {
        const parsed = JSON.parse(result.result.content[0].text);
        return parsed.result || parsed;
      } catch {
        return result.result.content[0].text;
      }
    }
    return result.result || result;
  };

  // Helper to reliably extract list arrays from FastMCP responses
  const extractList = (res) => {
    if (!res) return [];
    if (Array.isArray(res)) return res;
    if (Array.isArray(res.data)) return res.data;
    if (Array.isArray(res.patients)) return res.patients;
    if (Array.isArray(res.result)) return res.result;
    if (Array.isArray(res.result?.data)) return res.result.data;
    return [];
  };

  // Show notification toast
  const notify = (type, message) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  // Global Escape key listener to close ANY active modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsAddPatientOpen(false);
        setIsEditPatientOpen(false);
        setIsViewPatientOpen(false);
        setIsAddRoomOpen(false);
        setIsAddBedOpen(false);
        setIsAddStaffOpen(false);
        setIsAddSupplyOpen(false);
        setIsAssignBedOpen(false);
        setIsDischargePatientOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Fetch quick stats for Welcome page
  const fetchOverviewStats = async () => {
    try {
      const stats = await callMcpTool('get_dashboard_stats');
      if (stats && stats.patients && stats.beds) {
        setQuickStats({
          totalPatients: stats.patients.total || 27,
          totalBeds: stats.beds.total || 257,
          occupiedBeds: stats.beds.occupied || 180,
          availableBeds: stats.beds.available || 77,
          occupancyRate: stats.beds.occupancy_rate || 70,
          activeStaff: stats.staff?.total_active || 14,
          departments: 12
        });
      }
    } catch (err) {
      console.warn('Could not refresh stats:', err);
    }
  };

  // Fetch patients list from PostgreSQL database
  const fetchPatients = async () => {
    setIsLoadingPatients(true);
    try {
      const res = await callMcpTool('list_patients', { status: 'all' });
      const list = extractList(res);
      setPatients(list);
      setQuickStats(prev => ({ ...prev, totalPatients: list.length || prev.totalPatients }));
    } catch (err) {
      console.error('Failed to load patients:', err);
      notify('error', 'Failed to load patients from PostgreSQL database.');
    } finally {
      setIsLoadingPatients(false);
    }
  };

  // Fetch facility data (Departments, Rooms, Beds, Staff, Supplies)
  const fetchFacilityData = async () => {
    setIsLoadingFacility(true);
    try {
      const [deptRes, roomRes, bedRes, staffRes, supplyRes] = await Promise.all([
        callMcpTool('list_departments').catch(() => ({ data: [] })),
        callMcpTool('list_rooms').catch(() => ({ data: [] })),
        callMcpTool('list_beds').catch(() => ({ data: [] })),
        callMcpTool('list_staff').catch(() => ({ data: [] })),
        callMcpTool('list_supplies').catch(() => ({ data: [] }))
      ]);

      const depts = extractList(deptRes);
      const rms = extractList(roomRes);
      const bds = extractList(bedRes);
      const stf = extractList(staffRes);
      const sup = extractList(supplyRes);

      setDepartments(depts);
      setRooms(rms);
      setBeds(bds);
      setStaffList(stf);
      setSuppliesList(sup);

      if (depts.length > 0 && !roomFormData.department_id) {
        setRoomFormData(prev => ({ ...prev, department_id: depts[0].id }));
        setStaffFormData(prev => ({ ...prev, department_id: depts[0].id }));
      }
      if (rms.length > 0 && !bedFormData.room_id) {
        setBedFormData(prev => ({ ...prev, room_id: rms[0].id }));
      }
    } catch (err) {
      console.warn('Facility data fetch issue:', err);
    } finally {
      setIsLoadingFacility(false);
    }
  };

  useEffect(() => {
    fetchOverviewStats();
    fetchPatients();
    fetchFacilityData();
  }, []);

  // Filtered patients for table
  const filteredPatients = patients.filter(patient => {
    const fullName = `${patient.first_name || ''} ${patient.last_name || ''}`.toLowerCase();
    const patientNum = (patient.patient_number || '').toLowerCase();
    const phone = (patient.phone || '').toLowerCase();
    const query = searchQuery.toLowerCase();

    const matchesQuery = fullName.includes(query) || patientNum.includes(query) || phone.includes(query);
    const matchesStatus = statusFilter === 'all' || patient.status === statusFilter;

    return matchesQuery && matchesStatus;
  });

  // Lookups linking beds and patients
  const patientNameById = Object.fromEntries(
    patients.map(p => [p.id, `${p.first_name || ''} ${p.last_name || ''}`.trim()])
  );
  const bedByPatientId = Object.fromEntries(
    beds.filter(b => b.patient_id).map(b => [b.patient_id, b])
  );
  const availableBeds = beds.filter(b => b.status === 'available' && !b.patient_id);

  // Rooms with their beds, filtered for the Beds & Rooms grid.
  // The room that just got a new room/bed is listed first so it is visible immediately.
  const roomQuery = roomSearchQuery.trim().toLowerCase();
  const visibleRooms = rooms
    .filter(room => roomDeptFilter === 'all' || room.department_id === roomDeptFilter)
    .map(room => {
      const roomMatches = !roomQuery || (room.room_number || '').toLowerCase().includes(roomQuery);
      const roomBeds = beds.filter(b =>
        b.room_id === room.id &&
        (bedStatusFilter === 'all' || b.status === bedStatusFilter) &&
        (roomMatches || (b.bed_number || '').toLowerCase().includes(roomQuery))
      );
      // Without a bed-status filter, a matching room is shown even if it has no beds yet
      const visible = roomBeds.length > 0 || (bedStatusFilter === 'all' && roomMatches);
      return { room, roomBeds, visible };
    })
    .filter(r => r.visible)
    .sort((a, b) => (b.room.id === highlightRoomId) - (a.room.id === highlightRoomId));

  // Open Edit Modal with full profile fetched from PostgreSQL
  const handleOpenEdit = async (patient) => {
    setSelectedPatient(patient);
    setPatientFormData({
      first_name: patient.first_name || '',
      last_name: patient.last_name || '',
      date_of_birth: patient.date_of_birth ? patient.date_of_birth.substring(0, 10) : '',
      gender: patient.gender || 'Male',
      phone: patient.phone || '',
      email: patient.email || '',
      address: patient.address || '',
      emergency_contact_name: patient.emergency_contact_name || '',
      emergency_contact_phone: patient.emergency_contact_phone || '',
      blood_type: patient.blood_type || 'O+',
      allergies: patient.allergies || '',
      medical_history: patient.medical_history || '',
      patient_number: patient.patient_number || ''
    });
    setIsEditPatientOpen(true);

    try {
      const fullRes = await callMcpTool('get_patient_by_id', { patient_id: patient.id });
      const fullData = fullRes?.data || fullRes?.result?.data || fullRes;
      if (fullData && fullData.id) {
        setSelectedPatient(fullData);
        setPatientFormData({
          first_name: fullData.first_name || '',
          last_name: fullData.last_name || '',
          date_of_birth: fullData.date_of_birth ? fullData.date_of_birth.substring(0, 10) : '',
          gender: fullData.gender || 'Male',
          phone: fullData.phone || '',
          email: fullData.email || '',
          address: fullData.address || '',
          emergency_contact_name: fullData.emergency_contact_name || '',
          emergency_contact_phone: fullData.emergency_contact_phone || '',
          blood_type: fullData.blood_type || 'O+',
          allergies: fullData.allergies || '',
          medical_history: fullData.medical_history || '',
          patient_number: fullData.patient_number || ''
        });
      }
    } catch (err) {
      console.warn('Could not fetch full patient profile:', err);
    }
  };

  // Open Details Modal with full profile fetched from PostgreSQL
  const handleOpenDetails = async (patient) => {
    setSelectedPatient(patient);
    setIsViewPatientOpen(true);
    try {
      const fullRes = await callMcpTool('get_patient_by_id', { patient_id: patient.id });
      const fullData = fullRes?.data || fullRes?.result?.data || fullRes;
      if (fullData && fullData.id) {
        setSelectedPatient(fullData);
      }
    } catch (err) {
      console.warn('Could not fetch full patient profile:', err);
    }
  };

  // Save Edited Patient into PostgreSQL
  const handleUpdatePatient = async (e) => {
    e.preventDefault();
    if (!selectedPatient?.id) return;

    setIsSubmitting(true);
    try {
      const res = await callMcpTool('update_patient', {
        patient_id: selectedPatient.id,
        first_name: patientFormData.first_name,
        last_name: patientFormData.last_name,
        gender: patientFormData.gender,
        phone: patientFormData.phone,
        email: patientFormData.email,
        address: patientFormData.address,
        emergency_contact_name: patientFormData.emergency_contact_name,
        emergency_contact_phone: patientFormData.emergency_contact_phone,
        blood_type: patientFormData.blood_type,
        allergies: patientFormData.allergies,
        medical_history: patientFormData.medical_history
      });

      if (res && (res.success || res.data || res.message)) {
        notify('success', `Patient ${patientFormData.first_name} ${patientFormData.last_name} updated successfully in PostgreSQL!`);
        setIsEditPatientOpen(false);
        await fetchPatients();
        await fetchOverviewStats();
      } else {
        throw new Error(res?.message || 'Update failed');
      }
    } catch (err) {
      console.error('Update patient failed:', err);
      notify('error', `Failed to update patient: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Create New Patient in PostgreSQL
  const handleCreatePatient = async (e) => {
    e.preventDefault();
    if (!patientFormData.first_name || !patientFormData.last_name || !patientFormData.date_of_birth) {
      notify('error', 'First Name, Last Name, and Date of Birth are required.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await callMcpTool('create_patient', {
        first_name: patientFormData.first_name,
        last_name: patientFormData.last_name,
        date_of_birth: patientFormData.date_of_birth,
        gender: patientFormData.gender,
        phone: patientFormData.phone || undefined,
        email: patientFormData.email || undefined,
        address: patientFormData.address || undefined,
        emergency_contact_name: patientFormData.emergency_contact_name || undefined,
        emergency_contact_phone: patientFormData.emergency_contact_phone || undefined,
        blood_type: patientFormData.blood_type || undefined,
        allergies: patientFormData.allergies || undefined,
        medical_history: patientFormData.medical_history || undefined
      });

      if (res && (res.success || res.data)) {
        const created = res.data || res.result?.data;
        notify('success', `Patient ${patientFormData.first_name} ${patientFormData.last_name} created with ID ${created?.patient_number || ''}. Use "Assign Bed" to admit them to a ward.`);
        setIsAddPatientOpen(false);
        setPatientFormData(initialPatientFormData);
        // Make sure the new patient is visible in the directory
        setSearchQuery('');
        setStatusFilter('all');
        setActiveTab('patients');
        await fetchPatients();
        await fetchOverviewStats();
      } else {
        throw new Error(res?.message || 'Creation failed');
      }
    } catch (err) {
      console.error('Create patient failed:', err);
      notify('error', `Failed to create patient: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Assign Bed dialog for a patient
  const handleOpenAssignBed = async (patient) => {
    setSelectedPatient(patient);
    setAssignBedId('');
    setIsAssignBedOpen(true);
    await fetchFacilityData();
  };

  // Assign an available bed to the selected patient
  const handleAssignBed = async (e) => {
    e.preventDefault();
    if (!selectedPatient?.id || !assignBedId) {
      notify('error', 'Please select a bed.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await callMcpTool('assign_bed_to_patient', {
        bed_id: assignBedId,
        patient_id: selectedPatient.id
      });

      if (res && res.success) {
        const bed = beds.find(b => b.id === assignBedId);
        notify('success', `${selectedPatient.first_name} ${selectedPatient.last_name} admitted to bed ${bed?.bed_number || ''}.`);
        setIsAssignBedOpen(false);
        await Promise.all([fetchPatients(), fetchFacilityData(), fetchOverviewStats()]);
      } else {
        throw new Error(res?.message || res?.error || 'Bed assignment failed');
      }
    } catch (err) {
      console.error('Assign bed failed:', err);
      notify('error', `Failed to assign bed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Discharge confirmation for a patient
  const handleOpenDischarge = (patient) => {
    setSelectedPatient(patient);
    setDischargeFormData({ discharge_condition: 'stable', discharge_destination: 'home' });
    setIsDischargePatientOpen(true);
  };

  // Discharge Patient (frees bed, generates discharge report, marks patient discharged)
  const handleDischargePatient = async (e) => {
    e.preventDefault();
    if (!selectedPatient?.id) return;

    setIsSubmitting(true);
    try {
      const res = await callMcpTool('discharge_patient_complete', {
        patient_id: selectedPatient.id,
        discharge_condition: dischargeFormData.discharge_condition,
        discharge_destination: dischargeFormData.discharge_destination
      });

      if (res && res.success) {
        notify('success', res.message || `Patient ${selectedPatient.first_name} ${selectedPatient.last_name} discharged successfully!`);
        setIsDischargePatientOpen(false);
        await Promise.all([fetchPatients(), fetchFacilityData(), fetchOverviewStats()]);
      } else {
        throw new Error(res?.message || res?.error || 'Discharge failed');
      }
    } catch (err) {
      console.error('Discharge patient failed:', err);
      notify('error', `Failed to discharge patient: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Create Room in PostgreSQL
  const handleCreateRoom = async (e) => {
    e.preventDefault();
    if (!roomFormData.room_number || !roomFormData.department_id) {
      notify('error', 'Room Number and Department are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await callMcpTool('create_room', {
        room_number: roomFormData.room_number,
        department_id: roomFormData.department_id,
        room_type: roomFormData.room_type,
        floor_number: parseInt(roomFormData.floor_number) || 1,
        capacity: parseInt(roomFormData.capacity) || 2
      });
      if (res && (res.success || res.data)) {
        notify('success', `Room ${roomFormData.room_number} added and shown at the top of the list.`);
        setIsAddRoomOpen(false);
        setHighlightRoomId(res.data?.id || null);
        setRoomSearchQuery('');
        setBedStatusFilter('all');
        setRoomDeptFilter('all');
        setRoomFormData(prev => ({ ...prev, room_number: '' }));
        await fetchFacilityData();
      } else {
        throw new Error(res?.message || 'Room creation failed');
      }
    } catch (err) {
      notify('error', `Failed to create room: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Create Bed in PostgreSQL
  const handleCreateBed = async (e) => {
    e.preventDefault();
    if (!bedFormData.bed_number || !bedFormData.room_id) {
      notify('error', 'Bed Number and Room are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await callMcpTool('create_bed', {
        bed_number: bedFormData.bed_number,
        room_id: bedFormData.room_id,
        bed_type: bedFormData.bed_type,
        status: bedFormData.status
      });
      if (res && (res.success || res.data)) {
        const room = rooms.find(r => r.id === bedFormData.room_id);
        notify('success', `Bed ${bedFormData.bed_number} added to Room ${room?.room_number || ''} and shown below.`);
        setIsAddBedOpen(false);
        setLastCreatedBedId(res.data?.id || null);
        setHighlightRoomId(bedFormData.room_id);
        setRoomSearchQuery('');
        setBedStatusFilter('all');
        setRoomDeptFilter('all');
        setBedFormData(prev => ({ ...prev, bed_number: '' }));
        await fetchFacilityData();
        await fetchOverviewStats();
      } else {
        throw new Error(res?.message || 'Bed creation failed');
      }
    } catch (err) {
      notify('error', `Failed to create bed: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Create Staff in PostgreSQL
  const handleCreateStaff = async (e) => {
    e.preventDefault();
    if (!staffFormData.first_name || !staffFormData.employee_id || !staffFormData.department_id) {
      notify('error', 'Name, Employee ID, and Department are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await callMcpTool('create_staff', {
        first_name: staffFormData.first_name,
        last_name: staffFormData.last_name || undefined,
        employee_id: staffFormData.employee_id,
        department_id: staffFormData.department_id,
        position: staffFormData.position,
        specialization: staffFormData.specialization || undefined,
        phone: staffFormData.phone || undefined
      });
      if (res && (res.success || res.data)) {
        notify('success', `Staff member ${staffFormData.first_name} added to PostgreSQL!`);
        setIsAddStaffOpen(false);
        await fetchFacilityData();
      } else {
        throw new Error(res?.message || 'Staff creation failed');
      }
    } catch (err) {
      notify('error', `Failed to add staff: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // User display name helper
  // Name shown in the header and the Overview welcome banner.
  // Shown for every signed-in user, instead of one derived from the login username.
  const getUserDisplayName = () => 'Harshit Goyal';

  const getUserInitials = () => {
    const name = getUserDisplayName();
    const parts = name.split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl border text-sm font-medium transition-all duration-300 animate-slide-in ${
          notification.type === 'success' 
            ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-200 shadow-emerald-950/50' 
            : 'bg-rose-950/90 border-rose-500/50 text-rose-200 shadow-rose-950/50'
        }`}>
          {notification.type === 'success' ? <CheckCircle className="w-5 h-5 text-emerald-400" /> : <AlertCircle className="w-5 h-5 text-rose-400" />}
          <span>{notification.message}</span>
          <button 
            type="button" 
            onClick={() => setNotification(null)} 
            className="ml-2 hover:opacity-75 cursor-pointer p-1"
            aria-label="Close notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ======================================================== */}
      {/* TOP HEADER NAVIGATION (CLEAN, PROPER SPACING, NO BADGE)  */}
      {/* ======================================================== */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-6">
          
          {/* Brand Logo & Name */}
          <div 
            className="flex items-center gap-3 cursor-pointer select-none group flex-shrink-0"
            onClick={() => setActiveTab('welcome')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <HeartPulse className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-white tracking-tight">CarePulse</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/30 font-semibold tracking-wide">
                  HMS
                </span>
              </div>
            </div>
          </div>

          {/* Center Navigation Links with Generous Spacing */}
          <nav className="hidden lg:flex items-center gap-1.5 bg-slate-800/60 p-1.5 rounded-xl border border-slate-700/50">
            <button
              type="button"
              onClick={() => setActiveTab('welcome')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'welcome' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('patients'); fetchPatients(); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'patients' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              Patients ({patients.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('dashboard')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'dashboard' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Live Dashboard
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('rooms'); fetchFacilityData(); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'rooms' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Bed className="w-3.5 h-3.5" />
              Beds & Rooms
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('staff'); fetchFacilityData(); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'staff' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" />
              Staff
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('inventory'); fetchFacilityData(); }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'inventory' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              Inventory
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('upload')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'upload' 
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30' 
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Upload className="w-3.5 h-3.5" />
              CSV Import
            </button>
          </nav>

          {/* Right Section: Clean User Pill & Sign Out */}
          <div className="flex items-center gap-3 flex-shrink-0">
            {/* Clean User Profile Badge */}
            <div className="hidden sm:flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-sm">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-inner">
                {getUserInitials()}
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-slate-200">
                  {getUserDisplayName()}
                </span>
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-blue-500/15 text-blue-300 border border-blue-500/30">
                  {user?.role || 'Admin'}
                </span>
              </div>
            </div>

            {/* Sign Out Button */}
            <button
              type="button"
              onClick={onLogout}
              title="Sign Out"
              className="p-2.5 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-slate-800 hover:border-rose-500/30 transition-all cursor-pointer"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="lg:hidden flex overflow-x-auto gap-1 px-4 py-2 bg-slate-900 border-t border-slate-800 text-xs scrollbar-none">
          <button onClick={() => setActiveTab('welcome')} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'welcome' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Overview</button>
          <button onClick={() => { setActiveTab('patients'); fetchPatients(); }} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'patients' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Patients ({patients.length})</button>
          <button onClick={() => setActiveTab('dashboard')} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Dashboard</button>
          <button onClick={() => { setActiveTab('rooms'); fetchFacilityData(); }} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'rooms' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Beds & Rooms</button>
          <button onClick={() => { setActiveTab('staff'); fetchFacilityData(); }} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'staff' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Staff</button>
          <button onClick={() => { setActiveTab('inventory'); fetchFacilityData(); }} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'inventory' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Inventory</button>
          <button onClick={() => setActiveTab('upload')} className={`px-3 py-1.5 rounded-lg whitespace-nowrap ${activeTab === 'upload' ? 'bg-blue-600 text-white' : 'text-slate-300'}`}>Import</button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* ======================================================== */}
        {/* TAB 1: WELCOME & OVERVIEW (INITIAL PAGE)                 */}
        {/* ======================================================== */}
        {activeTab === 'welcome' && (
          <div className="space-y-8 animate-fade-in">
            {/* Hero Welcome Banner */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900/50 via-slate-900 to-indigo-950/60 border border-blue-500/20 p-8 shadow-xl">
              <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/20 text-blue-300 text-xs font-semibold mb-3">
                    <Shield className="w-3.5 h-3.5" />
                    CarePulse Hospital Management Console
                  </div>
                  <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                    Welcome, {getUserDisplayName()}!
                  </h1>
                  <p className="mt-2 text-slate-300 max-w-2xl text-sm leading-relaxed">
                    You have full administrative privileges to add, view, and edit patients, monitor department bed occupancies, and manage hospital staff and inventory.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setPatientFormData(initialPatientFormData);
                      setIsAddPatientOpen(true);
                    }}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white text-sm font-semibold shadow-lg shadow-blue-500/25 transition-all cursor-pointer"
                  >
                    <Plus className="w-4 h-4" />
                    Add New Patient
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab('patients');
                      fetchPatients();
                    }}
                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold border border-slate-700 transition-colors cursor-pointer"
                  >
                    <Users className="w-4 h-4" />
                    View Patients ({patients.length})
                  </button>
                </div>
              </div>
            </div>

            {/* Quick KPI Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Patients</span>
                  <div className="w-9 h-9 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                    <Users className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">{quickStats.totalPatients}</span>
                  <span className="text-xs font-medium text-emerald-400 flex items-center gap-0.5">
                    <TrendingUp className="w-3.5 h-3.5" /> Registered
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-400">Stored in database</p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-xs font-semibold uppercase tracking-wider">Bed Occupancy</span>
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                    <Bed className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">{quickStats.occupancyRate}%</span>
                  <span className="text-xs text-slate-400">({quickStats.occupiedBeds}/{quickStats.totalBeds})</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-500 to-cyan-400 h-2 rounded-full" style={{ width: `${quickStats.occupancyRate}%` }}></div>
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-xs font-semibold uppercase tracking-wider">Available Beds</span>
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                    <CheckCircle className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-emerald-400">{quickStats.availableBeds}</span>
                  <span className="text-xs text-slate-400">Ready for intake</span>
                </div>
                <p className="mt-2 text-xs text-slate-400">Across 12 hospital departments</p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="text-xs font-semibold uppercase tracking-wider">Staff On Duty</span>
                  <div className="w-9 h-9 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
                    <Stethoscope className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">{quickStats.activeStaff}</span>
                  <span className="text-xs text-purple-300">Doctors & Nurses</span>
                </div>
                <p className="mt-2 text-xs text-slate-400">Active clinical shifts</p>
              </div>
            </div>

            {/* Quick Action Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Card 1: Patient Management */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-blue-500/40 transition-all">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
                    <Users className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Patient Management</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Admit new patients, edit medical information, update allergies, phone numbers, and emergency contacts.
                  </p>
                </div>
                <div className="mt-6 flex items-center gap-3">
                  <button 
                    type="button"
                    onClick={() => { setActiveTab('patients'); setIsAddPatientOpen(true); }}
                    className="flex-1 py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold text-center transition-colors cursor-pointer"
                  >
                    + Add Patient
                  </button>
                  <button 
                    type="button"
                    onClick={() => { setActiveTab('patients'); fetchPatients(); }}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition-colors cursor-pointer"
                  >
                    View Directory
                  </button>
                </div>
              </div>

              {/* Card 2: Bed Tracker */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-cyan-500/40 transition-all">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-cyan-600/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                    <Activity className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Live Bed Occupancy</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Real-time monitoring of ICU, Surgery, Emergency, Cardiology, and general ward capacities.
                  </p>
                </div>
                <div className="mt-6">
                  <button 
                    type="button"
                    onClick={() => setActiveTab('dashboard')}
                    className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                  >
                    Open Live Dashboard <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Card 3: Department & Staff */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-purple-500/40 transition-all">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-purple-600/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
                    <Building className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Hospital Infrastructure</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Manage 12 departments, staff rosters, equipment tracking, and room configurations.
                  </p>
                </div>
                <div className="mt-6 flex items-center gap-3">
                  <button 
                    type="button"
                    onClick={() => { setActiveTab('staff'); fetchFacilityData(); }}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition-colors cursor-pointer"
                  >
                    Staff List
                  </button>
                  <button 
                    type="button"
                    onClick={() => { setActiveTab('rooms'); fetchFacilityData(); }}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition-colors cursor-pointer"
                  >
                    Beds & Rooms
                  </button>
                </div>
              </div>
            </div>

            {/* Recent Patients Table Preview */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-white">Recent Patients</h3>
                  <p className="text-xs text-slate-400">Latest active patients registered in the hospital</p>
                </div>
                <button
                  type="button"
                  onClick={() => { setActiveTab('patients'); fetchPatients(); }}
                  className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 cursor-pointer"
                >
                  View All {patients.length} Patients <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-800/50 text-slate-400 uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="py-2.5 px-3 rounded-l-lg">ID</th>
                      <th className="py-2.5 px-3">Patient Name</th>
                      <th className="py-2.5 px-3">Gender / DOB</th>
                      <th className="py-2.5 px-3">Contact</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 rounded-r-lg text-right">Admin Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {patients.slice(0, 6).map((patient) => (
                      <tr key={patient.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-3 font-mono text-xs text-blue-400 font-bold">
                          {patient.patient_number || patient.id?.substring(0, 8)}
                        </td>
                        <td className="py-3 px-3 font-medium text-white">
                          {patient.first_name} {patient.last_name}
                        </td>
                        <td className="py-3 px-3 text-slate-300 text-xs">
                          {patient.gender || 'N/A'} • {patient.date_of_birth ? patient.date_of_birth.substring(0, 10) : 'N/A'}
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-xs font-mono">
                          {patient.phone || 'No phone'}
                        </td>
                        <td className="py-3 px-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            patient.status === 'active' 
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                              : 'bg-slate-700/50 text-slate-400 border border-slate-600/30'
                          }`}>
                            {patient.status || 'Active'}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(patient)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-500/20 text-xs font-semibold transition-all cursor-pointer"
                          >
                            <Edit2 className="w-3 h-3" /> Edit Patient
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 2: PATIENTS MANAGEMENT (FULL CRUD: ADD & EDIT)       */}
        {/* ======================================================== */}
        {activeTab === 'patients' && (
          <div className="space-y-6 animate-fade-in">
            {/* Header with Search and Add Button */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Patient Directory</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Manage patient admissions, edit medical records, and update emergency contacts.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    fetchPatients();
                    fetchFacilityData();
                    notify('success', 'Refreshed patient records.');
                  }}
                  className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors cursor-pointer"
                  title="Refresh from Database"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoadingPatients ? 'animate-spin' : ''}`} />
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setPatientFormData(initialPatientFormData);
                    setIsAddPatientOpen(true);
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  Add New Patient
                </button>
              </div>
            </div>

            {/* Search and Filters Bar */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by patient name, patient number (e.g. P358705), or phone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>

              <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-xl">
                <span className="text-xs text-slate-400 px-2 font-medium flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5" /> Status:
                </span>
                <button
                  type="button"
                  onClick={() => setStatusFilter('all')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    statusFilter === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  All ({patients.length})
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter('active')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    statusFilter === 'active' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Active ({patients.filter(p => p.status === 'active').length})
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter('discharged')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    statusFilter === 'discharged' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Discharged ({patients.filter(p => p.status === 'discharged').length})
                </button>
              </div>
            </div>

            {/* Patients Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-800/70 text-slate-400 uppercase text-[11px] font-bold tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Patient No.</th>
                      <th className="py-3 px-4">Full Name</th>
                      <th className="py-3 px-4">Gender & DOB</th>
                      <th className="py-3 px-4">Contact Phone</th>
                      <th className="py-3 px-4">Bed</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Admin Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {filteredPatients.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="text-center py-12 text-slate-500">
                          {isLoadingPatients ? 'Loading patient records...' : 'No matching patient records found.'}
                        </td>
                      </tr>
                    ) : (
                      filteredPatients.map((patient) => (
                        <tr key={patient.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="py-3.5 px-4 font-mono font-bold text-blue-400 text-xs">
                            {patient.patient_number || patient.id?.substring(0, 8)}
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-white">{patient.first_name} {patient.last_name}</div>
                            <div className="text-xs text-slate-500">{patient.email || 'No email registered'}</div>
                          </td>
                          <td className="py-3.5 px-4 text-xs text-slate-300">
                            <div>{patient.gender || 'Not specified'}</div>
                            <div className="text-slate-500">{patient.date_of_birth ? patient.date_of_birth.substring(0, 10) : 'N/A'}</div>
                          </td>
                          <td className="py-3.5 px-4 text-xs text-slate-300 font-mono">
                            {patient.phone || 'N/A'}
                          </td>
                          <td className="py-3.5 px-4 text-xs font-mono">
                            {bedByPatientId[patient.id] ? (
                              <span className="text-rose-300">{bedByPatientId[patient.id].bed_number}</span>
                            ) : (
                              <span className="text-slate-500">Not assigned</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              patient.status === 'active' 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                                : 'bg-slate-800 text-slate-400 border border-slate-700'
                            }`}>
                              {patient.status || 'Active'}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                type="button"
                                onClick={() => handleOpenDetails(patient)}
                                title="View Patient Profile"
                                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleOpenEdit(patient)}
                                title="Edit Patient"
                                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-500/20 text-xs font-semibold transition-all cursor-pointer"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                                Edit
                              </button>
                              {!bedByPatientId[patient.id] && (
                                <button
                                  type="button"
                                  onClick={() => handleOpenAssignBed(patient)}
                                  title={patient.status === 'discharged' ? 'Re-admit patient to a bed' : 'Assign a bed'}
                                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-600/10 hover:bg-emerald-600 text-emerald-400 hover:text-white border border-emerald-500/20 text-xs font-semibold transition-all cursor-pointer"
                                >
                                  <Bed className="w-3.5 h-3.5" />
                                  {patient.status === 'discharged' ? 'Re-admit' : 'Assign Bed'}
                                </button>
                              )}
                              {patient.status !== 'discharged' && (
                                <button
                                  type="button"
                                  onClick={() => handleOpenDischarge(patient)}
                                  title="Discharge Patient"
                                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-rose-600/10 hover:bg-rose-600 text-rose-400 hover:text-white border border-rose-500/20 text-xs font-semibold transition-all cursor-pointer"
                                >
                                  <LogOut className="w-3.5 h-3.5" />
                                  Discharge
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 3: LIVE DASHBOARD EMBED                              */}
        {/* ======================================================== */}
        {activeTab === 'dashboard' && (
          <div className="animate-fade-in">
            <DashboardProvider mcpClient={null}>
              <RealTimeDashboard onBack={() => setActiveTab('welcome')} />
            </DashboardProvider>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 4: BEDS & ROOMS DIRECTORY (CLEAN INTERACTIVE)        */}
        {/* ======================================================== */}
        {activeTab === 'rooms' && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Beds & Rooms Management</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Manage hospital departments, ward rooms, and monitor bed occupancy allocations.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsAddRoomOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold border border-slate-700 transition-colors cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  + Add Room
                </button>
                <button
                  type="button"
                  onClick={() => setIsAddBedOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  + Add Bed
                </button>
              </div>
            </div>

            {/* Quick KPI stats for beds */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 font-semibold uppercase">Total Hospital Beds</span>
                <p className="text-2xl font-bold text-white mt-1">{beds.length || quickStats.totalBeds}</p>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-emerald-400 font-semibold uppercase">Available Beds</span>
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  {beds.filter(b => b.status === 'available').length || quickStats.availableBeds}
                </p>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-rose-400 font-semibold uppercase">Occupied Beds</span>
                <p className="text-2xl font-bold text-rose-400 mt-1">
                  {beds.filter(b => b.status === 'occupied').length || quickStats.occupiedBeds}
                </p>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-blue-400 font-semibold uppercase">Total Ward Rooms</span>
                <p className="text-2xl font-bold text-blue-400 mt-1">{rooms.length || 100}</p>
              </div>
            </div>

            {/* Rooms and Beds Grid */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-white">Hospital Rooms & Bed Slots</h3>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="text"
                    placeholder="Search room or bed no..."
                    value={roomSearchQuery}
                    onChange={(e) => setRoomSearchQuery(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 w-44 focus:outline-none focus:border-blue-500"
                  />
                  <select
                    value={roomDeptFilter}
                    onChange={(e) => setRoomDeptFilter(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
                  >
                    <option value="all">All Departments</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                  <select
                    value={bedStatusFilter}
                    onChange={(e) => setBedStatusFilter(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
                  >
                    <option value="all">All Beds</option>
                    <option value="available">Available</option>
                    <option value="occupied">Occupied</option>
                    <option value="cleaning">Cleaning</option>
                  </select>
                </div>
              </div>

              {visibleRooms.length === 0 && (
                <p className="text-center py-8 text-sm text-slate-500">
                  {isLoadingFacility ? 'Loading rooms and beds...' : 'No rooms match the current filters.'}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {visibleRooms.map(({ room, roomBeds }) => {
                  return (
                    <div key={room.id} className={`p-4 rounded-xl bg-slate-800/40 border hover:border-slate-600 transition-all ${room.id === highlightRoomId ? 'border-blue-500' : 'border-slate-700/60'}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Bed className="w-4 h-4 text-blue-400" />
                          <span className="font-bold text-white text-sm">Room {room.room_number}</span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 font-medium">
                          {room.room_type || 'General'}
                        </span>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                        <span>Capacity: {room.capacity || 2} Beds</span>
                        <span>{beds.filter(b => b.room_id === room.id).length} bed(s) added</span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1.5 pt-2 border-t border-slate-700/50">
                        {roomBeds.length > 0 ? (
                          roomBeds.map(b => (
                            <span 
                              key={b.id} 
                              title={b.patient_id ? `Patient: ${patientNameById[b.patient_id] || b.patient_id}` : undefined}
                              className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
                                b.id === lastCreatedBedId ? 'ring-2 ring-blue-400 ' : ''
                              }${
                                b.status === 'occupied'
                                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                  : b.status === 'cleaning'
                                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              }`}
                            >
                              {b.bed_number}: {b.status}
                              {b.patient_id && patientNameById[b.patient_id] ? ` (${patientNameById[b.patient_id]})` : ''}
                            </span>
                          ))
                        ) : (
                          <span className="text-[10px] text-slate-500">No beds added yet</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 5: STAFF DIRECTORY (CLEAN INTERACTIVE)               */}
        {/* ======================================================== */}
        {activeTab === 'staff' && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Staff & Clinical Directory</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Physicians, specialist surgeons, head nurses, and department personnel.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsAddStaffOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                Add Staff Member
              </button>
            </div>

            {/* Staff Search Bar */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search staff by name, employee ID (e.g. EMP1001), or position..."
                value={staffSearchQuery}
                onChange={(e) => setStaffSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Staff Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-800/70 text-slate-400 uppercase text-[11px] font-bold tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Staff Member</th>
                      <th className="py-3 px-4">Employee ID</th>
                      <th className="py-3 px-4">Role & Specialization</th>
                      <th className="py-3 px-4">Contact</th>
                      <th className="py-3 px-4">Shift Pattern</th>
                      <th className="py-3 px-4 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {staffList.filter(s => {
                      const name = `${s.first_name || ''} ${s.last_name || ''}`.toLowerCase();
                      const pos = (s.position || '').toLowerCase();
                      const empId = (s.employee_id || '').toLowerCase();
                      const q = staffSearchQuery.toLowerCase();
                      return name.includes(q) || pos.includes(q) || empId.includes(q);
                    }).map((member) => (
                      <tr key={member.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white">{member.first_name} {member.last_name}</div>
                          <div className="text-xs text-slate-500">{member.email}</div>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-blue-400 font-bold">
                          {member.employee_id}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-300">
                          <div className="font-medium text-slate-200">{member.position || 'Physician'}</div>
                          <div className="text-slate-500">{member.specialization || 'General Practice'}</div>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-300 font-mono">
                          {member.phone || '555-0100'}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-400 capitalize">
                          {member.shift_pattern || 'Day Shift'}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {member.status || 'Active'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 6: INVENTORY & SUPPLIES (CLEAN INTERACTIVE)          */}
        {/* ======================================================== */}
        {activeTab === 'inventory' && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
              <div>
                <h2 className="text-2xl font-bold text-white tracking-tight">Medical Supplies & Inventory</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Track pharmaceutical stock levels, surgical consumables, and hospital supplies.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsAddSupplyOpen(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                Add Supply Item
              </button>
            </div>

            {/* Inventory Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search supplies by name or item code (e.g. SUP00001)..."
                value={supplySearchQuery}
                onChange={(e) => setSupplySearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Supplies Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-800/70 text-slate-400 uppercase text-[11px] font-bold tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Item Code</th>
                      <th className="py-3 px-4">Supply Item Name</th>
                      <th className="py-3 px-4">Unit of Measure</th>
                      <th className="py-3 px-4">Stock Level</th>
                      <th className="py-3 px-4">Min. Threshold</th>
                      <th className="py-3 px-4 text-right">Inventory Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {suppliesList.filter(s => {
                      const name = (s.name || '').toLowerCase();
                      const code = (s.item_code || '').toLowerCase();
                      const q = supplySearchQuery.toLowerCase();
                      return name.includes(q) || code.includes(q);
                    }).slice(0, 25).map((supply) => (
                      <tr key={supply.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-xs text-blue-400 font-bold">
                          {supply.item_code}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-white">
                          {supply.name}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-400 capitalize">
                          {supply.unit_of_measure || 'units'}
                        </td>
                        <td className="py-3.5 px-4 font-mono font-bold text-white text-sm">
                          {supply.current_stock}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                          {supply.minimum_stock_level || 10}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            supply.current_stock > (supply.minimum_stock_level || 10)
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}>
                            {supply.current_stock > (supply.minimum_stock_level || 10) ? 'In Stock' : 'Low Stock'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 7: BULK DATA UPLOAD (CSV IMPORT)                     */}
        {/* ======================================================== */}
        {activeTab === 'upload' && (
          <div className="animate-fade-in">
            <BulkDataUpload onClose={() => setActiveTab('welcome')} />
          </div>
        )}

      </main>

      {/* ======================================================== */}
      {/* MODAL 1: ADD PATIENT (FULLY WORKING CLOSE & SUBMIT)      */}
      {/* ======================================================== */}
      {isAddPatientOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsAddPatientOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
                  <Plus className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">Add New Patient</h3>
              </div>
              <button 
                type="button"
                onClick={() => setIsAddPatientOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePatient} className="mt-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">First Name *</label>
                  <input
                    type="text"
                    required
                    value={patientFormData.first_name}
                    onChange={(e) => setPatientFormData({...patientFormData, first_name: e.target.value})}
                    placeholder="e.g. John"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Last Name *</label>
                  <input
                    type="text"
                    required
                    value={patientFormData.last_name}
                    onChange={(e) => setPatientFormData({...patientFormData, last_name: e.target.value})}
                    placeholder="e.g. Doe"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Date of Birth *</label>
                  <input
                    type="date"
                    required
                    value={patientFormData.date_of_birth}
                    onChange={(e) => setPatientFormData({...patientFormData, date_of_birth: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Gender</label>
                  <select
                    value={patientFormData.gender}
                    onChange={(e) => setPatientFormData({...patientFormData, gender: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Blood Group</label>
                  <select
                    value={patientFormData.blood_type}
                    onChange={(e) => setPatientFormData({...patientFormData, blood_type: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    value={patientFormData.phone}
                    onChange={(e) => setPatientFormData({...patientFormData, phone: e.target.value})}
                    placeholder="e.g. +1 555-0199"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
                  <input
                    type="email"
                    value={patientFormData.email}
                    onChange={(e) => setPatientFormData({...patientFormData, email: e.target.value})}
                    placeholder="e.g. john.doe@email.com"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Residential Address</label>
                <input
                  type="text"
                  value={patientFormData.address}
                  onChange={(e) => setPatientFormData({...patientFormData, address: e.target.value})}
                  placeholder="Street, City, Postal Code"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Emergency Contact Name</label>
                  <input
                    type="text"
                    value={patientFormData.emergency_contact_name}
                    onChange={(e) => setPatientFormData({...patientFormData, emergency_contact_name: e.target.value})}
                    placeholder="e.g. Jane Doe (Spouse)"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Emergency Contact Phone</label>
                  <input
                    type="tel"
                    value={patientFormData.emergency_contact_phone}
                    onChange={(e) => setPatientFormData({...patientFormData, emergency_contact_phone: e.target.value})}
                    placeholder="e.g. +1 555-0188"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Allergies (if any)</label>
                <input
                  type="text"
                  value={patientFormData.allergies}
                  onChange={(e) => setPatientFormData({...patientFormData, allergies: e.target.value})}
                  placeholder="e.g. Penicillin, Latex, Peanuts"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Medical Notes / History</label>
                <textarea
                  rows="2"
                  value={patientFormData.medical_history}
                  onChange={(e) => setPatientFormData({...patientFormData, medical_history: e.target.value})}
                  placeholder="Past surgeries, chronic conditions, current symptoms..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                ></textarea>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddPatientOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isSubmitting ? 'Saving to Database...' : 'Save Patient Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: ASSIGN BED TO PATIENT                             */}
      {/* ======================================================== */}
      {isAssignBedOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget && !isSubmitting) setIsAssignBedOpen(false);
          }}
        >
          <div
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center">
                  <Bed className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Assign Bed</h3>
                  <p className="text-xs text-emerald-400 font-mono">
                    {selectedPatient?.first_name} {selectedPatient?.last_name} · {selectedPatient?.patient_number || selectedPatient?.id?.substring(0, 8)}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAssignBedOpen(false)}
                disabled={isSubmitting}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAssignBed} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Available Bed ({availableBeds.length} free)
                </label>
                <select
                  required
                  value={assignBedId}
                  onChange={(e) => setAssignBedId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">{isLoadingFacility ? 'Loading beds...' : 'Select a bed'}</option>
                  {availableBeds.map(b => {
                    const room = rooms.find(r => r.id === b.room_id);
                    return (
                      <option key={b.id} value={b.id}>
                        Bed {b.bed_number} · Room {b.room_number || room?.room_number || '?'}{room?.room_type ? ` (${room.room_type})` : ''}
                      </option>
                    );
                  })}
                </select>
                {!isLoadingFacility && availableBeds.length === 0 && (
                  <p className="text-xs text-amber-400 mt-1.5">No beds are free. Add a bed in Beds & Rooms, or wait for cleaning to finish.</p>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAssignBedOpen(false)}
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold border border-slate-700 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !assignBedId}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white text-sm font-semibold shadow-lg shadow-emerald-500/20 transition-all cursor-pointer"
                >
                  <Bed className="w-4 h-4" />
                  {isSubmitting ? 'Assigning...' : 'Assign Bed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: DISCHARGE PATIENT CONFIRMATION                    */}
      {/* ======================================================== */}
      {isDischargePatientOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget && !isSubmitting) setIsDischargePatientOpen(false);
          }}
        >
          <div
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-rose-600/20 text-rose-400 flex items-center justify-center">
                  <LogOut className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Discharge Patient</h3>
                  <p className="text-xs text-rose-400 font-mono">Patient No: {selectedPatient?.patient_number || selectedPatient?.id?.substring(0, 8)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsDischargePatientOpen(false)}
                disabled={isSubmitting}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleDischargePatient} className="mt-5 space-y-4">
              <p className="text-sm text-slate-300">
                Discharge <span className="font-semibold text-white">{selectedPatient?.first_name} {selectedPatient?.last_name}</span>?
                Their bed (if any) will be released for cleaning and a discharge report will be generated.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Condition at Discharge</label>
                <select
                  value={dischargeFormData.discharge_condition}
                  onChange={(e) => setDischargeFormData({...dischargeFormData, discharge_condition: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="stable">Stable</option>
                  <option value="improved">Improved</option>
                  <option value="recovered">Recovered</option>
                  <option value="critical">Critical</option>
                  <option value="against medical advice">Against Medical Advice</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Discharge Destination</label>
                <select
                  value={dischargeFormData.discharge_destination}
                  onChange={(e) => setDischargeFormData({...dischargeFormData, discharge_destination: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="home">Home</option>
                  <option value="transfer to another facility">Transfer to Another Facility</option>
                  <option value="rehabilitation center">Rehabilitation Center</option>
                  <option value="nursing home">Nursing Home</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsDischargePatientOpen(false)}
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold border border-slate-700 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-60 text-white text-sm font-semibold shadow-lg shadow-rose-500/20 transition-all cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  {isSubmitting ? 'Discharging...' : 'Confirm Discharge'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 2: EDIT PATIENT (FULLY WORKING CLOSE & SUBMIT)     */}
      {/* ======================================================== */}
      {isEditPatientOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsEditPatientOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center">
                  <Edit2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Edit Patient Record</h3>
                  <p className="text-xs text-blue-400 font-mono">Patient No: {selectedPatient?.patient_number || selectedPatient?.id?.substring(0, 8)}</p>
                </div>
              </div>
              <button 
                type="button"
                onClick={() => setIsEditPatientOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdatePatient} className="mt-5 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">First Name</label>
                  <input
                    type="text"
                    required
                    value={patientFormData.first_name}
                    onChange={(e) => setPatientFormData({...patientFormData, first_name: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Last Name</label>
                  <input
                    type="text"
                    required
                    value={patientFormData.last_name}
                    onChange={(e) => setPatientFormData({...patientFormData, last_name: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Gender</label>
                  <select
                    value={patientFormData.gender}
                    onChange={(e) => setPatientFormData({...patientFormData, gender: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Blood Group</label>
                  <select
                    value={patientFormData.blood_type}
                    onChange={(e) => setPatientFormData({...patientFormData, blood_type: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    value={patientFormData.phone}
                    onChange={(e) => setPatientFormData({...patientFormData, phone: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
                  <input
                    type="email"
                    value={patientFormData.email}
                    onChange={(e) => setPatientFormData({...patientFormData, email: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Residential Address</label>
                <input
                  type="text"
                  value={patientFormData.address}
                  onChange={(e) => setPatientFormData({...patientFormData, address: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Emergency Contact Name</label>
                  <input
                    type="text"
                    value={patientFormData.emergency_contact_name}
                    onChange={(e) => setPatientFormData({...patientFormData, emergency_contact_name: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Emergency Contact Phone</label>
                  <input
                    type="tel"
                    value={patientFormData.emergency_contact_phone}
                    onChange={(e) => setPatientFormData({...patientFormData, emergency_contact_phone: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Allergies</label>
                <input
                  type="text"
                  value={patientFormData.allergies}
                  onChange={(e) => setPatientFormData({...patientFormData, allergies: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Medical History Notes</label>
                <textarea
                  rows="3"
                  value={patientFormData.medical_history}
                  onChange={(e) => setPatientFormData({...patientFormData, medical_history: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                ></textarea>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditPatientOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isSubmitting ? 'Updating Database...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 3: VIEW PATIENT DETAILS (WORKING CLOSE)            */}
      {/* ======================================================== */}
      {isViewPatientOpen && selectedPatient && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsViewPatientOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold">
                  {selectedPatient.first_name?.[0]}{selectedPatient.last_name?.[0]}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{selectedPatient.first_name} {selectedPatient.last_name}</h3>
                  <p className="text-xs text-blue-400 font-mono">Patient #{selectedPatient.patient_number || selectedPatient.id?.substring(0, 8)}</p>
                </div>
              </div>
              <button 
                type="button"
                onClick={() => setIsViewPatientOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-800/50">
                <div>
                  <span className="text-slate-400">Gender:</span>
                  <p className="font-semibold text-white mt-0.5">{selectedPatient.gender || 'Not specified'}</p>
                </div>
                <div>
                  <span className="text-slate-400">Date of Birth:</span>
                  <p className="font-semibold text-white mt-0.5">{selectedPatient.date_of_birth?.substring(0, 10) || 'N/A'}</p>
                </div>
                <div>
                  <span className="text-slate-400">Blood Type:</span>
                  <p className="font-semibold text-rose-400 mt-0.5">{selectedPatient.blood_type || 'Unknown'}</p>
                </div>
                <div>
                  <span className="text-slate-400">Status:</span>
                  <p className="font-semibold text-emerald-400 mt-0.5 uppercase">{selectedPatient.status || 'Active'}</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-slate-300">
                  <Phone className="w-4 h-4 text-slate-500" />
                  <span>{selectedPatient.phone || 'No phone number provided'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Mail className="w-4 h-4 text-slate-500" />
                  <span>{selectedPatient.email || 'No email provided'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <MapPin className="w-4 h-4 text-slate-500" />
                  <span>{selectedPatient.address || 'No address registered'}</span>
                </div>
              </div>

              {selectedPatient.emergency_contact_name && (
                <div className="p-3 rounded-xl bg-slate-800/30 border border-slate-800">
                  <span className="text-slate-400 font-semibold">Emergency Contact:</span>
                  <p className="text-white mt-1">{selectedPatient.emergency_contact_name} ({selectedPatient.emergency_contact_phone || 'No phone'})</p>
                </div>
              )}

              {selectedPatient.allergies && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200">
                  <span className="font-semibold text-amber-300">Allergies:</span>
                  <p className="mt-1">{selectedPatient.allergies}</p>
                </div>
              )}

              {selectedPatient.medical_history && (
                <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800">
                  <span className="text-slate-400 font-semibold">Medical History:</span>
                  <p className="text-slate-200 mt-1 whitespace-pre-wrap">{selectedPatient.medical_history}</p>
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsViewPatientOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-semibold transition-colors cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsViewPatientOpen(false);
                  handleOpenEdit(selectedPatient);
                }}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
              >
                Edit Patient Record
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 4: ADD ROOM (WORKING CLOSE & SUBMIT)               */}
      {/* ======================================================== */}
      {isAddRoomOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsAddRoomOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Bed className="w-5 h-5 text-blue-400" />
                Add New Room
              </h3>
              <button 
                type="button"
                onClick={() => setIsAddRoomOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRoom} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Room Number *</label>
                <input
                  type="text"
                  required
                  maxLength={10}
                  value={roomFormData.room_number}
                  onChange={(e) => setRoomFormData({ ...roomFormData, room_number: e.target.value })}
                  placeholder="e.g. 305, ICU-04"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Department *</label>
                <select
                  value={roomFormData.department_id}
                  onChange={(e) => setRoomFormData({ ...roomFormData, department_id: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Room Type</label>
                  <select
                    value={roomFormData.room_type}
                    onChange={(e) => setRoomFormData({ ...roomFormData, room_type: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="General">General</option>
                    <option value="ICU">ICU</option>
                    <option value="Emergency">Emergency</option>
                    <option value="Surgery">Surgery</option>
                    <option value="Private">Private</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Capacity</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={roomFormData.capacity}
                    onChange={(e) => setRoomFormData({ ...roomFormData, capacity: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddRoomOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isSubmitting ? 'Creating Room...' : 'Create Room'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 5: ADD BED (WORKING CLOSE & SUBMIT)                */}
      {/* ======================================================== */}
      {isAddBedOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsAddBedOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Bed className="w-5 h-5 text-emerald-400" />
                Add New Bed Slot
              </h3>
              <button 
                type="button"
                onClick={() => setIsAddBedOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateBed} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Bed Number *</label>
                <input
                  type="text"
                  required
                  maxLength={10}
                  value={bedFormData.bed_number}
                  onChange={(e) => setBedFormData({ ...bedFormData, bed_number: e.target.value })}
                  placeholder="e.g. 101-A, B-305"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Select Ward Room *</label>
                <select
                  value={bedFormData.room_id}
                  onChange={(e) => setBedFormData({ ...bedFormData, room_id: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  {rooms.map(r => (
                    <option key={r.id} value={r.id}>Room {r.room_number} ({r.room_type || 'General'})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Bed Type</label>
                  <select
                    value={bedFormData.bed_type}
                    onChange={(e) => setBedFormData({ ...bedFormData, bed_type: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Standard">Standard</option>
                    <option value="ICU">ICU</option>
                    <option value="Electric">Electric</option>
                    <option value="Pediatric">Pediatric</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Status</label>
                  <select
                    value={bedFormData.status}
                    onChange={(e) => setBedFormData({ ...bedFormData, status: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="available">Available</option>
                    <option value="occupied">Occupied</option>
                    <option value="maintenance">Maintenance</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddBedOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isSubmitting ? 'Creating Bed...' : 'Create Bed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 6: ADD STAFF (WORKING CLOSE & SUBMIT)              */}
      {/* ======================================================== */}
      {isAddStaffOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsAddStaffOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Stethoscope className="w-5 h-5 text-purple-400" />
                Add Staff Member
              </h3>
              <button 
                type="button"
                onClick={() => setIsAddStaffOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateStaff} className="mt-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">First Name *</label>
                  <input
                    type="text"
                    required
                    value={staffFormData.first_name}
                    onChange={(e) => setStaffFormData({ ...staffFormData, first_name: e.target.value })}
                    placeholder="e.g. Sarah"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={staffFormData.last_name}
                    onChange={(e) => setStaffFormData({ ...staffFormData, last_name: e.target.value })}
                    placeholder="e.g. Jenkins"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Employee ID *</label>
                  <input
                    type="text"
                    required
                    maxLength={20}
                    value={staffFormData.employee_id}
                    onChange={(e) => setStaffFormData({ ...staffFormData, employee_id: e.target.value })}
                    placeholder="e.g. EMP2025"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Position / Title</label>
                  <select
                    value={staffFormData.position}
                    onChange={(e) => setStaffFormData({ ...staffFormData, position: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Doctor">Doctor</option>
                    <option value="Nurse">Nurse</option>
                    <option value="Surgeon">Surgeon</option>
                    <option value="Technician">Technician</option>
                    <option value="Administrator">Administrator</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Department *</label>
                <select
                  value={staffFormData.department_id}
                  onChange={(e) => setStaffFormData({ ...staffFormData, department_id: e.target.value })}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                >
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Specialization</label>
                <input
                  type="text"
                  value={staffFormData.specialization}
                  onChange={(e) => setStaffFormData({ ...staffFormData, specialization: e.target.value })}
                  placeholder="e.g. Cardiology, Pediatrics, ICU"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddStaffOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isSubmitting ? 'Adding Staff...' : 'Add Staff Member'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 7: ADD SUPPLY (WORKING CLOSE & SUBMIT)             */}
      {/* ======================================================== */}
      {isAddSupplyOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsAddSupplyOpen(false);
          }}
        >
          <div 
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Package className="w-5 h-5 text-cyan-400" />
                Add Supply Item
              </h3>
              <button 
                type="button"
                onClick={() => setIsAddSupplyOpen(false)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={async (e) => {
              e.preventDefault();
              setIsSubmitting(true);
              try {
                const res = await callMcpTool('create_supply', {
                  item_code: supplyFormData.item_code,
                  name: supplyFormData.name,
                  category_id: suppliesList[0]?.category_id || undefined,
                  unit_of_measure: supplyFormData.unit_of_measure,
                  current_stock: parseInt(supplyFormData.current_stock) || 50,
                  minimum_stock_level: parseInt(supplyFormData.minimum_stock_level) || 10
                });
                if (res && (res.success || res.data)) {
                  notify('success', `Supply ${supplyFormData.name} added to PostgreSQL!`);
                  setIsAddSupplyOpen(false);
                  await fetchFacilityData();
                } else {
                  throw new Error(res?.message || 'Creation failed');
                }
              } catch (err) {
                notify('error', `Failed to create supply: ${err.message}`);
              } finally {
                setIsSubmitting(false);
              }
            }} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Item Code *</label>
                <input
                  type="text"
                  required
                  maxLength={20}
                  value={supplyFormData.item_code}
                  onChange={(e) => setSupplyFormData({ ...supplyFormData, item_code: e.target.value })}
                  placeholder="e.g. SUP00099"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Supply Name *</label>
                <input
                  type="text"
                  required
                  value={supplyFormData.name}
                  onChange={(e) => setSupplyFormData({ ...supplyFormData, name: e.target.value })}
                  placeholder="e.g. Sterile Gauze Pads (4x4)"
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Initial Stock</label>
                  <input
                    type="number"
                    min="1"
                    value={supplyFormData.current_stock}
                    onChange={(e) => setSupplyFormData({ ...supplyFormData, current_stock: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Unit</label>
                  <input
                    type="text"
                    value={supplyFormData.unit_of_measure}
                    onChange={(e) => setSupplyFormData({ ...supplyFormData, unit_of_measure: e.target.value })}
                    placeholder="pack, box, vial"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddSupplyOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isSubmitting ? 'Adding Supply...' : 'Add Supply Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default HospitalManagementSystem;

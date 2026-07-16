import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  Compass, MapPin, CheckCircle, Navigation, 
  Scan, Key, LogOut, Loader2, Play, ChevronRight, X
} from 'lucide-react';

const AgentDashboard = () => {
  const { user, logout } = useAuth();
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Verification Modal states
  const [activeStop, setActiveStop] = useState(null);
  const [modalType, setModalType] = useState(''); // 'qr' or 'otp'
  
  // Input fields
  const [qrCode, setQrCode] = useState('');
  const [otpCode, setOtpCode] = useState('');
  
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');

  const fetchRoster = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await api.get('/routes/agent/today');
      setRoute(response.data);
    } catch (e) {
      setError(e.response?.data?.message || 'No active route assigned today.');
      setRoute(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoster();
  }, [user]);

  const handleOpenModal = (stop, type) => {
    setActiveStop(stop);
    setModalType(type);
    setQrCode('');
    setOtpCode('');
    setActionError('');
  };

  const handleCloseModal = () => {
    setActiveStop(null);
    setModalType('');
    setActionError('');
  };

  // QR Validation (Intake Out For Delivery)
  const handleVerifyQR = async (e) => {
    e.preventDefault();
    if (!qrCode) {
      setActionError('Please enter or scan the parcel QR barcode hash.');
      return;
    }
    
    setActionLoading(true);
    setActionError('');
    try {
      await api.patch(`/shipments/${activeStop.shipment_id}/status`, {
        status: 'Out For Delivery',
        qr_payload: qrCode
      });
      fetchRoster(); // reload sequence
      handleCloseModal();
    } catch (err) {
      setActionError(err.response?.data?.message || 'QR validation failed. Code mismatch.');
    } finally {
      setActionLoading(false);
    }
  };

  // OTP Validation (Complete Delivery)
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!otpCode) {
      setActionError('Please input the customer OTP code.');
      return;
    }
    
    setActionLoading(true);
    setActionError('');
    try {
      await api.post(`/shipments/${activeStop.shipment_id}/verify-otp`, {
        otp: otpCode
      });
      fetchRoster(); // reload sequence
      handleCloseModal();
    } catch (err) {
      setActionError(err.response?.data?.message || 'OTP check failed. Invalid code.');
    } finally {
      setActionLoading(false);
    }
  };

  const getNavigationLink = (stop) => {
    // Launch turn-by-turn routing on Google Maps client
    return `https://www.google.com/maps/dir/?api=1&destination=${stop.lat},${stop.lng}&travelmode=driving`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Delivered':
        return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case 'Out For Delivery':
        return 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
      case 'Two Stops Away':
        return 'bg-purple-500/10 text-purple-400 border border-purple-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border border-slate-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 pb-12">
      {/* Navbar */}
      <nav className="border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-500 rounded-xl">
            <Compass className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-wider text-white">RouteX</span>
          <span className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-2 py-0.5 rounded">Courier Dashboard</span>
        </div>
        <div className="flex items-center space-x-6">
          <span className="text-sm text-slate-300">Agent: <strong className="text-white">{user?.name}</strong></span>
          <button 
            onClick={logout} 
            className="flex items-center space-x-2 text-slate-400 hover:text-red-400 font-semibold transition cursor-pointer"
          >
            <LogOut className="h-5 w-5" />
            <span>Logout</span>
          </button>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 mt-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Today's Routing Sequence</h2>
          <button 
            onClick={fetchRoster} 
            className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-indigo-400 font-semibold px-3 py-1.5 rounded-xl cursor-pointer"
          >
            Sync Route
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="glass-panel rounded-3xl p-12 text-center text-slate-500">
            <Compass className="h-16 w-16 mx-auto mb-4 text-slate-700" />
            <p className="text-lg font-bold text-slate-400">{error}</p>
            <p className="text-sm mt-2">Check back later when dispatcher assigns new stops.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {route?.stops.map((stop, index) => {
              const isUnvisited = !stop.visited_at;
              
              return (
                <div 
                  key={stop.id}
                  className={`glass-panel rounded-2xl p-6 border flex flex-col md:flex-row md:items-center md:justify-between transition duration-300 ${
                    isUnvisited ? 'border-slate-800' : 'border-emerald-500/20 bg-emerald-950/5 opacity-60'
                  }`}
                >
                  <div className="flex items-start space-x-4">
                    {/* Index Sequence number */}
                    <div className={`h-10 w-10 shrink-0 font-extrabold text-sm flex items-center justify-center rounded-xl border ${
                      isUnvisited 
                        ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/25' 
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                    }`}>
                      {stop.sequence_index}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-bold text-white text-lg">{stop.recipient_name}</h3>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full ${getStatusColor(stop.status)}`}>
                          {stop.status}
                        </span>
                      </div>
                      <p className="text-slate-400 text-sm flex items-center">
                        <MapPin className="h-4 w-4 inline mr-1 text-slate-500 shrink-0" />
                        {stop.delivery_address}
                      </p>
                      {stop.visited_at && (
                        <p className="text-slate-500 text-xs">
                          Completed: {new Date(stop.visited_at).toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions column */}
                  {isUnvisited && (
                    <div className="mt-4 md:mt-0 flex items-center space-x-2 md:self-center">
                      {/* Navigate link */}
                      <a
                        href={getNavigationLink(stop)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow shadow-indigo-600/20 transition cursor-pointer"
                      >
                        <Navigation className="h-4 w-4" />
                        <span>Navigate</span>
                      </a>

                      {/* Verification toggles */}
                      {stop.status === 'Assigned to Delivery Agent' ? (
                        <button
                          onClick={() => handleOpenModal(stop, 'qr')}
                          className="flex items-center space-x-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-bold border border-slate-700 rounded-xl transition cursor-pointer"
                        >
                          <Scan className="h-4 w-4" />
                          <span>Load QR</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleOpenModal(stop, 'otp')}
                          className="flex items-center space-x-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow shadow-emerald-600/20 transition cursor-pointer"
                        >
                          <Key className="h-4 w-4" />
                          <span>Verify OTP</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Verification overlay popups */}
      {modalType && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm glass-panel rounded-3xl p-6 relative border border-slate-800 shadow-2xl">
            <button 
              onClick={handleCloseModal}
              className="absolute top-4 right-4 text-slate-500 hover:text-white transition cursor-pointer"
            >
              <X className="h-6 w-6" />
            </button>

            {modalType === 'qr' ? (
              <form onSubmit={handleVerifyQR} className="space-y-4">
                <div className="text-center mb-4">
                  <Scan className="h-10 w-10 text-indigo-400 mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-white">Ingest Parcel QR</h3>
                  <p className="text-xs text-slate-400">Scan or submit the parcel label hash code to load package</p>
                </div>
                
                {actionError && <p className="text-xs text-red-400 text-center bg-red-950/30 border border-red-500/20 py-2 rounded">{actionError}</p>}
                
                <input
                  type="text"
                  value={qrCode}
                  onChange={(e) => setQrCode(e.target.value)}
                  placeholder="Paste SHA256 QR payload code"
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                />

                <button
                  type="submit"
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition cursor-pointer flex items-center justify-center"
                  disabled={actionLoading}
                >
                  {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Confirm QR Validation'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div className="text-center mb-4">
                  <Key className="h-10 w-10 text-emerald-400 mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-white">Delivery OTP Handshake</h3>
                  <p className="text-xs text-slate-400">Request the 6-digit numeric security code from customer</p>
                </div>

                {actionError && <p className="text-xs text-red-400 text-center bg-red-950/30 border border-red-500/20 py-2 rounded">{actionError}</p>}

                <input
                  type="text"
                  maxLength="6"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  placeholder="e.g. 583921"
                  className="w-full px-3 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white text-center text-lg tracking-widest font-extrabold focus:outline-none focus:border-emerald-500"
                />

                <button
                  type="submit"
                  className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition cursor-pointer flex items-center justify-center"
                  disabled={actionLoading}
                >
                  {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Finalize Handshake'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentDashboard;

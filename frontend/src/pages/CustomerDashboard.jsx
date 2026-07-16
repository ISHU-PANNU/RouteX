import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  Package, Plus, Calendar, Compass, 
  MapPin, User, CheckCircle, Truck, 
  Clock, ShieldAlert, Key, LogOut, ArrowRight, Loader2
} from 'lucide-react';

const CustomerDashboard = () => {
  const { user, logout } = useAuth();
  const [shipments, setShipments] = useState([]);
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [trackingDetails, setTrackingDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Booking Form State
  const [weight, setWeight] = useState('');
  const [length, setLength] = useState('');
  const [width, setWidth] = useState('');
  const [height, setHeight] = useState('');
  const [description, setDescription] = useState('');
  const [pickupAddress, setPickupAddress] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [recName, setRecName] = useState('');
  const [recPhone, setRecPhone] = useState('');
  const [recEmail, setRecEmail] = useState('');
  
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState('');
  const [bookingError, setBookingError] = useState('');
  const [activeTab, setActiveTab] = useState('list'); // 'list' or 'book'

  const fetchShipments = async () => {
    try {
      setLoading(true);
      const response = await api.get('/shipments', {
        params: { customer_id: user?.id }
      });
      setShipments(response.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShipments();
  }, [user]);

  const handleSelectShipment = async (shipment) => {
    setSelectedShipment(shipment);
    setTrackingDetails(null);
    try {
      const response = await api.get(`/tracking/${shipment.tracking_number}`);
      setTrackingDetails(response.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleBookShipment = async (e) => {
    e.preventDefault();
    setBookingError('');
    setBookingSuccess('');
    
    if (!weight || !pickupAddress || !deliveryAddress || !recName || !recPhone || !recEmail) {
      setBookingError('Please fill in all required shipment details fields.');
      return;
    }

    setBookingLoading(true);
    try {
      const response = await api.post('/shipments/book', {
        weight: parseFloat(weight),
        length_cm: length ? parseFloat(length) : null,
        width_cm: width ? parseFloat(width) : null,
        height_cm: height ? parseFloat(height) : null,
        description,
        pickup_address: pickupAddress,
        delivery_address: deliveryAddress,
        receiver_name: recName,
        receiver_phone: recPhone,
        receiver_email: recEmail
      });
      
      setBookingSuccess(`Parcel booked successfully! Tracking ID: ${response.data.tracking_number}`);
      // Clear fields
      setWeight(''); setLength(''); setWidth(''); setHeight(''); setDescription('');
      setPickupAddress(''); setDeliveryAddress(''); setRecName(''); setRecPhone(''); setRecEmail('');
      
      // Refresh shipments list
      fetchShipments();
      
      // Auto toggle tab back to list after delay
      setTimeout(() => {
        setActiveTab('list');
        setBookingSuccess('');
      }, 3000);
    } catch (e) {
      let errorMsg = 'Geocoding failed or input parameters invalid.';
      if (e.response?.data?.detail) {
        if (Array.isArray(e.response.data.detail)) {
          errorMsg = e.response.data.detail.map(d => d.msg).join(', ');
        } else {
          errorMsg = e.response.data.detail;
        }
      } else if (e.response?.data?.message) {
        errorMsg = e.response.data.message;
      }
      setBookingError(errorMsg);
    } finally {
      setBookingLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Delivered':
        return <CheckCircle className="h-5 w-5 text-emerald-400" />;
      case 'Out For Delivery':
      case 'Two Stops Away':
        return <Truck className="h-5 w-5 text-indigo-400 animate-pulse" />;
      default:
        return <Clock className="h-5 w-5 text-amber-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Delivered':
        return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case 'Out For Delivery':
        return 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
      case 'Two Stops Away':
        return 'bg-purple-500/10 text-purple-400 border border-purple-500/30 animate-pulse';
      default:
        return 'bg-slate-500/10 text-slate-400 border border-slate-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 pb-12">
      {/* Navigation Bar */}
      <nav className="border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-500 rounded-xl">
            <Compass className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-wider text-white">RouteX</span>
          <span className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-2 py-0.5 rounded">Customer Portal</span>
        </div>
        <div className="flex items-center space-x-6">
          <span className="text-sm text-slate-300">Welcome, <strong className="text-white">{user?.name}</strong></span>
          <button 
            onClick={logout} 
            className="flex items-center space-x-2 text-slate-400 hover:text-red-400 font-semibold transition cursor-pointer"
          >
            <LogOut className="h-5 w-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 mt-8">
        {/* Toggle navigation bar */}
        <div className="flex space-x-4 mb-8">
          <button
            onClick={() => { setActiveTab('list'); setSelectedShipment(null); }}
            className={`px-6 py-3 rounded-xl font-bold transition duration-300 cursor-pointer ${
              activeTab === 'list' 
                ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' 
                : 'bg-slate-800/40 border border-slate-700/50 text-slate-400 hover:text-white'
            }`}
          >
            <Package className="h-5 w-5 inline mr-2" />
            My Bookings
          </button>
          <button
            onClick={() => setActiveTab('book')}
            className={`px-6 py-3 rounded-xl font-bold transition duration-300 cursor-pointer ${
              activeTab === 'book' 
                ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' 
                : 'bg-slate-800/40 border border-slate-700/50 text-slate-400 hover:text-white'
            }`}
          >
            <Plus className="h-5 w-5 inline mr-2" />
            Book New Shipment
          </button>
        </div>

        {/* Tab content */}
        {activeTab === 'list' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left side: list of bookings */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="text-xl font-bold text-white mb-4">Booked Parcels</h2>
              {loading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
                </div>
              ) : shipments.length === 0 ? (
                <div className="glass-panel rounded-2xl p-12 text-center text-slate-400">
                  <Package className="h-16 w-16 mx-auto mb-4 text-slate-600" />
                  <p className="text-lg">No shipments booked yet.</p>
                  <button onClick={() => setActiveTab('book')} className="mt-4 text-indigo-400 font-bold hover:underline cursor-pointer">
                    Book your first shipment now <ArrowRight className="inline h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {shipments.map((s) => (
                    <div 
                      key={s.id} 
                      onClick={() => handleSelectShipment(s)}
                      className={`glass-card rounded-2xl p-6 cursor-pointer border ${
                        selectedShipment?.id === s.id ? 'border-indigo-500 bg-indigo-950/10' : 'border-slate-800/80'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <span className="text-xs text-slate-500 font-mono">{s.tracking_number}</span>
                        <span className={`text-xs px-2.5 py-1 rounded-full ${getStatusColor(s.status)}`}>
                          {s.status}
                        </span>
                      </div>
                      <h3 className="font-bold text-white text-lg mb-2">{s.receiver_name}</h3>
                      <p className="text-slate-400 text-sm line-clamp-1 mb-4">
                        <MapPin className="h-4 w-4 inline mr-1 text-slate-500" />
                        {s.delivery_address}
                      </p>
                      <div className="flex items-center text-xs text-slate-500">
                        <Calendar className="h-4 w-4 inline mr-1" />
                        {new Date(s.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right side: detail / tracking view */}
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-white mb-4">Live Tracking Timeline</h2>
              {selectedShipment ? (
                <div className="glass-panel rounded-3xl p-6 space-y-6">
                  <div>
                    <span className="text-xs text-slate-500 font-mono block mb-1">{selectedShipment.tracking_number}</span>
                    <h3 className="text-2xl font-bold text-white">{selectedShipment.receiver_name}</h3>
                    <div className={`inline-block mt-2 text-sm px-3 py-1 rounded-full ${getStatusColor(selectedShipment.status)}`}>
                      {selectedShipment.status}
                    </div>
                  </div>

                  {/* Proximity alerts */}
                  {trackingDetails?.two_stops_away_alert && (
                    <div className="p-4 bg-purple-950/30 border border-purple-500/30 rounded-2xl text-purple-400 text-sm flex items-start space-x-3 animate-pulse">
                      <ShieldAlert className="h-5 w-5 shrink-0 mt-0.5" />
                      <div>
                        <strong className="block font-bold">Courier is Two Stops Away!</strong>
                        Prepare to share your verification OTP code when they arrive.
                      </div>
                    </div>
                  )}

                  {/* OTP Code display */}
                  {trackingDetails?.otp_code && (
                    <div className="p-4 bg-indigo-950/20 border border-indigo-500/20 rounded-2xl flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Key className="h-5 w-5 text-indigo-400" />
                        <span className="text-slate-300 text-sm">Delivery Security OTP</span>
                      </div>
                      <span className="text-xl font-extrabold text-white tracking-widest bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
                        {trackingDetails.otp_code}
                      </span>
                    </div>
                  )}

                  {/* Route stop details */}
                  <div className="text-sm space-y-2 border-y border-slate-800 py-4">
                    <p className="text-slate-400">
                      <strong className="text-slate-300">Pickup Location:</strong> {selectedShipment.pickup_address}
                    </p>
                    <p className="text-slate-400">
                      <strong className="text-slate-300">Delivery Address:</strong> {selectedShipment.delivery_address}
                    </p>
                    <p className="text-slate-400">
                      <strong className="text-slate-300">Package Weight:</strong> {selectedShipment.weight} Kg
                    </p>
                  </div>

                  {/* Tracking history step stepper */}
                  <div>
                    <h4 className="font-bold text-white text-sm mb-4">Journey Path</h4>
                    <div className="relative border-l border-slate-800 pl-6 ml-3 space-y-6">
                      {trackingDetails?.timeline.map((t, idx) => (
                        <div key={idx} className="relative">
                          {/* Stepper node circle */}
                          <div className="absolute -left-[31px] bg-slate-900 border border-slate-800 p-1 rounded-full">
                            {getStatusIcon(t.status)}
                          </div>
                          <div>
                            <span className="font-bold text-white text-sm block">{t.status}</span>
                            <span className="text-slate-500 text-xs">{new Date(t.timestamp).toLocaleString()}</span>
                            {t.remarks && <p className="text-slate-400 text-xs mt-1">{t.remarks}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass-panel rounded-3xl p-8 text-center text-slate-500">
                  <Compass className="h-12 w-12 mx-auto mb-3 text-slate-700" />
                  <p>Select a parcel from the roster to view live status timelines and OTP keys.</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Book Shipment panel */
          <div className="max-w-2xl mx-auto glass-panel rounded-3xl p-8 shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-6">Book New Shipment</h2>
            
            {bookingSuccess && (
              <div className="mb-6 p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm text-center">
                {bookingSuccess}
              </div>
            )}
            {bookingError && (
              <div className="mb-6 p-4 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-sm text-center">
                {bookingError}
              </div>
            )}

            <form onSubmit={handleBookShipment} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Parcel Weight (Kg)*</label>
                  <input
                    type="number"
                    step="0.1"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    placeholder="2.5"
                    className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Length / Width / Height (cm)</label>
                  <div className="grid grid-cols-3 gap-2">
                    <input type="number" placeholder="L" value={length} onChange={(e) => setLength(e.target.value)} className="w-full px-3 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white text-center focus:outline-none focus:border-indigo-500" />
                    <input type="number" placeholder="W" value={width} onChange={(e) => setWidth(e.target.value)} className="w-full px-3 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white text-center focus:outline-none focus:border-indigo-500" />
                    <input type="number" placeholder="H" value={height} onChange={(e) => setHeight(e.target.value)} className="w-full px-3 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white text-center focus:outline-none focus:border-indigo-500" />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 text-sm font-semibold mb-2">Content Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Fragile home electronics"
                  className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none"
                />
              </div>

              <div className="border-t border-slate-800/80 pt-6 space-y-6">
                <h3 className="font-bold text-white text-lg">Routing Logistics</h3>
                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Pickup Location Address*</label>
                  <input
                    type="text"
                    value={pickupAddress}
                    onChange={(e) => setPickupAddress(e.target.value)}
                    placeholder="123 Warehouse Rd, San Francisco, CA"
                    className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Delivery Destination Address*</label>
                  <input
                    type="text"
                    value={deliveryAddress}
                    onChange={(e) => setDeliveryAddress(e.target.value)}
                    placeholder="456 Mission St, San Francisco, CA"
                    className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="border-t border-slate-800/80 pt-6 space-y-6">
                <h3 className="font-bold text-white text-lg">Recipient Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-slate-300 text-sm font-semibold mb-2">Recipient Name*</label>
                    <div className="relative">
                      <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                        <User className="h-5 w-5" />
                      </span>
                      <input
                        type="text"
                        value={recName}
                        onChange={(e) => setRecName(e.target.value)}
                        placeholder="Elena Rostova"
                        className="w-full pl-10 pr-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-slate-300 text-sm font-semibold mb-2">Recipient Phone*</label>
                    <input
                      type="text"
                      value={recPhone}
                      onChange={(e) => setRecPhone(e.target.value)}
                      placeholder="+15559876"
                      className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Recipient Email*</label>
                  <input
                    type="email"
                    value={recEmail}
                    onChange={(e) => setRecEmail(e.target.value)}
                    placeholder="elena@example.com"
                    className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="flex space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => setActiveTab('list')}
                  className="w-1/3 py-3 border border-slate-700 text-slate-400 font-bold rounded-xl hover:bg-slate-800/30 transition cursor-pointer"
                  disabled={bookingLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-2/3 py-3 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 hover:from-indigo-600 hover:to-purple-700 transition flex items-center justify-center cursor-pointer"
                  disabled={bookingLoading}
                >
                  {bookingLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Saving Booking...
                    </>
                  ) : (
                    'Finalize Booking'
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerDashboard;

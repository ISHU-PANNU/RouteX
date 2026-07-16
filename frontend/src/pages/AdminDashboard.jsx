import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import L from 'leaflet';
import { 
  Compass, BarChart3, Users, Route, 
  Download, Loader2, LogOut, Package, 
  CheckCircle2, Clock, AlertTriangle, UserCheck,
  X, Eye, Info
} from 'lucide-react';

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  
  // Dashboard Metrics states
  const [todayStats, setTodayStats] = useState(null);
  const [cumulativeStats, setCumulativeStats] = useState(null);
  const [unassignedShipments, setUnassignedShipments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Routing Dispatch Selection
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [selectedShipmentIds, setSelectedShipmentIds] = useState([]);
  const [routingLoading, setRoutingLoading] = useState(false);
  const [routingSuccess, setRoutingSuccess] = useState('');
  const [routingError, setRoutingError] = useState('');
  
  // Preview Optimization states
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  // CSV Export states
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [exportLoading, setExportLoading] = useState(false);

  // Live Tracking states
  const [activeShipments, setActiveShipments] = useState([]);
  const [selectedTrackingShipment, setSelectedTrackingShipment] = useState(null);
  const [trackingMapDetails, setTrackingMapDetails] = useState(null);
  const [trackingMapLoading, setTrackingMapLoading] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch stats parallel
      const [todayRes, cumulativeRes, shipmentsRes] = await Promise.all([
        api.get('/analytics/dashboard'),
        api.get('/analytics/admin/cumulative'),
        api.get('/shipments')
      ]);
      
      setTodayStats(todayRes.data);
      setCumulativeStats(cumulativeRes.data);
      
      // Filter unassigned shipments
      const unassigned = shipmentsRes.data.filter(s => !s.delivery_agent_id);
      setUnassignedShipments(unassigned);
      
      // Filter active (in-transit) shipments
      const active = shipmentsRes.data.filter(s => 
        s.status === 'Out For Delivery' || s.status === 'Two Stops Away'
      );
      setActiveShipments(active);
      
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTrackingShipment = async (shipment) => {
    if (!shipment) {
      setSelectedTrackingShipment(null);
      setTrackingMapDetails(null);
      return;
    }
    setSelectedTrackingShipment(shipment);
    setTrackingMapDetails(null);
    setTrackingMapLoading(true);
    try {
      const res = await api.get(`/tracking/${shipment.tracking_number}`);
      setTrackingMapDetails(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setTrackingMapLoading(false);
    }
  };

  useEffect(() => {
    if (!selectedTrackingShipment || !trackingMapDetails) return;

    const timer = setTimeout(() => {
      const container = document.getElementById('live-tracking-map');
      if (!container) return;

      // Clean up previous map if it exists
      if (container._leaflet_map) {
        container._leaflet_map.remove();
        delete container._leaflet_map;
      }

      const { courier_lat, courier_lng, destination_lat, destination_lng } = trackingMapDetails;
      
      const centerLat = courier_lat || destination_lat;
      const centerLng = courier_lng || destination_lng;
      
      const map = L.map('live-tracking-map', {
        zoomControl: true,
      }).setView([centerLat, centerLng], 13);

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      const courierIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="background-color: #a855f7; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #a855f7;"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      const destIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="background-color: #10b981; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px #10b981;"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      });

      const markers = [];

      const destMarker = L.marker([destination_lat, destination_lng], { icon: destIcon })
        .bindPopup(`<strong>Recipient: ${selectedTrackingShipment.receiver_name}</strong><br/>${selectedTrackingShipment.delivery_address}`)
        .addTo(map);
      markers.push([destination_lat, destination_lng]);

      if (courier_lat && courier_lng) {
        const courierMarker = L.marker([courier_lat, courier_lng], { icon: courierIcon })
          .bindPopup(`<strong>Courier Live Position</strong><br/>Status: ${trackingMapDetails.status}`)
          .addTo(map);
        markers.push([courier_lat, courier_lng]);
        
        L.polyline([[courier_lat, courier_lng], [destination_lat, destination_lng]], {
          color: '#a855f7',
          weight: 3,
          dashArray: '5, 8',
          opacity: 0.8
        }).addTo(map);
      }

      if (markers.length > 0) {
        map.fitBounds(markers, { padding: [50, 50] });
      }

      container._leaflet_map = map;
    }, 100);

    return () => {
      clearTimeout(timer);
      const container = document.getElementById('live-tracking-map');
      if (container && container._leaflet_map) {
        container._leaflet_map.remove();
        delete container._leaflet_map;
      }
    };
  }, [selectedTrackingShipment, trackingMapDetails]);

  const fetchAgents = async () => {
    try {
      // In production, we list drivers. We can filter shipments API by drivers 
      // or fetch users. Since we can extract agents from today's dashboard top_agents 
      // list or simulate, we can fetch shipments/agents. Let's do a fast query on users.
      // Since users requires admin roles, we can query users.
      const res = await api.get('/shipments');
      // Extract unique agent IDs and names that are assigned or listed in the system,
      // or mock drivers list. Let's register drivers from top agents and add defaults.
      setAgents([
        { id: 5, name: 'Delivery Agent Bob (agent@example.com)' },
        { id: 6, name: 'Delivery Agent Alice (agent2@example.com)' },
        { id: 2, name: 'Delivery Agent Ish (ishupannu08@gmail.com)' }
      ]);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchAgents();
  }, [user]);

  const handleSelectShipment = (id) => {
    setSelectedShipmentIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handlePreviewRoute = async (e) => {
    e.preventDefault();
    setRoutingError('');
    setRoutingSuccess('');
    
    if (!selectedAgentId) {
      setRoutingError('Please select a Delivery Agent.');
      return;
    }
    if (selectedShipmentIds.length === 0) {
      setRoutingError('Please select at least one shipment to route.');
      return;
    }
    
    setPreviewLoading(true);
    try {
      const res = await api.post('/routes/optimize-preview', {
        shipment_ids: selectedShipmentIds
      });
      setPreviewData(res.data);
      setShowPreviewModal(true);
    } catch (err) {
      setRoutingError(err.response?.data?.message || 'Routing optimizer preview failed.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleConfirmDispatch = async () => {
    setRoutingLoading(true);
    setRoutingError('');
    setRoutingSuccess('');
    try {
      await api.post('/routes/optimize-and-assign', {
        delivery_agent_id: parseInt(selectedAgentId),
        shipment_ids: selectedShipmentIds
      });
      
      setRoutingSuccess('Optimal route successfully assigned to courier!');
      setSelectedShipmentIds([]);
      setShowPreviewModal(false);
      setPreviewData(null);
      fetchDashboardData(); // reload statistics and unassigned pools
    } catch (err) {
      setRoutingError(err.response?.data?.message || 'Routing optimizer pipeline failed.');
    } finally {
      setRoutingLoading(false);
    }
  };

  useEffect(() => {
    if (!showPreviewModal || !previewData) return;

    // Wait a brief tick to ensure DOM element is mounted
    const timer = setTimeout(() => {
      const container = document.getElementById('preview-map');
      if (!container) return;

      const map = L.map('preview-map', {
        zoomControl: true,
      }).setView([previewData.depot_lat, previewData.depot_lng], 13);

      // Dark Mode Tiles (CartoDB Dark Matter)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      // Simple SVG icons
      const depotIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="background-color: #ef4444; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #ef4444;"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      const stopIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="background-color: #6366f1; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px #6366f1;"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      });

      // Add Depot marker
      L.marker([previewData.depot_lat, previewData.depot_lng], { icon: depotIcon })
        .bindPopup(`<strong>Depot (RouteX Hub)</strong><br/>${previewData.depot_address}`)
        .addTo(map);

      // Add Stop markers
      const stopCoords = previewData.stops.map(s => [s.lat, s.lng]);
      previewData.stops.forEach((stop, index) => {
        L.marker([stop.lat, stop.lng], { icon: stopIcon })
          .bindPopup(`<strong>Stop #${index + 1}:</strong> ${stop.recipient_name}<br/>${stop.delivery_address}`)
          .addTo(map);
      });

      // Original route sequence polylines (depot -> stops in default selected order -> depot)
      const originalLatLngs = previewData.original_sequence.map(idx => {
        if (idx === 0) return [previewData.depot_lat, previewData.depot_lng];
        const stop = previewData.stops[idx - 1];
        return [stop.lat, stop.lng];
      });

      // Optimized route sequence polylines
      const optimizedLatLngs = previewData.optimized_sequence.map(idx => {
        if (idx === 0) return [previewData.depot_lat, previewData.depot_lng];
        const stop = previewData.stops[idx - 1];
        return [stop.lat, stop.lng];
      });

      // Draw original sequence: Red dashed line
      L.polyline(originalLatLngs, {
        color: '#f87171',
        weight: 3,
        dashArray: '5, 8',
        opacity: 0.6
      }).addTo(map);

      // Draw optimized sequence: Emerald solid line
      L.polyline(optimizedLatLngs, {
        color: '#10b981',
        weight: 4,
        opacity: 0.95
      }).addTo(map);

      // Fit bounds
      const allCoords = [[previewData.depot_lat, previewData.depot_lng], ...stopCoords];
      map.fitBounds(allCoords, { padding: [50, 50] });

      // Clean up map ref
      container._leaflet_map = map;
    }, 100);

    return () => {
      clearTimeout(timer);
      const container = document.getElementById('preview-map');
      if (container && container._leaflet_map) {
        container._leaflet_map.remove();
        delete container._leaflet_map;
      }
    };
  }, [showPreviewModal, previewData]);

  const handleExportCSV = async (e) => {
    e.preventDefault();
    if (!startDate || !endDate) return;
    
    setExportLoading(true);
    try {
      const response = await api.get('/analytics/reports/export', {
        params: { start_date: startDate, end_date: endDate },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `RouteX_Report_${startDate}_to_${endDate}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    } finally {
      setExportLoading(false);
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
          <span className="text-xs bg-slate-800 border border-slate-700 text-slate-400 px-2 py-0.5 rounded">Admin Hub</span>
        </div>
        <div className="flex items-center space-x-6">
          <span className="text-sm text-slate-300">Admin: <strong className="text-white">{user?.name}</strong></span>
          <button 
            onClick={logout} 
            className="flex items-center space-x-2 text-slate-400 hover:text-red-400 font-semibold transition cursor-pointer"
          >
            <LogOut className="h-5 w-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 mt-8 space-y-8">
        
        {/* KPI Dashboard stats summary */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
          </div>
        ) : (
          <>
            {/* Top statistics counts */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Cumulative Parcels</span>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{cumulativeStats?.total_shipments}</h3>
                </div>
                <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400"><Package className="h-6 w-6" /></div>
              </div>

              <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">In Transit</span>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{cumulativeStats?.pending_shipments}</h3>
                </div>
                <div className="p-3 bg-amber-500/10 rounded-xl text-amber-400"><Clock className="h-6 w-6" /></div>
              </div>

              <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Completed</span>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{cumulativeStats?.delivered_shipments}</h3>
                </div>
                <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400"><CheckCircle2 className="h-6 w-6" /></div>
              </div>

              <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Active Agents</span>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{cumulativeStats?.active_delivery_agents}</h3>
                </div>
                <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400"><UserCheck className="h-6 w-6" /></div>
              </div>
            </div>

            {/* Middle Section: Routing solver & Reports */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Dispatch planning column */}
              <div className="lg:col-span-2 glass-panel rounded-3xl p-6 space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold text-white flex items-center">
                    <Route className="mr-2 h-5 w-5 text-indigo-400" />
                    Route Dispatch Center
                  </h2>
                  <span className="text-xs bg-slate-800 px-2.5 py-1 rounded text-slate-400">
                    {unassignedShipments.length} Unallocated Orders
                  </span>
                </div>

                {routingSuccess && <p className="p-3 bg-emerald-950/30 border border-emerald-500/20 text-emerald-400 text-sm rounded-xl text-center">{routingSuccess}</p>}
                {routingError && <p className="p-3 bg-red-950/30 border border-red-500/20 text-red-400 text-sm rounded-xl text-center">{routingError}</p>}

                <form onSubmit={handlePreviewRoute} className="space-y-6">
                  <div>
                    <label className="block text-slate-300 text-sm font-semibold mb-2">Select Target Courier</label>
                    <select
                      value={selectedAgentId}
                      onChange={(e) => setSelectedAgentId(e.target.value)}
                      className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">-- Choose Agent --</option>
                      {agents.map(a => (
                        <option key={a.id} value={a.id}>{a.name} (ID: {a.id})</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-3">
                    <label className="block text-slate-300 text-sm font-semibold">Select Shipments to optimize sequence</label>
                    {unassignedShipments.length === 0 ? (
                      <p className="text-slate-500 text-sm italic">All orders have been assigned to routes.</p>
                    ) : (
                      <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-xl divide-y divide-slate-800">
                        {unassignedShipments.map(s => (
                          <div 
                            key={s.id} 
                            onClick={() => handleSelectShipment(s.id)}
                            className="flex items-center space-x-3 px-4 py-3 hover:bg-slate-800/20 cursor-pointer transition"
                          >
                            <input
                              type="checkbox"
                              checked={selectedShipmentIds.includes(s.id)}
                              onChange={() => {}} // handled by div click
                              className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 h-4 w-4 cursor-pointer"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-bold text-white truncate">{s.receiver_name}</p>
                              <p className="text-xs text-slate-400 truncate">{s.delivery_address}</p>
                            </div>
                            <span className="text-xs text-slate-500 font-mono">{s.tracking_number}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow shadow-indigo-600/30 transition flex items-center justify-center cursor-pointer"
                    disabled={previewLoading}
                  >
                    {previewLoading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Generating Route Plan...
                      </>
                    ) : (
                      `Optimize & Preview ${selectedShipmentIds.length} Parcels`
                    )}
                  </button>
                </form>
              </div>

              {/* CSV Reports export column */}
              <div className="glass-panel rounded-3xl p-6 space-y-6 self-start">
                <h2 className="text-xl font-bold text-white flex items-center">
                  <Download className="mr-2 h-5 w-5 text-indigo-400" />
                  Export Reports
                </h2>
                <p className="text-xs text-slate-400">Download shipment logging statistics inside custom date intervals.</p>
                
                <form onSubmit={handleExportCSV} className="space-y-4">
                  <div>
                    <label className="block text-slate-300 text-sm font-semibold mb-2">From Date</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 text-sm font-semibold mb-2">To Date</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-white text-sm"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-bold rounded-xl border border-slate-700 transition flex items-center justify-center cursor-pointer"
                    disabled={exportLoading}
                  >
                    {exportLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Download CSV'}
                  </button>
                </form>
              </div>
            </div>

            {/* Live Tracking Map Section */}
            <div className="glass-panel rounded-3xl p-6 space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center">
                <Compass className="mr-2 h-5 w-5 text-indigo-400" />
                Live Active Deliveries Tracking
              </h2>
              <p className="text-xs text-slate-400">
                Track simulated courier positions and destination waypoints for active delivery shipments.
              </p>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Active Shipments List */}
                <div className="space-y-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Active Shipments ({activeShipments.length})
                  </span>
                  {activeShipments.length === 0 ? (
                    <p className="text-slate-500 text-sm italic">No shipments are currently in transit.</p>
                  ) : (
                    <div className="max-h-[350px] overflow-y-auto border border-slate-800 rounded-xl divide-y divide-slate-800">
                      {activeShipments.map(s => (
                        <div 
                          key={s.id}
                          onClick={() => handleSelectTrackingShipment(s)}
                          className={`flex items-center justify-between px-4 py-3 hover:bg-slate-800/20 cursor-pointer transition ${
                            selectedTrackingShipment?.id === s.id ? 'bg-indigo-950/20 border-l-2 border-indigo-500' : ''
                          }`}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold text-white truncate">{s.receiver_name}</p>
                            <p className="text-xs text-slate-400 truncate">{s.delivery_address}</p>
                            <span className="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full mt-1 inline-block">
                              {s.status}
                            </span>
                          </div>
                          <span className="text-xs text-slate-500 font-mono ml-2 shrink-0">{s.tracking_number}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Map Display */}
                <div className="lg:col-span-2 flex flex-col space-y-3">
                  {selectedTrackingShipment ? (
                    <>
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-300">
                          Tracking: <strong className="text-white">{selectedTrackingShipment.tracking_number}</strong> ({selectedTrackingShipment.receiver_name})
                        </span>
                        <button 
                          onClick={() => handleSelectTrackingShipment(null)}
                          className="text-red-400 hover:underline cursor-pointer"
                        >
                          Clear Map
                        </button>
                      </div>
                      
                      {trackingMapLoading ? (
                        <div className="w-full h-[350px] rounded-2xl border border-slate-800 bg-[#0d1527]/50 flex items-center justify-center">
                          <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
                        </div>
                      ) : (
                        <div 
                          id="live-tracking-map" 
                          className="w-full h-[350px] rounded-2xl border border-slate-800 overflow-hidden"
                          style={{ zIndex: 1 }}
                        />
                      )}
                      
                      {trackingMapDetails && (
                        <div className="flex items-center justify-center space-x-6 text-xs text-slate-400 bg-slate-900/50 py-2 rounded-xl border border-slate-800/40">
                          <div className="flex items-center space-x-1.5">
                            <span className="w-3.5 h-3.5 bg-purple-500 rounded-full inline-block"></span>
                            <span>Courier Simulated Location</span>
                          </div>
                          <div className="flex items-center space-x-1.5">
                            <span className="w-3.5 h-3.5 bg-emerald-500 rounded-full inline-block"></span>
                            <span>Destination Address</span>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="w-full h-[350px] rounded-2xl border border-slate-850/60 bg-[#0d1527]/20 border-dashed border-slate-700/50 flex flex-col items-center justify-center text-center p-6">
                      <Compass className="h-12 w-12 text-slate-600 mb-3" />
                      <p className="text-slate-400 text-sm">Select an active shipment from the list to view its live geolocated progress details.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Bottom Section: Recent completions and Monthly stat timelines */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="glass-panel rounded-3xl p-6 space-y-4">
                <h3 className="font-bold text-white text-lg flex items-center">
                  <BarChart3 className="mr-2 h-5 w-5 text-indigo-400" />
                  Monthly Shipments Volume
                </h3>
                <div className="space-y-3">
                  {cumulativeStats?.monthly_stats.length === 0 ? (
                    <p className="text-slate-500 text-sm">No monthly data available.</p>
                  ) : (
                    cumulativeStats?.monthly_stats.map((m, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm">
                        <span className="text-slate-400 font-semibold">{m.month}</span>
                        <div className="flex-1 mx-4 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500" style={{ width: `${Math.min(m.count * 10, 100)}%` }} />
                        </div>
                        <span className="text-white font-bold">{m.count} bookings</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="glass-panel rounded-3xl p-6 space-y-4">
                <h3 className="font-bold text-white text-lg flex items-center">
                  <CheckCircle2 className="mr-2 h-5 w-5 text-indigo-400" />
                  Recent Completed Deliveries
                </h3>
                <div className="divide-y divide-slate-800">
                  {cumulativeStats?.recent_deliveries.length === 0 ? (
                    <p className="text-slate-500 text-sm italic pt-2">No completed deliveries logged yet.</p>
                  ) : (
                    cumulativeStats?.recent_deliveries.map((r, idx) => (
                      <div key={idx} className="py-3 flex justify-between items-center text-sm">
                        <div>
                          <p className="font-bold text-white">{r.receiver_name}</p>
                          <span className="text-xs text-slate-500 font-mono">{r.tracking_number}</span>
                        </div>
                        <span className="text-slate-400 text-xs">
                          {r.delivered_at ? new Date(r.delivered_at).toLocaleTimeString() : ''}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
      {/* Route Preview Modal */}
      {showPreviewModal && previewData && (
        <div className="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center p-6 overflow-y-auto" style={{ zIndex: 9999 }}>
          <div className="w-full max-w-5xl bg-[#0b0f19] border border-slate-800/80 rounded-3xl p-6 relative shadow-2xl flex flex-col space-y-6">
            
            {/* Modal Header */}
            <div className="flex justify-between items-center border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400">
                  <Route className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">TSP Route Optimization Preview</h3>
                  <p className="text-xs text-slate-400">Heuristic 2-opt search compared to original booking sequence</p>
                </div>
              </div>
              <button 
                onClick={() => { setShowPreviewModal(false); setPreviewData(null); }}
                className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-xl transition cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              
              {/* Map Column */}
              <div className="lg:col-span-3 flex flex-col space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                  <Compass className="mr-1.5 h-4 w-4 text-indigo-400" />
                  Route Navigation Map
                </span>
                <div 
                  id="preview-map" 
                  className="w-full h-[400px] rounded-2xl border border-slate-800 overflow-hidden"
                  style={{ zIndex: 1 }}
                />
                <div className="flex items-center justify-center space-x-6 text-xs text-slate-400 bg-slate-900/50 py-2 rounded-xl border border-slate-800/40">
                  <div className="flex items-center space-x-1.5">
                    <span className="w-3.5 h-1 border-t-2 border-dashed border-red-400 inline-block"></span>
                    <span>Original Order Path</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-3.5 h-1 bg-emerald-500 inline-block rounded-full"></span>
                    <span>Optimized Sequence Path</span>
                  </div>
                </div>
              </div>

              {/* Stats & Controls Column */}
              <div className="lg:col-span-2 flex flex-col justify-between space-y-6">
                
                {/* Savings stats card */}
                <div className="space-y-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
                    <BarChart3 className="mr-1.5 h-4 w-4 text-indigo-400" />
                    Optimizer Efficiency Analytics
                  </span>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-4">
                      <span className="text-[10px] uppercase font-bold text-slate-500">Normal Distance</span>
                      <p className="text-lg font-extrabold text-slate-300 mt-0.5">
                        {(previewData.metrics.original_distance_meters / 1000).toFixed(2)} km
                      </p>
                    </div>
                    <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-2xl p-4 relative overflow-hidden group">
                      <div className="absolute -right-3 -bottom-3 text-emerald-500/5 transition-transform duration-500 group-hover:scale-110">
                        <Route className="h-16 w-16" />
                      </div>
                      <span className="text-[10px] uppercase font-bold text-emerald-500">Optimized Distance</span>
                      <p className="text-lg font-extrabold text-emerald-400 mt-0.5">
                        {(previewData.metrics.optimized_distance_meters / 1000).toFixed(2)} km
                      </p>
                      <span className="text-xs font-semibold text-emerald-400/90 inline-block bg-emerald-500/10 px-2 py-0.5 rounded-full mt-1.5">
                        Save {previewData.metrics.distance_savings_percent}%
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-4">
                      <span className="text-[10px] uppercase font-bold text-slate-500">Normal Duration</span>
                      <p className="text-lg font-extrabold text-slate-300 mt-0.5">
                        {Math.round(previewData.metrics.original_duration_seconds / 60)} mins
                      </p>
                    </div>
                    <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-2xl p-4 relative overflow-hidden group">
                      <div className="absolute -right-3 -bottom-3 text-emerald-500/5 transition-transform duration-500 group-hover:scale-110">
                        <Clock className="h-16 w-16" />
                      </div>
                      <span className="text-[10px] uppercase font-bold text-emerald-500">Optimized Duration</span>
                      <p className="text-lg font-extrabold text-emerald-400 mt-0.5">
                        {Math.round(previewData.metrics.optimized_duration_seconds / 60)} mins
                      </p>
                      <span className="text-xs font-semibold text-emerald-400/90 inline-block bg-emerald-500/10 px-2 py-0.5 rounded-full mt-1.5">
                        Save {previewData.metrics.duration_savings_percent}%
                      </span>
                    </div>
                  </div>

                  {/* Route Sequence Preview list */}
                  <div className="border border-slate-800 rounded-2xl p-4 bg-[#080d1a]/60 space-y-3">
                    <span className="text-[10px] uppercase font-bold text-slate-500 flex items-center">
                      <Info className="mr-1 h-3 w-3 text-slate-400" />
                      Dispatch sequence order
                    </span>
                    <div className="max-h-36 overflow-y-auto space-y-2 pr-1 divide-y divide-slate-800/50">
                      {previewData.stops.map((stop, sIdx) => {
                        // Find this stop's optimized index
                        const optStopSeq = previewData.optimized_sequence.indexOf(sIdx + 1);
                        return (
                          <div key={stop.shipment_id} className="pt-2 flex justify-between items-center text-xs">
                            <span className="text-slate-300 truncate max-w-[140px] font-bold">{stop.recipient_name}</span>
                            <div className="flex items-center space-x-2 shrink-0">
                              <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700/60 px-1.5 py-0.5 rounded">
                                Original #{sIdx + 1}
                              </span>
                              <span className="text-slate-500 font-bold">➔</span>
                              <span className="text-[10px] bg-emerald-950/40 text-emerald-400 border border-emerald-500/25 px-1.5 py-0.5 rounded font-extrabold">
                                Optimized #{optStopSeq}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Confirm Dispatch Actions */}
                <div className="space-y-3 pt-4">
                  <div className="p-3 bg-slate-900 border border-slate-800/80 rounded-2xl flex items-center justify-between text-sm">
                    <span className="text-slate-400">Assigned Courier:</span>
                    <span className="text-white font-extrabold">
                      {agents.find(a => a.id === parseInt(selectedAgentId))?.name || `Agent ID: ${selectedAgentId}`}
                    </span>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={() => { setShowPreviewModal(false); setPreviewData(null); }}
                      className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl border border-slate-700 transition cursor-pointer text-center text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmDispatch}
                      disabled={routingLoading}
                      className="flex-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold rounded-xl shadow-lg shadow-emerald-600/10 transition flex items-center justify-center cursor-pointer text-sm"
                    >
                      {routingLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Dispatching...
                        </>
                      ) : (
                        'Confirm & Dispatch'
                      )}
                    </button>
                  </div>
                </div>

              </div>

            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;

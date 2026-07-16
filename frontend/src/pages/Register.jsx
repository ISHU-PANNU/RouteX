import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, Lock, Mail, Phone, Loader2, ShieldCheck, Compass } from 'lucide-react';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Customer');
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [btnLoading, setBtnLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!name || !email || !phone || !password) {
      setError('Please fill in all registration fields.');
      return;
    }
    
    // E.164 phone check regex pattern
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    if (!phoneRegex.test(phone)) {
      setError('Invalid contact phone format. Use E.164 standard (e.g. +15550199).');
      return;
    }
    
    setBtnLoading(true);
    try {
      await register(name, email, password, phone, role);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError(err || 'Registration failed. Try checking input values.');
    } finally {
      setBtnLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden bg-[#0b0f19]">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md z-10">
        {/* Brand identity header */}
        <div className="flex flex-col items-center mb-6">
          <div className="p-3 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-2xl shadow-lg shadow-indigo-500/25 mb-4">
            <Compass className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">
            Route<span className="text-indigo-400">X</span>
          </h1>
          <p className="text-slate-400 text-sm text-center">Create your account to start shipping and tracking</p>
        </div>

        <div className="glass-panel rounded-3xl p-8 shadow-2xl relative">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">Get Started</h2>

          {success ? (
            <div className="p-6 bg-emerald-950/40 border border-emerald-500/30 rounded-2xl text-center text-emerald-400">
              <ShieldCheck className="h-12 w-12 mx-auto mb-3 text-emerald-400 animate-bounce" />
              <h3 className="text-lg font-bold mb-1">Registration Successful!</h3>
              <p className="text-sm text-slate-300">Redirecting to Sign In portal...</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-6 p-4 bg-red-950/40 border border-red-500/30 rounded-xl text-red-400 text-sm text-center">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Full Name</label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                      <User className="h-5 w-5" />
                    </span>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Sarah Jenkins"
                      className="w-full pl-10 pr-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                      disabled={btnLoading}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Email Address</label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                      <Mail className="h-5 w-5" />
                    </span>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="sarah.jenkins@example.com"
                      className="w-full pl-10 pr-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                      disabled={btnLoading}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Phone Number (E.164)</label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                      <Phone className="h-5 w-5" />
                    </span>
                    <input
                      type="text"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+15550198"
                      className="w-full pl-10 pr-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                      disabled={btnLoading}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Password</label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                      <Lock className="h-5 w-5" />
                    </span>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-10 pr-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                      disabled={btnLoading}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 text-sm font-semibold mb-2">Account Role Type</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0d1527]/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                    disabled={btnLoading}
                  >
                    <option value="Customer">Customer (Send / Track parcels)</option>
                    <option value="DeliveryAgent">Delivery Agent (Courier / Roster navigation)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full py-3 px-4 mt-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 hover:from-indigo-600 hover:to-purple-700 hover:shadow-indigo-500/30 active:scale-[0.98] transition flex items-center justify-center cursor-pointer"
                  disabled={btnLoading}
                >
                  {btnLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Creating Account...
                    </>
                  ) : (
                    'Register Account'
                  )}
                </button>
              </form>
            </>
          )}

          <div className="mt-8 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;

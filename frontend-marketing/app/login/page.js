"use client";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
import { useState } from "react";

const page = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Redirect to Django allauth login with credentials
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/accounts/login/';

      const csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      // Get CSRF token from cookie
      const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1] || '';
      csrfInput.value = csrfToken;
      form.appendChild(csrfInput);

      const emailInput = document.createElement('input');
      emailInput.type = 'hidden';
      emailInput.name = 'login';
      emailInput.value = email;
      form.appendChild(emailInput);

      const passwordInput = document.createElement('input');
      passwordInput.type = 'hidden';
      passwordInput.name = 'password';
      passwordInput.value = password;
      form.appendChild(passwordInput);

      const nextInput = document.createElement('input');
      nextInput.type = 'hidden';
      nextInput.name = 'next';
      nextInput.value = '/dashboard/';
      form.appendChild(nextInput);

      document.body.appendChild(form);
      form.submit();
    } catch (err) {
      setError("An error occurred. Please try again.");
      setLoading(false);
    }
  };

  return (
    <PlaxLayout bg={false}>
      {/* banner */}
      <div className="mil-banner mil-banner-inner mil-dissolve">
        <div className="container">
          <div className="row align-items-center justify-content-center">
            <div className="col-xl-6">
              <div className="mil-banner-text mil-text-center">
                <h1 className="mil-mb-30">Welcome Back</h1>
                <p className="mil-text-m mil-soft mil-mb-60">
                  Sign in to access your Aureon dashboard
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}

      {/* login form */}
      <div className="mil-p-120-90">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-5 col-lg-6 col-md-8">
              <div className="mil-out-frame mil-p-60">
                <form onSubmit={handleSubmit}>
                  {error && (
                    <div className="mil-mb-30" style={{
                      padding: '15px',
                      background: '#fee2e2',
                      borderRadius: '8px',
                      color: '#dc2626'
                    }}>
                      {error}
                    </div>
                  )}

                  <div className="mil-mb-30">
                    <label className="mil-text-m mil-mb-10" style={{ display: 'block' }}>
                      Email Address
                    </label>
                    <input
                      type="email"
                      className="mil-input"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '15px',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '16px'
                      }}
                    />
                  </div>

                  <div className="mil-mb-30">
                    <label className="mil-text-m mil-mb-10" style={{ display: 'block' }}>
                      Password
                    </label>
                    <input
                      type="password"
                      className="mil-input"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '15px',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '16px'
                      }}
                    />
                  </div>

                  <div className="mil-mb-30" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input type="checkbox" name="remember" />
                      <span className="mil-text-s mil-soft">Remember me</span>
                    </label>
                    <Link href="/accounts/password/reset/" className="mil-text-s mil-accent">
                      Forgot password?
                    </Link>
                  </div>

                  <button
                    type="submit"
                    className="mil-btn mil-btn-border"
                    disabled={loading}
                    style={{ width: '100%', marginBottom: '20px' }}
                  >
                    {loading ? 'Signing in...' : 'Sign In'}
                  </button>

                  <p className="mil-text-s mil-soft mil-text-center">
                    Don't have an account?{' '}
                    <Link href="/accounts/signup/" className="mil-accent">
                      Create one
                    </Link>
                  </p>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* login form end */}
    </PlaxLayout>
  );
};

export default page;

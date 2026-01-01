"use client";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
import { useState } from "react";

const page = () => {
  const [formData, setFormData] = useState({
    email: "",
    password1: "",
    password2: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password1 !== formData.password2) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      // Submit to Django allauth signup
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/accounts/signup/';

      const csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1] || '';
      csrfInput.value = csrfToken;
      form.appendChild(csrfInput);

      const emailInput = document.createElement('input');
      emailInput.type = 'hidden';
      emailInput.name = 'email';
      emailInput.value = formData.email;
      form.appendChild(emailInput);

      const password1Input = document.createElement('input');
      password1Input.type = 'hidden';
      password1Input.name = 'password1';
      password1Input.value = formData.password1;
      form.appendChild(password1Input);

      const password2Input = document.createElement('input');
      password2Input.type = 'hidden';
      password2Input.name = 'password2';
      password2Input.value = formData.password2;
      form.appendChild(password2Input);

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
                <h1 className="mil-mb-30">Create Your Account</h1>
                <p className="mil-text-m mil-soft mil-mb-60">
                  Start your 14-day free trial. No credit card required.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}

      {/* signup form */}
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
                      name="email"
                      className="mil-input"
                      placeholder="you@example.com"
                      value={formData.email}
                      onChange={handleChange}
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
                      name="password1"
                      className="mil-input"
                      placeholder="Create a password"
                      value={formData.password1}
                      onChange={handleChange}
                      required
                      minLength={8}
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
                      Confirm Password
                    </label>
                    <input
                      type="password"
                      name="password2"
                      className="mil-input"
                      placeholder="Confirm your password"
                      value={formData.password2}
                      onChange={handleChange}
                      required
                      minLength={8}
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
                    <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                      <input type="checkbox" name="terms" required style={{ marginTop: '4px' }} />
                      <span className="mil-text-s mil-soft">
                        I agree to the{' '}
                        <Link href="/terms-of-service/" className="mil-accent">Terms of Service</Link>
                        {' '}and{' '}
                        <Link href="/privacy-policy/" className="mil-accent">Privacy Policy</Link>
                      </span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    className="mil-btn mil-btn-border"
                    disabled={loading}
                    style={{ width: '100%', marginBottom: '20px' }}
                  >
                    {loading ? 'Creating account...' : 'Create Account'}
                  </button>

                  <p className="mil-text-s mil-soft mil-text-center">
                    Already have an account?{' '}
                    <Link href="/login/" className="mil-accent">
                      Sign in
                    </Link>
                  </p>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* signup form end */}
    </PlaxLayout>
  );
};

export default page;

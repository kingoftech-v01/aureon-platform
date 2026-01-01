"use client";
import { PageBanner } from "@/components/Banner";
import { CallToAction2 } from "@/components/CallToAction";
import PlaxLayout from "@/layouts/PlaxLayout";
import { useState, useEffect } from "react";
import { marketingApi } from "@/lib/api";

const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    message: '',
    consent: false,
  });
  const [status, setStatus] = useState({ type: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState({
    address: 'Montreal, Quebec, Canada',
    phone: '+1 (514) 555-0123',
    email: 'hello@aureon.io',
  });

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await marketingApi.getSiteSettings();
        if (response && response.data) {
          setSettings(prev => ({
            ...prev,
            ...response.data,
          }));
        }
      } catch (error) {
        console.error("Failed to fetch settings:", error);
      }
    };
    fetchSettings();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.consent) {
      setStatus({ type: 'error', message: 'Please agree to the data collection policy.' });
      return;
    }

    setLoading(true);
    setStatus({ type: '', message: '' });

    try {
      const response = await marketingApi.submitContact({
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        message: formData.message,
      });

      if (response && !response.error) {
        setStatus({ type: 'success', message: 'Thanks, your message is sent successfully!' });
        setFormData({ name: '', email: '', phone: '', message: '', consent: false });
      } else {
        setStatus({ type: 'error', message: response?.error || 'Failed to send message. Please try again.' });
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'Failed to send message. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PlaxLayout bg={false}>
      <PageBanner
        pageName="Contact us"
        title="Connect with Us: We are Here to Help You"
      />

      {/* contact */}
      <div className="mil-blog-list mil-p-0-160">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-9">
              <form onSubmit={handleSubmit}>
                <div className="row">
                  <div className="col-md-6 mil-mb-30">
                    <input
                      className="mil-input mil-up"
                      type="text"
                      placeholder="Name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      required
                    />
                  </div>
                  <div className="col-md-6 mil-mb-30">
                    <input
                      className="mil-input mil-up"
                      type="email"
                      placeholder="Email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                    />
                  </div>
                  <div className="col-xl-12 mil-mb-30">
                    <input
                      className="mil-input mil-up"
                      type="tel"
                      placeholder="Telephone number"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="col-xl-12 mil-mb-30 ">
                    <textarea
                      cols={30}
                      rows={10}
                      className="mil-up"
                      placeholder="Message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      required
                    />
                  </div>
                </div>
                <div className="mil-checkbox-frame mil-mb-30 mil-up">
                  <div className="mil-checkbox">
                    <input
                      type="checkbox"
                      id="checkbox"
                      name="consent"
                      checked={formData.consent}
                      onChange={handleChange}
                    />
                    <label htmlFor="checkbox" />
                  </div>
                  <p className="mil-text-xs mil-soft">
                    I agree that the data submitted, collected and stored *
                  </p>
                </div>
                <div className="mil-up">
                  <button
                    type="submit"
                    className="mil-btn mil-m"
                    disabled={loading}
                  >
                    {loading ? 'Sending...' : 'Send Message'}
                  </button>
                </div>
              </form>

              {status.type === 'success' && (
                <div className="alert-success" style={{ display: "block", marginTop: 20, padding: 15, background: '#d4edda', borderRadius: 8 }}>
                  <h5 style={{ color: '#155724', margin: 0 }}>{status.message}</h5>
                </div>
              )}

              {status.type === 'error' && (
                <div className="alert-danger" style={{ display: "block", marginTop: 20, padding: 15, background: '#f8d7da', borderRadius: 8 }}>
                  <h5 style={{ color: '#721c24', margin: 0 }}>{status.message}</h5>
                </div>
              )}

              <div className="mil-p-160-0">
                <h5 className="mil-mb-30 mil-up">
                  We are available on the following channels:
                </h5>
                <p className="mil-text-m mil-soft mil-mb-10 mil-up">
                  Address: {settings.address}
                </p>
                <p className="mil-text-m mil-soft mil-mb-10 mil-up">
                  Telephone: {settings.phone}
                </p>
                <p className="mil-text-m mil-soft mil-up">
                  Email: {settings.email}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* contact end */}
      {/* call to action */}
      <CallToAction2 />
      {/* call to action end */}
    </PlaxLayout>
  );
};
export default ContactPage;

/**
 * About Page
 * Aureon by Rhematek Solutions
 *
 * Company information, mission, team, and values
 */

import React from 'react';
import { Link } from 'react-router-dom';

const About: React.FC = () => {
  const values = [
    {
      title: 'Transparency',
      description: 'We believe in honest, clear communication. From our pricing to our product roadmap, transparency guides everything we do.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
    {
      title: 'Automation First',
      description: 'Manual work slows businesses down. We automate the repetitive so you can focus on what matters most: your clients.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
      ),
    },
    {
      title: 'Security & Trust',
      description: 'Your financial data deserves the highest protection. We use bank-grade encryption and maintain SOC 2-type controls.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      ),
    },
    {
      title: 'Customer Obsession',
      description: 'Every feature we build starts with a customer need. We listen, iterate, and deliver solutions that make a real difference.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
        </svg>
      ),
    },
  ];

  const teamMembers = [
    {
      name: 'Benjamin Ejim',
      role: 'Founder & CEO',
      initials: 'BE',
      bio: 'Passionate about building tools that empower service professionals to grow their businesses.',
    },
    {
      name: 'Amara Okafor',
      role: 'Head of Product',
      initials: 'AO',
      bio: 'Product leader focused on creating intuitive experiences that streamline complex financial workflows.',
    },
    {
      name: 'David Kim',
      role: 'Head of Engineering',
      initials: 'DK',
      bio: 'Full-stack engineer committed to building reliable, scalable, and secure platform infrastructure.',
    },
    {
      name: 'Sarah Mitchell',
      role: 'Head of Customer Success',
      initials: 'SM',
      bio: 'Dedicated to helping every Aureon customer get the most value from the platform.',
    },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-9 h-9 bg-gradient-to-br from-primary-500 via-primary-600 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">Aureon</span>
            </Link>

            <div className="flex items-center space-x-4">
              <Link to="/" className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                Back to Home
              </Link>
              <Link to="/auth/login" className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                Login
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white leading-tight">
            Empowering businesses to{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-accent-500">
              get paid faster
            </span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Aureon was born from a simple frustration: managing contracts, invoices, and payments shouldn't be this hard.
            We built the platform we wished existed when running our own service businesses.
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">Our Mission</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                We are on a mission to eliminate the administrative burden that holds service professionals back.
                Every hour spent chasing payments, drafting contracts, or reconciling invoices is an hour not spent delivering value to clients.
              </p>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Aureon automates the entire client financial workflow -- from lead capture and proposal generation to contract e-signatures,
                automated invoicing, payment collection, and receipt delivery. All in one unified platform.
              </p>
              <p className="text-gray-600 dark:text-gray-400">
                Built by Rhematek Solutions, Aureon serves freelancers, consultants, agencies, and service-based businesses
                in over 150 countries worldwide.
              </p>
            </div>
            <div className="bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-900/20 dark:to-accent-900/20 rounded-3xl p-8 flex items-center justify-center min-h-[300px]">
              <div className="text-center">
                <div className="w-24 h-24 bg-gradient-to-br from-primary-500 to-accent-500 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary-500/25">
                  <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">150+ Countries</p>
                <p className="text-gray-600 dark:text-gray-400">Trusted globally</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Our Values
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              The principles that guide how we build, how we serve, and how we grow.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value) => (
              <div
                key={value.title}
                className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700 transition-all duration-200 hover:shadow-lg"
              >
                <div className="w-14 h-14 bg-gradient-to-br from-primary-100 to-primary-50 dark:from-primary-900/30 dark:to-primary-800/20 rounded-xl flex items-center justify-center text-primary-600 dark:text-primary-400 mb-4">
                  {value.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {value.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Meet the Team
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              A passionate team dedicated to building the best financial workflow platform.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {teamMembers.map((member) => (
              <div
                key={member.name}
                className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 text-center"
              >
                <div className="w-20 h-20 bg-gradient-to-br from-primary-400 to-accent-500 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4 shadow-lg shadow-primary-500/20">
                  {member.initials}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {member.name}
                </h3>
                <p className="text-sm text-primary-600 dark:text-primary-400 font-medium mb-3">
                  {member.role}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {member.bio}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            Ready to join the future of business finance?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Start your free trial today and see how Aureon can transform your workflow.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/auth/register"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-2xl shadow-xl shadow-primary-500/25 transition-all duration-200"
            >
              Start Free Trial
            </Link>
            <Link
              to="/contact"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-2xl transition-colors"
            >
              Contact Us
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">A</span>
              </div>
              <span className="text-lg font-bold text-gray-900 dark:text-white">Aureon</span>
            </div>

            <div className="flex items-center space-x-8 text-sm text-gray-600 dark:text-gray-400">
              <Link to="/privacy" className="hover:text-gray-900 dark:hover:text-white transition-colors">Privacy</Link>
              <Link to="/terms" className="hover:text-gray-900 dark:hover:text-white transition-colors">Terms</Link>
              <Link to="/contact" className="hover:text-gray-900 dark:hover:text-white transition-colors">Support</Link>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-500 mt-4 md:mt-0">
              2026 Aureon by Rhematek Solutions. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default About;

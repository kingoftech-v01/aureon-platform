"use client";
import { CallToAction2 } from "@/components/CallToAction";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";

const teamMembers = [
  {
    name: "Isabella Haugen",
    role: "CEO & Founder",
    image: "img/inner-pages/team/1.png",
    bio: "Visionary leader with 15+ years in fintech innovation."
  },
  {
    name: "Alexandr Dahl",
    role: "Chief Technology Officer (CTO)",
    image: "img/inner-pages/team/2.png",
    bio: "Tech architect driving our platform's scalability and security."
  },
  {
    name: "Lucia Knutsen",
    role: "Director of Operations (COO)",
    image: "img/inner-pages/team/3.png",
    bio: "Operations expert ensuring seamless customer experiences."
  },
  {
    name: "Carlos Martinez",
    role: "Chief Information Security Officer (CISO)",
    image: "img/inner-pages/team/4.png",
    bio: "Security veteran protecting our users' financial data."
  }
];

const page = () => {
  return (
    <PlaxLayout bg={false}>
      {/* banner */}
      <div className="mil-banner mil-banner-inner mil-dissolve">
        <div className="container">
          <div className="row align-items-center justify-content-center">
            <div className="col-xl-8">
              <div className="mil-banner-text mil-text-center">
                <div className="mil-text-m mil-mb-20">Our Team</div>
                <h1 className="mil-mb-60">
                  Meet the People Behind Aureon
                </h1>
                <ul className="mil-breadcrumbs mil-pub-info mil-center">
                  <li>
                    <Link href="/">Home</Link>
                  </li>
                  <li>
                    <Link href="/team/">Team</Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}

      {/* intro */}
      <div className="mil-features mil-p-120-80">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-8 mil-text-center mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                A Team United by Innovation
              </h2>
              <p className="mil-text-m mil-soft mil-up">
                Our diverse team brings together expertise from finance, technology,
                and customer success to build the future of financial automation.
              </p>
            </div>
          </div>
        </div>
      </div>
      {/* intro end */}

      {/* team grid */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-visible mil-image mil-p-160-130">
            <div className="row justify-content-center mil-text-center">
              <div className="col-xl-8 mil-mb-80-adaptive-30">
                <h2 className="mil-light mil-up">Leadership Team</h2>
              </div>
            </div>
            <div className="row">
              {teamMembers.map((member, index) => (
                <div key={index} className="col-xl-3 col-md-6 col-sm-6">
                  <div className="mil-team-card mil-mb-30 mil-up">
                    <div className="mil-portrait mil-mb-30">
                      <img src={member.image} alt={member.name} />
                    </div>
                    <h5 className="mil-light mil-mb-15">{member.name}</h5>
                    <p className="mil-text-xs mil-soft mil-mb-15">{member.role}</p>
                    <p className="mil-text-xs mil-soft">{member.bio}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      {/* team grid end */}

      {/* values */}
      <div className="mil-features mil-p-160-80">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-8 mil-text-center mil-mb-60">
              <h2 className="mil-mb-30 mil-up">Our Values</h2>
            </div>
          </div>
          <div className="row">
            <div className="col-xl-4 mil-mb-60">
              <div className="mil-icon-box mil-up">
                <h5 className="mil-mb-20">Innovation First</h5>
                <p className="mil-text-m mil-soft">
                  We continuously push boundaries to deliver cutting-edge solutions
                  that transform how businesses manage their finances.
                </p>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-60">
              <div className="mil-icon-box mil-up">
                <h5 className="mil-mb-20">Customer Success</h5>
                <p className="mil-text-m mil-soft">
                  Your success is our success. We're dedicated to providing
                  exceptional support and features that grow with your business.
                </p>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-60">
              <div className="mil-icon-box mil-up">
                <h5 className="mil-mb-20">Trust & Security</h5>
                <p className="mil-text-m mil-soft">
                  We protect your data with industry-leading security practices
                  and maintain complete transparency in everything we do.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* values end */}

      <CallToAction2 />
    </PlaxLayout>
  );
};

export default page;

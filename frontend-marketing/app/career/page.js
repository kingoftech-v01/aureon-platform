import { PageBanner } from "@/components/Banner";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
const page = () => {
  return (
    <PlaxLayout>
      <PageBanner pageName="Careers" title="Where your Talent Finds a Home" />
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-5 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Be part of our Team of Experts
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Explore exciting opportunities and discover how your career can
                flourish at Plax.
              </p>
              <ul className="mil-list-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Innovation Culture</h5>
                    <p className="mil-text-m mil-soft">
                      At Plax, we foster an environment of constant innovation.
                      Here, your creativity and passion combine to drive
                      industry-leading solutions.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Professional growth</h5>
                    <p className="mil-text-m mil-soft">
                      We offer opportunities for continued professional
                      development. At Plax, you not only work on your job, but
                      on your career. Training, mentoring and significant
                      challenges await you.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <div className="mil-image-frame mil-up">
                <img
                  src="img/inner-pages/6.png"
                  alt="image"
                  className="mil-scale-img"
                  data-value-1={1}
                  data-value-2="1.2"
                />
              </div>
            </div>
          </div>
        </div>
      </div>{" "}
      {/* call to action */}
      <div className="mil-cta mil-p-0-160 mil-up">
        <div className="container">
          <div className="mil-out-frame mil-bg-2">
            <div className="row justify-content-center align-items-center mil-p-160-160">
              <div className="col-xl-7 mil-text-center">
                <h2 className="mil-light mil-mb-30 mil-up">
                  Join our team, where Innovation is our priority
                </h2>
                <p className="mil-text-m mil-light mil-mb-60 mil-up">
                  Join a dedicated, innovative team committed <br />
                  to excellence at every step.
                </p>
                <div className="mil-up">
                  <Link
                    href="register"
                    className="mil-btn mil-md mil-add-arrow"
                  >
                    Register now
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* vacancies */}
      <div className="mil-faq mil-p-0-130">
        <div className="container">
          <div className="mil-text-center">
            <h2 className="mil-mb-60 mil-up">
              Explore Career <br />
              Opportunities at Plax
            </h2>
          </div>
          <div className="mil-vacancie mil-mb-30 mil-up">
            <div className="mil-left">
              <h4 className="mil-mb-30">
                International Business Development Specialist
              </h4>
              <p className="mil-text-m mil-soft mil-mb-30">
                Develop and execute strategies to expand our presence in new
                international markets.
              </p>
              <ul className="mil-tags">
                <li>Business Development</li>
                <li>Office work</li>
                <li>Paris, France</li>
              </ul>
            </div>
            <div className="mil-right mil-up">
              <Link
                href="career-details"
                className="mil-btn mil-m mil-add-arrow"
              >
                See position
              </Link>
            </div>
          </div>
          <div className="mil-vacancie mil-mb-30 mil-up">
            <div className="mil-left">
              <h4 className="mil-mb-30">Frontend Software Engineer</h4>
              <p className="mil-text-m mil-soft mil-mb-30">
                Develop and execute strategies to expand our presence in new
                international markets.
              </p>
              <ul className="mil-tags">
                <li>Business Development</li>
                <li>Office work</li>
                <li>Paris, France</li>
              </ul>
            </div>
            <div className="mil-right mil-up">
              <Link
                href="career-details"
                className="mil-btn mil-m mil-add-arrow"
              >
                See position
              </Link>
            </div>
          </div>
          <div className="mil-vacancie mil-mb-30 mil-up">
            <div className="mil-left">
              <h4 className="mil-mb-30">Financial Data Analyst</h4>
              <p className="mil-text-m mil-soft mil-mb-30">
                Develop and execute strategies to expand our presence in new
                international markets.
              </p>
              <ul className="mil-tags">
                <li>Business Development</li>
                <li>Office work</li>
                <li>Paris, France</li>
              </ul>
            </div>
            <div className="mil-right mil-up">
              <Link
                href="career-details"
                className="mil-btn mil-m mil-add-arrow"
              >
                See position
              </Link>
            </div>
          </div>
          <div className="mil-vacancie mil-mb-30 mil-up">
            <div className="mil-left">
              <h4 className="mil-mb-30">Digital Marketing Specialist</h4>
              <p className="mil-text-m mil-soft mil-mb-30">
                Develop and execute strategies to expand our presence in new
                international markets.
              </p>
              <ul className="mil-tags">
                <li>Business Development</li>
                <li>Office work</li>
                <li>Paris, France</li>
              </ul>
            </div>
            <div className="mil-right mil-up">
              <Link
                href="career-details"
                className="mil-btn mil-m mil-add-arrow"
              >
                See position
              </Link>
            </div>
          </div>
          <div className="mil-vacancie mil-mb-60 mil-up">
            <div className="mil-left">
              <h4 className="mil-mb-30">Information Security Engineer</h4>
              <p className="mil-text-m mil-soft mil-mb-30">
                Develop and execute strategies to expand our presence in new
                international markets.
              </p>
              <ul className="mil-tags">
                <li>Business Development</li>
                <li>Office work</li>
                <li>Paris, France</li>
              </ul>
            </div>
            <div className="mil-right mil-up">
              <Link
                href="career-details"
                className="mil-btn mil-m mil-add-arrow"
              >
                See position
              </Link>
            </div>
          </div>
          <div className="mil-text-center mil-up">
            <a href="#" className="mil-btn mil-m mil-add-arrow">
              Loads more jobs
            </a>
          </div>
        </div>
      </div>
      {/* vacancies end */}
    </PlaxLayout>
  );
};
export default page;

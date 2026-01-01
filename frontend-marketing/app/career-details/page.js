import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
const page = () => {
  return (
    <PlaxLayout>
      {/* banner */}
      <div className="mil-banner mil-banner-inner mil-dissolve">
        <div className="container">
          <div className="row align-items-center justify-content-center">
            <div className="col-xl-8">
              <div className="mil-banner-text mil-text-center">
                <div className="mil-text-m mil-mb-20">Job Information</div>
                <h1 className="mil-mb-60">Frontend Software Engineer</h1>
                <ul className="mil-breadcrumbs mil-pub-info mil-center">
                  <li>
                    <Link href="home-3">Software Engineering</Link>
                  </li>
                  <li>
                    <Link href="about">Office work</Link>
                  </li>
                  <li>
                    <Link href="about">Paris, France</Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}
      {/* vacancie */}
      <div className="mil-blog-list mil-p-0-160">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-9">
              <h4 className="mil-mb-30 mil-up">Description:</h4>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                As a Frontend Software Engineer at Plax, you will be responsible
                for designing, developing and implementing attractive and
                effective user interfaces. You will work closely with backend
                designers and developers to ensure a smooth and enjoyable user
                experience.
              </p>
              <h4 className="mil-mb-30 mil-up">Your homework:</h4>
              <ul className="mil-text-mist mil-text-m mil-soft mil-mb-60">
                <li className="mil-up">
                  Develop interactive and responsive user interfaces.
                </li>
                <li className="mil-up">
                  Collaborate with designers to translate designs to code.
                </li>
                <li className="mil-up">
                  Optimize applications to ensure fast and efficient
                  performance.
                </li>
                <li className="mil-up">
                  Collaborate with the backend team to integrate
                  functionalities.
                </li>
                <li className="mil-up">
                  Collaborate with the backend team to integrate
                  functionalities.
                </li>
              </ul>
              <h4 className="mil-mb-30 mil-up">Requirements:</h4>
              <ul className="mil-text-mist mil-check mil-text-m mil-soft mil-mb-60">
                <li className="mil-up">
                  Proven experience in frontend software development.
                </li>
                <li className="mil-up">
                  Solid knowledge of HTML, CSS and JavaScript.
                </li>
                <li className="mil-up">
                  Experience in frontend frameworks such as React or Angular.
                </li>
                <li className="mil-up">
                  Ability to work in a collaborative and agile environment.
                </li>
                <li className="mil-up">
                  Passion for creating exceptional user experiences.
                </li>
              </ul>
              <h4 className="mil-mb-30 mil-up">Profile:</h4>
              <p className="mil-text-m mil-soft mil-up mil-mb-60">
                We are looking for an engineer passionate about frontend
                technology, with skills to transform creative designs into
                captivating user experiences. If you are passionate about
                innovation, collaboration and creating quality products, we want
                to meet you!
              </p>
              <div className="mil-up">
                <Link
                  href="contact"
                  className="mil-btn mil-m mil-add-arrow mil-add-arrow"
                >
                  Apply for this position
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* vacancie end */}
    </PlaxLayout>
  );
};
export default page;
